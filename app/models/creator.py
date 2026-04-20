from django.db import models
from django.contrib.auth.models import User

class Creator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='creator_profile')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)

    def __str__(self):
        return self.name or (self.user.username if self.user else "Unknown Creator")