# Search Engine

This project implements a search API using FastAPI and PostgreSQL. It allows users to search for documents based on a query and ranks the search results using the **TF-IDF (Term Frequency-Inverse Document Frequency)** algorithm.

## Features

- Search for documents based on a query
- Rank search results using TF-IDF scoring
- Retrieve document titles, URLs, and scores in search results
- Backend implemented in Python using FastAPI and psycopg2
- Frontend implemented in React.js
- Database storage and retrieval using PostgreSQL

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/pavanmanishd/search-engine.git
   ```

2. Stop Postgres before starting the Docker container:

   ```bash
   systemctl stop postgresql
   ```

3. Run Docker container:

   ```bash
   cd server
   docker compose up
   ```

4. Run the frontend to try it. Go to the root directory then:

   ```bash
   cd client
   npm install
   npm run dev
   ```

5. Try the search engine by visiting [localhost:5173](http://localhost:5173).

## Usage

- Send a POST request to `/search` with a JSON payload containing the query:

  ```bash
  curl -X 'POST' \
    'http://localhost:8000/search' \
    -H 'Content-Type: application/json' \
    -d '{
    "query": "your_search_query"
  }'
  ```

- Example response:

  ```json
  [
    {
      "url": "https://example.com/document1",
      "title": "Document 1 Title",
      "score": 0.784
    },
    {
      "url": "https://example.com/document2",
      "title": "Document 2 Title",
      "score": 0.657
    }
  ]
  ```