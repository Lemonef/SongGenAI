from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

def home(request):
    return HttpResponse("SongGenAI Home")

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("generation/", include("app.routes.generation_urls")),
    path("playback/", include("app.routes.playback_urls")),
    path("manager/", include("app.routes.manager_urls")),
    path("user/", include("app.routes.user_urls")),
]