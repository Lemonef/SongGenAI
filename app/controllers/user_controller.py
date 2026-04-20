from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from app.models import Creator
from app.models.listener import Listener
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


@login_required
def onboarding_view(request):
    user = request.user

    # If already has a role profile, skip onboarding
    if hasattr(user, 'creator_profile'):
        return redirect('/generation/')
    if hasattr(user, 'listener_profile'):
        return redirect('/browse/')

    if request.method == 'POST':
        role = request.POST.get('role')
        if role == 'creator':
            Creator.objects.create(
                user=user,
                name=user.get_full_name() or user.username,
                email=user.email or None,
            )
            return redirect('/generation/')
        elif role == 'listener':
            Listener.objects.create(
                user=user,
                name=user.get_full_name() or user.username,
                email=user.email or None,
            )
            return redirect('/browse/')

    return render(request, 'user/onboarding.html')