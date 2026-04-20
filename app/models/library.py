from django.db import models
from .user_profile import UserProfile
from .song import Song


class Library(models.Model):
    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        related_name="libraries",
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    songs = models.ManyToManyField(
        Song,
        related_name="libraries",
        blank=True
    )

    def __str__(self):
        return self.name