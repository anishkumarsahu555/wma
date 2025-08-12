from django.conf.urls import url
from .views import *

urlpatterns = [
    # pages
    url(r'^$', activate, name='activate'),
    ]