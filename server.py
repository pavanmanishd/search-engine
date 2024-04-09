from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import psycopg2
import os
from dotenv import load_dotenv
import uvicorn
from pydantic import BaseModel

load_dotenv()

# PostgreSQL connection details
host = os.getenv("DB_HOST")
database = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

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

def search_documents(query: str) -> List[dict]:
    query = query.lower()
    words = query.split()
    results = []
    frequencies = {}
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password
        )
        cur = conn.cursor()
        for word in words:
            cur.execute("SELECT document_id, term_frequency, inverse_document_frequency FROM WordDocuments WHERE word_id = (SELECT id FROM Words WHERE word = %s)", (word,))
            result = cur.fetchall()
            for r in result:
                if r[0] not in frequencies:
                    frequencies[r[0]] = 0
                frequencies[r[0]] += r[1] * r[2]
        for doc_id in frequencies:
            cur.execute("SELECT url, title FROM Documents WHERE id = %s", (doc_id,))
            result = cur.fetchone()
            if result:
                results.append({"url": result[0], "title": result[1], "score": frequencies[doc_id]})
        results = sorted(results, key=lambda x: x["score"], reverse=True)
        conn.close()
    except psycopg2.Error as e:
        raise HTTPException(status_code=500, detail=f"Error searching documents: {e}")
    return results

class SearchQuery(BaseModel):
    query: str

@app.post("/search")
def search(SearchQuery: SearchQuery):
    results = search_documents(SearchQuery.query)
    return results


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
