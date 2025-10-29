from django.urls import path
from . import views

app_name = 'locations'
urlpatterns = [
    path('', views.list_locations, name='list'),
    path('<slug:slug>/', views.detail, name='detail'),
]
