import os
import sqlite3
import urllib.parse
from flask import Flask, render_template, request, abort, redirect, url_for

app = Flask(__name__)

# Database path
DB_PATH = 'emails.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def sanitize_label(label):
    return ' '.join(label.split())

@app.route('/')
def index():
    conn = get_db_connection()
    labels = conn.execute('SELECT DISTINCT label FROM labels WHERE parent_label IS NULL ORDER BY label').fetchall()
    conn.close()
    return render_template('index.html', labels=labels)

@app.route('/label/<path:label>')
def view_label(label):
    sanitized_label = sanitize_label(urllib.parse.unquote(label))
    conn = get_db_connection()
    emails = conn.execute('''SELECT DISTINCT e.id, e.subject, e.sender, e.date 
                             FROM emails e
                             JOIN labels l ON e.id = l.email_id
                             WHERE l.label = ?
                             ORDER BY e.date DESC''', (sanitized_label,)).fetchall()
    sublabels = conn.execute('SELECT DISTINCT label FROM labels WHERE parent_label = ?', (sanitized_label,)).fetchall()
    parent_label = conn.execute('SELECT DISTINCT parent_label FROM labels WHERE label = ?', (sanitized_label,)).fetchone()
    conn.close()
    return render_template('label.html', label=sanitized_label, emails=emails, sublabels=sublabels, parent_label=parent_label)

@app.route('/email/<email_id>')
def view_email(email_id):
    conn = get_db_connection()
    email = conn.execute('SELECT * FROM emails WHERE id = ?', (email_id,)).fetchone()
    labels = conn.execute('SELECT label FROM labels WHERE email_id = ?', (email_id,)).fetchall()
    conn.close()
    if email is None:
        abort(404)
    return render_template('email.html', email=email, labels=labels)

@app.route('/delete/<email_id>', methods=['POST'])
def delete_email(email_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM emails WHERE id = ?', (email_id,))
    conn.execute('DELETE FROM labels WHERE email_id = ?', (email_id,))
    conn.commit()
    conn.close()
    return redirect(request.referrer or url_for('index'))

@app.route('/search')
def search():
    query = request.args.get('q', '')
    conn = get_db_connection()
    emails = conn.execute('''SELECT DISTINCT e.id, e.subject, e.sender, e.date, l.label
                             FROM emails e
                             LEFT JOIN labels l ON e.id = l.email_id
                             WHERE e.subject LIKE ? OR e.sender LIKE ? OR e.content LIKE ?
                             ORDER BY e.date DESC''', 
                          (f'%{query}%', f'%{query}%', f'%{query}%')).fetchall()
    conn.close()
    return render_template('search.html', emails=emails, query=query)

@app.template_filter('urlencode')
def urlencode_filter(s):
    return urllib.parse.quote(s)

if __name__ == '__main__':
    app.run(debug=True)