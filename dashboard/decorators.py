from django.shortcuts import redirect
from django.urls import reverse
from core_settings.models import SiteSettings

def dashboard_password_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        site_settings, _ = SiteSettings.objects.get_or_create(pk=1)

        is_granted = request.session.get("dashboard_access_granted")
        session_version = request.session.get("dashboard_password_version")

        if not is_granted or session_version != site_settings.dashboard_password_version:
            request.session.flush()
            return redirect(reverse("dashboard:password_login"))

        return view_func(request, *args, **kwargs)
    return _wrapped_view