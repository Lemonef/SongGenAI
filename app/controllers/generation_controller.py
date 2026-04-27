import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt

from app.models import Form, Song
from app.services.generation_service import generate_song_from_form
from app.services.song_manager_service import refund_credits_if_deducted
from app.strategies.exceptions import SunoOfflineError, SunoInsufficientCreditsError

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

        raw_duration = int(request.POST.get("requested_duration_seconds", 120))
        duration_seconds = max(120, min(360, raw_duration))

        form = Form.objects.create(
            creator=creator,
            prompt=request.POST.get("prompt", ""),
            genre=request.POST.get("genre", "Unknown"),
            mood=request.POST.get("mood", "Unknown"),
            tone=request.POST.get("tone", "Neutral"),
            occasion=request.POST.get("occasion", "General"),
            vocal_style=request.POST.get("vocal_style", "Any"),
            background_story=request.POST.get("background_story", ""),
            requested_title=request.POST.get("requested_title", "Untitled Song"),
            requested_duration_seconds=duration_seconds,
        )

        is_public = request.POST.get("is_public", "true").lower() == "true"
        force_mock = request.POST.get("force_mock", "false").lower() == "true"
        from django.conf import settings
        env_is_mock = getattr(settings, "GENERATOR_STRATEGY", "mock").lower() != "suno"
        use_mock = force_mock or env_is_mock

        # Credit Check (Only if not forcing mock)
        if not use_mock and creator.credit_balance <= 0:
            return JsonResponse({
                "status": "insufficient_credits",
                "message": "You have run out of credits. Would you like to use a Mock Song for free?"
            })

        try:
            song = generate_song_from_form(form, use_mock=use_mock)
        except SunoOfflineError:
            return JsonResponse({"status": "suno_offline"})
        except SunoInsufficientCreditsError:
            return JsonResponse({"status": "suno_no_credits"})
        except Exception as e:
            logger.warning(f"Suno generation failed: {str(e)}")
            return JsonResponse({"status": "suno_error"})

        # If editing an existing song, set version and parent
        parent_song_id = request.POST.get("parent_song_id")
        if parent_song_id:
            try:
                parent = Song.objects.get(id=int(parent_song_id), creator=creator)
                song.parent_song = parent
                song.version = parent.version + 1
            except Song.DoesNotExist:
                pass

        song.is_public = is_public
        song.save(update_fields=["is_public", "parent_song", "version"])

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
        "image_url": song.image_url,
        "duration_seconds": song.duration_seconds,
        "creator_name": song.creator.name,
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

    # Extract metadata
    audio_url = None
    image_url = None
    duration = None
    suno_tags = ""

    # Try different payload structures based on callback evolution
    if "data" in payload and isinstance(payload["data"], dict):
        resp_obj = payload["data"].get("response")
        if isinstance(resp_obj, dict):
            suno_data = resp_obj.get("sunoData") or []
            if isinstance(suno_data, list) and suno_data:
                audio_url = suno_data[0].get("audioUrl") or suno_data[0].get("audio_url")
                image_url = suno_data[0].get("imageUrl") or suno_data[0].get("image_url")
                duration = suno_data[0].get("duration") or suno_data[0].get("audio_duration")
                suno_tags = suno_data[0].get("tags") or ""

        # fallback
        if not audio_url:
            song_data_list = payload["data"].get("data") or []
            if isinstance(song_data_list, list) and song_data_list:
                audio_url = song_data_list[0].get("audio_url") or song_data_list[0].get("audioUrl")
                image_url = image_url or song_data_list[0].get("imageUrl") or song_data_list[0].get("image_url")
                duration = duration or song_data_list[0].get("duration") or song_data_list[0].get("audio_duration")
                suno_tags = suno_tags or song_data_list[0].get("tags") or ""
            elif "audioUrl" in payload["data"]:
                audio_url = payload["data"]["audioUrl"]
                image_url = image_url or payload["data"].get("imageUrl")
                duration = duration or payload["data"].get("duration") or payload["data"].get("audio_duration")

    if audio_url:
        song.audio_url = audio_url
        if image_url:
            song.image_url = image_url
        if duration:
            song.duration_seconds = int(float(duration))
        song.status = "SUCCESS"
        from app.strategies.mock_strategy import classify_explicit
        song.is_explicit = classify_explicit(song.form, suno_tags=suno_tags)
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
            refund_credits_if_deducted(song)
        # If it's something else like 'PROCESSING', we don't mark as FAILED
        # We just wait for the next callback or the poller to find the URL


    song.save()
    return JsonResponse({"message": "Callback processed", "song_id": song.id})
