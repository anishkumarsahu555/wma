from django.urls import path
from . import views

app_name = 'wmaApp'  # Add this line to specify the app_name

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
]