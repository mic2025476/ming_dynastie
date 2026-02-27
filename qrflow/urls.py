from django.urls import path
from . import views

urlpatterns = [
    path("qr/", views.select_location, name="select_location"),
    path("qr/<slug:slug>/", views.qr_landing, name="qr_landing"),
    path("qr/<slug:slug>/good/", views.qr_good, name="qr_good"),
    path("qr/<slug:slug>/bad/", views.qr_bad, name="qr_bad"),
path("feedback/", views.select_location, name="select_location"),
path("feedback/<slug:slug>/", views.qr_landing, name="feedback_landing"),
path("feedback/<slug:slug>/good/", views.qr_good, name="feedback_good"),
path("feedback/<slug:slug>/bad/", views.qr_bad, name="feedback_bad"),
]