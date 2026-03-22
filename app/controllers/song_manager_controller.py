from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

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


def manager_home(request):
    return HttpResponse("Manager page")


def creator_song_history(request, creator_id):
    creator = get_object_or_404(Creator, id=creator_id)
    songs = get_creator_song_history(creator)

    return JsonResponse({
        "creator": creator.name,
        "songs": [
            {
                "id": song.id,
                "title": song.title,
                "duration_seconds": song.duration_seconds,
            }
            for song in songs
        ]
    })


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


def add_song(request, library_id, song_id):
    library = add_song_to_library(library_id, song_id)

    return JsonResponse({
        "message": "Song added to library",
        "library_id": library.id,
        "library_name": library.name,
    })


def remove_song(request, library_id, song_id):
    library = remove_song_from_library(library_id, song_id)

    return JsonResponse({
        "message": "Song removed from library",
        "library_id": library.id,
        "library_name": library.name,
    })


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


def remove_share(request, share_id):
    delete_share(share_id)

    return JsonResponse({
        "message": "Share deleted successfully",
        "share_id": share_id,
    })