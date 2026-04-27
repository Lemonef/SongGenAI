from django.db import models
from .creator import Creator


class Form(models.Model):
    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="forms"
    )
    prompt = models.TextField()
    genre = models.CharField(max_length=50)
    mood = models.CharField(max_length=50)
    tone = models.CharField(max_length=50, default="Neutral")
    occasion = models.CharField(max_length=100, default="General")
    vocal_style = models.CharField(max_length=100, default="Any")
    background_story = models.TextField(blank=True, default="")
    requested_title = models.CharField(max_length=100, default="Untitled Song")
    requested_duration_seconds = models.PositiveIntegerField(default=120)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Form #{self.id} - {self.genre}"