from django.db.models import Sum, Case, When, IntegerField, F


def get_creator_balance(creator):
    result = creator.credit_transactions.aggregate(
        balance=Sum(
            Case(
                When(transaction_type="ADD", then=F("amount")),
                When(transaction_type="REFUND", then=F("amount")),
                When(transaction_type="DEDUCT", then=-F("amount")),
                output_field=IntegerField(),
            )
        )
    )
    return result["balance"] or 0