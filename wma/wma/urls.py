"""
URL configuration for wma project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import re
from urllib.parse import urlsplit

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from wma.media import uploaded_media

media_url = urlsplit(settings.MEDIA_URL)
media_prefix = media_url.path.strip('/')
media_patterns = []
if media_prefix and not media_url.scheme and not media_url.netloc:
    media_patterns.append(re_path(r'^' + re.escape(media_prefix) + r'/(?P<path>.*)$',
                                  uploaded_media, name='uploaded_media'))

urlpatterns = media_patterns + [
    path('healthz', lambda request: JsonResponse({'status': 'ok'})),
    path('admin/', admin.site.urls),
    path('', include('wmaApp.urls', namespace='wmaApp')),
    path('api/', include('wmaApp.api.urls', namespace='wma_api')),
    path('cached_api/', include('wmaApp.api_cached.urls', namespace='wma_api_cached')),
    path('', include('pwa.urls')),  # You MUST use an empty string as the URL prefix
]

# Static files are served by WhiteNoise in production.
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

