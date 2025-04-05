// WebSocket Connection Test Script
document.addEventListener('DOMContentLoaded', function() {
    const testContainer = document.getElementById('websocket-test-container');
    if (!testContainer) return;

    // Create test elements
    const statusElement = document.createElement('div');
    statusElement.className = 'alert alert-info';
    statusElement.textContent = 'Testing WebSocket connection...';
    
    const detailsElement = document.createElement('pre');
    detailsElement.className = 'mt-3 p-3 bg-light';
    detailsElement.style.maxHeight = '200px';
    detailsElement.style.overflow = 'auto';
    
    testContainer.appendChild(statusElement);
    testContainer.appendChild(detailsElement);
    
    // Function to log messages
    function logMessage(message) {
        const timestamp = new Date().toISOString().split('T')[1].slice(0, -1);
        detailsElement.textContent += `[${timestamp}] ${message}\n`;
        detailsElement.scrollTop = detailsElement.scrollHeight;
    }
    
    // Test WebSocket connection
    try {
        logMessage('Starting WebSocket connection test');
        
        // Get game code from URL or data attribute
        const gameCode = testContainer.dataset.gameCode || window.location.pathname.split('/').filter(p => p).pop();
        
        if (!gameCode) {
            statusElement.className = 'alert alert-danger';
            statusElement.textContent = 'Error: Could not determine game code';
            logMessage('Could not determine game code from URL');
            return;
        }
        
        logMessage(`Using game code: ${gameCode}`);
        
        // Create WebSocket connection
        const wsProtocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';
        const wsUrl = `${wsProtocol}${window.location.host}/ws/game/${gameCode}/`;
        
        logMessage(`Connecting to: ${wsUrl}`);
        
        const socket = new WebSocket(wsUrl);
        
        socket.onopen = function(e) {
            statusElement.className = 'alert alert-success';
            statusElement.textContent = 'WebSocket connection established!';
            logMessage('Connection opened successfully');
            
            // Try sending a ping message
            socket.send(JSON.stringify({
                'type': 'ping',
                'data': 'Connection test from websocket_test.js'
            }));
            logMessage('Sent ping message');
        };
        
        socket.onmessage = function(e) {
            logMessage(`Received message: ${e.data}`);
            try {
                const data = JSON.parse(e.data);
                logMessage(`Message type: ${data.type}`);
            } catch (err) {
                logMessage(`Error parsing message: ${err.message}`);
            }
        };
        
        socket.onclose = function(e) {
            statusElement.className = 'alert alert-warning';
            statusElement.textContent = 'WebSocket connection closed';
            
            if (e.wasClean) {
                logMessage(`Connection closed cleanly, code=${e.code}, reason=${e.reason}`);
            } else {
                logMessage('Connection died');
            }
        };
        
        socket.onerror = function(error) {
            statusElement.className = 'alert alert-danger';
            statusElement.textContent = 'WebSocket error occurred';
            logMessage(`WebSocket Error: ${error.message}`);
            
            // Check for common issues
            const errorChecks = [
                `- Is the server running with Daphne or another ASGI server?`,
                `- Is the routing pattern correct? Current URL: ${wsUrl}`,
                `- Check server logs for exceptions`,
                `- Ensure CHANNEL_LAYERS is properly configured in settings.py`,
                `- Check ASGI_APPLICATION setting is correct`
            ];
            
            errorChecks.forEach(check => logMessage(check));
        };
    } catch (error) {
        statusElement.className = 'alert alert-danger';
        statusElement.textContent = 'Error setting up WebSocket test';
        logMessage(`Error: ${error.message}`);
    }
});