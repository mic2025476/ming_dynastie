from __future__ import annotations
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect

from core_settings.models import SiteSettings
from .models import DaySlotBlockModel, ReservationModel, TimeSlotModel
from .forms import ReservationCreateForm
from django.views.decorators.http import require_GET
from datetime import timedelta
from urllib.parse import quote
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET, require_http_methods
from django.template.loader import render_to_string
from .auth import get_verified_email
from .email_sender import send_magic_link_via_gas, send_reservation_confirmation_via_gas
from .models import EmailSessionModel, ReservationModel
from django.db.models import Sum
from django.db import transaction

@require_POST
@csrf_protect
def create_reservation(request):
    form = ReservationCreateForm(request.POST)

    if form.is_valid():
        reservation = form.save(commit=False)
        reservation.slot = form.cleaned_data["slot"]

        try:
            with transaction.atomic():

                # 1️⃣ Lock slot row (prevents race conditions)
                locked_slot = (
                    TimeSlotModel.objects
                    .select_for_update()
                    .get(pk=reservation.slot_id, is_active=True)
                )

                # 2️⃣ Get per-day slot block
                block = DaySlotBlockModel.objects.filter(
                    blocked_day__date=reservation.date,
                    slot_id=reservation.slot_id
                ).first()

                if block and block.is_closed:
                    raise ValueError({
                        "code": "SLOT_CLOSED",
                        "title": "Zeitraum nicht verfügbar",
                        "text": "Dieser Zeitraum ist an diesem Tag nicht verfügbar."
                    })

                blocked_seats = block.blocked_seats if block else 0
                effective_capacity = max(locked_slot.capacity - blocked_seats, 0)

                # 3️⃣ Calculate already booked seats
                booked = (
                    ReservationModel.objects
                    .filter(
                        date=reservation.date,
                        slot_id=reservation.slot_id,
                        slot__is_active=True
                    )
                    .aggregate(total=Sum("party_size"))["total"] or 0
                )

                requested = reservation.party_size
                available = max(effective_capacity - booked, 0)

                # 4️⃣ First booking exceeds total capacity
                if booked == 0 and requested > effective_capacity:
                    raise ValueError({
                        "code": "FIRST_BOOKING_EXCEEDS",
                        "title": "Kapazität überschritten",
                        "text": (
                            f"Für diesen Zeitraum stehen insgesamt "
                            f"{effective_capacity} Plätze zur Verfügung. "
                            f"Sie haben {requested} Personen ausgewählt."
                        )
                    })

                # 5️⃣ Not enough remaining seats
                if requested > available:
                    raise ValueError({
                        "code": "SLOT_FULL",
                        "title": "Nicht genügend Plätze verfügbar",
                        "text": (
                            f"Es sind nur noch {available} Plätze verfügbar. "
                            f"Sie haben {requested} Personen ausgewählt."
                        )
                    })

                # 6️⃣ Save reservation
                reservation.save()
                session, raw_token = EmailSessionModel.create_for_email(
                    reservation.email.strip().lower(),
                    days_valid=30,
                    request=request,
                )

                next_url = f"/?rid={reservation.pk}#my-reservations"
                magic_url = request.build_absolute_uri(
                    reverse("reservations:magic_login")
                    + f"?token={raw_token}&next={quote(next_url, safe='/:?=#&')}"
                )
                send_reservation_confirmation_via_gas(
                    to_email=reservation.email.strip().lower(),
                    edit_cancel_url=magic_url,
                    restaurant_name="Ming Dynastie",
                    reservation_date=reservation.date.strftime("%d.%m.%Y"),
                    reservation_time=reservation.time.strftime("%H:%M"),
                    party_size=reservation.party_size,
                    customer_name=reservation.name,
                )


        except ValueError as e:
            error_payload = e.args[0] if e.args else {}

            return JsonResponse({
                "ok": False,
                "code": error_payload.get("code", "SLOT_FULL"),
                "errors": form.errors.get_json_data(),
                "popup": {
                    "title": error_payload.get("title", "Fehler"),
                    "text": error_payload.get("text", "Es ist ein Fehler aufgetreten.")
                }
            }, status=400)

        else:
            return JsonResponse({
                "ok": True,
                "message": "Danke für Ihre Reservierung. Sie erhalten alle Details per E-Mail."
            })

    # 🔹 Normal form validation errors
    errors_json = form.errors.get_json_data()
    clean_errors = {field: [e["message"] for e in errs] for field, errs in errors_json.items()}

    popup = None
    print(f'cleanedcleaned {clean_errors}')
    # If time field has error → show popup
    if "time" in clean_errors:
        popup = {
            "title": "Reservierung nicht möglich",
            "text": clean_errors["time"][0]
        }
    if "date" in clean_errors:
        popup = {
            "title": "Reservierung nicht möglich",
            "text": clean_errors["date"][0]
        }
    return JsonResponse({
        "ok": False,
        "code": "FORM_ERROR",
        "errors": clean_errors,
        "popup": popup
    }, status=400)

@require_http_methods(["GET", "POST"])
def start_magic_login(request):
    """
    Enter email → send magic link via Google Apps Script.
    If cookie already valid → redirect to /my/
    """
    verified = get_verified_email(request)
    if verified:
        return redirect("reservations:my")

    if request.method == "GET":
        return render(request, "/#my-reservations", {"sent": False})

    print(f'request.POST {request.POST}')
    email = (request.POST.get("email") or "").strip().lower()
    if not email:
        return render(request, "reservations/partials/start_modal.html", {"sent": False, "error": "Bitte E-Mail eingeben."})

    days_valid = getattr(settings, "RESV_SESSION_DAYS_VALID", 30)
    session, raw_token = EmailSessionModel.create_for_email(email, days_valid=days_valid, request=request)

    magic_url = request.build_absolute_uri(reverse("reservations:magic_login") + f"?token={raw_token}")

    try:
        send_magic_link_via_gas(to_email=email, magic_url=magic_url)
    except Exception:
        # optional: revoke token if sending fails
        session.is_revoked = True
        session.save(update_fields=["is_revoked"])
        return render(request, "reservations/partials/start_modal.html", {
            "sent": False,
            "error": "E-Mail konnte nicht gesendet werden. Bitte später erneut versuchen."
        })

    return render(request, "reservations/partials/start_modal.html", {"sent": True, "email": email})


@require_GET
def magic_login(request):
    """
    Click link → verify token → set cookie → redirect to /my/
    """
    raw = (request.GET.get("token") or "").strip()
    if not raw:
        return HttpResponse("Missing token.", status=400)

    token_hash = EmailSessionModel.hash_token(raw)
    session = EmailSessionModel.objects.filter(token_hash=token_hash).first()
    if not session or not session.is_valid():
        return HttpResponse("This link is invalid or expired. Please request a new one.", status=400)

    next_url = request.GET.get("next") or reverse("reservations:my")
    if not url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        next_url = reverse("reservations:my")

    resp = redirect(next_url)

    cookie_name = getattr(settings, "RESV_SESSION_COOKIE_NAME", "ming_resv_session")
    max_age = int((session.expires_at - session.created_at).total_seconds())
    secure = request.is_secure()

    resp.set_cookie(
        cookie_name,
        raw,
        max_age=max_age,
        httponly=True,
        secure=secure,   # True on HTTPS in prod
        samesite="Lax",
    )

    return resp


@require_GET
def my_reservations(request):
    """
    Show reservations for verified email.
    If not verified, redirect to start.
    """
    email = get_verified_email(request)
    if not email:
        return redirect("reservations:start")

    reservations = ReservationModel.objects.filter(email=email).order_by("-date", "-created_at")
    return render(request, "reservations/my.html", {"email": email, "reservations": reservations})


@require_GET
def resv_logout(request):
    """
    Deletes cookie.
    """
    resp = redirect("/#my-reservations")
    cookie_name = getattr(settings, "RESV_SESSION_COOKIE_NAME", "ming_resv_session")
    resp.delete_cookie(cookie_name)
    return resp

@require_GET
def start_modal(request):
    """
    Returns the HTML for the 'enter email' modal body.
    If already verified, returns the my reservations modal body.
    """
    email = get_verified_email(request)
    if email:
        return my_modal(request)

    html = render_to_string("reservations/partials/start_modal.html", {}, request=request)
    return JsonResponse({"ok": True, "html": html})


@require_POST
def send_magic_link_ajax(request):
    """
    AJAX: create EmailSession + send link. Returns success HTML message.
    """
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    email = (payload.get("email") or "").strip().lower()
    if not email:
        return JsonResponse({"ok": False, "error": "Bitte E-Mail eingeben."}, status=400)

    # Create token session
    session, raw = EmailSessionModel.create_for_email(email, days_valid=30, request=request)

    # IMPORTANT: redirect back to homepage and reopen modal
    next_url = "/#my-reservations"
    magic_url = request.build_absolute_uri(
        reverse("reservations:magic_login") + f"?token={raw}&next={next_url}"
    )

    try:
        send_magic_link_via_gas(to_email=email, magic_url=magic_url)
    except Exception:
        session.is_revoked = True
        session.save(update_fields=["is_revoked"])
        return JsonResponse({"ok": False, "error": "E-Mail konnte nicht gesendet werden. Bitte später erneut versuchen."}, status=500)

    html = render_to_string("reservations/partials/sent_modal.html", {"email": email}, request=request)
    return JsonResponse({"ok": True, "html": html})


@require_GET
def my_modal(request):
    """
    Returns reservations list modal body (HTML) for the verified email.
    """
    email = get_verified_email(request)
    if not email:
        html = render_to_string("reservations/partials/start_modal.html", {}, request=request)
        return JsonResponse({"ok": True, "html": html})

    reservations = ReservationModel.objects.filter(email=email).order_by("-date")
    for r in reservations:
        r.can_edit = _can_edit_reservation(r)
        print(f'r.can_editr.can_edit11 {r.can_edit}')

    html = render_to_string(
        "reservations/partials/my_modal.html",
        {"email": email, "reservations": reservations},
        request=request
    )
    return JsonResponse({"ok": True, "html": html})

def _can_edit_reservation(r: ReservationModel) -> bool:
    # editable only until 3 days before reservation date
    today = timezone.localdate()
    return today <= (r.date - timedelta(days=3))



@require_GET
def edit_reservation_ajax(request, pk: int):
    email = get_verified_email(request)
    if not email:
        return JsonResponse({"ok": False, "error": "not_authenticated"}, status=401)

    r = ReservationModel.objects.filter(pk=pk, email=email).first()
    if not r:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)

    # ✅ load settings (singleton pk=1)
    settings_obj = SiteSettings.objects.filter(pk=1).first()
    opening_time = settings_obj.opening_time if settings_obj else None
    closing_time = settings_obj.closing_time if settings_obj else None

    if not _can_edit_reservation(r):
        html = render_to_string(
            "reservations/partials/edit_not_allowed.html",
            {
                "reservation": r,
                "opening_time": opening_time,
                "closing_time": closing_time,
            },
            request=request
        )
        return JsonResponse({"ok": True, "html": html})

    form = ReservationCreateForm(instance=r)
    html = render_to_string(
        "reservations/partials/edit_form.html",
        {
            "form": form,
            "reservation": r,
            "opening_time": opening_time,
            "closing_time": closing_time,
        },
        request=request
    )
    return JsonResponse({"ok": True, "html": html})


@require_POST
def update_reservation_ajax(request, pk: int):
    """
    Updates reservation and returns refreshed list HTML.
    """
    email = get_verified_email(request)
    if not email:
        return JsonResponse({"ok": False, "error": "not_authenticated"}, status=401)

    r = ReservationModel.objects.filter(pk=pk, email=email).first()
    if not r:
        return JsonResponse({"ok": False, "error": "not_found"}, status=404)
    print(f'_can_edit_reservation {_can_edit_reservation(r)}')
    if not _can_edit_reservation(r):
        return JsonResponse({"ok": False, "error": "edit_not_allowed"}, status=403)

    form = ReservationCreateForm(request.POST, instance=r)
    settings_obj = SiteSettings.objects.filter(pk=1).first()
    opening_time = settings_obj.opening_time if settings_obj else None
    closing_time = settings_obj.closing_time if settings_obj else None

    if not form.is_valid():
        print("FORM ERRORS:", form.errors)
        html = render_to_string(
            "reservations/partials/edit_form.html",
            {"form": form, "reservation": r, "opening_time": opening_time, "closing_time": closing_time},
            request=request
        )
        return JsonResponse({"ok": False, "html": html}, status=400)

    form.save()

    # return updated list (same template you already use)
    reservations = ReservationModel.objects.filter(email=email).order_by("-date", "-created_at")
    for rr in reservations:
        rr.can_edit = _can_edit_reservation(rr)
    html = render_to_string(
        "reservations/partials/my_modal.html",
        {"email": email, "reservations": reservations},
        request=request
    )
    return JsonResponse({"ok": True, "html": html})

@require_GET
def reservation_detail(request, pk: int):
    """
    Show ONE reservation for the verified email (after magic login cookie is set).
    """
    email = get_verified_email(request)
    if not email:
        # user must come through magic link
        return redirect("reservations:start")

    r = ReservationModel.objects.filter(pk=pk, email=email).first()
    if not r:
        return HttpResponse("Reservation not found.", status=404)

    r.can_edit = _can_edit_reservation(r)

    return render(request, "reservations/reservation_detail.html", {
        "email": email,
        "reservation": r,
    })
