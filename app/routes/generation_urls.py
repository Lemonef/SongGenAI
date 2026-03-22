from django.urls import path
from app.controllers.generation_controller import generation_home, create_form_and_song

urlpatterns = [
    path("", generation_home, name="generation_home"),
    path("create/", create_form_and_song, name="create_form_and_song"),
]