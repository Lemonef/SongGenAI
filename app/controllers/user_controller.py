from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required

from app.models import Creator, UserProfile
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

    # Already picked a role — send them to the right place
    if hasattr(user, 'profile'):
        if user.profile.is_creator():
            return redirect('/generation/')
        else:
            return redirect('/browse/')

    if request.method == 'POST':
        role = request.POST.get('role')

        if role == 'creator':
            UserProfile.objects.create(user=user, role=UserProfile.CREATOR)
            Creator.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.get_full_name() or user.username,
                    'email': user.email or None,
                }
            )
            return redirect('/generation/')

        elif role == 'listener':
            UserProfile.objects.create(user=user, role=UserProfile.LISTENER)
            Listener.objects.get_or_create(
                user=user,
                defaults={
                    'name': user.get_full_name() or user.username,
                    'email': user.email or None,
                }
            )
            return redirect('/browse/')

    return render(request, 'user/onboarding.html')