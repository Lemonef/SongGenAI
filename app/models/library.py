from django.db import models
from .creator import Creator
from .song import Song


class Library(models.Model):
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="libraries"
    )
    name = models.CharField(max_length=100)
    songs = models.ManyToManyField(
        Song,
        related_name="libraries",
        blank=True
    )

    def __str__(self):
        return self.name