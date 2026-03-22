from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods

from app.models import Creator, Form
from app.services.generation_service import create_mock_song_from_form


def generation_home(request):
    return HttpResponse("Generation page")


@require_http_methods(["POST"])
def create_form_and_song(request):
    creator = Creator.objects.get(id=request.POST.get("creator_id"))

    form = Form.objects.create(
        creator=creator,
        prompt=request.POST.get("prompt", ""),
        genre=request.POST.get("genre", "unknown"),
        mood=request.POST.get("mood", "unknown"),
        requested_title=request.POST.get("requested_title", "Untitled Song"),
        requested_duration_seconds=int(request.POST.get("requested_duration_seconds", 30)),
    )

    song = create_mock_song_from_form(form)

    return JsonResponse({
        "message": "Song created successfully",
        "form_id": form.id,
        "song_id": song.id,
        "song_title": song.title,
    })