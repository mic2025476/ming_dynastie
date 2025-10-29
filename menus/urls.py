from django.urls import path
from . import views

app_name = 'menus'
urlpatterns = [
    path('', views.list_menus, name='list'),
]
