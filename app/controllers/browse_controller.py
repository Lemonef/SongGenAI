from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from app.models.song import Song


@login_required
def browse(request):
    """
    Community browse page with search support.
    """
    query = request.GET.get('q', '')
    
    songs = Song.objects.filter(is_public=True, status="SUCCESS").select_related('creator')
    
    if query:
        songs = songs.filter(title__icontains=query)
        
    songs = songs.order_by('-created_at')
    favorite_ids = list(request.user.profile.favorites.values_list('id', flat=True)) if hasattr(request.user, 'profile') else []

    return render(request, 'browse/index.html', {
        'songs': songs,
        'query': query,
        'favorite_ids': favorite_ids,
    })
