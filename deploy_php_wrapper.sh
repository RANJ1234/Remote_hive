#!/bin/bash

# Remote Hive PHP Wrapper Deployment Script
# This script deploys the PHP wrapper files to Hostinger via SSH

# Configuration
SSH_HOST="82.25.125.73"
SSH_PORT="65002"
SSH_USER="u231309170"
REMOTE_PATH="domains/darkturquoise-chinchilla-684738.hostingersite.com/public_html"

# Files to deploy
FILES=(
    "index.php"
    "test.php"
    "phpinfo.php"
    ".htaccess"
    "static/index.html"
    "static/css/style.css"
    "static/js/main.js"
)

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

# Create necessary directories on the remote server
print_message "Creating directories on the remote server..."
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "mkdir -p $REMOTE_PATH/static/css $REMOTE_PATH/static/js $REMOTE_PATH/cache"

# Deploy files
print_message "Deploying files to the remote server..."
for file in "${FILES[@]}"; do
    print_message "Uploading $file..."
    
    # Create directory if needed
    dir=$(dirname "$file")
    if [ "$dir" != "." ]; then
        ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "mkdir -p $REMOTE_PATH/$dir"
    fi
    
    # Upload file
    scp -P $SSH_PORT "$file" "$SSH_USER@$SSH_HOST:$REMOTE_PATH/$file"
    
    if [ $? -eq 0 ]; then
        print_message "Successfully uploaded $file"
    else
        print_error "Failed to upload $file"
    fi
done

# Set permissions
print_message "Setting permissions..."
ssh -p $SSH_PORT $SSH_USER@$SSH_HOST "chmod -R 755 $REMOTE_PATH && chmod -R 777 $REMOTE_PATH/cache"

print_message "Deployment completed!"
print_message "You can now access your PHP wrapper at: http://darkturquoise-chinchilla-684738.hostingersite.com/"
print_message "To test the wrapper, visit: http://darkturquoise-chinchilla-684738.hostingersite.com/test.php"
