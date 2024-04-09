import psycopg2
from collections import Counter
import logging
import os
from dotenv import load_dotenv

load_dotenv()
# PostgreSQL connection details
host = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def create_tables():
    try:
        logging.info("Connecting to the database to create tables...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        # Create the Documents table
        logging.info("Creating Documents table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Documents (
                id SERIAL PRIMARY KEY,
                url TEXT,
                title TEXT,
                content TEXT
            )
        """)

        # Create the Words table
        logging.info("Creating Words table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Words (
                id SERIAL PRIMARY KEY,
                word TEXT UNIQUE
            )
        """)

        # Create the WordDocuments table
        logging.info("Creating WordDocuments table...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS WordDocuments (
                word_id INT,
                document_id INT,
                term_frequency FLOAT,
                inverse_document_frequency FLOAT,
                PRIMARY KEY (word_id, document_id),
                FOREIGN KEY (word_id) REFERENCES Words(id),
                FOREIGN KEY (document_id) REFERENCES Documents(id)
            )
        """)

        conn.commit()
        conn.close()
        logging.info("Tables created successfully.")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error creating tables: {error}")

def populate_tables():
    try:
        logging.info("Connecting to the database to populate tables...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        # Retrieve data from the wikipedia_pages table
        logging.info("Retrieving data from wikipedia_pages table...")
        cur.execute("SELECT id, title, url, text FROM wikipedia_pages")
        results = cur.fetchall()

        for row in results:
            logging.info(f"Processing document {row[0]}...")

            document_id, title, url, content = row

            # Insert the document into the Documents table
            cur.execute("INSERT INTO Documents (id, url, title, content) VALUES (%s, %s, %s, %s)", (document_id, url, title, content))
            conn.commit()  # Commit after each document is inserted

            # Extract and insert the words into the Words table
            words = content.lower().split()
            word_counts = Counter(words)
            for word, count in word_counts.items():
                cur.execute("INSERT INTO Words (word) VALUES (%s) ON CONFLICT (word) DO NOTHING", (word,))
                conn.commit()  # Commit after each word is inserted
                cur.execute("SELECT id FROM Words WHERE word = %s", (word,))
                word_id = cur.fetchone()[0]
                cur.execute("INSERT INTO WordDocuments (word_id, document_id, term_frequency) VALUES (%s, %s, %s)", (word_id, document_id, count / len(words)))
            conn.commit()  # Commit after all words for a document are processed

        conn.close()
        logging.info("Tables populated successfully.")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error populating tables: {error}")

if __name__ == "__main__":
    create_tables()
    populate_tables()
