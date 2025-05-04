# Remote Hive PHP Wrapper

This PHP wrapper allows you to run your Flask application on a PHP hosting environment like Hostinger. It acts as a proxy between the PHP server and your Flask application hosted elsewhere.

## How It Works

1. The PHP wrapper receives requests from users
2. It forwards these requests to your Flask application hosted elsewhere
3. It receives the responses from your Flask application
4. It returns these responses to the users

This approach allows you to:
- Use a PHP hosting environment for a Python application
- Keep your Flask application code unchanged
- Deploy your application without requiring Python on the hosting server

## Files Included

- `index.php`: The main PHP wrapper that handles all requests
- `test.php`: A script to test if the wrapper is working correctly
- `phpinfo.php`: A script to check the PHP environment
- `.htaccess`: Apache configuration for the wrapper
- `static/index.html`: A static HTML file for testing
- `static/css/style.css`: CSS styles for testing
- `static/js/main.js`: JavaScript for testing
- `deploy_php_wrapper.sh`: Bash script for deploying to Hostinger
- `deploy_php_wrapper.bat`: Windows batch script for deploying to Hostinger
- `deploy_php_wrapper.ps1`: PowerShell script for deploying to Hostinger

## Configuration

Before using the wrapper, you need to configure it:

1. Edit `index.php` and set the `flask_app_url` to your Flask application URL:

```php
$config = [
    // URL of your Flask application hosted elsewhere
    'flask_app_url' => 'https://your-flask-app.example.com',
    
    // Other configuration options...
];
```

2. Deploy your Flask application to a Python-friendly hosting service like:
   - PythonAnywhere
   - Heroku
   - Render
   - Vercel
   - Railway

## Deployment

### Using SSH (Linux/macOS)

1. Make the deployment script executable:
   ```bash
   chmod +x deploy_php_wrapper.sh
   ```

2. Run the deployment script:
   ```bash
   ./deploy_php_wrapper.sh
   ```

### Using Windows Command Prompt

1. Run the batch script:
   ```
   deploy_php_wrapper.bat
   ```

### Using PowerShell

1. Run the PowerShell script:
   ```powershell
   .\deploy_php_wrapper.ps1
   ```

## Testing

After deployment, you can test if the wrapper is working correctly:

1. Visit `http://your-domain.com/test.php` to run the test script
2. Visit `http://your-domain.com/?test=true` to check the configuration
3. Visit `http://your-domain.com/phpinfo.php` to check the PHP environment

## Troubleshooting

If you encounter issues with the wrapper:

1. **Check the Flask application URL**: Make sure your Flask application is accessible from the internet
2. **Check the PHP version**: The wrapper requires PHP 7.0 or higher
3. **Check the cURL extension**: The wrapper requires the cURL extension to be enabled
4. **Check the cache directory**: Make sure the cache directory is writable
5. **Check the .htaccess file**: Make sure the .htaccess file is properly configured

## Limitations

The PHP wrapper has some limitations:

1. **Performance**: There's some overhead in proxying requests
2. **WebSockets**: WebSockets are not supported
3. **File uploads**: Large file uploads may not work correctly
4. **Session handling**: Flask sessions may not work as expected

## Security Considerations

1. **HTTPS**: Use HTTPS for both your PHP hosting and Flask application
2. **API keys**: Don't expose sensitive API keys in your code
3. **Rate limiting**: Implement rate limiting to prevent abuse
4. **Input validation**: Validate all user input to prevent attacks

## Support

If you need help with the PHP wrapper, please contact us at support@remotehive.com.
