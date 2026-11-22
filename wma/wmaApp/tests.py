from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth.models import Group, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from wmaApp.models import Customer, Location, Owner, StaffUser, UserGroup


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class ProfilePhotoUpdateTests(TestCase):
    def setUp(self):
        media = TemporaryDirectory()
        self.addCleanup(media.cleanup)
        settings = override_settings(MEDIA_ROOT=media.name)
        settings.enable()
        self.addCleanup(settings.disable)

        user = User.objects.create_user(username="owner")
        user.groups.add(Group.objects.create(name="Owner"))
        owner = Owner.objects.create(userID=user)
        group = UserGroup.objects.create(ownerID=owner, name="Driver")
        location = Location.objects.create(ownerID=owner, name="Main")
        staff_user = User.objects.create_user(username="staff")
        self.staff = StaffUser.objects.create(ownerID=owner, userID=staff_user, groupID=group)
        self.customer = Customer.objects.create(ownerID=owner, locationID=location)
        self.client = Client(enforce_csrf_checks=True)
        self.client.force_login(user)
        self.assertEqual(self.client.get(reverse("wmaApp:manage_staff")).status_code, 200)
        self.client.defaults["HTTP_X_CSRFTOKEN"] = self.client.cookies["csrftoken"].value
        self.fields = {"name": "Updated name", "address": "Main road", "phone": "1234567890"}
        self.staff_fields = {
            **self.fields, "id": self.staff.pk, "email": "staff@example.com",
            "group": group.name, "password": "test-password", "is_active": "Active",
        }
        self.customer_fields = {**self.fields, "id": self.customer.pk, "location": location.pk}

    def test_replacement_and_text_only_edit(self):
        for api, instance, fields in (
            ("update_staff_api", self.staff, self.staff_fields),
            ("update_customer_api", self.customer, self.customer_fields),
        ):
            with self.subTest(api=api):
                url = reverse(f"wma_api:{api}")
                image = BytesIO()
                Image.new("RGB", (256, 256)).save(image, "PNG")
                photo = SimpleUploadedFile("photo.png", image.getvalue(), "image/png")
                response = self.client.post(url, {**fields, "profile_pic": photo})
                self.assertEqual(response.status_code, 200, response.content)

                instance.refresh_from_db()
                photo_name = instance.profile_pic.name
                with Image.open(instance.profile_pic.path) as original:
                    self.assertEqual(original.size, (256, 256))
                with Image.open(instance.profile_pic.thumb.path) as thumbnail:
                    self.assertEqual(thumbnail.size, (128, 128))

                response = self.client.post(url, {**fields, "name": "Text only"})
                self.assertEqual(response.status_code, 200, response.content)
                instance.refresh_from_db()
                self.assertEqual(instance.name, "Text only")
                self.assertEqual(instance.profile_pic.name, photo_name)

    def test_invalid_upload_leaves_record_unchanged(self):
        photo = SimpleUploadedFile("invalid.png", b"invalid image", "image/png")
        response = self.client.post(
            reverse("wma_api:update_staff_api"), {**self.staff_fields, "profile_pic": photo}
        )
        self.assertEqual(response.status_code, 400)
        self.staff.refresh_from_db()
        self.assertIsNone(self.staff.name)
        self.assertFalse(self.staff.profile_pic)
