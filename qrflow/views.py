from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseBadRequest
from .models import Location, Feedback
from reservations.email_sender import send_feedback_notification_via_gas
from qrflow.models import Location

def select_location(request):
    locations = Location.objects.all().order_by("name")
    return render(request, "qrflow/select_location.html", {"locations": locations})

def qr_landing(request, slug):
    location = get_object_or_404(Location, slug=slug)
    return render(request, "qrflow/landing.html", {"location": location})

def qr_good(request, slug):
    location = get_object_or_404(Location, slug=slug)
    google_url = f"https://search.google.com/local/writereview?placeid={location.place_id}"
    return redirect(google_url)

def qr_bad(request, slug):
    location = get_object_or_404(Location, slug=slug)

    if request.method == "POST":
        what = (request.POST.get("what_went_wrong") or "").strip()
        email = (request.POST.get("email") or "").strip()

        Feedback.objects.create(
            location_slug=location.slug,
            what_went_wrong=what,
            email=email,
        )

        # SEND EMAIL ONLY FOR EUROPA CENTER
        if location.slug == "ming-europa-center":
            send_feedback_notification_via_gas(
                restaurant_name=location.name,
                feedback_text=what,
                customer_email=email,
            )

        return render(request, "qrflow/thanks.html", {"location": location})

    return render(request, "qrflow/questionnaire.html", {"location": location})