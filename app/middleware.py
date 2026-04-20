from django.shortcuts import redirect
from django.urls import reverse

class OnboardingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for unauthenticated users, static files, admin, and logout
        if not request.user.is_authenticated:
            return self.get_response(request)

        # Allow onboarding page, logout, and admin
        path = request.path
        if path.startswith('/user/onboarding/') or \
           path.startswith('/accounts/logout/') or \
           path.startswith('/admin/') or \
           path.startswith('/static/'):
            return self.get_response(request)

        # If user is logged in but has no profile, force onboarding
        if not hasattr(request.user, 'profile'):
            return redirect('/user/onboarding/')

        return self.get_response(request)
