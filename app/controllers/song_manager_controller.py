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

    return JsonResponse({
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
                "audio_url": song.audio_url,
                "creator_name": song.creator.name,
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

    return JsonResponse({
        "library_id": library.id,
        "library_name": library.name,
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
                "audio_url": song.audio_url,
                "creator_name": song.creator.name,
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


def open_shared_song(request, token):
    share = get_share_by_token(token)

    return JsonResponse({
        "message": "Shared song opened",
        "song_id": share.song.id,
        "song_title": share.song.title,
        "duration_seconds": share.song.duration_seconds,
    })


@require_http_methods(["POST"])
def remove_share(request, share_id):
    delete_share(share_id)

    return JsonResponse({
        "message": "Share deleted successfully",
        "share_id": share_id,
    })