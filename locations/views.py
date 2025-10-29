from django.shortcuts import render, get_object_or_404
from .models import Location

def list_locations(request):
    return render(request, 'locations/list.html', {
        'locations': Location.objects.all()
    })

def detail(request, slug):
    loc = get_object_or_404(Location, slug=slug)
    return render(request, 'locations/detail.html', {'loc': loc})
