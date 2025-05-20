import sys
import os
import scrapy
import re
import json
from bs4 import BeautifulSoup
from scrapy.crawler import CrawlerProcess
import uuid
import time
from urllib.parse import urlparse

# 🛠️ Fix import path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import insert_data, initialize_database

# 🛡️ Setup Proxy
os.environ['http_proxy'] = 'http://127.0.0.1:8118'
os.environ['https_proxy'] = 'http://127.0.0.1:8118'

# 🚀 Read URL from argument
if len(sys.argv) < 2:
    print("❌ ERROR: Please provide a starting .onion URL as an argument.\nExample:\n  python3 crawler/decimal_crawler.py http://example.onion/")
    sys.exit(1)

start_url = sys.argv[1].strip()

# 🌎 Track visited URLs
visited_urls = set()
pages_scraped = 0

# 📄 Load keywords from keywords.json
def load_keywords():
    try:
        with open('keywords.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ ERROR loading keywords.json: {e}")
        return []

keywords_list = load_keywords()

def generate_run_id():
    """Generate a unique run_id using UUID and timestamp"""
    return str(uuid.uuid4()) + "_" + str(int(time.time()))

class DecimalCrawlerSpider(scrapy.Spider):
    name = "decimal_crawler"

    custom_settings = {
        'DOWNLOAD_DELAY': 1.5,
        'RETRY_TIMES': 5,
        'HTTPPROXY_ENABLED': True,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
        'LOG_LEVEL': 'WARNING',
        'REQUEST_FINGERPRINTER_IMPLEMENTATION': '2.7'
    }

    def __init__(self, *args, **kwargs):
        super(DecimalCrawlerSpider, self).__init__(*args, **kwargs)
        initialize_database()
        self.start_urls = [start_url]
        self.run_id = generate_run_id()
        print(f"🚀 Starting crawl with run ID: {self.run_id}")

    def parse(self, response):
        global visited_urls, pages_scraped

        url = response.url

        if url in visited_urls:
            return
        visited_urls.add(url)

        print(f"Processing URL: {url}")

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string.strip() if soup.title else 'No Title'
        text = soup.get_text()

        emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}', text)
        bitcoin_addresses = re.findall(r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b', text)
        pgp_keys = re.findall(r'-----BEGIN PGP PUBLIC KEY BLOCK-----.*?-----END PGP PUBLIC KEY BLOCK-----', text, re.DOTALL)
        matched_keywords = [kw for kw in keywords_list if kw.lower() in text.lower()]

        insert_data(
            url=url,
            title=title,
            email=','.join(emails),
            bitcoin=','.join(bitcoin_addresses),
            pgp_key='\n\n'.join(pgp_keys),
            matched_keywords=','.join(matched_keywords),
            run_id=self.run_id
        )

        pages_scraped += 1
        print(f"✅ [{pages_scraped}] Scraped and saved: {url}")

        if pages_scraped % 10 == 0:
            print(f"💓 Heartbeat: {pages_scraped} pages scraped so far...")

        # 🌐 Process and validate links
        for link in soup.find_all('a', href=True):
            href = link['href'].strip()

            # Skip known bad/malformed link types
            if any(href.startswith(prefix) for prefix in ('javascript:', 'mailto:', '#', 'tel:', 'ftp:', '220:', '//')):
                continue

            # Normalize relative URLs
            if href.startswith("http://") or href.startswith("https://"):
                next_link = href
            elif href.startswith("/"):
                next_link = response.urljoin(href)
            else:
                continue

            # Extra URL structure validation using urlparse
            try:
                parsed = urlparse(next_link)
                if not parsed.scheme or not parsed.netloc:
                    continue
            except Exception as e:
                print(f"⚠️ Skipping malformed URL: {href} — {e}")
                continue

            if next_link not in visited_urls:
                yield scrapy.Request(url=next_link, callback=self.parse)

# 🚀 Entry point
if __name__ == "__main__":
    print("\n🚀 Starting Decimal Crawler...\n")
    process = CrawlerProcess()
    process.crawl(DecimalCrawlerSpider)
    process.start()
