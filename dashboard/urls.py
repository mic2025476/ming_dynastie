from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_home, name="home"),

    path("timeslots/create/", views.timeslot_create, name="timeslot_create"),
    path("timeslots/<int:pk>/update/", views.timeslot_update, name="timeslot_update"),
    path("timeslots/<int:pk>/delete/", views.timeslot_delete, name="timeslot_delete"),
    path("timeslots/<int:pk>/toggle-active/", views.timeslot_toggle_active, name="timeslot_toggle_active"),

    path("blocked-days/create/", views.blocked_day_create, name="blocked_day_create"),
    path("blocked-days/<int:pk>/update/", views.blocked_day_update, name="blocked_day_update"),
    path("blocked-days/<int:pk>/delete/", views.blocked_day_delete, name="blocked_day_delete"),
]