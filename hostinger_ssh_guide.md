# Accessing Hostinger via SSH

This guide will help you enable and use SSH access for your Hostinger hosting account.

## Enabling SSH Access in Hostinger

Before you can connect via SSH, you need to enable SSH access in your Hostinger control panel:

1. **Log in to your Hostinger account**
   - Go to [https://hpanel.hostinger.com/](https://hpanel.hostinger.com/)
   - Enter your email and password

2. **Navigate to the SSH Access section**
   - In the left sidebar, find and click on "Advanced"
   - Select "SSH Access"

3. **Enable SSH Access**
   - Click the toggle to enable SSH access
   - You may need to set up an SSH password or upload an SSH key
   - Note the SSH hostname, username, and port provided by Hostinger

## Connecting via SSH

### Using Terminal (Windows, macOS, Linux)

1. **Open your terminal application**
   - Windows: Command Prompt, PowerShell, or Windows Terminal
   - macOS: Terminal
   - Linux: Terminal

2. **Connect using the SSH command**
   ```bash
   ssh username@hostname -p port
   ```
   
   Replace:
   - `username` with your Hostinger SSH username
   - `hostname` with your Hostinger SSH hostname
   - `port` with your Hostinger SSH port (usually 65002 for Hostinger)

   Example:
   ```bash
   ssh u231309170@blue-flamingo-576401.hostingersite.com -p 65002
   ```

3. **Enter your password when prompted**
   - Type your SSH password (it won't be visible as you type)
   - Press Enter

### Using PuTTY (Windows)

1. **Download and install PuTTY**
   - Download from [https://www.putty.org/](https://www.putty.org/)
   - Install the application

2. **Configure PuTTY**
   - Host Name: Your Hostinger SSH hostname
   - Port: Your Hostinger SSH port (usually 65002)
   - Connection type: SSH

3. **Connect**
   - Click "Open" to start the connection
   - Enter your username and password when prompted

## Common SSH Commands

Once connected, you can use these common commands:

- `ls` - List files and directories
- `cd directory_name` - Change directory
- `pwd` - Show current directory
- `mkdir directory_name` - Create a directory
- `rm file_name` - Remove a file
- `rm -r directory_name` - Remove a directory
- `cp file1 file2` - Copy a file
- `mv file1 file2` - Move or rename a file
- `nano file_name` - Edit a file using Nano editor
- `cat file_name` - Display file contents
- `exit` - Close the SSH connection

## Troubleshooting SSH Connection Issues

If you're having trouble connecting via SSH:

1. **Verify SSH is enabled**
   - Check your Hostinger control panel to ensure SSH access is enabled

2. **Check your credentials**
   - Confirm you're using the correct username, hostname, and port
   - Make sure your password is correct

3. **Check for firewall restrictions**
   - Your local network might be blocking outgoing SSH connections
   - Try connecting from a different network

4. **Contact Hostinger support**
   - If you still can't connect, contact Hostinger support for assistance

## Using SSH for Deployment

Once connected via SSH, you can deploy your application:

1. **Navigate to your web directory**
   ```bash
   cd public_html
   ```

2. **Create a virtual environment (if needed)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your application**
   ```bash
   nano .env  # Edit your environment variables
   ```

5. **Set up the web server**
   ```bash
   nano .htaccess  # Edit Apache configuration
   ```

Remember to check Hostinger's documentation for specific requirements and limitations for Python applications.
