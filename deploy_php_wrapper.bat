@echo off
setlocal enabledelayedexpansion

:: Remote Hive PHP Wrapper Deployment Script for Windows
:: This script deploys the PHP wrapper files to Hostinger via SSH

:: Configuration
set SSH_HOST=82.25.125.73
set SSH_PORT=65002
set SSH_USER=u231309170
set REMOTE_PATH=domains/darkturquoise-chinchilla-684738.hostingersite.com/public_html

:: Files to deploy
set FILES=index.php test.php phpinfo.php .htaccess static/index.html static/css/style.css static/js/main.js

echo [%date% %time%] Creating directories on the remote server...
ssh -p %SSH_PORT% %SSH_USER%@%SSH_HOST% "mkdir -p %REMOTE_PATH%/static/css %REMOTE_PATH%/static/js %REMOTE_PATH%/cache"

echo [%date% %time%] Deploying files to the remote server...
for %%f in (%FILES%) do (
    echo [%date% %time%] Uploading %%f...
    
    :: Create directory if needed
    for /f "tokens=1* delims=/" %%a in ("%%f") do (
        if not "%%b"=="" (
            ssh -p %SSH_PORT% %SSH_USER%@%SSH_HOST% "mkdir -p %REMOTE_PATH%/%%a"
        )
    )
    
    :: Upload file
    scp -P %SSH_PORT% "%%f" "%SSH_USER%@%SSH_HOST%:%REMOTE_PATH%/%%f"
    
    if !errorlevel! equ 0 (
        echo [%date% %time%] Successfully uploaded %%f
    ) else (
        echo [%date% %time%] ERROR: Failed to upload %%f
    )
)

:: Set permissions
echo [%date% %time%] Setting permissions...
ssh -p %SSH_PORT% %SSH_USER%@%SSH_HOST% "chmod -R 755 %REMOTE_PATH% && chmod -R 777 %REMOTE_PATH%/cache"

echo [%date% %time%] Deployment completed!
echo [%date% %time%] You can now access your PHP wrapper at: http://darkturquoise-chinchilla-684738.hostingersite.com/
echo [%date% %time%] To test the wrapper, visit: http://darkturquoise-chinchilla-684738.hostingersite.com/test.php

pause
