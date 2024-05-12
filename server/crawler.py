import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
from urllib.parse import urlparse
from dotenv import load_dotenv
import os
from indexer import index_document, reverse_index, create_tables
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import time

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
        # Add the link to visited_links regardless of whether it's a redirect or not
        visited_links.add(link)
        if response.status_code == 404:
            logging.error(f"404 Not Found: {link}")
            return
        if response.status_code == 403:
            logging.error(f"403 Forbidden: {link}")
            return
        if response.status_code == 500:
            logging.error(f"500 Internal Server Error: {link}")
            return
        if response.status_code == 503:
            logging.error(f"503 Service Unavailable: {link}")
            return
        while link != response.url:
            logging.info(f"Redirected to {response.url}")
            logging.info(f"Status Code: {response.status_code}")
            logging.info(response.history)
            logging.info(links_to_crawl.qsize())

            link = response.url
            visited_links.add(link)
            logging.info(f"Current URL: {link}")
            response = requests.get(link)

        if response.status_code != 200:
            logging.error(f"Failed to crawl {link}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string
        text = '\n'.join([p.get_text() for p in soup.find_all('p')])
        
        document_id = save_to_database(title, link, text)
        index_document(document_id, text)

        logging.info(f"Title: {title}")
        logging.info(f"URL: {link}")
        logging.info(f"Text Length: {len(str(text))}")

        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            href = href.rstrip("/")
            href = href.split("#")[0]
            parsed_href = urlparse(href)
            if parsed_href.netloc == "" and (base_url + href) not in visited_links and (base_url + href) not in links_to_crawl.queue and href.startswith("/"):
                if not parsed_href.scheme:
                    href = base_url + href
                links_to_crawl.put(href)
                logging.info(f"Added to crawl queue: {href}")

    except (requests.exceptions.RequestException, AttributeError, psycopg2.Error) as e:
        logging.error(f"Error processing {link}: {e}")

def crawl_and_index(base_url):
    visited_links = set()
    threads = []

    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            # Check if there are threads running and the queue is empty
            if len(threads) > 0 or not links_to_crawl.empty():
                # Fill the threads pool if there is space
                while len(threads) < 10 and not links_to_crawl.empty():
                    link = links_to_crawl.get()
                    if link not in visited_links:
                        visited_links.add(link)
                        # Start a new thread for crawling
                        thread = executor.submit(process_link, link, visited_links, base_url)
                        threads.append(thread)

                # Remove completed threads
                for thread in threads:
                    if thread.done():
                        threads.remove(thread)

                # Sleep a short interval to avoid busy-waiting
                time.sleep(0.1)
            else:
                # All threads are completed and queue is empty, break the loop
                break

    # Reverse index
    reverse_index()

# if __name__ == "__main__":
def crawl():
    create_tables()
    crawl_and_index(base_url)
