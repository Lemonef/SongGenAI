from django.db import models
from .creator import Creator
from .form import Form
from .song import Song


class CreditTransaction(models.Model):
    TRANSACTION_TYPES = [
        ("ADD", "Add"),
        ("DEDUCT", "Deduct"),
        ("REFUND", "Refund"),
    ]

    creator = models.ForeignKey(
        Creator,
        on_delete=models.CASCADE,
        related_name="credit_transactions"
    )
    form = models.ForeignKey(
        Form,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_transactions"
    )
    song = models.ForeignKey(
        Song,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="credit_transactions"
    )
    transaction_type = models.CharField(
        max_length=10,
        choices=TRANSACTION_TYPES
    )
    amount = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    note = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.transaction_type} {self.amount} for {self.creator.name}"