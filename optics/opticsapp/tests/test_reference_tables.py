from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from ..models import (
    Airframe,
    Terrain,
    Status,
    Task,
    SupportType,
    WaypointType,
    ThreatType,
    AirframeDefaults,
)
from ..forms import (
    AirframeForm,
    TerrainForm,
    StatusForm,
    TaskForm,
    SupportTypeForm,
    WaypointTypeForm,
    ThreatTypeForm,
    AirframeDefaultsForm,
)


class ReferenceTablesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")
        self.client.login(username="testuser", password="12345")

    def test_reference_tables_view(self):
        url = reverse("reference_tables")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_reference_object_add_view(self):
        url = reverse("reference_object_add", args=["airframe"])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_reference_object_add_post(self):
        url = reverse("reference_object_add", args=["airframe"])
        data = {"name": "Test Airframe", "description": "Test Description"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertTrue(Airframe.objects.filter(name="Test Airframe").exists())
