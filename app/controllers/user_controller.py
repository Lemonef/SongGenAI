from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404

from app.models import Creator
from app.services.user_service import get_creator_balance


def user_home(request):
    return HttpResponse("User page")


def creator_balance(request, creator_id):
    creator = get_object_or_404(Creator, id=creator_id)
    balance = get_creator_balance(creator)

    return JsonResponse({
        "creator": creator.name,
        "credit_balance": balance,
    })