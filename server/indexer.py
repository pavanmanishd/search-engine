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
port = 5432
# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

def create_tables():
    try:
        logging.info("Connecting to the database to create tables...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
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

def index_document(document_id, text):
    try:
        logging.info("Connecting to the database to index documents...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        # Extract and insert the words into the Words table
        words = text.lower().split()
        word_counts = Counter(words)
        for word, count in word_counts.items():
            cur.execute("INSERT INTO Words (word) VALUES (%s) ON CONFLICT (word) DO NOTHING", (word,))
            conn.commit()  # Commit after each word is inserted
            cur.execute("SELECT id FROM Words WHERE word = %s", (word,))
            word_id = cur.fetchone()[0]
            cur.execute("INSERT INTO WordDocuments (word_id, document_id, term_frequency) VALUES (%s, %s, %s)", (word_id, document_id, count / len(words)))
        conn.commit()  # Commit after all words for a document are processed
        conn.close()
        logging.info("Documents indexed successfully.")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error indexing documents: {error}")

def reverse_index():
    try:
        logging.info("Connecting to the database to reverse index documents...")
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()

        #populate inverse document frequency
        logging.info("Populating inverse document frequency...")
        cur.execute("SELECT DISTINCT word_id FROM WordDocuments")
        words = cur.fetchall()
        
        cur.execute("SELECT COUNT(DISTINCT id) FROM Documents")
        no_of_documents = cur.fetchone()[0]

        for word_id in words:
            logging.info(f"Processing word {word_id}...")
            cur.execute("SELECT COUNT(DISTINCT document_id) FROM WordDocuments WHERE word_id = %s", (word_id,))
            document_count = cur.fetchone()[0]
            cur.execute("UPDATE WordDocuments SET inverse_document_frequency = %s WHERE word_id = %s", (document_count / no_of_documents, word_id))
            conn.commit()

        conn.close()
        logging.info("Reverse index completed successfully.")
    except (Exception, psycopg2.Error) as error:
        logging.error(f"Error reverse indexing documents: {error}")
