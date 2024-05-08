# Use the official Python image as base
FROM python:3.9-slim

# # Set environment variables for PostgreSQL connection details
ENV DB_HOST="172.25.11.2"
ENV DB_NAME="searchengine"
ENV DB_USER="postgres"
ENV DB_PASSWORD="mysecretpassword"

# Set working directory in the container
WORKDIR .
 
# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN apt-get update
RUN apt-get install -y postgresql-client
RUN pip install --no-cache-dir -r requirements.txt

# Copy the source code
COPY . .

# Run the crawler first
# CMD ["sh", "-c", "python crawler.py && python server.py"]
CMD ["python", "crawler.py"]

