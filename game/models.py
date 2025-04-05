from django.db import models
from django.utils import timezone
from typing import Optional


class GameSession(models.Model):
    """Game session model to track a quiz game instance."""
    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    current_round = models.PositiveIntegerField(default=1)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Game Session"
        verbose_name_plural = "Game Sessions"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.code})"
    
    @property
    def player_count(self) -> int:
        return self.players.count()
    
    def start_new_round(self) -> None:
        """Start a new round in the game."""
        self.current_round += 1
        self.save()


class Player(models.Model):
    """Player model for participants in the game."""
    game_session = models.ForeignKey(
        GameSession, 
        on_delete=models.CASCADE, 
        related_name='players'
    )
    name = models.CharField(max_length=50)
    device_id = models.CharField(max_length=100)
    buzzer_sound = models.CharField(max_length=20, default='default')
    score = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-score', 'name']
        verbose_name = "Player"
        verbose_name_plural = "Players"
        unique_together = [['game_session', 'name']]
    
    def __str__(self) -> str:
        return f"{self.name} in {self.game_session.code}"
    
    def increment_score(self, points: int = 1) -> None:
        """Increment the player's score."""
        self.score += points
        self.save()


class BuzzEvent(models.Model):
    """Model to track buzz events with timing information."""
    game_session = models.ForeignKey(
        GameSession, 
        on_delete=models.CASCADE, 
        related_name='buzz_events'
    )
    player = models.ForeignKey(
        Player, 
        on_delete=models.CASCADE, 
        related_name='buzz_events'
    )
    client_timestamp = models.BigIntegerField()  # Milliseconds since epoch from client
    server_timestamp = models.BigIntegerField(default=0)  # Milliseconds since epoch from server
    time_offset = models.IntegerField(default=0)  # Calculated offset in milliseconds
    round_number = models.PositiveIntegerField()
    is_correct = models.BooleanField(null=True, blank=True)  # True/False/None (not judged yet)
    
    class Meta:
        ordering = ['client_timestamp']
        verbose_name = "Buzz Event"
        verbose_name_plural = "Buzz Events"
    
    def __str__(self) -> str:
        return f"{self.player.name} buzzed in round {self.round_number}"
    
    def save(self, *args, **kwargs) -> None:
        """Override save to set server timestamp if not provided."""
        if not self.server_timestamp:
            self.server_timestamp = int(timezone.now().timestamp() * 1000)
        if not self.time_offset:
            self.time_offset = self.server_timestamp - self.client_timestamp
        super().save(*args, **kwargs)