#!/bin/bash

# Remote Hive Deployment Script
# This script deploys the Remote Hive application to a production server

# Exit on error
set -e

# Configuration
APP_DIR="/var/www/remotehive"
BACKUP_DIR="/var/backups/remotehive"
VENV_DIR="$APP_DIR/venv"
GIT_REPO="https://github.com/yourusername/remotehive.git"
BRANCH="main"
SERVICE_NAME="remotehive"

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

# Create backup of current deployment
if [ -d "$APP_DIR" ]; then
    print_message "Creating backup of current deployment..."
    BACKUP_FILE="$BACKUP_DIR/remotehive_$(date '+%Y%m%d_%H%M%S').tar.gz"
    tar -czf "$BACKUP_FILE" -C "$(dirname "$APP_DIR")" "$(basename "$APP_DIR")"
    print_message "Backup created at $BACKUP_FILE"
fi

# Update or clone the repository
if [ -d "$APP_DIR/.git" ]; then
    print_message "Updating repository..."
    cd "$APP_DIR"
    git fetch --all
    git checkout "$BRANCH"
    git pull
else
    print_message "Cloning repository..."
    mkdir -p "$APP_DIR"
    git clone -b "$BRANCH" "$GIT_REPO" "$APP_DIR"
    cd "$APP_DIR"
fi

# Create or update virtual environment
if [ ! -d "$VENV_DIR" ]; then
    print_message "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment and install dependencies
print_message "Installing dependencies..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn gevent

# Create logs directory if it doesn't exist
if [ ! -d "$APP_DIR/logs" ]; then
    print_message "Creating logs directory..."
    mkdir -p "$APP_DIR/logs"
    chown -R www-data:www-data "$APP_DIR/logs"
fi

# Create uploads directory if it doesn't exist
if [ ! -d "$APP_DIR/static/uploads" ]; then
    print_message "Creating uploads directory..."
    mkdir -p "$APP_DIR/static/uploads"
    mkdir -p "$APP_DIR/static/uploads/company_logos"
    mkdir -p "$APP_DIR/static/uploads/resumes"
    mkdir -p "$APP_DIR/static/uploads/profile_pictures"
    chown -R www-data:www-data "$APP_DIR/static/uploads"
fi

# Check if .env file exists, create from example if not
if [ ! -f "$APP_DIR/.env" ]; then
    print_warning ".env file not found. Creating from example..."
    if [ -f "$APP_DIR/.env.example" ]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        print_message "Please update the .env file with your production settings."
    else
        print_error ".env.example file not found. Please create a .env file manually."
    fi
fi

# Set correct permissions
print_message "Setting permissions..."
chown -R www-data:www-data "$APP_DIR"
chmod -R 755 "$APP_DIR"
chmod -R 775 "$APP_DIR/static/uploads"
chmod -R 775 "$APP_DIR/logs"

# Create or update systemd service
print_message "Configuring systemd service..."
cat > "/etc/systemd/system/$SERVICE_NAME.service" << EOF
[Unit]
Description=Gunicorn instance to serve Remote Hive
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
ExecStart=$VENV_DIR/bin/gunicorn -c gunicorn_config.py wsgi:application
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, restart the service
print_message "Restarting service..."
systemctl daemon-reload
systemctl restart "$SERVICE_NAME"
systemctl enable "$SERVICE_NAME"

# Check if Nginx is installed
if command -v nginx >/dev/null 2>&1; then
    print_message "Checking Nginx configuration..."
    if [ -f "$APP_DIR/nginx.conf.example" ]; then
        print_message "Nginx example configuration found."
        print_message "Please review and adapt the Nginx configuration at $APP_DIR/nginx.conf.example"
    fi
else
    print_warning "Nginx not found. Please install and configure Nginx manually."
fi

# Final message
print_message "Deployment completed successfully!"
print_message "Please check the service status with: systemctl status $SERVICE_NAME"
print_message "And verify the application is running at your domain."
