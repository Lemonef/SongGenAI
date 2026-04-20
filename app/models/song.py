from django.db import models
from .creator import Creator
from .form import Form


class Song(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("TEXT_SUCCESS", "Text Success"),
        ("FIRST_SUCCESS", "First Success"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
    ]

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
    audio_url = models.URLField(blank=True, default="")
    task_id = models.CharField(max_length=100, blank=True, default="")
    image_url = models.URLField(blank=True, default="")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title