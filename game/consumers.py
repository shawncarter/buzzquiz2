import json
import logging
from typing import Dict, Any, List, Optional
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from .models import GameSession, Player, BuzzEvent

# Set up logging
logger = logging.getLogger('django.channels')


class GameConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for game communication."""
    
    async def connect(self):
        """Handle WebSocket connection."""
        try:
            self.game_code = self.scope['url_route']['kwargs']['game_code']
            self.game_group_name = f'game_{self.game_code}'
            
            logger.info(f"WebSocket connection attempt to game {self.game_code}")
            
            # Join the game group
            await self.channel_layer.group_add(
                self.game_group_name,
                self.channel_name
            )
            
            # Accept the connection
            await self.accept()
            logger.info(f"WebSocket connection accepted for game {self.game_code}")
            
            # Send game state to the new connection
            game_session = await self.get_game_session()
            if game_session:
                # First get player list
                players = await self.get_players()
                
                # Send state directly to this connection
                await self.send(text_data=json.dumps({
                    'type': 'game_state',
                    'game': game_session,
                    'players': players,
                    'current_round': game_session['current_round']
                }))
                
                # Also send player list separately to ensure it's properly processed
                await self.send(text_data=json.dumps({
                    'type': 'player_list',
                    'players': players
                }))
                
                logger.info(f"Game state sent to new connection {self.channel_name} for game {self.game_code}")
                
                # Broadcast to all clients that a new client has connected (for debugging)
                if len(players) > 0:
                    logger.info(f"Broadcasting player list with {len(players)} players to all clients")
                    await self.channel_layer.group_send(
                        self.game_group_name,
                        {
                            'type': 'player_list_message',
                            'players': players
                        }
                    )
            else:
                logger.warning(f"Game session not found for code {self.game_code}")
        except Exception as e:
            logger.error(f"Error in connect: {str(e)}")
            raise
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection."""
        # Leave the game group
        await self.channel_layer.group_discard(
            self.game_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle messages received from WebSocket."""
        try:
            logger.info(f"Received raw message: {text_data}")
            data = json.loads(text_data)
            message_type = data.get('type')
            
            logger.info(f"Processing message of type: {message_type} for game {self.game_code}")
            
            if message_type == 'buzz':
                await self.handle_buzz(data)
            elif message_type == 'join_game':
                await self.handle_join_game(data)
            elif message_type == 'start_round':
                logger.info(f"Handling start_round message: {data}")
                await self.handle_start_round(data)
            elif message_type == 'end_round':
                await self.handle_end_round(data)
            elif message_type == 'judge_answer':
                await self.handle_judge_answer(data)
            elif message_type == 'sync_time':
                await self.handle_sync_time(data)
            elif message_type == 'ping':
                await self.handle_ping(data)
            elif message_type == 'get_game_state':
                await self.handle_get_game_state(data)
            else:
                logger.warning(f"Unknown message type: {message_type} in game {self.game_code}")
        except json.JSONDecodeError:
            logger.error("JSON decode error in receive")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Error in receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': f'Error processing message: {str(e)}'
            }))
    
    async def handle_buzz(self, data):
        """Handle buzz event from player."""
        player_id = data.get('player_id')
        client_timestamp = data.get('timestamp')
        round_number = data.get('round')
        
        # Store buzz event
        await self.store_buzz_event(player_id, client_timestamp, round_number)
        
        # Get ordered buzzes for this round
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
    
    async def handle_join_game(self, data):
        """Handle new player joining the game."""
        player_name = data.get('name')
        device_id = data.get('device_id')
        buzzer_sound = data.get('buzzer_sound', 'default')
        
        # Register player
        player = await self.register_player(player_name, device_id, buzzer_sound)
        
        if player:
            # Broadcast updated player list
            players = await self.get_players()
            
            logger.info(f"Broadcasting updated player list with {len(players)} players")
            # Broadcast to the whole group including the host
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_list_message',
                    'players': players
                }
            )
            
            # Also broadcast full game state update to ensure all clients have latest data
            game = await self.get_game_session()
            if game:
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'game_state_message',
                        'game': game,
                        'players': players,
                        'current_round': game['current_round']
                    }
                )
            
            # Send confirmation to the player
            await self.send(text_data=json.dumps({
                'type': 'join_confirmed',
                'player_id': player['id'],
                'game_name': player['game_name'],
                'actual_name': player['name']  # Send back the actual name that was assigned
            }))
    
    async def handle_start_round(self, data):
        """Handle host starting a new round."""
        is_host = data.get('is_host', False)
        
        logger.info(f"Received start_round message: {data}, is_host={is_host}")
        
        if is_host:
            # Increment round
            new_round = await self.start_new_round()
            
            if new_round:
                logger.info(f"Starting round {new_round} for game {self.game_code}")
                
                # Important: Send a direct response to confirm receipt to the client that sent the request
                await self.send(text_data=json.dumps({
                    'type': 'start_round_confirmed',
                    'round': new_round
                }))
                
                # Broadcast round start to all clients
                message = {
                    'type': 'round_state_message',
                    'state': 'started',
                    'round': new_round
                }
                logger.info(f"Broadcasting message to group {self.game_group_name}: {message}")
                
                await self.channel_layer.group_send(
                    self.game_group_name,
                    message
                )
                
                # Also update game state for everyone to ensure synchronization
                game = await self.get_game_session()
                players = await self.get_players()
                
                if game:
                    await self.channel_layer.group_send(
                        self.game_group_name,
                        {
                            'type': 'game_state_message',
                            'game': game,
                            'players': players,
                            'current_round': new_round
                        }
                    )
            else:
                logger.error(f"Failed to start round for game {self.game_code}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to start round'
                }))
        else:
            logger.warning(f"Received start_round message but is_host is False: {data}")
    
    async def handle_end_round(self, data):
        """Handle host ending a round."""
        is_host = data.get('is_host', False)
        
        if is_host:
            game_session = await self.get_game_session()
            if game_session:
                current_round = game_session['current_round']
                
                # Broadcast round end
                await self.channel_layer.group_send(
                    self.game_group_name,
                    {
                        'type': 'round_state_message',
                        'state': 'ended',
                        'round': current_round
                    }
                )
    
    async def handle_judge_answer(self, data):
        """Handle host judging an answer."""
        is_host = data.get('is_host', False)
        
        if is_host:
            player_id = data.get('player_id')
            is_correct = data.get('is_correct')
            round_number = data.get('round')
            
            # Update buzz event
            await self.update_buzz_correctness(player_id, round_number, is_correct)
            
            # If correct, update player score
            if is_correct:
                await self.increment_player_score(player_id)
            
            # Get updated players for leaderboard
            players = await self.get_players()
            
            # Broadcast updated state
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_list_message',
                    'players': players
                }
            )
    
    async def handle_sync_time(self, data):
        """Handle time synchronization request."""
        client_time = data.get('client_time')
        receive_time = int(timezone.now().timestamp() * 1000)
        
        await self.send(text_data=json.dumps({
            'type': 'sync_time_response',
            'client_time': client_time,
            'server_time': receive_time
        }))
    
    async def handle_ping(self, data):
        """Handle ping message (for connection testing)."""
        logger.info(f"Received ping from client in game {self.game_code}")
        
        # Send a pong response
        await self.send(text_data=json.dumps({
            'type': 'pong',
            'timestamp': int(timezone.now().timestamp() * 1000),
            'message': 'Connection is working!'
        }))
        
    async def handle_get_game_state(self, data):
        """Handle request for current game state."""
        logger.info(f"Received get_game_state request from client in game {self.game_code}")
        
        # Get current game state
        game = await self.get_game_session()
        players = await self.get_players()
        
        if game:
            # Send directly to the requesting client
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'game': game,
                'players': players,
                'current_round': game['current_round']
            }))
            
            # Also send a player_list message specifically
            await self.send(text_data=json.dumps({
                'type': 'player_list',
                'players': players
            }))
            
            # For debugging, also broadcast to all clients
            await self.channel_layer.group_send(
                self.game_group_name,
                {
                    'type': 'player_list_message',
                    'players': players
                }
            )
    
    # Channel layer message handlers
    
    async def buzz_order_message(self, event):
        """Send buzz order to clients."""
        await self.send(text_data=json.dumps({
            'type': 'buzz_order',
            'ordered_buzzes': event['ordered_buzzes'],
            'round': event['round']
        }))
    
    async def player_list_message(self, event):
        """Send player list to clients."""
        await self.send(text_data=json.dumps({
            'type': 'player_list',
            'players': event['players']
        }))
    
    async def round_state_message(self, event):
        """Send round state to clients."""
        logger.info(f"Sending round state: {event['state']} for round {event['round']} to {self.channel_name}")
        
        message = {
            'type': 'round_state',
            'state': event['state'],
            'round': event['round']
        }
        
        logger.info(f"Sending message to client: {json.dumps(message)}")
        
        await self.send(text_data=json.dumps(message))
    
    async def game_state_message(self, event):
        """Send game state to clients."""
        logger.info(f"Sending game state to client {self.channel_name}")
        await self.send(text_data=json.dumps({
            'type': 'game_state',
            'game': event['game'],
            'players': event['players'],
            'current_round': event['current_round']
        }))
    
    # Database access methods
    
    @database_sync_to_async
    def get_game_session(self) -> Optional[Dict[str, Any]]:
        """Get game session by code."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            return {
                'id': game.id,
                'code': game.code,
                'name': game.name,
                'is_active': game.is_active,
                'current_round': game.current_round
            }
        except GameSession.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_players(self) -> List[Dict[str, Any]]:
        """Get all players in the current game."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            return [
                {
                    'id': player.id,
                    'name': player.name,
                    'score': player.score,
                    'buzzer_sound': player.buzzer_sound
                }
                for player in game.players.all().order_by('-score', 'name')
            ]
        except GameSession.DoesNotExist:
            return []
    
    @database_sync_to_async
    def register_player(self, name, device_id, buzzer_sound) -> Optional[Dict[str, Any]]:
        """Register a new player or update existing player."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            
            # Log player registration attempt
            logger.info(f"Registering player {name} with device_id {device_id} for game {self.game_code}")
            
            # Check if player with this device_id already exists
            existing_player = Player.objects.filter(
                game_session=game,
                device_id=device_id
            ).first()
            
            # Check for duplicate names in this game session
            if not existing_player:
                original_name = name
                suffix = 1
                
                # Keep checking and incrementing suffix until we find a unique name
                while Player.objects.filter(game_session=game, name=name).exists():
                    name = f"{original_name} ({suffix})"
                    suffix += 1
                    logger.info(f"Name {original_name} already taken, trying {name}")
                
                player = Player.objects.create(
                    game_session=game,
                    device_id=device_id,
                    name=name,
                    buzzer_sound=buzzer_sound
                )
                logger.info(f"Created new player: {name} (ID: {player.id})")
            else:
                # Update existing player
                existing_player.buzzer_sound = buzzer_sound
                # Only update name if not already taken by someone else
                if not Player.objects.filter(game_session=game, name=name).exclude(id=existing_player.id).exists():
                    existing_player.name = name
                existing_player.save()
                player = existing_player
                logger.info(f"Updated existing player: {player.name} (ID: {player.id})")
            
            return {
                'id': player.id,
                'name': player.name,
                'game_name': game.name,
                'buzzer_sound': player.buzzer_sound,
                'score': player.score
            }
        except GameSession.DoesNotExist:
            logger.error(f"Game not found with code {self.game_code} during player registration")
            return None
        except Exception as e:
            logger.error(f"Error registering player: {str(e)}")
            return None
    
    @database_sync_to_async
    def store_buzz_event(self, player_id, client_timestamp, round_number) -> None:
        """Store a buzz event in the database."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            player = Player.objects.get(id=player_id, game_session=game)
            
            BuzzEvent.objects.create(
                game_session=game,
                player=player,
                client_timestamp=client_timestamp,
                round_number=round_number
            )
        except (GameSession.DoesNotExist, Player.DoesNotExist):
            pass
    
    @database_sync_to_async
    def get_ordered_buzzes(self, round_number) -> List[Dict[str, Any]]:
        """Get ordered list of buzzes for a specific round."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            buzz_events = BuzzEvent.objects.filter(
                game_session=game,
                round_number=round_number
            ).order_by('client_timestamp')
            
            return [
                {
                    'id': buzz.id,
                    'player_id': buzz.player.id,
                    'player_name': buzz.player.name,
                    'timestamp': buzz.client_timestamp,
                    'is_correct': buzz.is_correct
                }
                for buzz in buzz_events
            ]
        except GameSession.DoesNotExist:
            return []
    
    @database_sync_to_async
    def update_buzz_correctness(self, player_id, round_number, is_correct) -> None:
        """Update the correctness of a buzz event."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            player = Player.objects.get(id=player_id)
            
            buzz = BuzzEvent.objects.get(
                game_session=game,
                player=player,
                round_number=round_number
            )
            
            buzz.is_correct = is_correct
            buzz.save()
        except (GameSession.DoesNotExist, Player.DoesNotExist, BuzzEvent.DoesNotExist):
            pass
    
    @database_sync_to_async
    def increment_player_score(self, player_id, points=1) -> None:
        """Increment a player's score."""
        try:
            player = Player.objects.get(id=player_id)
            player.increment_score(points)
        except Player.DoesNotExist:
            pass
    
    @database_sync_to_async
    def start_new_round(self) -> None:
        """Start a new round in the game."""
        try:
            game = GameSession.objects.get(code=self.game_code)
            old_round = game.current_round
            
            # Start new round
            game.start_new_round()
            
            # Confirm the round actually changed
            game.refresh_from_db()
            new_round = game.current_round
            
            logger.info(f"Round changed from {old_round} to {new_round} for game {self.game_code}")
            
            return new_round
        except GameSession.DoesNotExist:
            logger.error(f"Game not found with code {self.game_code} when starting new round")
            return None
        except Exception as e:
            logger.error(f"Error starting new round: {str(e)}")
            return None
    
    async def send_game_state(self) -> None:
        """Send the current game state to the connected client."""
        game = await self.get_game_session()
        players = await self.get_players()
        
        if game:
            await self.send(text_data=json.dumps({
                'type': 'game_state',
                'game': game,
                'players': players,
                'current_round': game['current_round']
            }))
            
            # Also send a separate player_list message to ensure player list is updated
            await self.send(text_data=json.dumps({
                'type': 'player_list',
                'players': players
            }))