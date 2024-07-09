
import os
import sqlite3
import mailbox
import email
import hashlib
import shutil
from email.header import decode_header

# Paths
MBOX_DIR = 'mbox'
PROCESSED_DIR = 'processed_mbox'
DB_PATH = 'emails.db'

def decode_header_string(header):
    decoded_parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            decoded_parts.append(part.decode(encoding or 'utf-8', errors='replace'))
        else:
            decoded_parts.append(str(part))
    return ' '.join(decoded_parts)

def get_email_content(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                return part.get_payload(decode=True).decode(errors='replace')
    else:
        return msg.get_payload(decode=True).decode(errors='replace')

def sanitize_label(label):
    return ' '.join(label.split())

def create_database():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS emails
                 (id TEXT PRIMARY KEY, subject TEXT, sender TEXT, recipient TEXT, 
                  date TEXT, content TEXT, content_type TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS labels
                 (email_id TEXT, label TEXT, parent_label TEXT,
                  FOREIGN KEY(email_id) REFERENCES emails(id),
                  PRIMARY KEY(email_id, label))''')
    conn.commit()
    return conn

def process_mbox(mbox_file, conn):
    mbox = mailbox.mbox(mbox_file)
    c = conn.cursor()

    for message in mbox:
        email_id = hashlib.md5(message.as_bytes()).hexdigest()

        subject = decode_header_string(message['subject'] or '')
        sender = decode_header_string(message['from'] or '')
        recipient = decode_header_string(message['to'] or '')
        date = message['date'] or ''
        content = get_email_content(message)
        content_type = 'text/html' if content.strip().startswith('<') else 'text/plain'

        c.execute('''INSERT OR REPLACE INTO emails 
                     (id, subject, sender, recipient, date, content, content_type) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (email_id, subject, sender, recipient, date, content, content_type))

        labels = message.get_all('X-Gmail-Labels')
        if labels:
            label = sanitize_label(labels[0].split(',')[-1].strip())
            
            if '/' in label:
                parent_label, child_label = label.rsplit('/', 1)
                c.execute('INSERT OR IGNORE INTO labels (email_id, label, parent_label) VALUES (?, ?, ?)',
                          (email_id, parent_label, None))
                c.execute('INSERT OR IGNORE INTO labels (email_id, label, parent_label) VALUES (?, ?, ?)',
                          (email_id, label, parent_label))
            else:
                c.execute('INSERT OR IGNORE INTO labels (email_id, label, parent_label) VALUES (?, ?, ?)',
                          (email_id, label, None))

    conn.commit()

def process_all_mbox_files():
    conn = create_database()
    
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    for filename in os.listdir(MBOX_DIR):
        if filename.endswith('.mbox'):
            mbox_file = os.path.join(MBOX_DIR, filename)
            print(f"Processing {mbox_file}...")
            process_mbox(mbox_file, conn)
            
            # Move processed file
            shutil.move(mbox_file, os.path.join(PROCESSED_DIR, filename))
            print(f"Moved {filename} to {PROCESSED_DIR}")

    conn.close()

if __name__ == '__main__':
    process_all_mbox_files()
    print("Database update complete.")