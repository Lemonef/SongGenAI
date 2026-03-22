from django.urls import path
from app.controllers.user_controller import user_home, creator_balance

urlpatterns = [
    path("", user_home, name="user_home"),
    path("balance/<int:creator_id>/", creator_balance, name="creator_balance"),
]