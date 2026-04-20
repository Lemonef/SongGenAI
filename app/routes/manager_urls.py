from django.urls import path
from app.controllers.song_manager_controller import (
    manager_home,
    default_song_history,
    list_libraries,
    create_library,
    library_detail,
    add_song,
    remove_song,
    create_share,
    list_song_shares,
    open_shared_song,
    remove_share,
)

urlpatterns = [
    path("", manager_home, name="manager_home"),
    path("history/", default_song_history, name="default_song_history"),
    path("libraries/", list_libraries, name="list_libraries"),
    path("library/create/", create_library, name="create_library"),
    path("library/<int:library_id>/", library_detail, name="library_detail"),
    path("library/<int:library_id>/add-song/<int:song_id>/", add_song, name="add_song"),
    path("library/<int:library_id>/remove-song/<int:song_id>/", remove_song, name="remove_song"),

    path("song/<int:song_id>/shares/", list_song_shares, name="list_song_shares"),
    path("song/<int:song_id>/share/", create_share, name="create_share"),
    path("share/<uuid:token>/", open_shared_song, name="open_shared_song"),
    path("share/<int:share_id>/delete/", remove_share, name="remove_share"),
]