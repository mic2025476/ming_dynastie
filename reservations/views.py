from django.shortcuts import render
def request_reservation(request): return render(request, 'reservations/form.html')
