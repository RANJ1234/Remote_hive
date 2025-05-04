#!/bin/bash

# Remote Hive Backup Script
# This script creates backups of the Remote Hive application and database

# Exit on error
set -e

# Configuration
APP_DIR="/var/www/remotehive"
BACKUP_DIR="/var/backups/remotehive"
BACKUP_RETENTION_DAYS=14
MONGODB_HOST="localhost"
MONGODB_PORT="27017"
MONGODB_DB="remotehive"
MONGODB_USER=""
MONGODB_PASSWORD=""
DATE=$(date +"%Y-%m-%d_%H-%M-%S")

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check if running as root
if [ "$(id -u)" != "0" ]; then
   print_error "This script must be run as root" 
   exit 1
fi

# Create backup directory if it doesn't exist
if [ ! -d "$BACKUP_DIR" ]; then
    print_message "Creating backup directory..."
    mkdir -p "$BACKUP_DIR"
fi

# Create subdirectories for different backup types
mkdir -p "$BACKUP_DIR/application"
mkdir -p "$BACKUP_DIR/database"
mkdir -p "$BACKUP_DIR/uploads"

# Backup application files
print_message "Backing up application files..."
APP_BACKUP_FILE="$BACKUP_DIR/application/remotehive_app_$DATE.tar.gz"
tar -czf "$APP_BACKUP_FILE" -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")" \
    --exclude="$(basename "$APP_DIR")/venv" \
    --exclude="$(basename "$APP_DIR")/logs" \
    --exclude="$(basename "$APP_DIR")/static/uploads" \
    --exclude="$(basename "$APP_DIR")/.git"
print_message "Application backup created at $APP_BACKUP_FILE"

# Backup uploads directory separately
print_message "Backing up uploads..."
UPLOADS_BACKUP_FILE="$BACKUP_DIR/uploads/remotehive_uploads_$DATE.tar.gz"
if [ -d "$APP_DIR/static/uploads" ]; then
    tar -czf "$UPLOADS_BACKUP_FILE" -C "$APP_DIR/static" "uploads"
    print_message "Uploads backup created at $UPLOADS_BACKUP_FILE"
else
    print_warning "Uploads directory not found, skipping uploads backup"
fi

# Backup MongoDB database
print_message "Backing up MongoDB database..."
DB_BACKUP_DIR="$BACKUP_DIR/database/remotehive_db_$DATE"
mkdir -p "$DB_BACKUP_DIR"

# Build mongodump command based on authentication settings
MONGODUMP_CMD="mongodump --host $MONGODB_HOST --port $MONGODB_PORT --db $MONGODB_DB --out $DB_BACKUP_DIR"
if [ -n "$MONGODB_USER" ] && [ -n "$MONGODB_PASSWORD" ]; then
    MONGODUMP_CMD="$MONGODUMP_CMD --username $MONGODB_USER --password $MONGODB_PASSWORD --authenticationDatabase admin"
fi

# Execute mongodump
if $MONGODUMP_CMD; then
    # Compress the database backup
    DB_BACKUP_FILE="$BACKUP_DIR/database/remotehive_db_$DATE.tar.gz"
    tar -czf "$DB_BACKUP_FILE" -C "$(dirname "$DB_BACKUP_DIR")" "$(basename "$DB_BACKUP_DIR")"
    rm -rf "$DB_BACKUP_DIR"
    print_message "Database backup created at $DB_BACKUP_FILE"
else
    print_error "Database backup failed"
fi

# Remove old backups
print_message "Removing backups older than $BACKUP_RETENTION_DAYS days..."
find "$BACKUP_DIR/application" -name "remotehive_app_*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
find "$BACKUP_DIR/database" -name "remotehive_db_*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete
find "$BACKUP_DIR/uploads" -name "remotehive_uploads_*.tar.gz" -type f -mtime +$BACKUP_RETENTION_DAYS -delete

# Final message
print_message "Backup completed successfully!"
print_message "Application backup: $APP_BACKUP_FILE"
print_message "Database backup: $DB_BACKUP_FILE"
if [ -d "$APP_DIR/static/uploads" ]; then
    print_message "Uploads backup: $UPLOADS_BACKUP_FILE"
fi
