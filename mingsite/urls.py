from django.urls import path
from . import views

app_name = 'mingsite'

urlpatterns = [
    path('', views.index, name='index'),
]
