<?php
/**
 * Remote Hive PHP Wrapper
 * 
 * This script acts as a proxy between Hostinger PHP hosting and a Flask application
 * hosted elsewhere. It forwards all requests to the Flask application and returns
 * the responses.
 */

// Configuration
$config = [
    // URL of your Flask application hosted elsewhere (change this to your actual Flask app URL)
    'flask_app_url' => 'https://your-flask-app.example.com',
    
    // Enable debug mode (set to false in production)
    'debug' => true,
    
    // Cache settings
    'cache_enabled' => true,
    'cache_dir' => 'cache',
    'cache_time' => 3600, // 1 hour
    
    // Static files that should be served directly
    'static_dirs' => ['static', 'assets', 'images', 'css', 'js'],
    
    // File extensions that should be served with appropriate content types
    'content_types' => [
        'css' => 'text/css',
        'js' => 'application/javascript',
        'jpg' => 'image/jpeg',
        'jpeg' => 'image/jpeg',
        'png' => 'image/png',
        'gif' => 'image/gif',
        'svg' => 'image/svg+xml',
        'ico' => 'image/x-icon',
        'pdf' => 'application/pdf',
        'json' => 'application/json',
    ],
];

// Create cache directory if it doesn't exist
if ($config['cache_enabled'] && !is_dir($config['cache_dir'])) {
    mkdir($config['cache_dir'], 0755, true);
}

/**
 * Debug logging function
 */
function debug_log($message) {
    global $config;
    if ($config['debug']) {
        error_log('[RemoteHive] ' . $message);
    }
}

/**
 * Get the requested path
 */
function get_request_path() {
    $request_uri = $_SERVER['REQUEST_URI'];
    $path = parse_url($request_uri, PHP_URL_PATH);
    
    // Remove script name from path if it's included
    $script_name = $_SERVER['SCRIPT_NAME'];
    if (strpos($path, $script_name) === 0) {
        $path = substr($path, strlen($script_name));
    }
    
    // Ensure path starts with a slash
    if (empty($path) || $path[0] !== '/') {
        $path = '/' . $path;
    }
    
    return $path;
}

/**
 * Check if the request is for a static file
 */
function is_static_file($path) {
    global $config;
    
    // Extract the first directory from the path
    $parts = explode('/', trim($path, '/'));
    $first_dir = $parts[0] ?? '';
    
    // Check if it's in the static directories list
    return in_array($first_dir, $config['static_dirs']);
}

/**
 * Serve a static file directly
 */
function serve_static_file($path) {
    global $config;
    
    // Remove leading slash
    $file_path = ltrim($path, '/');
    
    // Check if file exists
    if (!file_exists($file_path)) {
        http_response_code(404);
        echo "File not found: $file_path";
        return;
    }
    
    // Get file extension
    $ext = pathinfo($file_path, PATHINFO_EXTENSION);
    
    // Set content type
    if (isset($config['content_types'][$ext])) {
        header('Content-Type: ' . $config['content_types'][$ext]);
    } else {
        header('Content-Type: application/octet-stream');
    }
    
    // Set cache headers
    $max_age = 86400; // 1 day
    header('Cache-Control: max-age=' . $max_age);
    header('Expires: ' . gmdate('D, d M Y H:i:s', time() + $max_age) . ' GMT');
    
    // Output file contents
    readfile($file_path);
}

/**
 * Generate a cache key for the current request
 */
function generate_cache_key() {
    $key = $_SERVER['REQUEST_METHOD'] . '_' . $_SERVER['REQUEST_URI'];
    
    // Add query string if present
    if (!empty($_SERVER['QUERY_STRING'])) {
        $key .= '_' . $_SERVER['QUERY_STRING'];
    }
    
    // Add POST data for POST requests
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $key .= '_' . md5(file_get_contents('php://input'));
    }
    
    // Make the key safe for filenames
    return md5($key);
}

/**
 * Check if a cached response exists and is still valid
 */
function get_cached_response() {
    global $config;
    
    if (!$config['cache_enabled']) {
        return false;
    }
    
    // Don't cache non-GET requests
    if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
        return false;
    }
    
    $cache_key = generate_cache_key();
    $cache_file = $config['cache_dir'] . '/' . $cache_key;
    
    if (file_exists($cache_file)) {
        $cache_time = filemtime($cache_file);
        
        // Check if cache is still valid
        if (time() - $cache_time < $config['cache_time']) {
            debug_log("Serving from cache: " . $_SERVER['REQUEST_URI']);
            
            // Get cached headers and content
            $cached_data = unserialize(file_get_contents($cache_file));
            
            // Set headers
            foreach ($cached_data['headers'] as $header) {
                header($header);
            }
            
            // Return content
            return $cached_data['content'];
        }
    }
    
    return false;
}

/**
 * Save a response to the cache
 */
function cache_response($headers, $content) {
    global $config;
    
    if (!$config['cache_enabled']) {
        return;
    }
    
    // Don't cache non-GET requests
    if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
        return;
    }
    
    // Don't cache if there's a Set-Cookie header
    foreach ($headers as $header) {
        if (strpos(strtolower($header), 'set-cookie:') === 0) {
            return;
        }
    }
    
    $cache_key = generate_cache_key();
    $cache_file = $config['cache_dir'] . '/' . $cache_key;
    
    $cached_data = [
        'headers' => $headers,
        'content' => $content
    ];
    
    file_put_contents($cache_file, serialize($cached_data));
    debug_log("Cached response: " . $_SERVER['REQUEST_URI']);
}

/**
 * Forward the request to the Flask application
 */
function forward_request() {
    global $config;
    
    // Get the requested path
    $path = get_request_path();
    debug_log("Forwarding request: " . $_SERVER['REQUEST_METHOD'] . " " . $path);
    
    // Check for cached response
    $cached_response = get_cached_response();
    if ($cached_response !== false) {
        echo $cached_response;
        return;
    }
    
    // Build the target URL
    $url = rtrim($config['flask_app_url'], '/') . $path;
    if (!empty($_SERVER['QUERY_STRING'])) {
        $url .= '?' . $_SERVER['QUERY_STRING'];
    }
    
    // Set up cURL to forward the request
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HEADER, true);
    
    // Forward request method
    curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $_SERVER['REQUEST_METHOD']);
    
    // Forward headers
    $headers = [];
    foreach (getallheaders() as $name => $value) {
        if (strtolower($name) != 'host' && strtolower($name) != 'connection') {
            $headers[] = "$name: $value";
        }
    }
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    
    // Forward POST data
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        curl_setopt($ch, CURLOPT_POSTFIELDS, file_get_contents('php://input'));
    }
    
    // Execute the request
    $response = curl_exec($ch);
    $header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
    $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    curl_close($ch);
    
    // Split headers and body
    $header_text = substr($response, 0, $header_size);
    $body = substr($response, $header_size);
    
    // Parse headers
    $headers = [];
    foreach (explode("\r\n", $header_text) as $header) {
        if (!empty($header)) {
            if (strpos($header, 'HTTP/') === 0) {
                // Skip the status line
                continue;
            }
            if (strpos($header, 'Transfer-Encoding:') === 0) {
                // Skip Transfer-Encoding header
                continue;
            }
            if (strpos($header, 'Connection:') === 0) {
                // Skip Connection header
                continue;
            }
            $headers[] = $header;
        }
    }
    
    // Set status code
    http_response_code($status_code);
    
    // Forward response headers
    foreach ($headers as $header) {
        header($header);
    }
    
    // Cache the response
    cache_response($headers, $body);
    
    // Output the response body
    echo $body;
}

/**
 * Check if this is a test request
 */
function is_test_request() {
    return isset($_GET['test']) && $_GET['test'] === 'true';
}

/**
 * Run tests to verify the wrapper is working
 */
function run_tests() {
    global $config;
    
    // Set content type to HTML
    header('Content-Type: text/html; charset=utf-8');
    
    echo '<!DOCTYPE html>
<html>
<head>
    <title>Remote Hive PHP Wrapper Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        h1 { color: #333; }
        .test { margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; }
        .success { background-color: #dff0d8; border-color: #d6e9c6; }
        .failure { background-color: #f2dede; border-color: #ebccd1; }
        .test h3 { margin-top: 0; }
        pre { background-color: #f5f5f5; padding: 10px; overflow: auto; }
    </style>
</head>
<body>
    <h1>Remote Hive PHP Wrapper Test</h1>
    <p>This page tests the functionality of the PHP wrapper for the Remote Hive application.</p>
    
    <div class="test">
        <h3>Configuration</h3>
        <pre>' . htmlspecialchars(print_r($config, true)) . '</pre>
    </div>';
    
    // Test 1: PHP Version
    $php_version = phpversion();
    $php_version_ok = version_compare($php_version, '7.0.0', '>=');
    echo '<div class="test ' . ($php_version_ok ? 'success' : 'failure') . '">
        <h3>PHP Version</h3>
        <p>Current version: ' . $php_version . '</p>
        <p>' . ($php_version_ok ? 'Success: PHP version is compatible.' : 'Failure: PHP version should be 7.0.0 or higher.') . '</p>
    </div>';
    
    // Test 2: cURL Extension
    $curl_enabled = function_exists('curl_init');
    echo '<div class="test ' . ($curl_enabled ? 'success' : 'failure') . '">
        <h3>cURL Extension</h3>
        <p>' . ($curl_enabled ? 'Success: cURL extension is enabled.' : 'Failure: cURL extension is required but not enabled.') . '</p>
    </div>';
    
    // Test 3: Cache Directory
    $cache_dir_writable = is_writable($config['cache_dir']);
    echo '<div class="test ' . ($cache_dir_writable ? 'success' : 'failure') . '">
        <h3>Cache Directory</h3>
        <p>Cache directory: ' . $config['cache_dir'] . '</p>
        <p>' . ($cache_dir_writable ? 'Success: Cache directory is writable.' : 'Failure: Cache directory is not writable.') . '</p>
    </div>';
    
    // Test 4: Flask App URL
    $flask_app_url = $config['flask_app_url'];
    $flask_app_url_valid = filter_var($flask_app_url, FILTER_VALIDATE_URL) !== false;
    echo '<div class="test ' . ($flask_app_url_valid ? 'success' : 'failure') . '">
        <h3>Flask App URL</h3>
        <p>URL: ' . $flask_app_url . '</p>
        <p>' . ($flask_app_url_valid ? 'Success: Flask app URL is valid.' : 'Failure: Flask app URL is not valid.') . '</p>
    </div>';
    
    // Test 5: Connection to Flask App
    $flask_app_reachable = false;
    $flask_app_response = '';
    if ($flask_app_url_valid) {
        $ch = curl_init($flask_app_url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_TIMEOUT, 5);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
        $flask_app_response = curl_exec($ch);
        $http_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);
        
        $flask_app_reachable = $http_code >= 200 && $http_code < 500;
    }
    echo '<div class="test ' . ($flask_app_reachable ? 'success' : 'failure') . '">
        <h3>Connection to Flask App</h3>
        <p>' . ($flask_app_reachable ? 'Success: Flask app is reachable.' : 'Failure: Could not connect to Flask app.') . '</p>
        <p>Note: If this test fails, make sure your Flask app is running and the URL is correct.</p>
    </div>';
    
    // Test 6: Static Files
    $static_dir_exists = is_dir('static');
    echo '<div class="test ' . ($static_dir_exists ? 'success' : 'failure') . '">
        <h3>Static Files Directory</h3>
        <p>' . ($static_dir_exists ? 'Success: Static directory exists.' : 'Warning: Static directory does not exist. Static files will not be served.') . '</p>
    </div>';
    
    echo '<div class="test">
        <h3>Request Information</h3>
        <pre>' . htmlspecialchars(print_r($_SERVER, true)) . '</pre>
    </div>';
    
    echo '<p><a href="' . $_SERVER['PHP_SELF'] . '">Back to Main Site</a></p>
</body>
</html>';
}

// Main execution
if (is_test_request()) {
    // Run tests
    run_tests();
} else if (is_static_file(get_request_path())) {
    // Serve static file
    serve_static_file(get_request_path());
} else {
    // Forward request to Flask app
    forward_request();
}
