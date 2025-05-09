#!/bin/bash
# Deployment script for Remote Hive

# Exit on error
set -e

# Configuration
APP_DIR="/home/ubuntu/Remote_hive"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="remotehive"
NGINX_CONF="/etc/nginx/sites-available/remotehive"
DOMAIN="remotehive.in"
ADMIN_DOMAIN="admin.remotehive.in"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting Remote Hive deployment...${NC}"

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root or with sudo${NC}"
  exit 1
fi

# Update system packages
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update
apt-get upgrade -y

# Install required packages if not already installed
echo -e "${YELLOW}Installing required packages...${NC}"
apt-get install -y python3-pip python3-venv nginx certbot python3-certbot-nginx

# Navigate to app directory
echo -e "${YELLOW}Navigating to app directory...${NC}"
cd $APP_DIR

# Pull latest code from git repository
echo -e "${YELLOW}Pulling latest code from git repository...${NC}"
git pull

# Create or update virtual environment
if [ ! -d "$VENV_DIR" ]; then
  echo -e "${YELLOW}Creating virtual environment...${NC}"
  python3 -m venv $VENV_DIR
else
  echo -e "${YELLOW}Virtual environment already exists...${NC}"
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn gevent

# Set environment variables
echo -e "${YELLOW}Setting environment variables...${NC}"
export FLASK_ENV=production

# Create or update systemd service
echo -e "${YELLOW}Configuring systemd service...${NC}"
cp $APP_DIR/remotehive.service /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > $NGINX_CONF << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}

server {
    listen 80;
    server_name $ADMIN_DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000/admin;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }
}
EOF

# Create symbolic link to enable the site
ln -sf $NGINX_CONF /etc/nginx/sites-enabled/

# Test Nginx configuration
echo -e "${YELLOW}Testing Nginx configuration...${NC}"
nginx -t

# Restart Nginx
echo -e "${YELLOW}Restarting Nginx...${NC}"
systemctl restart nginx

# Setup SSL with Certbot
echo -e "${YELLOW}Setting up SSL certificates...${NC}"
certbot --nginx -d $DOMAIN -d www.$DOMAIN -d $ADMIN_DOMAIN --non-interactive --agree-tos --email admin@remotehive.in

# Restart the application
echo -e "${YELLOW}Restarting the application...${NC}"
systemctl restart $SERVICE_NAME

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
systemctl status $SERVICE_NAME --no-pager

echo -e "${GREEN}Deployment completed successfully!${NC}"
echo -e "${GREEN}Main site: https://$DOMAIN${NC}"
echo -e "${GREEN}Admin site: https://$ADMIN_DOMAIN${NC}"
