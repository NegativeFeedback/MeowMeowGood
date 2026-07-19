from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class ImpersonationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser("admin", password="unused")
        self.alice = User.objects.create_user("alice")
        self.bob = User.objects.create_user("bob")

    def test_non_superuser_cannot_view_user_list(self):
        self.client.force_login(self.alice)
        response = self.client.get(reverse("accounts:user_list"))
        self.assertEqual(response.status_code, 403)

    def test_non_superuser_cannot_start_impersonation(self):
        self.client.force_login(self.alice)
        response = self.client.post(reverse("accounts:impersonate_start", args=[self.bob.pk]))
        self.assertEqual(response.status_code, 403)

    def test_superuser_can_impersonate_another_user(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("accounts:impersonate_start", args=[self.alice.pk]), follow=True)
        self.assertEqual(response.wsgi_request.user, self.alice)
        self.assertEqual(self.client.session.get("impersonator_id"), self.admin.pk)

    def test_stop_impersonating_restores_original_user(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:impersonate_start", args=[self.alice.pk]))

        response = self.client.post(reverse("accounts:impersonate_stop"), follow=True)
        self.assertEqual(response.wsgi_request.user, self.admin)
        self.assertNotIn("impersonator_id", self.client.session)

    def test_cannot_impersonate_self(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("accounts:impersonate_start", args=[self.admin.pk]), follow=True)
        self.assertEqual(response.wsgi_request.user, self.admin)
        self.assertNotIn("impersonator_id", self.client.session)
