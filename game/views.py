import json
import random
import string
import time
from typing import Dict, Any

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse, HttpRequest
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View, TemplateView, FormView
from django.conf import settings

from .models import GameSession, Player, BuzzEvent


def generate_game_code(length=6) -> str:
    """Generate a random game code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class HomeView(TemplateView):
    """Home page view."""
    template_name = 'game/home.html'


class HostCreateView(TemplateView):
    """View for host to create a new game."""
    template_name = 'game/host_create.html'
    
    def post(self, request: HttpRequest, *args, **kwargs) -> HttpResponse:
        """Handle game creation form submission."""
        game_name = request.POST.get('game_name', 'Quiz Game')
        
        # Generate a unique game code
        while True:
            game_code = generate_game_code()
            if not GameSession.objects.filter(code=game_code).exists():
                break
        
        # Create the game session
        game = GameSession.objects.create(
            code=game_code,
            name=game_name,
            is_active=True
        )
        
        # Redirect to the host game page
        return redirect(reverse('host_game', kwargs={'game_code': game_code}))


class HostGameView(TemplateView):
    """View for the host's game dashboard."""
    template_name = 'game/host_game.html'
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add game data to context."""
        context = super().get_context_data(**kwargs)
        game_code = self.kwargs.get('game_code')
        
        game = get_object_or_404(GameSession, code=game_code)
        players = game.players.all().order_by('-score', 'name')
        
        context.update({
            'game': game,
            'players': players,
            'game_url': self.request.build_absolute_uri(
                reverse('player_join', kwargs={'game_code': game_code})
            )
        })
        
        return context


class PlayerJoinView(TemplateView):
    """View for players to join a game."""
    template_name = 'game/player_join.html'
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests and validate game code."""
        game_code = self.kwargs.get('game_code')
        
        try:
            # Check if game exists and is active
            GameSession.objects.get(code=game_code, is_active=True)
            return super().get(request, *args, **kwargs)
        except GameSession.DoesNotExist:
            # Render an error message for non-existent or inactive games
            return render(request, 'game/game_error.html', {
                'error_message': f"Game with code '{game_code}' does not exist or is no longer active.",
                'back_url': reverse('home')
            })
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add game data to context."""
        context = super().get_context_data(**kwargs)
        game_code = self.kwargs.get('game_code')
        
        # We can safely use get_object_or_404 here since we've already checked in get()
        game = get_object_or_404(GameSession, code=game_code)
        
        context.update({
            'game': game,
            'buzzer_sounds': [
                {'id': 'default', 'name': 'Default'},
                {'id': 'bell', 'name': 'Bell'},
                {'id': 'buzzer', 'name': 'Buzzer'},
                {'id': 'ding', 'name': 'Ding'},
                {'id': 'horn', 'name': 'Horn'},
            ]
        })
        
        return context


class PlayerGameView(TemplateView):
    """View for the player's game interface."""
    template_name = 'game/player_game.html'
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests and validate game code."""
        game_code = self.kwargs.get('game_code')
        
        try:
            # Check if game exists and is active
            GameSession.objects.get(code=game_code, is_active=True)
            return super().get(request, *args, **kwargs)
        except GameSession.DoesNotExist:
            # Render an error message for non-existent or inactive games
            return render(request, 'game/game_error.html', {
                'error_message': f"Game with code '{game_code}' does not exist or is no longer active.",
                'back_url': reverse('home')
            })
    
    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        """Add game data to context."""
        context = super().get_context_data(**kwargs)
        game_code = self.kwargs.get('game_code')
        player_name = self.kwargs.get('player_name')
        
        game = get_object_or_404(GameSession, code=game_code)
        
        context.update({
            'game': game,
            'player_name': player_name
        })
        
        return context


class WebSocketTestView(TemplateView):
    """View for testing WebSocket connections."""
    template_name = 'game/websocket_test.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['game_code'] = self.kwargs.get('game_code')
        return context


class TestGameView(TemplateView):
    """View for testing the game with a single interface."""
    template_name = 'game/test_game.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['game_code'] = self.kwargs.get('game_code')
        context['current_time'] = int(time.time())
        return context


@method_decorator(csrf_exempt, name='dispatch')
class SyncTimeView(View):
    """View for time synchronization."""
    
    def get(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Handle GET requests."""
        return JsonResponse({
            'server_time': int(time.time() * 1000)
        })
    
    def post(self, request: HttpRequest, *args, **kwargs) -> JsonResponse:
        """Handle POST requests."""
        try:
            data = json.loads(request.body)
            client_time = data.get('client_time')
            server_time = int(time.time() * 1000)
            
            return JsonResponse({
                'client_time': client_time,
                'server_time': server_time
            })
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)