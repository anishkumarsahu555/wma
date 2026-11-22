"""Authenticated delivery of mutable uploads in the direct Gunicorn deployment."""
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication


@api_view(['GET', 'HEAD'])
@authentication_classes([SessionAuthentication, JWTAuthentication])
@permission_classes([IsAuthenticated])
def uploaded_media(request, path):
    """Stream files inside MEDIA_ROOT; do not expose directories or hidden files."""
    try:
        relative = Path(path)
        if relative.is_absolute() or any(part.startswith('.') for part in relative.parts):
            raise Http404
        root = Path(settings.MEDIA_ROOT).resolve()
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file():
            raise Http404
        stream = target.open('rb')
    except (OSError, ValueError):
        raise Http404 from None
    content_type = mimetypes.guess_type(target.name)[0] or 'application/octet-stream'
    # Only passive raster formats render inline on the application's origin.
    inline = content_type in {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/avif',
        'image/bmp', 'image/tiff', 'image/x-icon', 'image/vnd.microsoft.icon',
    }
    response = FileResponse(stream, content_type=content_type,
                            as_attachment=not inline, filename=target.name)
    response['Cache-Control'] = 'private, no-store'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Content-Security-Policy'] = "sandbox; default-src 'none'"
    return response
