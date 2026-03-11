from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models.deletion import ProtectedError

from reservations.models import TimeSlotModel, BlockedDayModel
from .forms import TimeSlotForm, BlockedDayForm


def dashboard_home(request):
    section = request.GET.get("section", "timeslots")
    mode = request.GET.get("mode", "list")
    edit_id = request.GET.get("id")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.all().order_by("-date")

    form = None
    selected_slot = None
    selected_blocked_day = None

    if section == "timeslots":
        if mode == "create":
            form = TimeSlotForm()
        elif mode == "edit" and edit_id:
            selected_slot = get_object_or_404(TimeSlotModel, pk=edit_id)
            form = TimeSlotForm(instance=selected_slot)
        else:
            mode = "list"

    elif section == "blocked-days":
        if mode == "create":
            form = BlockedDayForm()
        elif mode == "edit" and edit_id:
            selected_blocked_day = get_object_or_404(BlockedDayModel, pk=edit_id)
            form = BlockedDayForm(instance=selected_blocked_day)
        else:
            mode = "list"

    return render(request, "dashboard/index.html", {
        "section": section,
        "mode": mode,
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "selected_slot": selected_slot,
        "selected_blocked_day": selected_blocked_day,
    })


def timeslot_create(request):
    if request.method != "POST":
        return redirect("dashboard:home")

    form = TimeSlotForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Time slot created successfully.")
        return redirect("dashboard:home")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.all().order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")
    return render(request, "dashboard/index.html", {
        "section": "timeslots",
        "mode": "create",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "selected_slot": None,
        "selected_blocked_day": None,
    })


def timeslot_update(request, pk):
    slot = get_object_or_404(TimeSlotModel, pk=pk)

    if request.method != "POST":
        return redirect("dashboard:home")

    form = TimeSlotForm(request.POST, instance=slot)
    if form.is_valid():
        form.save()
        messages.success(request, "Time slot updated successfully.")
        return redirect("dashboard:home")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.all().order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")
    return render(request, "dashboard/index.html", {
        "section": "timeslots",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "selected_slot": slot,
        "selected_blocked_day": None,
    })


def timeslot_delete(request, pk):
    if request.method != "POST":
        return redirect("dashboard:home")

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

    return redirect("dashboard:home")


def timeslot_toggle_active(request, pk):
    if request.method != "POST":
        return redirect("dashboard:home")

    slot = get_object_or_404(TimeSlotModel, pk=pk)
    slot.is_active = not slot.is_active
    slot.save(update_fields=["is_active"])

    if slot.is_active:
        messages.success(request, f'"{slot.label}" is now active.')
    else:
        messages.success(request, f'"{slot.label}" is now inactive.')

    return redirect("dashboard:home")


def blocked_day_create(request):
    if request.method != "POST":
        return redirect("dashboard:home")

    form = BlockedDayForm(request.POST)
    if form.is_valid():
        form.save()
        messages.success(request, "Blocked day created successfully.")
        return redirect("dashboard:home?section=blocked-days")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.all().order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")
    return render(request, "dashboard/index.html", {
        "section": "blocked-days",
        "mode": "create",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "selected_slot": None,
        "selected_blocked_day": None,
    })


def blocked_day_update(request, pk):
    blocked_day = get_object_or_404(BlockedDayModel, pk=pk)

    if request.method != "POST":
        return redirect("dashboard:home?section=blocked-days")

    form = BlockedDayForm(request.POST, instance=blocked_day)
    if form.is_valid():
        form.save()
        messages.success(request, "Blocked day updated successfully.")
        return redirect("dashboard:home?section=blocked-days")

    slots = TimeSlotModel.objects.all().order_by("sort_order", "start_time")
    blocked_days = BlockedDayModel.objects.all().order_by("-date")
    messages.error(request, "Please fix the form errors and try again.")
    return render(request, "dashboard/index.html", {
        "section": "blocked-days",
        "mode": "edit",
        "slots": slots,
        "blocked_days": blocked_days,
        "form": form,
        "selected_slot": None,
        "selected_blocked_day": blocked_day,
    })


def blocked_day_delete(request, pk):
    if request.method != "POST":
        return redirect("dashboard:home?section=blocked-days")

    blocked_day = get_object_or_404(BlockedDayModel, pk=pk)
    blocked_day.delete()
    messages.success(request, f'Blocked day "{blocked_day.date}" was deleted successfully.')
    return redirect("dashboard:home?section=blocked-days")