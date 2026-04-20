from django.urls import path
from app.controllers.browse_controller import browse

urlpatterns = [
    path("", browse, name="browse"),
]
