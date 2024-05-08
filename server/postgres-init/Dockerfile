# Use the official PostgreSQL image as base
#FROM postgres:latest
# Copy the custom pg_hba.conf file into the container
#COPY pg_hba.conf /etc/postgresql/$PG_MAJOR/main/pg_hba.conf
# Expose the PostgreSQL port
#EXPOSE 5432
FROM postgres
COPY ./init.sh /docker-entrypoint-initdb.d/
