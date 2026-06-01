#!/bin/bash
# Wait for PostgreSQL to be ready, then apply initial schema if not already applied
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER"; do
  sleep 1
done

echo "PostgreSQL is ready."

# Check if schema already applied (users table exists)
TABLE_EXISTS=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc \
  "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users');")

if [ "$TABLE_EXISTS" = "f" ]; then
  echo "Applying initial schema migration..."
  PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" \
    -f /migrations/001_initial_schema.sql
  echo "Schema applied successfully."
else
  echo "Schema already exists, skipping migration."
fi
