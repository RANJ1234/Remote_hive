#!/usr/bin/env python
"""
Remote Hive Deployment Script for Hostinger
-------------------------------------------
This script prepares and deploys the Remote Hive application to Hostinger via FTP.
"""

import os
import sys
import shutil
import ftplib
import getpass
import zipfile
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

# FTP Configuration
FTP_HOST = "ftp://blue-flamingo-576401.hostingersite.com"
FTP_IP = "82.25.125.65"
FTP_USERNAME = "u231309170.blue-flamingo-576401.hostingersite.com"
FTP_PASSWORD = None  # Will prompt for password
UPLOAD_PATH = "public_html"

# Files and directories to exclude from deployment
EXCLUDE_PATTERNS = [
    "__pycache__",
    "*.pyc",
    ".git",
    ".gitignore",
    ".env",
    ".venv",
    "venv",
    "env",
    ".idea",
    ".vscode",
    "*.log",
    "instance",
    "tests",
    "*.db",
    "*.sqlite",
    "*.sqlite3",
    "node_modules",
    "backup.sh",
    "deploy.sh",
    "deploy_to_hostinger.py",
    "create_test_users.py",
    "setup_and_run.py",
    "seed_database.py"
]

# Files to modify for production
PRODUCTION_SETTINGS = {
    ".env": {
        "FLASK_ENV": "production",
        "DEBUG": "False",
        # Add other production settings here
    }
}

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_step(message):
    """Print a step message."""
    print(f"\n>> {message}")

def create_deployment_package(target_dir):
    """Create a deployment package with production-ready files."""
    print_header("Creating Deployment Package")
    
    # Create a temporary directory for the deployment package
    temp_dir = Path(target_dir)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)
    
    # Copy files to the deployment directory
    print_step("Copying files to deployment directory")
    for item in Path(".").iterdir():
        # Skip excluded patterns
        if any(item.match(pattern) for pattern in EXCLUDE_PATTERNS):
            print(f"  Skipping {item}")
            continue
        
        # Copy the item
        if item.is_dir():
            shutil.copytree(item, temp_dir / item.name, 
                           ignore=shutil.ignore_patterns(*EXCLUDE_PATTERNS))
            print(f"  Copied directory: {item}")
        else:
            shutil.copy2(item, temp_dir / item.name)
            print(f"  Copied file: {item}")
    
    # Create production .env file
    print_step("Creating production .env file")
    env_example = Path(".env.example")
    if env_example.exists():
        with open(env_example, "r") as f:
            env_content = f.read()
        
        # Replace development settings with production settings
        for key, value in PRODUCTION_SETTINGS.get(".env", {}).items():
            env_content = env_content.replace(f"{key}=development", f"{key}={value}")
            env_content = env_content.replace(f"{key}=True", f"{key}={value}")
        
        # Write the production .env file
        with open(temp_dir / ".env", "w") as f:
            f.write(env_content)
        print("  Created production .env file")
    
    # Create a .htaccess file for Apache
    print_step("Creating .htaccess file")
    htaccess_content = """
# Enable mod_rewrite
RewriteEngine On

# Set the base directory
RewriteBase /

# Redirect to HTTPS
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]

# Serve static files directly
RewriteRule ^static/(.*)$ static/$1 [L]

# Forward all other requests to the WSGI script
RewriteCond %{REQUEST_FILENAME} !-f
RewriteRule ^(.*)$ wsgi.py/$1 [QSA,L]

# Set environment variables
SetEnv FLASK_ENV production
"""
    with open(temp_dir / ".htaccess", "w") as f:
        f.write(htaccess_content)
    print("  Created .htaccess file")
    
    # Create a passenger_wsgi.py file for Hostinger
    print_step("Creating passenger_wsgi.py file")
    passenger_wsgi_content = """
import os
import sys

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import the WSGI application
from wsgi import application
"""
    with open(temp_dir / "passenger_wsgi.py", "w") as f:
        f.write(passenger_wsgi_content)
    print("  Created passenger_wsgi.py file")
    
    return temp_dir

def deploy_via_ftp(source_dir, password=None):
    """Deploy the application to Hostinger via FTP."""
    print_header("Deploying via FTP")
    
    # Get FTP password if not provided
    if password is None:
        password = getpass.getpass(f"Enter FTP password for {FTP_USERNAME}: ")
    
    try:
        # Connect to FTP server
        print_step(f"Connecting to FTP server: {FTP_HOST}")
        ftp = ftplib.FTP(FTP_IP)
        ftp.login(user=FTP_USERNAME, passwd=password)
        print(f"  Connected to FTP server as {FTP_USERNAME}")
        
        # Navigate to upload directory
        print_step(f"Navigating to {UPLOAD_PATH}")
        try:
            ftp.cwd(UPLOAD_PATH)
        except ftplib.error_perm:
            print(f"  Directory {UPLOAD_PATH} does not exist, creating it")
            ftp.mkd(UPLOAD_PATH)
            ftp.cwd(UPLOAD_PATH)
        
        # Upload files
        print_step("Uploading files")
        source_dir = Path(source_dir)
        for item in source_dir.glob("**/*"):
            if item.is_dir():
                # Create directory on FTP server
                rel_path = str(item.relative_to(source_dir)).replace("\\", "/")
                if rel_path:
                    try:
                        ftp.mkd(rel_path)
                        print(f"  Created directory: {rel_path}")
                    except ftplib.error_perm:
                        print(f"  Directory already exists: {rel_path}")
            elif item.is_file():
                # Upload file to FTP server
                rel_path = str(item.relative_to(source_dir)).replace("\\", "/")
                with open(item, "rb") as f:
                    ftp.storbinary(f"STOR {rel_path}", f)
                print(f"  Uploaded file: {rel_path}")
        
        # Close FTP connection
        ftp.quit()
        print_step("FTP deployment completed successfully")
        
    except ftplib.all_errors as e:
        print(f"FTP Error: {e}")
        return False
    
    return True

def main():
    """Main deployment function."""
    print_header("Remote Hive Deployment to Hostinger")
    
    # Create a timestamp for the deployment
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    deploy_dir = f"deploy_package_{timestamp}"
    
    try:
        # Create deployment package
        package_dir = create_deployment_package(deploy_dir)
        
        # Deploy via FTP
        success = deploy_via_ftp(package_dir)
        
        if success:
            print_header("Deployment Completed Successfully")
            print("Your application has been deployed to Hostinger.")
            print("Next steps:")
            print("1. Configure your domain in Hostinger control panel")
            print("2. Set up a MongoDB database (if not already done)")
            print("3. Update the .env file on the server with your MongoDB connection string")
            print("4. Test your application by visiting your domain")
        else:
            print_header("Deployment Failed")
            print("Please check the error messages above and try again.")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        # Clean up deployment directory
        if Path(deploy_dir).exists():
            shutil.rmtree(deploy_dir)
            print(f"Cleaned up deployment directory: {deploy_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
