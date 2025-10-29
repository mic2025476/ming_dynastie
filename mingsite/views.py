from django.shortcuts import render
from locations.models import Location

def index(request):
    locations = Location.objects.all().prefetch_related('menus')
    return render(request, 'mingsite/index.html', {'locations': locations})
