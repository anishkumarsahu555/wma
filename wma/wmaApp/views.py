from django.shortcuts import render

# Create your views here.

def dashboard(request):
    return render(request, 'wmaApp/dashboard.html')

def admin_home(request):
    return render(request, 'admin_home.html')

