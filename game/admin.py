from django.contrib import admin
from .models import GameSession, Player, BuzzEvent


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at', 'current_round', 'player_count')
    search_fields = ('code', 'name')
    list_filter = ('is_active', 'created_at')


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ('name', 'game_session', 'score', 'buzzer_sound')
    list_filter = ('game_session', 'buzzer_sound')
    search_fields = ('name', 'device_id')


@admin.register(BuzzEvent)
class BuzzEventAdmin(admin.ModelAdmin):
    list_display = ('player', 'game_session', 'round_number', 'formatted_client_time', 'is_correct')
    list_filter = ('game_session', 'round_number', 'is_correct')
    
    def formatted_client_time(self, obj):
        """Format the timestamp for readability."""
        from datetime import datetime
        dt = datetime.fromtimestamp(obj.client_timestamp / 1000)
        return dt.strftime('%H:%M:%S.%f')[:-3]
    
    formatted_client_time.short_description = 'Buzz Time'