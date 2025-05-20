import sqlite3
import os
from uuid import uuid4  # to generate unique run IDs

# Fix path: ensure the correct path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'decimal_scraped_data.db')

def initialize_database():
    """Create the database and scraped_data table if not exists."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scraped_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT,
            title TEXT,
            email TEXT,
            bitcoin TEXT,
            pgp_key TEXT,
            matched_keywords TEXT,
            run_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database initialized and 'scraped_data' table is created/verified.")

def insert_data(url, title, email, bitcoin, pgp_key, matched_keywords, run_id):
    """Insert a single row of scraped data."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO scraped_data (url, title, email, bitcoin, pgp_key, matched_keywords, run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (url, title, email, bitcoin, pgp_key, matched_keywords, run_id))
    conn.commit()
    conn.close()
    print(f"✅ Data inserted: {url}, {title}, {email}, {bitcoin}")

def fetch_all_data(run_id=None):
    """Fetch all records, optionally filtered by run_id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if run_id:
        query = 'SELECT * FROM scraped_data WHERE run_id = ? ORDER BY created_at DESC'
        c.execute(query, (run_id,))
    else:
        query = 'SELECT * FROM scraped_data ORDER BY created_at DESC'
        c.execute(query)
    
    data = c.fetchall()
    conn.close()
    print(f"✅ Fetched data: {len(data)} records")
    return data

def count_total_sites():
    """Return the count of unique sites (URLs) crawled."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT url) FROM scraped_data")
    count = c.fetchone()[0]
    conn.close()
    print(f"✅ Total unique sites crawled: {count}")
    return count

def count_total_alerts():
    """Return total number of rows where matched_keywords are found."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM scraped_data WHERE matched_keywords IS NOT NULL AND matched_keywords != ''")
    count = c.fetchone()[0]
    conn.close()
    print(f"✅ Total alerts found: {count}")
    return count
