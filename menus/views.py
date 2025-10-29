from django.shortcuts import render
from .models import MenuDocument

def list_menus(request):
    # group by location for display
    menus = MenuDocument.objects.filter(is_active=True).select_related('location')
    # build a dict: {location: [docs]}
    grouped = {}
    for m in menus:
        grouped.setdefault(m.location, []).append(m)
    return render(request, 'menus/list.html', {'grouped': grouped})
