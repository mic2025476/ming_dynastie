from __future__ import annotations

from django.conf import settings
from .models import EmailSessionModel


def get_verified_email(request) -> str | None:
    cookie_name = getattr(settings, "RESV_SESSION_COOKIE_NAME", "ming_resv_session")
    raw = request.COOKIES.get(cookie_name)
    if not raw:
        return None

    token_hash = EmailSessionModel.hash_token(raw)
    session = EmailSessionModel.objects.filter(token_hash=token_hash).first()
    if not session or not session.is_valid():
        return None

    return session.email
