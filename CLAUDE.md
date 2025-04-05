# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Lint/Test Commands
- Setup: `python -m pip install -r requirements.txt`
- Run server: `python manage.py runserver`
- Run tests: `python manage.py test`
- Run single test: `python manage.py test game.tests.TestCaseName.test_method_name`
- Lint: `flake8`
- Type check: `mypy .`

## Code Style Guidelines
- Formatting: Follow PEP 8 with 120 character line limit
- Imports: Group standard library, Django packages, and local imports with a blank line between
- Types: Use type hints for function parameters and return values
- Naming: Use snake_case for variables/functions, CamelCase for classes
- Django models: Define Meta class with ordering and verbose names
- WebSockets: Handle connections gracefully with error handling
- JS: Use modern ES6+ syntax with consistent promise handling
- Time: Use millisecond precision for all buzz-related timestamps
- Error handling: Use try/except blocks with specific exceptions

# Buzz Quiz Game System Requirements Document

## Overview

The Buzz Quiz Game System is a web-based application allowing a host to run interactive quiz games where players join via mobile devices and compete to answer questions by being the first to "buzz in." The system tracks the exact timing of player buzzes with millisecond precision to determine who buzzed first, second, third, etc.

## System Architecture

The application will use the following technologies:
- Backend: Django with Django Channels for WebSocket support
- Database: SQLite in development (PostgreSQL recommended for production)
- Frontend: HTML, CSS, JavaScript
- Real-time Communication: WebSockets via Django Channels
- Channel Layer: In-memory for development (Redis recommended for production)

## Functional Requirements

### 1. Game Session Management

1.1. Host Interface
- Create new game sessions with custom names
- Generate and display a QR code for players to join
- View list of connected players
- Start and stop game rounds
- View buzz results in real-time with accurate timing information
- Mark player answers as correct or incorrect
- End game sessions and view final results

1.2. Player Interface
- Join a game by scanning QR code or entering game code
- Register with a name
- Select a buzzer sound from predefined options
- View game status (waiting, active round, etc.)
- Press a buzz button during active rounds
- See their position in the buzz order after each round
- View their current score and standing

### 2. User Management

2.1. Player Recognition
- Store device ID in browser cookies
- Remember returning players' names and preferences
- Allow players to update their information

2.2. Host Authentication
- Simple password protection for host interface
- Session persistence for hosts

### 3. Real-time Communication

3.1. WebSocket Connection
- Establish persistent WebSocket connections between server and clients
- Handle connection/disconnection gracefully
- Broadcast game state changes to all connected clients

3.2. Time Synchronization
- Implement clock synchronization protocol between server and clients
- Account for network latency in timing calculations
- Store both client and server timestamps for buzz events
- Calculate time offsets for accurate comparison

### 4. Game Flow

4.1. Game Setup
- Host creates game with unique code
- QR code generated linking to player join page
- Players scan code and enter name/select buzzer sound
- Host sees connected players in real-time

4.2. Round Flow
- Host manually starts a round
- Host asks a question verbally
- Players can buzz in by tapping their button
- System records buzz timestamps and orders players by time
- Host sees ordered list of players who buzzed
- Host selects player to answer (typically the first to buzz)
- Host marks answer as correct/incorrect
- Host ends round and can start a new one

4.3. Scoring
- Track correct/incorrect answers for each player
- Maintain leaderboard based on correct answers
- Optional: Implement weighted scoring based on buzz speed

## Technical Requirements

### 5. Django Models

5.1. GameSession Model
- Unique game code
- Session name
- Active/inactive status
- Creation timestamp
- Current round number

5.2. Player Model
- Foreign key to GameSession
- Player name
- Device ID for recognition
- Selected buzzer sound
- Score

5.3. BuzzEvent Model
- Foreign key to GameSession
- Foreign key to Player
- Client timestamp (provided by player device)
- Server timestamp (when server received buzz)
- Time offset (calculated)
- Round number
- Correctness status (true/false/null)

### 6. WebSocket Implementation

6.1. Channel Configuration
- Configure Django Channels
- Set up channel layer (InMemory for dev, Redis for production)
- Define routing for WebSocket connections

6.2. Game Consumer
- Handle WebSocket connections based on game code
- Process different message types (buzz, join, game state changes, etc.)
- Broadcast updates to all connected clients
- Access database models asynchronously

### 7. Views and URLs

7.1. Host Views
- Create game form
- Game management dashboard
- QR code generation
- Game results view

7.2. Player Views
- Join game form
- Buzzer interface
- Game status display
- Results view

7.3. API Endpoints
- Time synchronization
- Player registration
- Game state queries

### 8. Frontend Implementation

8.1. Host Interface
- Clean, intuitive dashboard
- Real-time updates without page refresh
- Clear display of buzz order with timing
- Easy controls for managing game flow

8.2. Player Interface
- Mobile-friendly design
- Large, easy-to-hit buzzer button
- Clear feedback on buzz actions
- Status indicators for game state
- Responsive design for various devices

8.3. JavaScript Functions
- WebSocket connection management
- Time synchronization
- Buzz event handling
- UI updates based on game state

## Non-Functional Requirements

### 9. Performance Requirements

9.1. Timing Accuracy
- Buzz timing accurate to within 50ms
- Regular time synchronization to maintain accuracy

9.2. Responsiveness
- Maximum latency of 100ms for buzz registration
- Real-time updates to all clients within 200ms

9.3. Scalability
- Support for at least 50 concurrent players per game
- Multiple simultaneous game sessions

### 10. Security Requirements

10.1. Data Protection
- Secure WebSocket connections
- Protection against common web vulnerabilities
- Basic rate limiting to prevent abuse

10.2. Access Control
- Only hosts can control game flow
- Players can only interact with their own buzzer

### 11. User Experience Requirements

11.1. Accessibility
- High contrast interface
- Screen reader compatibility
- Keyboard navigation support

11.2. Usability
- Intuitive interface requiring minimal instruction
- Clear feedback for all user actions
- Engaging visual and audio feedback

## Project Structure

The project should follow a standard Django structure with the following additions:

```
buzz_quiz_game/
├── manage.py
├── buzz_quiz_game/  # Project directory
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── routing.py  # WebSocket routing
├── game/  # Main app
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── consumers.py  # WebSocket consumers
│   ├── models.py
│   ├── routing.py  # App-level routing
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── static/
│   ├── css/
│   ├── js/
│   └── sounds/  # Buzzer sound files
└── templates/
    └── game/
        ├── host_create.html
        ├── host_game.html
        ├── player_join.html
        └── player_game.html
```

## Implementation Details

### Key Components

1. **Time Synchronization Protocol**:
   ```python
   # views.py
   def sync_time(request):
       return JsonResponse({'server_time': int(time.time() * 1000)})
   ```

   ```javascript
   // client-side
   function syncTime() {
       const clientTime = Date.now();
       fetch('/api/sync-time/')
           .then(response => response.json())
           .then(data => {
               const receiveTime = Date.now();
               const roundTripTime = receiveTime - clientTime;
               const estimatedServerTime = data.server_time + (roundTripTime / 2);
               const offset = estimatedServerTime - receiveTime;
               localStorage.setItem('timeOffset', offset);
           });
   }
   ```

2. **Buzz Handling**:
   ```javascript
   // client-side
   function buzz() {
       const offset = parseInt(localStorage.getItem('timeOffset') || '0');
       const clientTime = Date.now();
       const adjustedTime = clientTime + offset;
       
       socket.send(JSON.stringify({
           'type': 'buzz',
           'player_id': playerId,
           'timestamp': adjustedTime,
           'round': currentRound
       }));
       
       // UI feedback
       buzzerButton.classList.add('active');
       playBuzzerSound();
   }
   ```

3. **WebSocket Consumer Core Logic**:
   ```python
   # consumers.py
   async def receive(self, text_data):
       data = json.loads(text_data)
       message_type = data.get('type')
       
       if message_type == 'buzz':
           player_id = data.get('player_id')
           client_timestamp = data.get('timestamp')
           round_number = data.get('round')
           
           # Store buzz event
           await self.store_buzz(player_id, client_timestamp, round_number)
           
           # Get ordered buzz list for this round
           ordered_buzzes = await self.get_ordered_buzzes(round_number)
           
           # Broadcast to all clients
           await self.channel_layer.group_send(
               self.game_group_name,
               {
                   'type': 'buzz_order_message',
                   'ordered_buzzes': ordered_buzzes,
                   'round': round_number
               }
           )
   ```

## Deployment Recommendations

For production deployment:

1. Use PostgreSQL instead of SQLite
2. Configure Redis as the channel layer backend
3. Deploy using Daphne or uvicorn to serve the ASGI application
4. Consider adding HTTPS for secure WebSocket connections
5. Implement proper error logging and monitoring

## Acceptance Criteria

The system will be considered complete when:

1. Hosts can create games and generate QR codes
2. Players can join via QR code or game code
3. Time synchronization is implemented and working
4. Buzz timing is accurate to within 50ms
5. Host can see ordered list of buzzes with timing
6. Host can mark answers as correct/incorrect
7. Multiple concurrent games work without interference
8. Player state persists between sessions
9. UI is responsive and mobile-friendly
10. System can handle at least 50 players without performance degradation
