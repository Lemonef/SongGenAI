from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models.song import Song


@login_required
def browse(request):
    songs = Song.objects.filter(is_public=True, status="SUCCESS").select_related('creator').order_by('-created_at')
    return render(request, 'browse/index.html', {'songs': songs})
