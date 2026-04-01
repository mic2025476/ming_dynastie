from django.urls import path
from . import views

app_name = "locations"

urlpatterns = [
    path("", views.dashboard_home, name="home"),

    # Time Slots
    path("timeslots/create/",                  views.timeslot_create,        name="timeslot_create"),
    path("timeslots/<int:pk>/update/",         views.timeslot_update,        name="timeslot_update"),
    path("timeslots/<int:pk>/delete/",         views.timeslot_delete,        name="timeslot_delete"),
    path("timeslots/<int:pk>/toggle-active/",  views.timeslot_toggle_active, name="timeslot_toggle_active"),

    # Blocked Days
    path("blocked-days/create/",               views.blocked_day_create,     name="blocked_day_create"),
    path("blocked-days/<int:pk>/update/",      views.blocked_day_update,     name="blocked_day_update"),
    path("blocked-days/<int:pk>/delete/",      views.blocked_day_delete,     name="blocked_day_delete"),

    # Reservations
    path("reservations/create/",               views.reservation_create,     name="reservation_create"),
    path("reservations/<int:pk>/update/",      views.reservation_update,     name="reservation_update"),
    path("reservations/<int:pk>/delete/",      views.reservation_delete,     name="reservation_delete"),



    # Locations
    path("locations/create/",                  views.location_create,       name="location_create"),
    path("locations/<int:pk>/update/",         views.location_update,       name="location_update"),
    path("locations/<int:pk>/delete/",         views.location_delete,       name="location_delete"),
    # Feedback
    path("feedback/<int:pk>/delete/",          views.feedback_delete,        name="feedback_delete"),
]
