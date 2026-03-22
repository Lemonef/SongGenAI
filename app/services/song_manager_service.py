from django.shortcuts import get_object_or_404
from app.models import Song, Library, Share


def get_creator_song_history(creator):
    return Song.objects.filter(creator=creator).order_by("-created_at")


def add_song_to_library(library_id, song_id):
    library = get_object_or_404(Library, id=library_id)
    song = get_object_or_404(Song, id=song_id)

    library.songs.add(song)
    return library


def remove_song_from_library(library_id, song_id):
    library = get_object_or_404(Library, id=library_id)
    song = get_object_or_404(Song, id=song_id)

    library.songs.remove(song)
    return library


def get_library_songs(library_id):
    library = get_object_or_404(Library, id=library_id)
    return library.songs.all()


def create_share_for_song(song_id):
    song = get_object_or_404(Song, id=song_id)
    share = Share.objects.create(song=song)
    return share


def get_song_shares(song_id):
    song = get_object_or_404(Song, id=song_id)
    return song.shares.all()


def get_share_by_token(token):
    return get_object_or_404(Share, token=token)


def delete_share(share_id):
    share = get_object_or_404(Share, id=share_id)
    share.delete()