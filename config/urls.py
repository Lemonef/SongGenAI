from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

def home(request):
    return render(request, 'home.html')

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("accounts/", include("allauth.urls")),
    path("generation/", include("app.routes.generation_urls")),
    path("browse/", include("app.routes.browse_urls")),
    path("playback/", include("app.routes.playback_urls")),
    path("manager/", include("app.routes.manager_urls")),
    path("user/", include("app.routes.user_urls")),
]