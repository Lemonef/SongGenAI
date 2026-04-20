from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from app.services.playback_service import get_song_playback_info


@login_required
def play_song(request, song_id):
    """
    Returns song information and audio URL for the global playback bar.
    """
    try:
        info = get_song_playback_info(song_id)
        return JsonResponse({
            "status": "success",
            "song": info,
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=404)