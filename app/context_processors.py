from app.services.user_service import get_creator_balance

def creator_credits(request):
    """
    Adds creator_balance and is_creator to the context for all templates.
    """
    context = {
        'user_credits': 0,
        'is_creator_user': False
    }

    if request.user.is_authenticated:
        # Check if they have a profile and are a creator
        if hasattr(request.user, 'profile') and request.user.profile.is_creator():
            context['is_creator_user'] = True
            
            # Use creator_profile related name from Creator model
            creator = getattr(request.user, 'creator_profile', None)
            if creator:
                context['user_credits'] = get_creator_balance(creator)
            
    return context
