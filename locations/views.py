import json
from datetime import date, timedelta

from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from core_settings.models import SiteSettings
from .forms import SiteSettingsForm
from locations.models import Location
from reservations.models import TimeSlotModel, BlockedDayModel, ReservationModel
from qrflow.models import Feedback  # adjust import path if different in your project
from .forms import TimeSlotForm, BlockedDayForm, BlockedDaySlotBlockFormSet, ReservationForm, LocationForm



# ─────────────────────────────────────────────
#  MAIN DASHBOARD HOME (handles all sections)
# ─────────────────────────────────────────────

def dashboard_home(request):
    section = request.GET.get("section", "reservations")
    mode    = request.GET.get("mode", "list")
    edit_id = request.GET.get("id")

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")

    form                = None
    slot_block_formset  = None
    selected_slot       = None
    selected_blocked_day = None
    selected_reservation = None
    selected_feedback   = None
    selected_location   = None
    reservations        = None
    feedback_list       = None
    locations_list      = None
    site_settings       = None
    date_filter         = "upcoming"
    slot_filter         = ""
    search              = ""
    location_filter     = ""
    location_search     = ""
    slots_json          = "[]"
    today               = date.today()

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
    # ── Settings ─────────────────────────────────────────────
    elif section == "settings":
        site_settings, _ = SiteSettings.objects.get_or_create(pk=1)
        form = SiteSettingsForm(instance=site_settings)
        mode = "edit"
    # ── Locations ────────────────────────────────────────────
    elif section == "locations":
        location_search = request.GET.get("search", "").strip()
        locations_list = Location.objects.all().order_by("name")

        if location_search:
            locations_list = locations_list.filter(
                Q(name__icontains=location_search)
                | Q(slug__icontains=location_search)
                | Q(address__icontains=location_search)
                | Q(phone__icontains=location_search)
                | Q(email__icontains=location_search)
            )

        if mode == "create":
            form = LocationForm()
        elif mode == "edit" and edit_id:
            selected_location = get_object_or_404(Location, pk=edit_id)
            form = LocationForm(instance=selected_location)
        else:
            mode = "list"

    # ── Reservations ─────────────────────────────────────────
    elif section == "reservations":
        date_filter = request.GET.get("date_filter", "upcoming")
        slot_filter = request.GET.get("slot_filter", "")
        search      = request.GET.get("search", "")

        reservations = ReservationModel.objects.select_related("slot").order_by("-date", "-time")

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
                {"reservations": reservations, "today": today},
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
                "dashboard/_feedback_rows.html",
                {"feedback_list": feedback_list, "selected_feedback": selected_feedback},
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
            "site_settings": site_settings,
            "slots":            slots,
            "blocked_days":     blocked_days,
            "form":             None,
            "slot_block_formset": None,
            "selected_slot":    None,
            "selected_blocked_day": None,
            "reservations":     None,
            "selected_reservation": None,
            "feedback_list":    feedback_list,
            "locations_list":   locations_list,
            "selected_feedback": selected_feedback,
            "selected_location": selected_location,
            "date_filter":      date_filter,
            "location_filter":  location_filter,
            "location_slugs":   location_slugs,
            "search":           search,
            "slot_filter":      "",
            "location_search":  location_search,
            "slots_json":       "[]",
            "today":            today,
        })

    return render(request, "dashboard/index.html", {
        "section":           section,
        "mode":              mode,
        "slots":             slots,
        "blocked_days":      blocked_days,
        "form":              form,
        "slot_block_formset": slot_block_formset,
        "selected_slot":     selected_slot,
        "selected_blocked_day": selected_blocked_day,
        "reservations":      reservations,
        "selected_reservation": selected_reservation,
        "feedback_list":     feedback_list,
        "locations_list":    locations_list,
        "selected_feedback": selected_feedback,
        "selected_location": selected_location,
        "date_filter":       date_filter,
        "location_filter":   location_filter,
        "location_slugs":    [],
        "search":            search,
        "slot_filter":       slot_filter,
        "location_search":   location_search,
        "slots_json":        slots_json,
        "today":             today,
    })


# ─────────────────────────────────────────────
#  TIME SLOT VIEWS
# ─────────────────────────────────────────────

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


def reservation_update(request, pk):
    reservation = get_object_or_404(ReservationModel, pk=pk)

    if request.method != "POST":
        return redirect(_reservation_list_url())

    form = ReservationForm(request.POST, instance=reservation)
    if form.is_valid():
        form.save()
        messages.success(request, f'Reservation for "{reservation.name}" updated successfully.')
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
        "section": "reservations", "mode": "edit",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": reservations, "selected_reservation": reservation,
        "feedback_list": None, "selected_feedback": None,
        "date_filter": "upcoming", "slot_filter": "", "search": "",
        "slots_json": slots_json, "today": date.today(),
    })


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
            {"reservations": reservations, "today": today},
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


def _location_list_url():
    return f"{reverse('dashboard:home')}?section=locations"


def location_create(request):
    if request.method != "POST":
        return redirect(_location_list_url())

    form = LocationForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        messages.success(request, "Location created successfully.")
        return redirect(_location_list_url())

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    locations_list = Location.objects.all().order_by("name")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "locations", "mode": "create",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": None, "selected_reservation": None,
        "feedback_list": None, "selected_feedback": None,
        "selected_location": None, "locations_list": locations_list,
        "location_search": "", "today": date.today(),
    })


def location_update(request, pk):
    location = get_object_or_404(Location, pk=pk)

    if request.method != "POST":
        return redirect(_location_list_url())

    form = LocationForm(request.POST, request.FILES, instance=location)
    if form.is_valid():
        form.save()
        messages.success(request, f'Location "{location.name}" updated successfully.')
        return redirect(_location_list_url())

    slots        = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    locations_list = Location.objects.all().order_by("name")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "locations", "mode": "edit",
        "slots": slots, "blocked_days": blocked_days,
        "form": form, "slot_block_formset": None,
        "selected_slot": None, "selected_blocked_day": None,
        "reservations": None, "selected_reservation": None,
        "feedback_list": None, "selected_feedback": None,
        "selected_location": location, "locations_list": locations_list,
        "location_search": "", "today": date.today(),
    })


def location_delete(request, pk):
    if request.method != "POST":
        return redirect(_location_list_url())

    location = get_object_or_404(Location, pk=pk)
    name = location.name
    location.delete()
    messages.success(request, f'Location "{name}" was deleted successfully.')
    return redirect(_location_list_url())


# ─────────────────────────────────────────────
#  FEEDBACK VIEWS
# ─────────────────────────────────────────────

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
