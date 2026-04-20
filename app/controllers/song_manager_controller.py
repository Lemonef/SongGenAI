from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from app.models import Creator, Library
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
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return render(request, 'errors/not_creator.html', status=403)
    return render(request, 'manager/index.html')


@login_required
def default_song_history(request):
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
            }
            for song in songs
        ]
    })

@login_required
def list_libraries(request):
    user = request.user
    if not hasattr(user, 'profile') or not user.profile.is_creator():
        return JsonResponse({"error": "Only creators can view libraries."}, status=403)
    creator = user.creator_profile
    libraries = Library.objects.filter(creator=creator)
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
        if not hasattr(user, 'profile') or not user.profile.is_creator():
            return JsonResponse({"error": "Only creators can create libraries."}, status=403)
        data = json.loads(request.body)
        name = data.get("name", "New Library")
        creator = user.creator_profile
        library = Library.objects.create(creator=creator, name=name)
        return JsonResponse({"message": "Library created", "library_id": library.id, "library_name": library.name})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def library_detail(request, library_id):
    library = get_object_or_404(Library, id=library_id)
    songs = get_library_songs(library_id)

    return JsonResponse({
        "library_id": library.id,
        "library_name": library.name,
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
            }
            for song in songs
        ]
    })


@require_http_methods(["POST"])
def add_song(request, library_id, song_id):
    library = add_song_to_library(library_id, song_id)

    return JsonResponse({
        "message": "Song added to library",
        "library_id": library.id,
        "library_name": library.name,
    })


@require_http_methods(["POST"])
def remove_song(request, library_id, song_id):
    library = remove_song_from_library(library_id, song_id)

    return JsonResponse({
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