import json
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from core_settings.models import SiteSettings
from django.contrib import messages
from datetime import date, timedelta, datetime
from django.db.models import Q
from django.db import transaction
from reservations.email_sender import send_reservation_update_via_gas
from django.utils.translation import gettext as _
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.middleware.csrf import rotate_token
from django.http import JsonResponse
from django.template.loader import render_to_string
from .decorators import dashboard_password_required
from mingdyn import settings
from reservations.models import TimeSlotModel, BlockedDayModel, ReservationModel
from qrflow.models import Feedback  # adjust import path if different in your project
from core_settings.models import SiteSettings
from .forms import TimeSlotForm, BlockedDayForm, BlockedDaySlotBlockFormSet, ReservationForm, SiteSettingsForm
from django.utils import timezone

# ─────────────────────────────────────────────
#  MAIN DASHBOARD HOME (handles all sections)
# ─────────────────────────────────────────────

@dashboard_password_required
def reservation_mark_arrived(request, pk):
    if request.method != "POST":
        return redirect(_reservation_list_url())

    reservation = get_object_or_404(ReservationModel, pk=pk)

    reservation.is_arrived = not reservation.is_arrived

    if reservation.is_arrived:
        reservation.arrival_marked_at = timezone.now()
    else:
        reservation.arrival_marked_at = None

    reservation.save(update_fields=["is_arrived", "arrival_marked_at"])
    reservation.save(update_fields=["is_arrived", "arrival_marked_at"])

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        today = date.today()
        now_time = datetime.now().time()
        date_filter = request.GET.get("date_filter", "upcoming")
        slot_filter = request.GET.get("slot_filter", "")
        search = request.GET.get("search", "").strip()

        reservations = ReservationModel.objects.select_related("slot")

        if date_filter == "today":
            reservations = reservations.filter(date=today)
        elif date_filter == "upcoming":
            reservations = reservations.filter(date__gte=today)
        elif date_filter == "past":
            reservations = reservations.filter(date__lt=today)

        if slot_filter:
            reservations = reservations.filter(slot_id=slot_filter)

        if search:
            reservations = reservations.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        reservations = reservations.order_by("date", "time")

        html = render_to_string(
            "dashboard/_reservation_rows.html",
            {
                "reservations": reservations,
                "today": today,
                "now_time": now_time,
            },
            request=request,
        )
        return JsonResponse({
            "success": True,
            "message": f'"{reservation.name}" marked as arrived.',
            "html": html,
            "now_time": now_time,
            "count": reservations.count(),
        })

    messages.success(request, f'"{reservation.name}" marked as arrived.')
    return redirect(_reservation_list_url())

@dashboard_password_required
def dashboard_home(request):
    section = request.GET.get("section", "reservations")
    mode    = request.GET.get("mode", "list")
    edit_id = request.GET.get("id")
    filter_type = request.GET.get("filter")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")

    form                = None
    slot_block_formset  = None
    selected_slot       = None
    selected_blocked_day = None
    selected_reservation = None
    selected_feedback   = None
    reservations        = None
    feedback_list       = None
    date_filter         = "upcoming"
    slot_filter         = ""
    search              = ""
    location_filter     = ""
    slots_json          = "[]"
    site_settings       = None
    today               = date.today()
    now_time = datetime.now().time()

    today_reservations = (
        ReservationModel.objects.select_related("slot")
        .filter(date=today)
        .order_by("time")
    )
    print(f'today {today}')
    print(f'now_time {now_time}')
    no_shows_today = ReservationModel.objects.filter(
        date=today,
        time__lt=now_time,
        is_arrived=False,
    ).count()
    print(f'no_shows_today {no_shows_today}')
    total_today_reservations = today_reservations.count()
    total_today_guests = sum((r.party_size or 0) for r in today_reservations)

    next_reservation = (
        ReservationModel.objects.select_related("slot")
        .filter(
            Q(date__gt=today) |
            Q(date=today, time__gte=now_time)
        )
        .order_by("date", "time")
        .first()
    )
    active_slots_today = TimeSlotModel.objects.filter(is_active=True).count()

    dashboard_overview = {
        "total_today_reservations": total_today_reservations,
        "total_today_guests": total_today_guests,
        "next_reservation": next_reservation,
        "active_slots_today": active_slots_today,
        "no_shows_today": no_shows_today,
    }
    # ── Time Slots ──────────────────────────────────────────
    if section == "timeslots":
        if mode == "create":
            form = TimeSlotForm()
        elif mode == "edit" and edit_id:
            selected_slot = get_object_or_404(TimeSlotModel, pk=edit_id)
            form = TimeSlotForm(instance=selected_slot)
        else:
            mode = "list"

    # ── Blocked Days ─────────────────────────────────────────
    elif section == "blocked-days":
        if mode == "create":
            form = BlockedDayForm()
            slot_block_formset = BlockedDaySlotBlockFormSet(prefix="slot_blocks")
        elif mode == "edit" and edit_id:
            selected_blocked_day = get_object_or_404(BlockedDayModel, pk=edit_id)
            form = BlockedDayForm(instance=selected_blocked_day)
            slot_block_formset = BlockedDaySlotBlockFormSet(
                instance=selected_blocked_day,
                prefix="slot_blocks",
            )
        else:
            mode = "list"

    # ── Site Settings ────────────────────────────────────────
    elif section == "settings":
        site_settings = SiteSettings.objects.first()
        if site_settings is None:
            site_settings = SiteSettings()

        form = SiteSettingsForm(instance=site_settings)
        mode = "edit"
    # ── Reservations ─────────────────────────────────────────
    elif section == "reservations":
        date_filter = request.GET.get("date_filter", "upcoming")
        slot_filter = request.GET.get("slot_filter", "")
        search      = request.GET.get("search", "")
        reservation_id = request.GET.get("reservation_id", "")
        selected_date = request.GET.get("selected_date", "").strip()

        reservations = ReservationModel.objects.select_related("slot").order_by("-date", "-time")
        if selected_date:
            try:
                parsed_selected_date = datetime.strptime(selected_date, "%Y-%m-%d").date()
                reservations = reservations.filter(date=parsed_selected_date)
                date_filter = "custom"
            except ValueError:
                selected_date = ""
        if filter_type == "no_show_today":
            reservations = reservations.filter(
                date=today,
                time__lt=now_time,
                is_arrived=False,
            )
        if not selected_date:
            if date_filter == "today":
                reservations = reservations.filter(date=today)
            elif date_filter == "upcoming":
                reservations = reservations.filter(date__gte=today)
            elif date_filter == "past":
                reservations = reservations.filter(date__lt=today)
        if slot_filter:
            reservations = reservations.filter(slot_id=slot_filter)

        if search:
            reservations = reservations.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )
        if reservation_id:
            reservations = reservations.filter(id=reservation_id)
        slots_data = list(
            TimeSlotModel.objects.filter(is_active=True)
            .values("id", "start_time", "end_time")
            .order_by("sort_order", "start_time")
        )
        slots_json = json.dumps({
            str(s["id"]): {
                "start": s["start_time"].strftime("%H:%M"),
                "end":   s["end_time"].strftime("%H:%M"),
            }
            for s in slots_data
        })
        reservations = reservations.order_by("date", "time")

        # ── Calendar JSON for the weekly calendar view ──
        reservations_json = json.dumps([
            {
                "id":     r.id,
                "date":   r.date.strftime("%Y-%m-%d"),
                "time":   r.time.strftime("%H:%M") if r.time else (r.slot.start_time.strftime("%H:%M") if r.slot else ""),
                "name":   r.name,
                "guests": r.party_size or 0,
                "status": "arrived" if r.is_arrived else "confirmed",
                "phone":  r.phone or "",
                "email":  r.email or "",
            }
            for r in reservations
        ], default=str)

        if mode == "create":
            form = ReservationForm()
        elif mode == "edit" and edit_id:
            selected_reservation = get_object_or_404(ReservationModel, pk=edit_id)
            form = ReservationForm(instance=selected_reservation)
        else:
            mode = "list"

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string(
                "dashboard/_reservation_rows.html",
                {
                    "reservations": reservations,
                    "today": today,
                    "now_time": now_time,
                },
                request=request,
            )
            return JsonResponse({"html": html, "count": reservations.count()})

    # ── Feedback ─────────────────────────────────────────────
    elif section == "feedback":
        date_filter     = request.GET.get("date_filter", "all")
        location_filter = request.GET.get("location_filter", "")
        search          = request.GET.get("search", "")

        feedback_list = Feedback.objects.order_by("-created_at")

        # Date filter
        if date_filter == "today":
            feedback_list = feedback_list.filter(created_at__date=today)
        elif date_filter == "week":
            feedback_list = feedback_list.filter(created_at__date__gte=today - timedelta(days=7))
        elif date_filter == "month":
            feedback_list = feedback_list.filter(created_at__date__gte=today - timedelta(days=30))

        # Location filter
        if location_filter:
            feedback_list = feedback_list.filter(location_slug=location_filter)

        # Search
        if search:
            feedback_list = feedback_list.filter(
                Q(what_went_wrong__icontains=search)
                | Q(email__icontains=search)
                | Q(location_slug__icontains=search)
            )

        # Detail view — show selected feedback in right panel
        if mode == "view" and edit_id:
            selected_feedback = get_object_or_404(Feedback, pk=edit_id)
        else:
            mode = "list"

        # AJAX live search
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            html = render_to_string(
                "dashboard/_reservation_rows.html",
                {
                    "reservations": reservations,
                    "today": today,
                    "now_time": now_time,
                },
                request=request,
            )
            return JsonResponse({"html": html, "count": feedback_list.count()})

        # Distinct location slugs for the filter dropdown
        location_slugs = (
            Feedback.objects
            .exclude(location_slug__isnull=True)
            .exclude(location_slug="")
            .values_list("location_slug", flat=True)
            .distinct()
            .order_by("location_slug")
        )

        return render(request, "dashboard/index.html", {
            "section":          section,
            "mode":             mode,
            "dashboard_overview": dashboard_overview,
            "slots":            slots,
            "blocked_days":     blocked_days,
            "form":             None,
            "slot_block_formset": None,
            "selected_slot":    None,
            "selected_blocked_day": None,
            "reservations":     None,
            "selected_reservation": None,
            "feedback_list":    feedback_list,
            "selected_feedback": selected_feedback,
        "site_settings": site_settings,
            "date_filter":      date_filter,
            "location_filter":  location_filter,
            "location_slugs":   location_slugs,
            "search":           search,
            "slot_filter":      "",
            "slots_json":       "[]",
            "today":            today,
        })

    return render(request, "dashboard/index.html", {
        "section":           section,
        "mode":              mode,
        "dashboard_overview": dashboard_overview,
        "slots":             slots,
        "blocked_days":      blocked_days,
        "form":              form,
        "slot_block_formset": slot_block_formset,
        "selected_slot":     selected_slot,
        "selected_blocked_day": selected_blocked_day,
        "reservations":      reservations,
        "selected_reservation": selected_reservation,
        "feedback_list":     feedback_list,
        "selected_feedback": selected_feedback,
        "site_settings": site_settings,
        "date_filter":       date_filter,
        "location_filter":   location_filter,
        "location_slugs":    [],
        "search":            search,
        "slot_filter":       slot_filter,
        "slots_json":        slots_json,
        "reservations_json": reservations_json if section == "reservations" else "[]",
        "today":             today,
            })

@dashboard_password_required
def site_settings_save(request):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=settings")

    site_settings = SiteSettings.objects.first() or SiteSettings()
    form = SiteSettingsForm(request.POST, instance=site_settings)

    if form.is_valid():
        site_settings = form.save(commit=False)

        new_password = form.cleaned_data.get("new_dashboard_password")

        if new_password:
            site_settings.dashboard_password_hash = make_password(new_password)
            site_settings.dashboard_password_version += 1

        site_settings.save()

        if new_password:
            messages.success(request, "Settings saved. Dashboard password updated and all active users have been logged out.")
        else:
            messages.success(request, "Site settings updated successfully.")

        return redirect(f"{reverse('dashboard:home')}?section=settings")
    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "settings",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": None,
        "selected_slot": None,
        "selected_blocked_day": None,
        "reservations": None,
        "selected_reservation": None,
        "feedback_list": None,
        "selected_feedback": None,
        "site_settings": site_settings,
        "date_filter": "upcoming",
        "location_filter": "",
        "location_slugs": [],
        "search": "",
        "slot_filter": "",
        "slots_json": "[]",
        "today": date.today(),
    })


# ─────────────────────────────────────────────
#  TIME SLOT VIEWS
# ─────────────────────────────────────────────
@dashboard_password_required
def timeslot_create(request):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    form = TimeSlotForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Time slot created successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "timeslots", "mode": "create",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": None, "feedback_list": None,
        "selected_feedback": None, "today": date.today(),
    })

@dashboard_password_required
def timeslot_update(request, pk):
    slot = get_object_or_404(TimeSlotModel, pk=pk)

    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    form = TimeSlotForm(request.POST, instance=slot)
    if form.is_valid():
        form.save()
        messages.success(request, "Time slot updated successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "timeslots", "mode": "edit",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": slot, "selected_blocked_day": None,
        "reservations": None, "feedback_list": None,
        "selected_feedback": None, "today": date.today(),
    })

@dashboard_password_required
def timeslot_delete(request, pk):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    slot = get_object_or_404(TimeSlotModel, pk=pk)
    try:
        label = slot.label
        slot.delete()
        messages.success(request, f'"{label}" was deleted successfully.')
    except ProtectedError:
        messages.error(
            request,
            f'"{slot.label}" cannot be deleted because it is already used in reservations. '
            f'Please deactivate it instead.'
        )
    return redirect(f"{reverse('dashboard:home')}?section=timeslots")

@dashboard_password_required
def timeslot_toggle_active(request, pk):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=timeslots")

    slot = get_object_or_404(TimeSlotModel, pk=pk)
    slot.is_active = not slot.is_active
    slot.save(update_fields=["is_active"])
    msg = f'"{slot.label}" is now {"active" if slot.is_active else "inactive"}.'
    messages.success(request, msg)
    return redirect(f"{reverse('dashboard:home')}?section=timeslots")


# ─────────────────────────────────────────────
#  BLOCKED DAY VIEWS
# ─────────────────────────────────────────────
@dashboard_password_required
def blocked_day_create(request):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    form    = BlockedDayForm(request.POST)
    formset = BlockedDaySlotBlockFormSet(request.POST, prefix="slot_blocks")

    if form.is_valid() and formset.is_valid():
        blocked_day          = form.save()
        formset.instance     = blocked_day
        formset.save()
        messages.success(request, "Blocked day created successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "blocked-days", "mode": "create",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": formset,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": None, "feedback_list": None,
        "selected_feedback": None, "today": date.today(),
    })

@dashboard_password_required
def blocked_day_update(request, pk):
    blocked_day = get_object_or_404(BlockedDayModel, pk=pk)

    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    form    = BlockedDayForm(request.POST, instance=blocked_day)
    formset = BlockedDaySlotBlockFormSet(request.POST, instance=blocked_day, prefix="slot_blocks")

    if form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, "Blocked day updated successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "blocked-days", "mode": "edit",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": formset,
        "selected_slot": None, "selected_blocked_day": blocked_day,
        "reservations": None, "feedback_list": None,
        "selected_feedback": None, "today": date.today(),
    })

@dashboard_password_required
def blocked_day_delete(request, pk):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    blocked_day = get_object_or_404(BlockedDayModel, pk=pk)
    blocked_day.delete()
    messages.success(request, f'Blocked day "{blocked_day.date}" was deleted successfully.')
    return redirect(f"{reverse('dashboard:home')}?section=blocked-days")


# ─────────────────────────────────────────────
#  RESERVATION VIEWS
# ─────────────────────────────────────────────
def _reservation_list_url(extra=""):
    base = f"{reverse('dashboard:home')}?section=reservations"
    return f"{base}{extra}"

@dashboard_password_required
def reservation_create(request):
    if request.method != "POST":
        return redirect(_reservation_list_url())

    form = ReservationForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Reservation created successfully.")
        return redirect(_reservation_list_url())

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    reservations = ReservationModel.objects.select_related("slot").filter(
        date__gte=date.today()
    ).order_by("-date", "-time")
    messages.error(request, "Please fix the form errors and try again.")

    slots_data = list(
        TimeSlotModel.objects.filter(is_active=True)
        .values("id", "start_time", "end_time")
        .order_by("sort_order", "start_time")
    )
    slots_json = json.dumps({
        str(s["id"]): {"start": s["start_time"].strftime("%H:%M"), "end": s["end_time"].strftime("%H:%M")}
        for s in slots_data
    })

    return render(request, "dashboard/index.html", {
        "section": "reservations", "mode": "create",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": reservations, "selected_reservation": None,
        "feedback_list": None, "selected_feedback": None,
        "date_filter": "upcoming", "slot_filter": "", "search": "",
        "slots_json": slots_json, "today": date.today(),
    })

def _get_reservation_changes(old_reservation, new_reservation):
    changed_fields = []

    field_labels = {
        "date": "Datum",
        "time": "Uhrzeit",
        "party_size": "Personenzahl",
        "name": "Name",
        "email": "E-Mail",
        "phone": "Telefon",
        "slot": "Zeitfenster",
        "notes": "Notizen",
    }

    for field in ["date", "time", "party_size", "name", "email", "phone", "notes"]:
        old_value = getattr(old_reservation, field, None)
        new_value = getattr(new_reservation, field, None)

        if old_value != new_value:
            changed_fields.append({
                "field": field,
                "label": field_labels.get(field, field),
                "old": old_value,
                "new": new_value,
            })

    old_slot_id = getattr(old_reservation, "slot_id", None)
    new_slot_id = getattr(new_reservation, "slot_id", None)
    if old_slot_id != new_slot_id:
        changed_fields.append({
            "field": "slot",
            "label": field_labels["slot"],
            "old": old_reservation.slot.label if old_reservation.slot else "",
            "new": new_reservation.slot.label if new_reservation.slot else "",
        })
    print(f'changed_fields {changed_fields}')
    return changed_fields

@dashboard_password_required
def reservation_update(request, pk):
    reservation = get_object_or_404(ReservationModel, pk=pk)

    if request.method != "POST":
        return redirect(_reservation_list_url())

    old_snapshot = ReservationModel.objects.select_related("slot").get(pk=reservation.pk)
    form = ReservationForm(request.POST, instance=reservation)

    if form.is_valid():
        updated_reservation = form.save()
        changed_fields = _get_reservation_changes(old_snapshot, updated_reservation)
        print("changed_fields", changed_fields)

        relevant_fields = {"date", "time", "party_size", "name", "email", "phone", "slot"}
        relevant_changes = [c for c in changed_fields if c["field"] in relevant_fields]
        print(f'relevant_changesrelevant_changes {relevant_changes}')
        print(f'updated_reservation.email {updated_reservation.email}')
        if relevant_changes and updated_reservation.email:
            change_lines = "\n".join(
                f'- {c["label"]}: "{c["old"]}" → "{c["new"]}"'
                for c in relevant_changes
            )

            def send_update_email():
                try:
                    send_reservation_update_via_gas(
                        to_email=updated_reservation.email.strip().lower(),
                        restaurant_name="Ming Dynastie",
                        reservation_date=updated_reservation.date.strftime("%d.%m.%Y"),
                        reservation_time=updated_reservation.time.strftime("%H:%M"),
                        party_size=updated_reservation.party_size,
                        customer_name=updated_reservation.name,
                        changes_text=change_lines,
                    )
                except Exception as e:
                    print("email failed:", e)

            transaction.on_commit(send_update_email)

        messages.success(request, f'Reservation for "{updated_reservation.name}" updated successfully.')
        return redirect(_reservation_list_url())
    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    reservations = ReservationModel.objects.select_related("slot").filter(
        date__gte=date.today()
    ).order_by("-date", "-time")
    messages.error(request, "Please fix the form errors and try again.")

    slots_data = list(
        TimeSlotModel.objects.filter(is_active=True)
        .values("id", "start_time", "end_time")
        .order_by("sort_order", "start_time")
    )
    slots_json = json.dumps({
        str(s["id"]): {
            "start": s["start_time"].strftime("%H:%M"),
            "end": s["end_time"].strftime("%H:%M"),
        }
        for s in slots_data
    })

    return render(request, "dashboard/index.html", {
        "section": "reservations",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": None,
        "selected_slot": None,
        "selected_blocked_day": None,
        "reservations": reservations,
        "selected_reservation": reservation,
        "feedback_list": None,
        "selected_feedback": None,
        "date_filter": "upcoming",
        "slot_filter": "",
        "search": "",
        "slots_json": slots_json,
        "today": date.today(),
    })

@dashboard_password_required
def reservation_delete(request, pk):
    if request.method != "POST":
        return redirect(_reservation_list_url())

    reservation = get_object_or_404(ReservationModel, pk=pk)
    name = reservation.name
    reservation.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        today       = date.today()
        date_filter = request.GET.get("date_filter", "upcoming")
        slot_filter = request.GET.get("slot_filter", "")
        search      = request.GET.get("search", "").strip()

        reservations = ReservationModel.objects.select_related("slot")

        if date_filter == "today":
            reservations = reservations.filter(date=today)
        elif date_filter == "upcoming":
            reservations = reservations.filter(date__gte=today)
        elif date_filter == "past":
            reservations = reservations.filter(date__lt=today)

        if slot_filter:
            reservations = reservations.filter(slot_id=slot_filter)

        if search:
            reservations = reservations.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        reservations = reservations.order_by("date", "time")

        html = render_to_string(
            "dashboard/_reservation_rows.html",
            {
                "reservations": reservations,
                "today": today,
                "now_time": datetime.now().time(),
            },
            request=request,
        )
        return JsonResponse({
            "success": True,
            "message": f'Reservation for "{name}" was deleted successfully.',
            "html":    html,
            "count":   reservations.count(),
        })

    messages.success(request, f'Reservation for "{name}" was deleted successfully.')
    return redirect(_reservation_list_url())


# ─────────────────────────────────────────────
#  FEEDBACK VIEWS
# ─────────────────────────────────────────────
@dashboard_password_required
def feedback_delete(request, pk):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=feedback")

    feedback = get_object_or_404(Feedback, pk=pk)
    feedback.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        today           = date.today()
        date_filter     = request.GET.get("date_filter", "all")
        location_filter = request.GET.get("location_filter", "")
        search          = request.GET.get("search", "").strip()

        feedback_list = Feedback.objects.order_by("-created_at")

        if date_filter == "today":
            feedback_list = feedback_list.filter(created_at__date=today)
        elif date_filter == "week":
            feedback_list = feedback_list.filter(created_at__date__gte=today - timedelta(days=7))
        elif date_filter == "month":
            feedback_list = feedback_list.filter(created_at__date__gte=today - timedelta(days=30))

        if location_filter:
            feedback_list = feedback_list.filter(location_slug=location_filter)

        if search:
            feedback_list = feedback_list.filter(
                Q(what_went_wrong__icontains=search)
                | Q(email__icontains=search)
                | Q(location_slug__icontains=search)
            )

        html = render_to_string(
            "dashboard/_feedback_rows.html",
            {"feedback_list": feedback_list, "selected_feedback": None},
            request=request,
        )
        return JsonResponse({"html": html, "count": feedback_list.count()})

    messages.success(request, "Feedback entry deleted successfully.")
    return redirect(f"{reverse('dashboard:home')}?section=feedback")

def dashboard_password_login(request):
    site_settings, _ = SiteSettings.objects.get_or_create(pk=1)
    print(f'sdvsdvvsvsdvsd {request.session.get("dashboard_access_granted")}')
    if request.session.get("dashboard_access_granted"):
        session_version = request.session.get("dashboard_password_version")
        if session_version == site_settings.dashboard_password_version:
            return redirect("dashboard:home")

    if request.method == "POST":
        password = request.POST.get("password", "").strip()

        if site_settings.dashboard_password_hash and check_password(password, site_settings.dashboard_password_hash):
            request.session["dashboard_access_granted"] = True
            request.session["dashboard_password_version"] = site_settings.dashboard_password_version
            rotate_token(request)
            return redirect("dashboard:home")

        messages.error(request, "Wrong password. Please try again.")

    return render(request, "dashboard/password_gate.html")

def dashboard_password_logout(request):
    request.session.flush()
    return redirect("dashboard:password_login")