#!/bin/bash

# Simple PostgreSQL installation and setup script for Ubuntu
set -e

echo "Installing PostgreSQL..."
sudo apt update
sudo apt install -y postgresql postgresql-contrib

echo "Starting PostgreSQL service..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "Setting up database..."
sudo -u postgres psql << 'EOF'
CREATE DATABASE book_store_db;
CREATE USER book_store_user WITH PASSWORD 'book_store_password';
ALTER USER book_store_user WITH CREATEDB;
ALTER ROLE book_store_user SET client_encoding TO 'utf8';
ALTER ROLE book_store_user SET timezone TO 'UTC';
ALTER DATABASE book_store_db OWNER TO book_store_user;
GRANT ALL PRIVILEGES ON DATABASE book_store_db TO book_store_user;
\q
EOF


echo "Setup complete!"
echo "Database: book_store_db"
echo "User: book_store_user"
echo "Password: book_store_password"
echo ""
echo "To connect: PGPASSWORD='book_store_password' psql -h localhost -U book_store_user -d book_store_db"
