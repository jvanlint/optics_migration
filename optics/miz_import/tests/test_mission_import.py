from pathlib import Path
import pytest
from anytree import AnyNode
from anytree.exporter import JsonExporter
from django.urls import reverse
from model_bakery import baker
from pytest_django.asserts import assertRedirects

import optics.miz_import.util as util
from optics.miz_import.tests.data import TestData
from optics.opticsapp.models import Aircraft, Flight, Package, Waypoint, WaypointType

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
    airframe_A10C = baker.make("Airframe", dcs_mapping="A-10C")
    airframe_A10C2 = baker.make("Airframe", dcs_mapping="A-10C_2")
    airframe_F18 = baker.make("Airframe", dcs_mapping="F/A-18C")
    airframe_AV8B = baker.make("Airframe", dcs_mapping="AV8BNA")
    airframe_F15C = baker.make("Airframe", dcs_mapping="F-15C")
    airframe_unmapped = baker.make("Airframe")


@pytest.fixture
def package(db, authenticated_user) -> Package:
    return baker.make(
        Package, created_by=authenticated_user, _fill_optional=["mission"]
    )


@pytest.mark.django_db()
def test_build_full_flight_adds_all_children(full_tree: AnyNode):
    new_flight = util.build_full_flight(full_tree, "flight348")
    assert new_flight.aircraft_set.filter(tailcode="812").exists()
    assert new_flight.aircraft_set.filter(tailcode="813").exists()
    assert new_flight.aircraft_set.filter(tailcode="814").exists()
    assert new_flight.aircraft_set.filter(tailcode="815").exists()
    assert new_flight.waypoint_set.filter(number="1").exists()
    assert new_flight.waypoint_set.filter(number="2").exists()


@pytest.mark.django_db()
def test_unit_nodes_are_created(full_tree: AnyNode):
    selected_items = ["unit879", "unit880", "unit881", "unit882"]
    units = util.create_units(full_tree, selected_items)
    assert units[0].tailcode == "812"
    assert units[1].tailcode == "813"
    assert units[2].tailcode == "814"
    assert units[3].tailcode == "815"


@pytest.mark.django_db()
def test_waypoint_nodes_are_created(full_tree: AnyNode):
    selected_items = ["waypoint34800", "waypoint34801"]
    waypoints = util.create_waypoints(full_tree, selected_items)
    assert waypoints[0].name == "TakeOffParking - Alt 18"
    assert waypoints[1].name == "Turning Point - Alt 2000"


def test_copy_flight_to_package_returns_correct_packageID(flight, package):
    returned_id = util.copy_flight_to_package(flight, package)
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
def test_import_to_package_works_with_mixed_tree_levels(
    package, authenticated_user, full_tree, airframes, client
):
    url = reverse("import_to_package")
    client.user = authenticated_user
    session = client.session
    session["return_url"] = reverse("package_v2", args={package.id})
    session["package_id"] = package.id
    session["full_tree"] = JsonExporter().export(full_tree)
    session["import_entry_point"] = "package"
    session.save()
    selected_values = '["flight348","flight470", "unit883"]'
    # client.force_login(client.user)
    response = client.post(url, data={"selected": selected_values}, follow=True)
    # redirected to the package page
    assertRedirects(
        response, session["return_url"], status_code=302, target_status_code=200
    )
    # correct flights were made and attached to package
    assert Package.objects.filter(flight__callsign__icontains="KOB").exists()
    assert Package.objects.filter(flight__callsign__icontains="Harrier").exists()
    assert Package.objects.filter(flight__callsign__icontains="Boar").exists()

    # correct aircraft were made
    assert Aircraft.objects.filter(tailcode="812").exists()  # Boar
    assert Aircraft.objects.filter(tailcode="813").exists()
    assert Aircraft.objects.filter(tailcode="814").exists()
    assert Aircraft.objects.filter(tailcode="815").exists()
    assert Aircraft.objects.filter(tailcode="010").exists()  # KOB F15
    assert Aircraft.objects.filter(tailcode="951").exists()
    assert Aircraft.objects.filter(tailcode="208").exists()  # GUD Harrier

    # Aircraft assigned to correct flights
    assert (
        Flight.objects.filter(aircraft__type__dcs_mapping="F-15C").first().callsign
        == "KOB F15"
    )
    assert (
        Flight.objects.filter(aircraft__type__dcs_mapping="AV8BNA").first().callsign
        == "GUD Harrier 1"
    )


@pytest.mark.django_db()
def test_import_to_package_works_with_country_selected(
    client, package, authenticated_user, full_tree, airframes
):
    url = reverse("import_to_package")
    session = client.session
    session["package_id"] = package.id
    session["full_tree"] = JsonExporter().export(full_tree)
    session["import_entry_point"] = "package"
    session.save()
    client.user = authenticated_user
    selected_values = '["country2"]'
    response = client.post(url, data={"selected": selected_values})
    # redirected to the package page
    assertRedirects(
        response,
        reverse("package_v2", args={package.id}),
        status_code=302,
        target_status_code=200,
    )

    # correct flights were made and attached to package
    assert Package.objects.filter(flight__callsign__icontains="KOB").exists()
    assert Package.objects.filter(flight__callsign__icontains="Harrier").exists()
    assert Package.objects.filter(flight__callsign__icontains="Boar").exists()

    # correct aircraft were made
    assert Aircraft.objects.filter(tailcode="812").exists()  # Boar
    assert Aircraft.objects.filter(tailcode="813").exists()
    assert Aircraft.objects.filter(tailcode="814").exists()
    assert Aircraft.objects.filter(tailcode="815").exists()
    assert Aircraft.objects.filter(tailcode="010").exists()  # KOB F15
    assert Aircraft.objects.filter(tailcode="951").exists()
    assert Aircraft.objects.filter(tailcode="208").exists()  # GUD Harrier

    # Aircraft assigned to correct flights
    assert (
        Flight.objects.filter(aircraft__type__dcs_mapping="F-15C").first().callsign
        == "KOB F15"
    )
    assert (
        Flight.objects.filter(aircraft__type__dcs_mapping="AV8BNA").first().callsign
        == "GUD Harrier 1"
    )


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
    assertRedirects(
        response,
        reverse("package_v2", args={package.id}),
        status_code=302,
        target_status_code=200,
    )


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


# -----------------------------------------------
# Test data setup
# -----------------------------------------------


@pytest.mark.skip("Only used to build test data")
def test_build_client_air_units_from_existing_mission():
    mission, _ = util.load_external_mission(test_mission_file)
    tree = util.build_client_air_units_tree(mission)
    exporter = JsonExporter()
    tree_dump = exporter.export(tree)
    # ** Pause at the line above **
    # Save this data to conftest if necessary
    # Note that the unit tests are very tightly coupled to this data.
    assert True
