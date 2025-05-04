<?php
/**
 * Remote Hive PHP Wrapper Test Script
 * 
 * This script tests the functionality of the PHP wrapper for the Remote Hive application.
 */

// Set content type to HTML
header('Content-Type: text/html; charset=utf-8');

// Function to test a URL and return the result
function test_url($url, $method = 'GET', $data = null) {
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_HEADER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 10);
    
    if ($method === 'POST') {
        curl_setopt($ch, CURLOPT_POST, true);
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
        }
    }
    
    $response = curl_exec($ch);
    $header_size = curl_getinfo($ch, CURLINFO_HEADER_SIZE);
    $status_code = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $content_type = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    $total_time = curl_getinfo($ch, CURLINFO_TOTAL_TIME);
    curl_close($ch);
    
    $headers = substr($response, 0, $header_size);
    $body = substr($response, $header_size);
    
    return [
        'status_code' => $status_code,
        'content_type' => $content_type,
        'total_time' => $total_time,
        'headers' => $headers,
        'body' => $body
    ];
}

// Get the base URL
$protocol = isset($_SERVER['HTTPS']) && $_SERVER['HTTPS'] === 'on' ? 'https' : 'http';
$host = $_SERVER['HTTP_HOST'];
$base_url = $protocol . '://' . $host;

// Define test cases
$test_cases = [
    [
        'name' => 'Home Page',
        'url' => $base_url . '/',
        'method' => 'GET',
        'expected_status' => 200,
        'expected_content_type' => 'text/html'
    ],
    [
        'name' => 'Static CSS File',
        'url' => $base_url . '/static/css/style.css',
        'method' => 'GET',
        'expected_status' => 200,
        'expected_content_type' => 'text/css'
    ],
    [
        'name' => 'Static JavaScript File',
        'url' => $base_url . '/static/js/main.js',
        'method' => 'GET',
        'expected_status' => 200,
        'expected_content_type' => 'application/javascript'
    ],
    [
        'name' => 'Login Page',
        'url' => $base_url . '/login',
        'method' => 'GET',
        'expected_status' => 200,
        'expected_content_type' => 'text/html'
    ],
    [
        'name' => 'API Endpoint',
        'url' => $base_url . '/api/jobs',
        'method' => 'GET',
        'expected_status' => 200,
        'expected_content_type' => 'application/json'
    ],
    [
        'name' => 'POST Request',
        'url' => $base_url . '/login',
        'method' => 'POST',
        'data' => 'username=test&password=test',
        'expected_status' => 200,
        'expected_content_type' => 'text/html'
    ],
    [
        'name' => 'Non-existent Page',
        'url' => $base_url . '/this-page-does-not-exist',
        'method' => 'GET',
        'expected_status' => 404,
        'expected_content_type' => 'text/html'
    ]
];

// Run the tests
$results = [];
foreach ($test_cases as $test) {
    $result = test_url($test['url'], $test['method'], $test['data'] ?? null);
    $results[] = [
        'test' => $test,
        'result' => $result,
        'passed' => $result['status_code'] === $test['expected_status'] && 
                   strpos($result['content_type'], $test['expected_content_type']) !== false
    ];
}

// Output the results
?>
<!DOCTYPE html>
<html>
<head>
    <title>Remote Hive PHP Wrapper Test Results</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        h1, h2 { color: #333; }
        .test { margin-bottom: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 4px; }
        .passed { background-color: #dff0d8; border-color: #d6e9c6; }
        .failed { background-color: #f2dede; border-color: #ebccd1; }
        .test h3 { margin-top: 0; }
        .details { margin-top: 10px; }
        .details table { width: 100%; border-collapse: collapse; }
        .details th, .details td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .details th { background-color: #f5f5f5; }
        pre { background-color: #f5f5f5; padding: 10px; overflow: auto; max-height: 300px; }
        .summary { margin-bottom: 20px; }
        .summary table { width: 100%; border-collapse: collapse; }
        .summary th, .summary td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        .summary th { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>Remote Hive PHP Wrapper Test Results</h1>
    
    <div class="summary">
        <h2>Summary</h2>
        <table>
            <tr>
                <th>Total Tests</th>
                <th>Passed</th>
                <th>Failed</th>
                <th>Success Rate</th>
            </tr>
            <tr>
                <td><?php echo count($results); ?></td>
                <td><?php echo count(array_filter($results, function($r) { return $r['passed']; })); ?></td>
                <td><?php echo count(array_filter($results, function($r) { return !$r['passed']; })); ?></td>
                <td><?php echo round(count(array_filter($results, function($r) { return $r['passed']; })) / count($results) * 100); ?>%</td>
            </tr>
        </table>
    </div>
    
    <h2>Test Details</h2>
    
    <?php foreach ($results as $index => $result): ?>
    <div class="test <?php echo $result['passed'] ? 'passed' : 'failed'; ?>">
        <h3>Test <?php echo $index + 1; ?>: <?php echo htmlspecialchars($result['test']['name']); ?></h3>
        <p>
            <strong>URL:</strong> <?php echo htmlspecialchars($result['test']['url']); ?><br>
            <strong>Method:</strong> <?php echo htmlspecialchars($result['test']['method']); ?><br>
            <strong>Status:</strong> <?php echo $result['result']['status_code']; ?> 
            (Expected: <?php echo $result['test']['expected_status']; ?>)<br>
            <strong>Content Type:</strong> <?php echo htmlspecialchars($result['result']['content_type']); ?> 
            (Expected: <?php echo htmlspecialchars($result['test']['expected_content_type']); ?>)<br>
            <strong>Response Time:</strong> <?php echo round($result['result']['total_time'] * 1000); ?> ms
        </p>
        
        <div class="details">
            <h4>Response Headers</h4>
            <pre><?php echo htmlspecialchars($result['result']['headers']); ?></pre>
            
            <h4>Response Body (first 500 characters)</h4>
            <pre><?php echo htmlspecialchars(substr($result['result']['body'], 0, 500)) . (strlen($result['result']['body']) > 500 ? '...' : ''); ?></pre>
        </div>
    </div>
    <?php endforeach; ?>
    
    <p><a href="<?php echo $base_url; ?>/?test=true">Run Configuration Tests</a></p>
    <p><a href="<?php echo $base_url; ?>/">Back to Main Site</a></p>
</body>
</html>
