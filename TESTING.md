# Testing the Buzz Quiz Game

This document provides instructions for testing the Buzz Quiz Game, particularly the WebSocket connections and game functionality.

## Running the Server

To properly test the game with WebSocket support, you **must** run the server using the provided script:

```bash
./run_server.sh
```

This starts the Daphne ASGI server which is required for WebSocket connections. Using the standard Django development server (`python manage.py runserver`) will not properly support WebSockets.

## Test Game Interface

A dedicated test interface is available to help debug WebSocket connections and game functionality. You can access it at:

```
/diagnostics/test-game/<game_code>/
```

Or click on the "Test Game Interface" link from the host game page.

### Using the Test Interface

1. Enter a valid game code and click "Connect"
2. To simulate a player:
   - Enter a player name
   - Click "Register Player"
   - Use the "Buzz!" button when a round is active
3. To simulate the host:
   - Use the "Start Round" and "End Round" buttons
   - Check the log for events and messages

The test interface logs all WebSocket communication, making it easy to debug issues.

## Common Issues and Solutions

### Multiple Players on Same Device

Each player now gets a unique device ID, even on the same computer, so you can test with multiple browser tabs.

### Game Round Not Starting

If clicking the "Start Round" button doesn't work:

1. Check that you're running the server with `./run_server.sh`
2. Look at the server console for any error messages
3. Ensure the game session exists in the database
4. Use the test interface to see detailed logs

### No Real-time Updates

If the game doesn't update in real-time:

1. Check browser console for WebSocket errors
2. Ensure ASGI configuration is correct
3. Verify the WebSocket URL format is correct

## WebSocket Connection Diagnostics

For advanced debugging of WebSocket connections, use the dedicated diagnostics page:

```
/diagnostics/websocket/<game_code>/
```

This page tests the raw WebSocket connection and reports any issues.