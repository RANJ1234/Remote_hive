#!/usr/bin/env python
"""
FTP Connection Troubleshooter for Hostinger
-------------------------------------------
This script helps diagnose common FTP connection issues with Hostinger.
"""

import os
import sys
import socket
import ftplib
import getpass
import time
import platform
import subprocess
from urllib.parse import urlparse

# FTP Configuration
FTP_HOSTS = [
    "82.25.125.65",  # IP address
    "blue-flamingo-576401.hostingersite.com",  # Hostname
    "ftp.blue-flamingo-576401.hostingersite.com"  # FTP prefix hostname
]
FTP_USERNAME = "u231309170.blue-flamingo-576401.hostingersite.com"
FTP_PORT = 21  # Standard FTP port

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_step(message):
    """Print a step message."""
    print(f"\n>> {message}")

def check_internet_connection():
    """Check if there is an active internet connection."""
    print_step("Checking internet connection")
    
    try:
        # Try to connect to a reliable server
        socket.create_connection(("www.google.com", 80), timeout=5)
        print("  Internet connection is working")
        return True
    except OSError:
        print("  No internet connection available")
        return False

def ping_host(host):
    """Ping the host to check if it's reachable."""
    print_step(f"Pinging host: {host}")
    
    # Determine the ping command based on the operating system
    param = "-n" if platform.system().lower() == "windows" else "-c"
    command = ["ping", param, "4", host]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  Host {host} is reachable")
            return True
        else:
            print(f"  Host {host} is not reachable")
            print(f"  {result.stdout}")
            return False
    except Exception as e:
        print(f"  Error pinging host: {e}")
        return False

def check_dns_resolution(host):
    """Check if the hostname can be resolved to an IP address."""
    print_step(f"Checking DNS resolution for: {host}")
    
    try:
        ip = socket.gethostbyname(host)
        print(f"  Hostname {host} resolves to IP: {ip}")
        return True
    except socket.gaierror:
        print(f"  Cannot resolve hostname: {host}")
        return False

def test_ftp_connection(host, username, password=None, port=21):
    """Test FTP connection to the specified host."""
    print_step(f"Testing FTP connection to: {host}:{port}")
    print(f"  Username: {username}")
    
    try:
        # Try to connect
        print("  Establishing connection...")
        ftp = ftplib.FTP()
        ftp.connect(host, port, timeout=10)
        print("  Connection established")
        
        # Try to login if password is provided
        if password:
            print("  Attempting login...")
            ftp.login(user=username, passwd=password)
            print("  Login successful!")
            
            # List directories
            print("\n  Directory listing:")
            files = ftp.nlst()
            for file in files[:10]:  # Show only first 10 files
                print(f"    {file}")
            
            if len(files) > 10:
                print(f"    ... and {len(files) - 10} more files/directories")
            
            # Close connection
            ftp.quit()
            print("  Connection closed successfully")
        else:
            print("  No password provided, skipping login")
            ftp.quit()
        
        return True
        
    except ftplib.all_errors as e:
        print(f"  FTP Error: {e}")
        return False

def check_ftp_url_format(url):
    """Check if the FTP URL is properly formatted."""
    print_step(f"Checking FTP URL format: {url}")
    
    if not url.startswith("ftp://"):
        print("  URL should start with 'ftp://'")
        url = "ftp://" + url
        print(f"  Corrected URL: {url}")
    
    try:
        parsed = urlparse(url)
        if not parsed.netloc:
            print("  Invalid URL format")
            return False
        
        print("  URL format is valid")
        return True
    except Exception as e:
        print(f"  Error parsing URL: {e}")
        return False

def main():
    """Main troubleshooting function."""
    print_header("Hostinger FTP Connection Troubleshooter")
    
    # Check internet connection
    if not check_internet_connection():
        print("\nPlease check your internet connection and try again.")
        return 1
    
    # Check FTP URL format
    ftp_url = "ftp://blue-flamingo-576401.hostingersite.com"
    check_ftp_url_format(ftp_url)
    
    # Check DNS resolution for hostnames
    for host in FTP_HOSTS:
        if not host.replace(".", "").isdigit():  # Skip IP addresses
            check_dns_resolution(host)
    
    # Ping hosts
    reachable_hosts = []
    for host in FTP_HOSTS:
        if ping_host(host):
            reachable_hosts.append(host)
    
    if not reachable_hosts:
        print("\nNone of the hosts are reachable. Please check your network connection or contact Hostinger support.")
        return 1
    
    # Test FTP connection without login
    for host in reachable_hosts:
        if test_ftp_connection(host, FTP_USERNAME):
            print(f"\nFTP connection to {host} was successful!")
            print("To test login, run the script again with your password.")
            
            # Ask if user wants to test login
            try:
                answer = input("\nDo you want to test login with your password? (y/n): ")
                if answer.lower() == 'y':
                    password = getpass.getpass("Enter your FTP password: ")
                    test_ftp_connection(host, FTP_USERNAME, password)
            except KeyboardInterrupt:
                print("\nLogin test cancelled.")
            
            break
    else:
        print("\nCould not establish FTP connection to any of the hosts.")
        print("Common issues:")
        print("1. Incorrect FTP hostname or IP address")
        print("2. FTP port (21) is blocked by your firewall or network")
        print("3. FTP service is not running on the server")
        print("4. Your IP might be blocked by the server")
        print("\nPlease contact Hostinger support for assistance.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
