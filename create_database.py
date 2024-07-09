import os
import re
import sqlite3
import mailbox
import hashlib
import traceback
from email.header import decode_header

# Configuration
MBOX_DIR = 'mbox'
PROCESSED_DIR = 'processed_mbox'
DB_FILE = 'emails.db'

def decode_mime_header(header):
    parts = []
    for part, encoding in decode_header(header):
        if isinstance(part, bytes):
            try:
                parts.append(part.decode(encoding or 'utf-8', errors='replace'))
            except:
                parts.append(part.decode('utf-8', errors='replace'))
        else:
            parts.append(str(part))
    return ''.join(parts)

def clean_label(label):
    """Clean and validate email label."""
    label = decode_mime_header(label)
    label = re.sub(r'=\?[^?]+\?[QB]\?[^?]+\?=', '', label)
    label = re.sub(r'\?=\s*=\?', '', label)
    label = label.replace('_', ' ')
    label = re.sub(r'\s+', ' ', label).strip()
    
    excluded_labels = [
        'Archived', 'Category forums', 'Category personal', 'Category promotions',
        'Category purchases', 'Category travel', 'Category updates', 'Chat',
        'IMAP receipt-handled', 'IMAP=5Freceipt-handled', 'Important', 'Inbox',
        'Opened', 'Sent', 'Starred', 'Unread', 'Category'
    ]

    if any(label.lower().startswith(excluded.lower()) for excluded in excluded_labels):
        return None

    # Exclude labels with non-ASCII characters (including Hebrew)
    if not all(ord(c) < 128 for c in label):
        return None

    return label.strip() if label.strip() else None

def get_email_content(msg):
    """Extract email content from message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() in ["text/plain", "text/html"]:
                return part.get_payload(decode=True).decode(errors='replace')
    else:
        return msg.get_payload(decode=True).decode(errors='replace')
    return ""

def create_database():
    """Create SQLite database and tables."""
    conn = sqlite3.connect(DB_FILE)
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

def process_labels(c, email_id, labels):
    """Process and insert email labels into database."""
    for label_group in labels:
        for label in label_group.split(','):
            cleaned_label = clean_label(label.strip())
            if cleaned_label:
                if '/' in cleaned_label:
                    parts = cleaned_label.split('/')
                    for i in range(1, len(parts) + 1):
                        parent_label = '/'.join(parts[:i-1]) if i > 1 else None
                        current_label = '/'.join(parts[:i])
                        c.execute('INSERT OR IGNORE INTO labels (email_id, label, parent_label) VALUES (?, ?, ?)',
                                  (email_id, current_label, parent_label))
                else:
                    c.execute('INSERT OR IGNORE INTO labels (email_id, label, parent_label) VALUES (?, ?, ?)',
                              (email_id, cleaned_label, None))

def process_mbox(mbox_file, conn):
    """Process a single mbox file and insert data into database."""
    mbox = mailbox.mbox(mbox_file)
    c = conn.cursor()

    for i, message in enumerate(mbox):
        try:
            email_id = hashlib.md5(message.as_bytes()).hexdigest()

            subject = decode_mime_header(message['subject'] or '')
            sender = decode_mime_header(message['from'] or '')
            recipient = decode_mime_header(message['to'] or '')
            date = message['date'] or ''
            content = get_email_content(message)
            content_type = 'text/html' if content and content.strip().startswith('<') else 'text/plain'

            c.execute('''INSERT OR REPLACE INTO emails 
                         (id, subject, sender, recipient, date, content, content_type) 
                         VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (email_id, subject, sender, recipient, date, content, content_type))

            labels = message.get_all('X-Gmail-Labels')
            if labels:
                process_labels(c, email_id, labels)

        except Exception as e:
            print(f"Error processing email {i} in {mbox_file}:")
            print(traceback.format_exc())
            continue

        if i % 1000 == 0:
            print(f"Processed {i} emails from {mbox_file}")
            conn.commit()

    conn.commit()
    print(f"Finished processing {mbox_file}. Total emails processed: {i+1}")

def process_all_mbox_files():
    """Process all mbox files in the MBOX_DIR."""
    conn = create_database()
    
    if not os.path.exists(PROCESSED_DIR):
        os.makedirs(PROCESSED_DIR)

    for filename in os.listdir(MBOX_DIR):
        if filename.endswith('.mbox'):
            mbox_file = os.path.join(MBOX_DIR, filename)
            print(f"Processing {mbox_file}...")
            process_mbox(mbox_file, conn)
            
            # Move processed file
            os.rename(mbox_file, os.path.join(PROCESSED_DIR, filename))
            print(f"Moved {filename} to {PROCESSED_DIR}")

    conn.close()

if __name__ == '__main__':
    process_all_mbox_files()
    print("Database update complete.")