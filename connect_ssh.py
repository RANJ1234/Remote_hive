#!/usr/bin/env python
"""
SSH Connection Script for Hostinger
-----------------------------------
This script helps establish an SSH connection to your Hostinger server.
"""

import os
import sys
import subprocess
import platform
import getpass

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def print_step(message):
    """Print a step message."""
    print(f"\n>> {message}")

def connect_ssh():
    """Connect to the server via SSH."""
    print_header("SSH Connection to Hostinger")
    
    # Get SSH connection details
    hostname = input("Enter SSH hostname (e.g., blue-flamingo-576401.hostingersite.com): ")
    username = input("Enter SSH username: ")
    port = input("Enter SSH port (default: 22): ") or "22"
    
    print_step(f"Connecting to {username}@{hostname} on port {port}")
    
    # Determine the SSH command based on the operating system
    if platform.system().lower() == "windows":
        # On Windows, use the built-in ssh client if available, otherwise suggest PuTTY
        try:
            # Check if ssh is available
            subprocess.run(["ssh", "-V"], capture_output=True, check=True)
            
            # Build the SSH command
            ssh_command = f"ssh {username}@{hostname} -p {port}"
            print(f"Running command: {ssh_command}")
            
            # Execute the SSH command
            os.system(ssh_command)
            
        except (subprocess.SubprocessError, FileNotFoundError):
            print("SSH client not found. Please install OpenSSH or use PuTTY.")
            print("\nTo connect using PuTTY:")
            print(f"1. Open PuTTY")
            print(f"2. Enter hostname: {hostname}")
            print(f"3. Enter port: {port}")
            print(f"4. Enter username: {username}")
            print(f"5. Click 'Open' to connect")
    else:
        # On Unix-like systems, use the ssh command
        ssh_command = f"ssh {username}@{hostname} -p {port}"
        print(f"Running command: {ssh_command}")
        
        # Execute the SSH command
        os.system(ssh_command)

if __name__ == "__main__":
    connect_ssh()
