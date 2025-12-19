from django.shortcuts import render

def impressum(request):
    return render(request, "legal/impressum.html")

def datenschutz(request):
    return render(request, "legal/datenschutz.html")
