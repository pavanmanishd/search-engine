from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psycopg2
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel
import math

load_dotenv()

# PostgreSQL connection details
host = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")
port = 5432
# Initialize FastAPI
app = FastAPI()

# Allow CORS for all origins (you can customize origins if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def calculate_tfidf(tf, idf, max_tf):
    return (1 + math.log(tf)) * idf / math.log(1 + max_tf)

def search_documents(query: str) -> List[dict]:
    query = query.lower()
    words = query.split()
    results = []
    frequencies = {}
    max_tf_in_doc = {}

    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        cur = conn.cursor()

        # Calculate TF, IDF, and max TF for each word in the query
        for word in words:
            cur.execute("""
                SELECT wd.document_id, wd.term_frequency, wd.inverse_document_frequency, MAX(wd.term_frequency) 
                FROM WordDocuments wd 
                JOIN Words w ON wd.word_id = w.id 
                WHERE w.word = %s
                GROUP BY wd.document_id, wd.inverse_document_frequency, wd.term_frequency
            """, (word,))
            word_results = cur.fetchall()

            for doc_id, tf, idf, max_tf in word_results:
                if doc_id not in frequencies:
                    frequencies[doc_id] = {}
                    max_tf_in_doc[doc_id] = 0
                frequencies[doc_id][word] = tf
                max_tf_in_doc[doc_id] = max(max_tf_in_doc[doc_id], max_tf)

        # Calculate TF-IDF scores for each document
        for doc_id in frequencies:
            doc_score = 0
            for word in frequencies[doc_id]:
                tf = frequencies[doc_id][word]
                idf = word_results[0][2]  # IDF is the same for all occurrences of the word in the document
                tfidf = calculate_tfidf(tf, idf, max_tf_in_doc[doc_id])
                doc_score += tfidf
            # Fetch URL and title of the document
            cur.execute("SELECT url, title FROM Documents WHERE id = %s", (doc_id,))
            result = cur.fetchone()
            if result:
                url, title = result
                results.append({"url": url, "title": title, "score": doc_score})

        conn.close()
    except psycopg2.Error as e:
        print(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching documents: {e}")

    # Sort results by score in descending order
    results = sorted(results, key=lambda x: x["score"], reverse=True)
    return results

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
def search(SearchQuery: SearchQuery):
    results = search_documents(SearchQuery.query)
    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
