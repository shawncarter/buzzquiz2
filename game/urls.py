from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('host/create/', views.HostCreateView.as_view(), name='host_create'),
    path('host/game/<str:game_code>/', views.HostGameView.as_view(), name='host_game'),
    path('player/join/<str:game_code>/', views.PlayerJoinView.as_view(), name='player_join'),
    path('player/game/<str:game_code>/<str:player_name>/', views.PlayerGameView.as_view(), name='player_game'),
    path('api/sync-time/', views.SyncTimeView.as_view(), name='sync_time'),
    path('diagnostics/websocket/<str:game_code>/', views.WebSocketTestView.as_view(), name='websocket_test'),
    path('diagnostics/test-game/<str:game_code>/', views.TestGameView.as_view(), name='test_game'),
]