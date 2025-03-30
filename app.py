from flask import Flask, render_template, request, redirect, url_for
import smtplib, sqlite3
from email.mime.text import MIMEText
from datetime import datetime
import uuid

app = Flask(__name__)



def init_db():
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS subscribers (id INTEGER PRIMARY KEY, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS templates (id INTEGER PRIMARY KEY, name TEXT, subject TEXT, body TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS email_logs (
        id TEXT PRIMARY KEY,
        email TEXT,
        subject TEXT,
        opened INTEGER,
        clicked INTEGER,
        sent_at TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')



@app.route('/subscribers', methods=['GET', 'POST'])
def subscribers():
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    if request.method == 'POST':
        email = request.form['email']
        c.execute("INSERT INTO subscribers (email) VALUES (?)", (email,))
        conn.commit()
    c.execute("SELECT * FROM subscribers")
    subs = c.fetchall()
    conn.close()
    return render_template('subscribers.html', subscribers=subs)

@app.route('/templates', methods=['GET', 'POST'])
def templates():
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        body = request.form['body']
        c.execute("INSERT INTO templates (name, subject, body) VALUES (?, ?, ?)", (name, subject, body))
        conn.commit()
    c.execute("SELECT * FROM templates")
    temps = c.fetchall()
    conn.close()
    return render_template('templates.html', templates=temps)

@app.route('/compose', methods=['GET', 'POST'])
def compose():
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    c.execute("SELECT * FROM templates")
    templates = c.fetchall()

    if request.method == 'POST':
        template_id = request.form['template']
        sender = request.form['sender']

        c.execute("SELECT subject, body FROM templates WHERE id = ?", (template_id,))
        subject, body = c.fetchone()

        c.execute("SELECT email FROM subscribers")
        emails = [row[0] for row in c.fetchall()]

        for email in emails:
            email_id = str(uuid.uuid4())
            body_with_tracking = body + f'<img src="{url_for("track_open", email_id=email_id, _external=True)}" width="1" height="1">'
            body_with_tracking += f'<p><a href="{url_for("track_click", email_id=email_id, _external=True)}">Click Here</a></p>'
            send_email(email, subject, body_with_tracking, sender)
            c.execute("INSERT INTO email_logs (id, email, subject, opened, clicked, sent_at) VALUES (?, ?, ?, 0, 0, ?)",
                      (email_id, email, subject, datetime.now().isoformat()))
        conn.commit()

    conn.close()
    return render_template('compose.html', templates=templates)

@app.route('/track/open/<email_id>')
def track_open(email_id):
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    c.execute("UPDATE email_logs SET opened = 1 WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/track/click/<email_id>')
def track_click(email_id):
    conn = sqlite3.connect('email_app.db')
    c = conn.cursor()
    c.execute("UPDATE email_logs SET clicked = 1 WHERE id = ?", (email_id,))
    conn.commit()
    conn.close()
    return redirect('https://example.com')

def send_email(to_email, subject, body, sender_key):
    credentials = {
        "gmail": {
            "email": "yourname@gmail.com",
            "password": "your_gmail_app_password"
        },
        "info": {
            "email": "info@kapasiwin.com",
            "password": "your_info_account_password"
        }
    }

    from_email = credentials[sender_key]["email"]
    password = credentials[sender_key]["password"]

    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, to_email, msg.as_string())

if __name__ == '__main__':
    app.run(debug=True)
