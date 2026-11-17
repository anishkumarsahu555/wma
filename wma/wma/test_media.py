"""Media delivery works in production without exposing files outside uploads."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import AccessToken


@override_settings(DEBUG=False, ALLOWED_HOSTS=['testserver'], SECURE_SSL_REDIRECT=False)
class MediaTests(SimpleTestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name) / 'uploads'
        self.root.mkdir()
        (self.root / 'Employee').mkdir()
        (self.root / 'Employee' / 'test photo.png').write_bytes(b'uploaded-image')
        self.settings_override = override_settings(MEDIA_ROOT=self.root)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.client = APIClient()
        self.user = SimpleNamespace(is_authenticated=True, is_active=True)

    def test_authenticated_image_in_production_and_new_upload(self):
        self.client.force_authenticate(user=self.user)
        for filename in ('test photo.png', 'uploaded-after-first-request.png'):
            (self.root / 'Employee' / filename).write_bytes(b'uploaded-image')
            response = self.client.get('/media/Employee/' + filename)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response['Content-Type'], 'image/png')
            self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
            self.assertIn('private', response['Cache-Control'])
            self.assertTrue(response['Content-Disposition'].startswith('inline'))
            self.assertEqual(b''.join(response.streaming_content), b'uploaded-image')
            response.close()
        response = self.client.head('/media/Employee/test%20photo.png')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'')
        response.close()

    @patch('rest_framework.authentication.SessionAuthentication.authenticate')
    def test_browser_session_is_accepted(self, authenticate):
        authenticate.return_value = (self.user, None)
        response = self.client.get('/media/Employee/test%20photo.png')
        self.assertEqual(response.status_code, 200)
        response.close()

    @patch('rest_framework_simplejwt.authentication.JWTAuthentication.get_user')
    def test_mobile_jwt_and_legacy_header_are_accepted(self, get_user):
        get_user.return_value = self.user
        token = AccessToken()
        token['user_id'] = 1
        for prefix in ('Bearer', 'JWT'):
            response = self.client.get('/media/Employee/test%20photo.png',
                                       HTTP_AUTHORIZATION=f'{prefix} {token}')
            self.assertEqual(response.status_code, 200)
            response.close()

    def test_anonymous_access_denied(self):
        self.assertIn(self.client.get('/media/Employee/test%20photo.png').status_code, (401, 403))

    def test_missing_directories_traversal_hidden_and_symlink_escape(self):
        self.client.force_authenticate(user=self.user)
        outside = Path(self.directory.name) / 'secret.txt'
        outside.write_text('private')
        (self.root / 'escape.txt').symlink_to(outside)
        (self.root / '.env').write_text('private')
        for path in ('missing.png', 'Employee/', '../secret.txt', '%2e%2e/secret.txt', '.env', 'escape.txt'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get('/media/' + path).status_code, 404)

    def test_active_content_downloads_and_writes_rejected(self):
        self.client.force_authenticate(user=self.user)
        (self.root / 'test.html').write_text('<script>alert(1)</script>')
        response = self.client.get('/media/test.html')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response['Content-Disposition'].startswith('attachment'))
        self.assertIn('sandbox', response['Content-Security-Policy'])
        response.close()
        self.assertEqual(self.client.post('/media/test.html').status_code, 405)
