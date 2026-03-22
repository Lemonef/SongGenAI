from django.db import models
from .creator import Creator
from .form import Form


class Song(models.Model):
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="songs"
    )
    form = models.OneToOneField(
        Form,
        on_delete=models.CASCADE,
        related_name="song"
    )
    title = models.CharField(max_length=100)
    duration_seconds = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title