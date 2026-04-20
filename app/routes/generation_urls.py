from django.urls import path
from app.controllers.generation_controller import (
    generation_home,
    create_form_and_song,
    get_song_status,
    suno_callback,
)

urlpatterns = [
    path("", generation_home, name="generation_home"),
    path("create/", create_form_and_song, name="create_form_and_song"),
    path("status/<int:song_id>/", get_song_status, name="get_song_status"),
    path("suno/callback/", suno_callback, name="suno_callback"),
]
