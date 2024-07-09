# gmail_mbox_viewer_py

This is a Flask-based web application that allows users to view and manage emails exported from Gmail mbox files. It provides a simple interface to browse emails by labels, search for specific emails, and delete unwanted messages.

## Directory Structure

```
mail/
│
├── app.py                 # Main Flask application
├── create_database.py     # Script to create and populate the database
├── requirements.txt       # Python dependencies
├── README.md              # This file
│
├── templates/             # HTML templates
│   ├── index.html
│   ├── label.html
│   ├── email.html
│   └── search.html
│
├── static/                # Static files (CSS, JS, etc.)
│   └── styles.css
│
├── mbox/                  # Directory for new mbox files to be processed
│
├── processed_mbox/        # Directory for processed mbox files
│
└── emails.db              # SQLite database (created by create_database.py)
```

## Developer Guide

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/gmail_mbox_viewer_py.git
   cd gmail_mbox_viewer_py
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Place your Gmail mbox files in the `mbox/` directory.

5. Create the database and process mbox files:
   ```
   python create_database.py
   ```

6. Run the Flask application:
   ```
   python app.py
   ```

7. Open a web browser and navigate to `http://localhost:5000`.

### Customization

- To modify the database schema, update the `create_database.py` script and the corresponding queries in `app.py`.
- To change the appearance, edit the HTML templates in the `templates/` directory and the CSS in `static/styles.css`.
- To add new features, modify `app.py` and create new routes and templates as needed.

## User Guide

### Adding New Emails

1. Export your emails from Gmail as mbox files.
2. Place the exported mbox files in the `mbox/` directory.
3. Run `python create_database.py` to process the new files.
4. The processed files will be moved to the `processed_mbox/` directory.

### Viewing Emails

1. On the main page, you'll see a list of email labels.
2. Click on a label to view emails associated with that label.
3. In the label view, you can see sublabels (if any) and a list of emails.
4. Click on an email subject to view the full email content.

### Searching Emails

1. Use the search bar at the top of the main page to search for emails.
2. Enter keywords related to the subject, sender, or content of the email you're looking for.
3. Click the "Search" button to see the results.

### Deleting Emails

1. In the label view or search results, each email has a "Delete" button.
2. Click the "Delete" button and confirm to permanently remove the email from the database.

### Navigation

- Use the "Back to labels" link to return to the main page from any view.
- When viewing an email, you can click on its labels to see other emails with the same label.

## Troubleshooting

- If you encounter issues with label links or missing emails, try recreating the database by running `create_database.py` again.
- Ensure that your mbox files are properly formatted and placed in the `mbox/` directory before processing.
- Check the console output for any error messages when running the application.
- If emails are not showing up after processing, check that the mbox files have been moved to the `processed_mbox/` directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.