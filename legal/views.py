from django.shortcuts import render

def impressum(request):
    return render(request, "ming/legal/impressum.html")

def datenschutz(request):
    return render(request, "ming/legal/datenschutz.html")