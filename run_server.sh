#!/bin/bash
echo "Starting Buzz Quiz Game server with WebSocket support using Daphne..."
echo "Make sure you've installed all required packages: pip install -r requirements.txt"
echo

source venv/bin/activate

# Print versions of key packages
echo "Using Django $(python -c 'import django; print(django.__version__)')"
echo "Using Channels $(python -c 'import channels; print(channels.__version__)')"
echo "Using Daphne $(python -c 'import daphne; print(daphne.__version__)')"
echo

# Run the server
echo "Starting server on http://127.0.0.1:8000"
echo "WebSocket connections will be available at ws://127.0.0.1:8000/ws/game/<game_code>/"
echo
echo "=================================================================="
echo "IMPORTANT: Use this server instead of 'python manage.py runserver'"
echo "           for proper WebSocket support."
echo "=================================================================="
echo 
echo "Press Ctrl+C to stop the server."
echo

daphne -b 0.0.0.0 -p 8000 buzz_quiz_game.asgi:application -v2