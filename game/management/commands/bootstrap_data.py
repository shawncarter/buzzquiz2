from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from game.models import GameSession, Player
import random
import string


def generate_game_code(length=6):
    """Generate a random game code."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


class Command(BaseCommand):
    help = 'Bootstrap initial data for development'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating superuser...')
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            self.stdout.write(self.style.SUCCESS('Superuser created successfully'))
        else:
            self.stdout.write(self.style.WARNING('Superuser already exists'))

        self.stdout.write('Creating sample game session...')
        game_code = generate_game_code()
        game = GameSession.objects.create(
            code=game_code,
            name="Sample Quiz Game",
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f'Sample game created with code: {game_code}'))

        self.stdout.write('Creating sample players...')
        sample_players = [
            {"name": "Alice", "buzzer_sound": "bell"},
            {"name": "Bob", "buzzer_sound": "buzzer"},
            {"name": "Charlie", "buzzer_sound": "ding"},
            {"name": "Diana", "buzzer_sound": "horn"}
        ]

        for i, player_data in enumerate(sample_players):
            Player.objects.create(
                game_session=game,
                name=player_data["name"],
                device_id=f"sample_device_{i}",
                buzzer_sound=player_data["buzzer_sound"],
                score=random.randint(0, 5)
            )

        self.stdout.write(self.style.SUCCESS('Sample players created successfully'))
        self.stdout.write(self.style.SUCCESS(f'Setup complete! Visit the game at /player/join/{game_code}/'))