# Use the official Python image as base
FROM python:3.9-slim

# # Set environment variables for PostgreSQL connection details
ENV DB_HOST="127.0.0.1"
ENV DB_NAME="searchengine"
ENV DB_USER="postgres"
ENV DB_PASSWORD="mysecretpassword"

# Set working directory in the container
WORKDIR .

# Copy the wait script
# COPY wait-for-postgres.sh ./wait-for-postgres.sh
# RUN chmod +x ./wait-for-postgres.sh

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN apt-get update && apt-get install -y postgresql-client
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Run the crawler after waiting for PostgreSQL to be ready
# CMD ["wait-for-postgres.sh", "python", "crawler.py"]

