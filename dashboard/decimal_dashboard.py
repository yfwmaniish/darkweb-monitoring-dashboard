import sys
import os
import csv
import io
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, Response
from dotenv import load_dotenv

# Fix import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
from models import fetch_all_data, count_total_sites, count_total_alerts

# Load environment variables
load_dotenv()
USERNAME = os.getenv("DASHBOARD_USERNAME")
PASSWORD = os.getenv("DASHBOARD_PASSWORD")

# Flask setup
app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = os.urandom(24)

# ----------------- ROUTES -----------------

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == USERNAME and request.form['password'] == PASSWORD:
            session['logged_in'] = True
            return redirect('/dashboard')
        return render_template('login.html', error="Invalid Credentials.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect('/')

    data = fetch_all_data()
    total_sites = count_total_sites()
    total_alerts = count_total_alerts()

    highlighted_data = []
    for row in data:
        id, url, title, email, bitcoin, pgp_key, keywords, run_id, _ = row  # ignore created_at

        keyword_tags = []
        if keywords:
            for kw in keywords.split(','):
                clean_kw = kw.strip()
                if clean_kw:
                    keyword_tags.append(clean_kw)

        highlighted_data.append({
            'id': id,
            'url': url,
            'title': highlight_keywords(title),
            'email': email if email else '-',
            'bitcoin': bitcoin if bitcoin else '-',
            'pgp_key': '🔑' if pgp_key else '-',
            'keywords': keyword_tags if keyword_tags else ['-']
        })

    return render_template('index.html',
                           data=highlighted_data,
                           total_sites=total_sites,
                           total_alerts=total_alerts)

@app.route('/download_csv')
def download_csv():
    if not session.get('logged_in'):
        return redirect('/')

    data = fetch_all_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'URL', 'Title', 'Email', 'Bitcoin', 'PGP Key', 'Matched Keywords', 'Run ID', 'Timestamp'])

    for row in data:
        id, url, title, email, bitcoin, pgp_key, keywords, run_id, created_at = row
        try:
            formatted_time = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S').strftime('%b %d, %Y %H:%M')
        except Exception:
            formatted_time = created_at
        writer.writerow([id, url, title, email, bitcoin, pgp_key, keywords, run_id, formatted_time])

    output.seek(0)
    return Response(output, mimetype="text/csv",
                    headers={"Content-Disposition": "attachment;filename=darkweb_data.csv"})

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# ----------------- HELPERS -----------------

def highlight_keywords(text):
    if not text:
        return text
    keywords = ['india', 'drugs', 'arms', 'weapons', 'fake id', 'passport', 'bitcoin', 'hack', 'cybercrime', 'ransomware']
    for kw in keywords:
        text = text.replace(kw, f"<span class='highlight'>{kw}</span>")
        text = text.replace(kw.capitalize(), f"<span class='highlight'>{kw.capitalize()}</span>")
    return text

# ----------------- MAIN -----------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
