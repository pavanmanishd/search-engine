#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
CREATE DATABASE searchengine;
\c searchengine;

CREATE TABLE IF NOT EXISTS Documents (
    id SERIAL PRIMARY KEY,
    url TEXT,
    title TEXT,
    content TEXT
);

CREATE TABLE IF NOT EXISTS Words (
    id SERIAL PRIMARY KEY,
    word TEXT UNIQUE
);

CREATE TABLE IF NOT EXISTS WordDocuments (
    word_id INT,
    document_id INT,
    term_frequency REAL,
    inverse_document_frequency REAL,
    PRIMARY KEY (word_id, document_id),
    FOREIGN KEY (word_id) REFERENCES Words(id),
    FOREIGN KEY (document_id) REFERENCES Documents(id)
);

CREATE INDEX ON WordDocuments(word_id);
CREATE INDEX ON WordDocuments(document_id);
EOSQL


