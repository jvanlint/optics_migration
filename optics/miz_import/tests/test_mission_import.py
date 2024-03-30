from pathlib import Path

import pytest
from anytree import AnyNode
from anytree.exporter import JsonExporter
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

import optics.miz_import.tree_parser as tree_parser
from optics.miz_import import mission_parser
from optics.opticsapp.models import (
    Aircraft,
    Campaign,
    Flight,
    Mission,
    Package,
    Waypoint,
    WaypointType,
)

# NOTE: full_tree is stored in conftest.py


THIS_DIR = Path(__file__).parent
test_mission_file = THIS_DIR / "missions/test1.miz"


@pytest.fixture
def flight(db) -> Flight:
    flight = baker.make(Flight)
    waypoints = baker.make(Waypoint, _quantity=6, flight=flight)
    aircraft = baker.make(Aircraft, _quantity=5, flight=flight)
    return flight


@pytest.fixture
def airframes(db):
    airframe_A10C = baker.make("Airframe", dcsname="A-10C")
    airframe_A10C2 = baker.make("Airframe", dcsname="A-10C_2")
    airframe_F18 = baker.make("Airframe", dcsname="F/A-18C")
    airframe_AV8B = baker.make("Airframe", dcsname="AV8BNA")
    airframe_F15C = baker.make("Airframe", dcsname="F-15C")
    airframe_unmapped = baker.make("Airframe", dcsname="Not-Mapped")


@pytest.fixture
def campaign() -> Campaign:
    return baker.make(Campaign, _fill_optional=True)


@pytest.fixture
def mission(campaign) -> Mission:
    return baker.make(Mission, campaign=campaign)


@pytest.fixture
def package(authenticated_user, mission) -> Package:
    return baker.make(Package, created_by=authenticated_user, mission=mission)


def test_copy_flight_to_package_returns_correct_packageID(flight, package):
    returned_id = tree_parser.copy_flight_to_package(flight, package)
    assert returned_id == package.id


def test_import_to_package_returns_404_for_no_package(authenticated_user, client):
    url = reverse("import_to_package")
    client.user = authenticated_user
    # session: https://docs.djangoproject.com/en/4.0/topics/testing/tools/#django.test.Client.session
    session = client.session
    session["package_id"] = None
    session.save()
    response = client.post(url)
    assert response.status_code == 404


@pytest.mark.django_db()
def test_correct_import_to_package_redirects_to_mision_page(
    client, package, authenticated_user, full_tree
):
    url = reverse("import_to_package")
    session = client.session
    session["package_id"] = package.id
    session["full_tree"] = JsonExporter().export(full_tree)
    session["import_entry_point"] = "package"
    session.save()
    client.user = authenticated_user
    selected_values = '["flight348","flight470", "unit883"]'
    response = client.post(url, data={"selected": selected_values})
    # redirected to the package page
    assertRedirects(response, reverse("package_v2", args={package.id}))
    # ,
    #     status_code=302,
    #     target_status_code=200,
    # )


# -----------------------------------------------
# Smoke Tests
# -----------------------------------------------


@pytest.mark.skip("Smoke Tests")
def test_authenticated_user_works(client, authenticated_user):
    client.user = authenticated_user
    response = client.get(reverse("reference_tables"))
    assert response.status_code == 200


@pytest.mark.skip("Smoke Tests")
def test_client_without_authenticated_user(client):
    response = client.get(reverse("reference_tables"))
    assert response.status_code == 302
