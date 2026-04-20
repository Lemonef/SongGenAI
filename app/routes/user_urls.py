from django.urls import path
from app.controllers.user_controller import user_home, creator_balance, onboarding_view

urlpatterns = [
    path("", user_home, name="user_home"),
    path("onboarding/", onboarding_view, name="onboarding"),
    path("balance/<int:creator_id>/", creator_balance, name="creator_balance"),
]