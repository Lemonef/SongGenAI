from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    CREATOR = 'CREATOR'
    LISTENER = 'LISTENER'
    ROLE_CHOICES = [
        (CREATOR, 'Creator'),
        (LISTENER, 'Listener'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    favorites = models.ManyToManyField('Song', related_name='favorited_by', blank=True)

    def is_creator(self):
        return self.role == self.CREATOR

    def is_listener(self):
        return self.role == self.LISTENER

    def __str__(self):
        return f"{self.user.username} ({self.role})"
