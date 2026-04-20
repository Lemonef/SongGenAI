import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from app.models import Creator, Form, Song
from app.services.generation_service import generate_song_from_form

logger = logging.getLogger(__name__)


@login_required
def generation_home(request):
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return render(request, 'errors/not_creator.html', status=403)
    return render(request, 'generation/index.html')


@login_required
@require_http_methods(["POST"])
def create_form_and_song(request):
    try:
        user = request.user
        if not hasattr(user, 'profile') or not user.profile.is_creator():
            return JsonResponse({"error": "Only creators can generate songs."}, status=403)
        creator = user.creator_profile

        form = Form.objects.create(
            creator=creator,
            prompt=request.POST.get("prompt", ""),
            genre=request.POST.get("genre", "Unknown"),
            mood=request.POST.get("mood", "Unknown"),
            requested_title=request.POST.get("requested_title", "Untitled Song"),
            requested_duration_seconds=int(request.POST.get("requested_duration_seconds", 30)),
        )

        is_public = request.POST.get("is_public", "true").lower() == "true"
        song = generate_song_from_form(form)
        song.is_public = is_public
        song.save(update_fields=["is_public"])

        return JsonResponse({
            "message": "Song created successfully",
            "form_id": form.id,
            "song_id": song.id,
            "song_title": song.title,
            "duration_seconds": song.duration_seconds,
            "status": song.status,
            "audio_url": song.audio_url,
            "task_id": song.task_id,
        })
    except ValueError as e:
        logger.error(f"ValueError in create_form_and_song: {str(e)}")
        return JsonResponse({"error": f"Invalid input: {str(e)}"}, status=400)
    except Exception as e:
        logger.error(f"Exception in create_form_and_song: {str(e)}", exc_info=True)
        return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)


@require_http_methods(["GET"])
def get_song_status(request, song_id):
    from app.models import Song
    song = get_object_or_404(Song, id=song_id)
    return JsonResponse({
        "song_id": song.id,
        "song_title": song.title,
        "status": song.status,
        "audio_url": song.audio_url,
        "task_id": song.task_id,
    })


@csrf_exempt
@require_http_methods(["POST"])
def suno_callback(request):
    print("[SUNO CALLBACK] Received callback request:", request.body)
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        print("[SUNO CALLBACK] Invalid JSON payload:", request.body)
        return JsonResponse({"error": "Invalid JSON payload"}, status=400)

    # Suno official format: payload['data']['task_id'], payload['data']['data'][0]['audio_url']
    data = payload.get("data") or {}
    task_id = data.get("task_id")
    if not task_id:
        return JsonResponse({"error": "Missing task_id in callback"}, status=400)

    song = Song.objects.filter(task_id=task_id).first()
    if not song:
        return JsonResponse({"error": "Song not found for task_id"}, status=404)

    # Extract audio_url
    audio_url = None
    
    # Try different payload structures based on callback evolution
    if "data" in payload and isinstance(payload["data"], dict):
        resp_obj = payload["data"].get("response")
        if isinstance(resp_obj, dict):
            suno_data = resp_obj.get("sunoData") or []
            if isinstance(suno_data, list) and suno_data:
                audio_url = suno_data[0].get("audioUrl") or suno_data[0].get("audio_url")
                
        # fallback as before
        if not audio_url:
            song_data_list = payload["data"].get("data") or []
            if isinstance(song_data_list, list) and song_data_list:
                audio_url = song_data_list[0].get("audio_url") or song_data_list[0].get("audioUrl")
            elif "audioUrl" in payload["data"]:
                 audio_url = payload["data"]["audioUrl"]

    if audio_url:
        song.audio_url = audio_url
        song.status = "SUCCESS"
    else:
        # Fallback to status from payload if present
        payload_status = data.get("status")
        # Only update status if it is a terminal state (SUCCESS/FAILED)
        # If it is intermediate (e.g. PROCESSING, QUEUED), leave it as is or update it
        # but avoid the logic that forced it to FAILED previously
        if payload_status == "SUCCESS":
            # If we don't have an audio_url yet, leave it as is (likely PENDING)
            pass
        elif payload_status == "FAILED":
            song.status = "FAILED"
        # If it's something else like 'PROCESSING', we don't mark as FAILED
        # We just wait for the next callback or the poller to find the URL


    song.save()
    return JsonResponse({"message": "Callback processed", "song_id": song.id})
