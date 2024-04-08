import requests
from bs4 import BeautifulSoup
import psycopg2
import logging
import time
import random
from dotenv import load_dotenv
import os
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

load_dotenv()
# PostgreSQL connection details
host = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

# Define the starting URL
starting_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

def get_links(url):
    links = []
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a', href=True):
            if link['href'].startswith('/wiki/'):
                links.append("https://en.wikipedia.org" + link['href'])
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting links from {url}: {e}")
    return links

def get_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extract the main article text
        article_text = '\n'.join([p.get_text() for p in soup.find_all('p')])
        return article_text
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting text from {url}: {e}")
        return ""

def get_title(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.title.string
        return title
    except (requests.exceptions.RequestException, AttributeError) as e:
        logging.error(f"Error getting title from {url}: {e}")
        return ""

def save_to_database(title, url, text):
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()
        cur.execute("INSERT INTO wikipedia_pages (title, url, text) VALUES (%s, %s, %s)", (title, url, text))
        conn.commit()
        conn.close()
    except psycopg2.Error as e:
        logging.error(f"Error saving data to database: {e}")

def crawl_page(link):
    logging.info(f"Crawling: {link}")
    try:
        links = get_links(link)
        text = get_text(link)
        title = get_title(link)

        logging.info(f"Saving to database")
        save_to_database(title, link, text)

        logging.info(f"Title: {title}")
        logging.info(f"URL: {link}")
        logging.info(f"Text Length: {len(str(text))}")
        logging.info(f"Extracted links: {len(links)}")
        return links
    except Exception as e:
        logging.error(f"Error processing {link}: {e}")
        return []

def main():
    # Initialize variables
    crawled = set()
    to_crawl = [starting_url]
    count = 0
    max_pages = 1000

    with ThreadPoolExecutor(max_workers=10) as executor:
        while count < max_pages and to_crawl:
            link = to_crawl.pop(0)
            if link in crawled:
                continue
            crawled.add(link)

            try:
                new_links = executor.submit(crawl_page, link).result()
                for l in new_links:
                    if l not in crawled and l not in to_crawl:
                        to_crawl.append(l)
                count += 1
            except Exception as e:
                logging.error(f"Error processing {link}: {e}")

            time.sleep(random.uniform(0.5, 2))  # Add random delay to avoid overloading the server

if __name__ == "__main__":
    main()