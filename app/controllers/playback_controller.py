from django.http import JsonResponse
from django.shortcuts import render
from app.services.playback_service import get_song_playback_info


def playback_home(request):
    return render(request, 'playback/index.html')


def play_song(request, song_id):
    info = get_song_playback_info(song_id)
    return JsonResponse({
        "message": "Mock playback started",
        "song": info,
    })