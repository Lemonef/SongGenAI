from django.shortcuts import get_object_or_404
from app.models import Song


def get_song_for_playback(song_id):
    return get_object_or_404(Song, id=song_id)


def get_song_playback_info(song_id):
    song = get_object_or_404(Song, id=song_id)
    return {
        "id": song.id,
        "title": song.title,
        "duration_seconds": song.duration_seconds,
    }