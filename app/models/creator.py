from django.db import models
from django.contrib.auth.models import User
from django.db.models import Sum

class Creator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='creator_profile')
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)

    @property
    def credit_balance(self):
        from .credit_transaction import CreditTransaction
        adds = self.credit_transactions.filter(transaction_type='ADD').aggregate(Sum('amount'))['amount__sum'] or 0
        deducts = self.credit_transactions.filter(transaction_type='DEDUCT').aggregate(Sum('amount'))['amount__sum'] or 0
        refunds = self.credit_transactions.filter(transaction_type='REFUND').aggregate(Sum('amount'))['amount__sum'] or 0
        return adds - deducts + refunds

    def __str__(self):
        return self.name or (self.user.username if self.user else "Unknown Creator")