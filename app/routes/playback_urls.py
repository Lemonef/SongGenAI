from django.urls import path
from app.controllers.playback_controller import playback_home, play_song

urlpatterns = [
    path("", playback_home, name="playback_home"),
    path("play/<int:song_id>/", play_song, name="play_song"),
]