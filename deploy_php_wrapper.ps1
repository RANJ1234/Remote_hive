# Remote Hive PHP Wrapper Deployment Script for PowerShell
# This script deploys the PHP wrapper files to Hostinger via SSH

# Configuration
$SSH_HOST = "82.25.125.73"
$SSH_PORT = "65002"
$SSH_USER = "u231309170"
$REMOTE_PATH = "domains/darkturquoise-chinchilla-684738.hostingersite.com/public_html"

# Files to deploy
$FILES = @(
    "index.php",
    "test.php",
    "phpinfo.php",
    ".htaccess",
    "static/index.html",
    "static/css/style.css",
    "static/js/main.js"
)

# Function to print colored messages
function Write-ColoredMessage {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$Color = "Green"
    )
    
    Write-Host "[$([DateTime]::Now.ToString('yyyy-MM-dd HH:mm:ss'))] $Message" -ForegroundColor $Color
}

# Create necessary directories on the remote server
Write-ColoredMessage "Creating directories on the remote server..."
ssh -p $SSH_PORT "$SSH_USER@$SSH_HOST" "mkdir -p $REMOTE_PATH/static/css $REMOTE_PATH/static/js $REMOTE_PATH/cache"

# Deploy files
Write-ColoredMessage "Deploying files to the remote server..."
foreach ($file in $FILES) {
    Write-ColoredMessage "Uploading $file..."
    
    # Create directory if needed
    $dir = Split-Path -Path $file -Parent
    if ($dir -ne "") {
        ssh -p $SSH_PORT "$SSH_USER@$SSH_HOST" "mkdir -p $REMOTE_PATH/$dir"
    }
    
    # Upload file
    scp -P $SSH_PORT "$file" "$SSH_USER@$SSH_HOST`:$REMOTE_PATH/$file"
    
    if ($LASTEXITCODE -eq 0) {
        Write-ColoredMessage "Successfully uploaded $file"
    } else {
        Write-ColoredMessage "Failed to upload $file" -Color "Red"
    }
}

# Set permissions
Write-ColoredMessage "Setting permissions..."
ssh -p $SSH_PORT "$SSH_USER@$SSH_HOST" "chmod -R 755 $REMOTE_PATH && chmod -R 777 $REMOTE_PATH/cache"

Write-ColoredMessage "Deployment completed!"
Write-ColoredMessage "You can now access your PHP wrapper at: http://darkturquoise-chinchilla-684738.hostingersite.com/"
Write-ColoredMessage "To test the wrapper, visit: http://darkturquoise-chinchilla-684738.hostingersite.com/test.php"

Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
