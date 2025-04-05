# Buzz Quiz Game

An interactive web-based quiz game platform where players can buzz in to answer questions. Perfect for classroom quizzes, trivia nights, or friendly competitions!

## Features

- Real-time buzzer system with millisecond precision
- Host interface for managing games and reviewing buzz order
- QR code generation for easy player joining
- Player leaderboard with scoring
- Custom buzzer sounds for each player
- Synchronization for accurate buzz timing

## Technology Stack

- Backend: Django with Django Channels for WebSocket support
- Database: SQLite (development) / PostgreSQL (production)
- Real-time Communication: WebSockets via Django Channels
- Frontend: HTML, CSS, JavaScript

## Setup

1. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run migrations:
   ```
   python manage.py migrate
   ```

4. Create a superuser (optional):
   ```
   python manage.py createsuperuser
   ```

5. Run the development server:
   ```
   python manage.py runserver
   ```

6. Visit `http://127.0.0.1:8000/` in your browser.

## How It Works

1. **Host creates a game**: The host creates a new game and gets a unique game code and QR code.
2. **Players join**: Players scan the QR code or enter the game code to join the game.
3. **Host starts a round**: The host starts a round when ready to ask a question.
4. **Players buzz in**: Players press their buzzer button to answer.
5. **System records buzzes**: The system records the buzz order with millisecond precision.
6. **Host sees results**: The host sees the ordered list of players who buzzed in.
7. **Host judges answers**: The host marks answers as correct/incorrect and awards points.

## Production Deployment

For production deployment:

1. Use PostgreSQL instead of SQLite
2. Configure Redis as the channel layer backend
3. Deploy using Daphne or uvicorn to serve the ASGI application
4. Implement HTTPS for secure WebSocket connections
5. Set up proper logging and monitoring