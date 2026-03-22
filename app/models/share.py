from django.db import models
from .song import Song
import uuid


class Share(models.Model):
    song = models.ForeignKey(
        Song,
        on_delete=models.CASCADE,
        related_name="shares"
    )
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Share #{self.id} for {self.song.title}"

    @property
    def share_link(self):
        return f"/manager/share/{self.token}/"