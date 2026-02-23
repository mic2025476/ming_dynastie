from django.urls import path
from . import views

app_name = "reservations"

urlpatterns = [
    path("create/", views.create_reservation, name="create"),

    # magic link auth
    path("start/", views.start_magic_login, name="start"),
    path("magic-login/", views.magic_login, name="magic_login"),
    path("my/", views.my_reservations, name="my"),
    path("logout/", views.resv_logout, name="logout"),
path("start-modal/", views.start_modal, name="start_modal"),
path("send-link/", views.send_magic_link_ajax, name="send_link"),
path("my-modal/", views.my_modal, name="my_modal"),
path("edit/<int:pk>/", views.edit_reservation_ajax, name="edit"),
path("update/<int:pk>/", views.update_reservation_ajax, name="update"),
path("r/<int:pk>/", views.reservation_detail, name="reservation_detail"),
]
