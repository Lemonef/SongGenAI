from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from app.models import Library, Song
from app.services.song_manager_service import (
    get_creator_song_history,
    add_song_to_library,
    remove_song_from_library,
    get_library_songs,
    create_share_for_song,
    get_song_shares,
    get_share_by_token,
    delete_share,
    toggle_song_favorite,
    get_user_favorite_ids,
    get_user_favorite_songs,
    delete_song as delete_song_service,
    get_song_edit_data,
)
import json

@login_required
def manager_home(request):
    """
    Main library page. Accessible to everyone with a profile.
    """
    if not hasattr(request.user, 'profile'):
        return render(request, 'errors/not_creator.html', status=403)
    return render(request, 'manager/index.html')


@login_required
def default_song_history(request):
    """
    Fetch history. Only relevant for creators.
    """
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return JsonResponse({"error": "Only creators can view history."}, status=403)
    
    creator = user.creator_profile
    songs = get_creator_song_history(creator)
    fav_ids = set(get_user_favorite_ids(user.profile))

    return JsonResponse({
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
                "audio_url": song.audio_url,
                "image_url": song.image_url,
                "creator_name": song.creator.name,
                "is_public": song.is_public,
                "is_explicit": song.is_explicit,
                "status": song.status,
                "failure_reason": song.failure_reason,
                "version": song.version,
                "parent_song_id": song.parent_song_id,
                "parent_song": {
                    "id": song.parent_song.id,
                    "title": song.parent_song.title,
                    "audio_url": song.parent_song.audio_url,
                    "image_url": song.parent_song.image_url,
                    "duration_seconds": song.parent_song.duration_seconds,
                    "created_at": song.parent_song.created_at.strftime("%d %b %Y, %H:%M"),
                    "version": song.parent_song.version,
                    "genre": song.parent_song.form.genre,
                    "mood": song.parent_song.form.mood,
                    "tone": song.parent_song.form.tone,
                    "occasion": song.parent_song.form.occasion,
                    "vocal_style": song.parent_song.form.vocal_style,
                } if song.parent_song_id and song.parent_song else None,
                "occasion": song.form.occasion,
                "genre": song.form.genre,
                "mood": song.form.mood,
                "tone": song.form.tone,
                "vocal_style": song.form.vocal_style,
                "background_story": song.form.background_story,
                "created_at": song.created_at.strftime("%d %b %Y, %H:%M"),
                "can_edit_visibility": (song.creator.user == user),
                "is_favorited": song.id in fav_ids,
            }
            for song in songs
        ]
    })

@login_required
def list_libraries(request):
    """
    List all libraries for the current user (Creator or Listener).
    """
    user = request.user
    if not hasattr(user, 'profile'):
         return JsonResponse({"error": "Profile not found."}, status=403)
    
    libraries = Library.objects.filter(profile=user.profile)
    return JsonResponse({
        "libraries": [
            {
                "id": lib.id,
                "name": lib.name
            }
            for lib in libraries
        ]
    })

@login_required
@require_http_methods(["POST"])
def create_library(request):
    try:
        user = request.user
        if not hasattr(user, 'profile'):
             return JsonResponse({"error": "Profile not found."}, status=403)
             
        data = json.loads(request.body)
        name = data.get("name", "New Library")
        library = Library.objects.create(profile=user.profile, name=name)
        return JsonResponse({"message": "Library created", "library_id": library.id, "library_name": library.name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def library_detail(request, library_id):
    user = request.user
    library = get_object_or_404(Library, id=library_id, profile=user.profile)
    songs = get_library_songs(library_id)
    fav_ids = set(get_user_favorite_ids(user.profile))

    return JsonResponse({
        "library_id": library.id,
        "library_name": library.name,
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
                "audio_url": song.audio_url,
                "image_url": song.image_url,
                "creator_name": song.creator.name,
                "is_public": song.is_public,
                "is_explicit": song.is_explicit,
                "status": song.status,
                "failure_reason": song.failure_reason,
                "version": song.version,
                "occasion": song.form.occasion,
                "genre": song.form.genre,
                "mood": song.form.mood,
                "created_at": song.created_at.strftime("%d %b %Y, %H:%M"),
                "can_edit_visibility": (song.creator.user == user),
                "is_favorited": song.id in fav_ids,
            }
            for song in songs
        ]
    })
    
@login_required
@require_http_methods(["POST"])
def delete_library(request, library_id):
    """
    Deletes a library. Enforces ownership.
    """
    user = request.user
    library = get_object_or_404(Library, id=library_id, profile=user.profile)
    library.delete()
    return JsonResponse({"status": "success", "message": "Library deleted."})

@login_required
@require_http_methods(["POST"])
def add_song(request, library_id, song_id):
    """
    Adds a song to a specific library. Enforces ownership of the library.
    """
    user = request.user
    if not hasattr(user, 'profile'):
        return JsonResponse({"error": "Profile not found."}, status=403)
        
    library = get_object_or_404(Library, id=library_id, profile=user.profile)
    song = get_object_or_404(Song, id=song_id)

    library.songs.add(song)
    
    return JsonResponse({
        "status": "success",
        "message": f"Added '{song.title}' to {library.name}.",
        "library_id": library.id,
        "library_name": library.name,
    })


@login_required
@require_http_methods(["POST"])
def remove_song(request, library_id, song_id):
    """
    Removes a song from a specific library. Enforces ownership.
    """
    user = request.user
    library = get_object_or_404(Library, id=library_id, profile=user.profile)
    song = get_object_or_404(Song, id=song_id)

    library.songs.remove(song)

    return JsonResponse({
        "status": "success",
        "message": "Song removed from library",
        "library_id": library.id,
        "library_name": library.name,
    })


@require_http_methods(["POST"])
def create_share(request, song_id):
    share = create_share_for_song(song_id)

    return JsonResponse({
        "message": "Share created successfully",
        "share_id": share.id,
        "song_id": share.song.id,
        "song_title": share.song.title,
        "token": str(share.token),
        "share_link": share.share_link,
    })


def list_song_shares(request, song_id):
    shares = get_song_shares(song_id)

    return JsonResponse({
        "song_id": song_id,
        "shares": [
            {
                "id": share.id,
                "token": str(share.token),
                "share_link": share.share_link,
                "created_at": share.created_at,
            }
            for share in shares
        ]
    })


@require_http_methods(["POST"])
def remove_share(request, share_id):
    delete_share(share_id)

    return JsonResponse({
        "message": "Share deleted successfully",
        "share_id": share_id,
    })

@login_required
@require_http_methods(["POST"])
def toggle_song_visibility(request, song_id):
    """
    Toggles a song's visibility (Public/Private).
    Only the original creator of the song can change its visibility.
    """
    song = get_object_or_404(Song, id=song_id)
    
    # Ownership Check: Only the creator (linked to user) can edit
    if not song.creator or song.creator.user != request.user:
        return JsonResponse({"error": "Only the creator of this song can change its visibility."}, status=403)
    
    song.is_public = not song.is_public
    song.save(update_fields=["is_public"])
    
    return JsonResponse({
        "status": "success",
        "is_public": song.is_public,
        "message": f"Song is now {'Public' if song.is_public else 'Private'}"
    })

@login_required # Anyone can help sync duration if they can play the song
@require_http_methods(["POST"])
def update_song_duration(request, song_id):
    """
    Updates the song's duration in the database if it's currently inaccurate.
    This helps fix '30s' placeholders with real metadata from the player.
    """
    song = get_object_or_404(Song, id=song_id)
    try:
        data = json.loads(request.body)
        new_duration = int(float(data.get("duration", 0)))
        
        # Only update if the current duration is the default placeholder (30) 
        # or if there is a significant discrepancy.
        if 0 < new_duration <= 3600: # Sanity check (max 1 hour)
            if song.duration_seconds == 30 or abs(song.duration_seconds - new_duration) > 5:
                song.duration_seconds = new_duration
                song.save(update_fields=["duration_seconds"])
                return JsonResponse({"status": "updated", "new_duration": new_duration})
                
        return JsonResponse({"status": "unchanged"})
    except (ValueError, json.JSONDecodeError):
        return JsonResponse({"error": "Invalid duration data"}, status=400)


@login_required
@require_http_methods(["POST"])
def toggle_favorite(request, song_id):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({"error": "Profile not found."}, status=403)
    is_fav = toggle_song_favorite(request.user.profile, song_id)
    return JsonResponse({"is_favorited": is_fav})


@login_required
def get_user_favorites(request):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({"error": "Profile not found."}, status=403)
    return JsonResponse({"favorite_ids": get_user_favorite_ids(request.user.profile)})


@login_required
def get_favorite_songs(request):
    if not hasattr(request.user, 'profile'):
        return JsonResponse({"error": "Profile not found."}, status=403)
    user = request.user
    songs = get_user_favorite_songs(user.profile)
    fav_ids = set(get_user_favorite_ids(user.profile))

    return JsonResponse({
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
                "audio_url": song.audio_url,
                "image_url": song.image_url,
                "creator_name": song.creator.name,
                "is_public": song.is_public,
                "is_explicit": song.is_explicit,
                "status": song.status,
                "failure_reason": song.failure_reason,
                "version": song.version,
                "occasion": song.form.occasion,
                "genre": song.form.genre,
                "mood": song.form.mood,
                "created_at": song.created_at.strftime("%d %b %Y, %H:%M"),
                "can_edit_visibility": hasattr(user, 'creator_profile') and song.creator.user == user,
                "is_favorited": song.id in fav_ids,
            }
            for song in songs
        ]
    })


@login_required
@require_http_methods(["POST"])
def reset_song_version(request, song_id):
    """Reset kept song to v1 with no parent after version comparison."""
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return JsonResponse({"error": "Only creators can do this."}, status=403)
    song = get_object_or_404(Song, id=song_id, creator=user.creator_profile)
    song.version = 1
    song.parent_song = None
    song.save(update_fields=["version", "parent_song"])
    return JsonResponse({"status": "success", "version": song.version})


@login_required
@require_http_methods(["POST"])
def delete_song(request, song_id):
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return JsonResponse({"error": "Only creators can delete songs."}, status=403)
    creator = user.creator_profile
    try:
        delete_song_service(song_id, creator)
        return JsonResponse({"status": "success", "message": "Song deleted."})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


@login_required
def get_song_edit_data_view(request, song_id):
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return JsonResponse({"error": "Only creators can edit songs."}, status=403)
    creator = user.creator_profile
    data = get_song_edit_data(song_id, creator)
    return JsonResponse(data)


@login_required
def open_shared_song(request, token):
    from app.models import Share
    share = get_object_or_404(Share, token=token)
    song = share.song
    return render(request, 'manager/share.html', {
        "song": song,
        "form": song.form,
        "share": share,
    })


@login_required
def song_profile(request, song_id):
    song = get_object_or_404(Song, id=song_id)
    if not song.is_public:
        if not hasattr(request.user, 'creator_profile') or song.creator.user != request.user:
            from django.http import Http404
            raise Http404
    return render(request, 'manager/share.html', {
        "song": song,
        "form": song.form,
        "share": None,
    })