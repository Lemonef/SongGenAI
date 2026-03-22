from django.http import HttpResponse, JsonResponse
from app.services.playback_service import get_song_playback_info


def playback_home(request):
    return HttpResponse("Playback page")


def play_song(request, song_id):
    info = get_song_playback_info(song_id)
    return JsonResponse({
        "message": "Mock playback started",
        "song": info,
    })