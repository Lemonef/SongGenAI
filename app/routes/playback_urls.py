from django.urls import path
from app.controllers.playback_controller import play_song

urlpatterns = [
    # API endpoints for global player
    path("play/<int:song_id>/", play_song, name="play_song"),
]