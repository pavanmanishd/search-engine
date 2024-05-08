import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from indexer import index_document, reverse_index, create_tables
from queue import Queue
import threading

load_dotenv()

base_url = "https://react.dev"
# Queue to store links to be crawled
links_to_crawl = Queue()
links_to_crawl.put(base_url)

# PostgreSQL connection details
host = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = 5432
# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')


def save_to_database(title, url, text):
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO Documents (url, title, content) VALUES (%s, %s, %s) RETURNING id", (url, title, text))
        document_id = cur.fetchone()[0]
        conn.commit()
        conn.close()
        return document_id
    except psycopg2.Error as e:
        logging.error(f"Error saving data to database: {e}")

def process_link(link, visited_links, base_url):
    try:
        response = requests.get(link)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string
        # Extract the main article text
        text = '\n'.join([p.get_text() for p in soup.find_all('p')])
        
        # Save the document to the database
        document_id = save_to_database(title, link, text)
        
        # Index the document
        index_document(document_id, text)

        logging.info(f"Title: {title}")
        logging.info(f"URL: {link}")
        logging.info(f"Text Length: {len(str(text))}")

        # Mark the link as visited
        visited_links.add(link)

        # Extract all links from the page
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            # Remove "/" from the end of the URL
            href = href.rstrip("/")
            # Remove the fragment part of the URL
            href = href.split("#")[0]
            # Check if the link belongs to the same domain and has not been visited yet
            parsed_href = urlparse(href)
            # print(parsed_href)
            if parsed_href.netloc == "" and (base_url+href) not in visited_links and (base_url+href) not in links_to_crawl.queue and href.startswith("/"):
                # Convert relative links to absolute links
                if not parsed_href.scheme:
                    href = base_url + href
                links_to_crawl.put(href)
                print("put", href)

    except (requests.exceptions.RequestException, AttributeError, psycopg2.Error) as e:
        logging.error(f"Error processing {link}: {e}")

def crawl_and_index(base_url):
    visited_links = set()
    threads = []

    while True:
        if len(threads) >= 10:
            for thread in threads:
                thread.join()
            threads = []
        if links_to_crawl.empty() and len(threads) == 0:
            break

        if links_to_crawl.empty():
            continue

        link = links_to_crawl.get()

        if link in visited_links:
            continue

        logging.info(f"Crawling: {link}")

        # Create and start a thread for crawling
        thread = threading.Thread(target=process_link, args=(link, visited_links, base_url))
        thread.start()
        threads.append(thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

    # Reverse index
    reverse_index()

if __name__ == "__main__":
    create_tables()
    crawl_and_index(base_url)
