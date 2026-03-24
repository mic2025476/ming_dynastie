import json
from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.http import JsonResponse
from django.template.loader import render_to_string
from reservations.models import TimeSlotModel, BlockedDayModel, ReservationModel
from .forms import TimeSlotForm, BlockedDayForm, BlockedDaySlotBlockFormSet, ReservationForm


# ─────────────────────────────────────────────
#  MAIN DASHBOARD HOME (handles all sections)
# ─────────────────────────────────────────────

def dashboard_home(request):
    section = request.GET.get("section", "timeslots")
    mode = request.GET.get("mode", "list")
    edit_id = request.GET.get("id")

    # Always load these for the left panel list
    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")

    form = None
    slot_block_formset = None
    selected_slot = None
    selected_blocked_day = None
    selected_reservation = None
    reservations = None
    date_filter = "upcoming"
    slot_filter = ""
    search = ""
    slots_json = "[]"
    today = date.today()

    # ── Time Slots section ──
    if section == "timeslots":
        if mode == "create":
            form = TimeSlotForm()
        elif mode == "edit" and edit_id:
            selected_slot = get_object_or_404(TimeSlotModel, pk=edit_id)
            form = TimeSlotForm(instance=selected_slot)
        else:
            mode = "list"

    # ── Blocked Days section ──
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

    # ── Reservations section ──
    elif section == "reservations":
        today = date.today()
        date_filter = request.GET.get("date_filter", "upcoming")
        slot_filter = request.GET.get("slot_filter", "")
        search = request.GET.get("search", "")

        reservations = ReservationModel.objects.select_related("slot").order_by("-date", "-time")
        print(f'reservations {len(reservations)}')
        # Apply date filter
        if date_filter == "today":
            reservations = reservations.filter(date=today)
        elif date_filter == "upcoming":
            reservations = reservations.filter(date__gte=today)
        elif date_filter == "past":
            reservations = reservations.filter(date__lt=today)
        # "all" → no date filter

        # Apply slot filter
        if slot_filter:
            reservations = reservations.filter(slot_id=slot_filter)

        # Apply search filter
        if search:
            reservations = reservations.filter(
                Q(name__icontains=search)
                | Q(email__icontains=search)
                | Q(phone__icontains=search)
            )

        # Build slot → {start, end} JSON for reservation time range JS
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

        if mode == "create":
            form = ReservationForm()
        elif mode == "edit" and edit_id:
            selected_reservation = get_object_or_404(ReservationModel, pk=edit_id)
            form = ReservationForm(instance=selected_reservation)
        else:
            mode = "list"
        # ADD THIS at the end of the reservations block:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            html = render_to_string(
                'dashboard/_reservation_rows.html',
                {'reservations': reservations, 'today': today},
                request=request,
            )
            return JsonResponse({
                'html': html,
                'count': reservations.count(),
            })

    return render(request, "dashboard/index.html", {
        "section": section,
        "mode": mode,
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": slot_block_formset,
        "selected_slot": selected_slot,
        "selected_blocked_day": selected_blocked_day,
        # Reservations extras
        "reservations": reservations,
        "selected_reservation": selected_reservation,
        "date_filter": date_filter,
        "slot_filter": slot_filter,
        "search": search,
        "slots_json": slots_json,
        "today": today,
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

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "timeslots",
        "mode": "create",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": None,
        "selected_slot": None,
        "selected_blocked_day": None,
        "reservations": None,
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

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "timeslots",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": None,
        "selected_slot": slot,
        "selected_blocked_day": None,
        "reservations": None,
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

    if slot.is_active:
        messages.success(request, f'"{slot.label}" is now active.')
    else:
        messages.success(request, f'"{slot.label}" is now inactive.')

    return redirect(f"{reverse('dashboard:home')}?section=timeslots")


# ─────────────────────────────────────────────
#  BLOCKED DAY VIEWS
# ─────────────────────────────────────────────

def blocked_day_create(request):
    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    form = BlockedDayForm(request.POST)
    formset = BlockedDaySlotBlockFormSet(request.POST, prefix="slot_blocks")

    if form.is_valid() and formset.is_valid():
        blocked_day = form.save()
        formset.instance = blocked_day
        formset.save()
        messages.success(request, "Blocked day created successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "blocked-days",
        "mode": "create",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": formset,
        "selected_slot": None,
        "selected_blocked_day": None,
        "reservations": None,
    })


def blocked_day_update(request, pk):
    blocked_day = get_object_or_404(BlockedDayModel, pk=pk)

    if request.method != "POST":
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    form = BlockedDayForm(request.POST, instance=blocked_day)
    formset = BlockedDaySlotBlockFormSet(
        request.POST,
        instance=blocked_day,
        prefix="slot_blocks",
    )

    if form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        messages.success(request, "Blocked day updated successfully.")
        return redirect(f"{reverse('dashboard:home')}?section=blocked-days")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.prefetch_related("slot_blocks__slot").order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")

    return render(request, "dashboard/index.html", {
        "section": "blocked-days",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": formset,
        "selected_slot": None,
        "selected_blocked_day": blocked_day,
        "reservations": None,
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
        "mode": "create",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "slot_block_formset": None,
        "selected_slot": None,
        "selected_blocked_day": None,
        "reservations": reservations,
        "selected_reservation": None,
        "date_filter": "upcoming",
        "slot_filter": "",
        "search": "",
        "slots_json": slots_json,
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
        "date_filter": "upcoming",
        "slot_filter": "",
        "search": "",
        "slots_json": slots_json,
    })

def reservation_delete(request, pk):
    if request.method != "POST":
        return redirect(_reservation_list_url())

    reservation = get_object_or_404(ReservationModel, pk=pk)
    name = reservation.name
    reservation.delete()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        today = date.today()

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
                Q(name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search)
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
            "html": html,
            "count": reservations.count(),
        })

    messages.success(request, f'Reservation for "{name}" was deleted successfully.')
    return redirect(_reservation_list_url())
