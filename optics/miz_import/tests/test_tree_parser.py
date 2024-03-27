import dcs
import pytest
from anytree import ContRoundStyle, Node, RenderTree
from anytree import search as tree_search
from django.core.exceptions import ObjectDoesNotExist
from model_bakery import baker

from optics.miz_import import tree_parser
from optics.opticsapp.models import (
    Aircraft,
    Airframe,
    DCSAirframe,
    Flight,
    Mission,
    Package,
    Waypoint,
)


@pytest.fixture
def airframes(db):  # , dcsnames):
    # dcs_airframe_A10C = DCSAirframe(dcsname=dcsnames.A10)
    # dcs_airframe_F18C = DCSAirframe(dcsname=dcsnames.F18)
    A10 = DCSAirframe.objects.create(dcsname="A-10C_2")
    F18 = DCSAirframe.objects.create(dcsname="FA-18C_hornet")
    airframe_A10C = Airframe.objects.create(dcsname=A10)
    airframe_F18C = Airframe.objects.create(dcsname=F18)
    return [airframe_A10C, airframe_F18C]


@pytest.fixture
def red_airframes(db):
    SU33 = DCSAirframe.objects.create(dcsname="Su-33")
    airframe_SU33 = Airframe.objects.create(dcsname=SU33)
    return [airframe_SU33]


@pytest.fixture
def package():
    package = baker.make(Package)
    mission = baker.make(Mission, package=package)
    return package


@pytest.fixture
def flight_node(full_tree):
    '''
    AnyNode(name='mission', start_time='2011-06-01T12:00:00+00:00', state={'opened': True}, text='', type='root')
    ╰── AnyNode(name='blue', state={'opened': True}, type='coalition')
        ╰── AnyNode(name='USA', state={'opened': True}, type='country')
            ├── AnyNode(frequency=251, name='A10 Group', state={'opened': True}, task='CAS', type='flight')
            │   ├── AnyNode(ETA='12:00:00', action='FromParkingAreaHot', alt=0, lat='41°55\'41.68"N', latlng='41°55\'42"N 41°52\'13"E', long='41°52\'13.10"E', name='wp00', text='TakeOffParkingHot', type='waypoint', waypoint_type='TakeOffParkingHot')
            │   ├── AnyNode(ETA='12:00:00', action='TurningPoint', alt=300, lat='41°54\'59.14"N', latlng='41°54\'59"N 41°47\'28"E', long='41°47\'28.40"E', name='wp01', text='Turning Point', type='waypoint', waypoint_type='Turning Point')
            │   ├── AnyNode(ETA='12:00:00', action='TurningPoint', alt=300, lat='41°39\'39.10"N', latlng='41°39\'39"N 41°32\'01"E', long='41°32\'0.93"E', name='wp02', text='Turning Point', type='waypoint', waypoint_type='Turning Point')
            │   ├── AnyNode(ETA='12:00:00', action='TurningPoint', alt=5000, lat='41°37\'3.39"N', latlng='41°37\'03"N 41°36\'48"E', long='41°36\'47.87"E', name='wp03', text='Turning Point', type='waypoint', waypoint_type='Turning Point')
            │   ├── AnyNode(ETA='12:00:00', action='TurningPoint', alt=6000, lat='41°37\'32.22"N', latlng='41°37\'32"N 41°37\'35"E', long='41°37\'34.90"E', name='wp04', text='Turning Point', type='waypoint', waypoint_type='Turning Point')
            │   ├── AnyNode(ETA='12:00:00', action='Landing', alt=0, lat='41°36\'34.55"N', latlng='41°36\'35"N 41°36\'01"E', long='41°36\'0.85"E', name='wp05', text='Land', type='waypoint', waypoint_type='Land')
            │   ╰── AnyNode(airframe_type='A-10C_2', callsign='Enfield11', id=1, name='Enfield11', onboard_num='064', state={'opened': True}, text='A10 Group Pilot #1', type='unit')

    '''
    return tree_search.find_by_attr(full_tree, value="A10 Group", name='id')


@pytest.mark.django_db
def test_build_full_flight_adds_all_children(flight_node, airframes):
    result = tree_parser.build_full_flight(flight_node)
    assert result.waypoint_set.count() == 6
    assert result.aircraft_set.count() == 1


@pytest.fixture
def unit_node(full_tree):
    '''
    AnyNode(airframe_type='FA-18C_hornet', callsign='Colt11', id='airframe-7', onboard_num='912', state={'opened': True}, text='F18 Carrier Group Pilot #1', type='unit')
    '''
    return tree_search.find_by_attr(full_tree, value="Colt11", name='callsign')


@pytest.mark.django_db
def test_create_aircraft_sets_correct_tailcode(unit_node, airframes):
    aircraft = tree_parser.create_aircraft(unit_node)
    assert aircraft.tailcode == '912'


@pytest.mark.django_db
def test_create_aircraft_sets_correct_airframe(unit_node, airframes):
    aircraft = tree_parser.create_aircraft(unit_node)
    assert aircraft.type == airframes[1]  # FA-18C_hornet


@pytest.mark.django_db
def test_create_aircraft_returns_aircraft_instance(unit_node, airframes):
    aircraft = tree_parser.create_aircraft(unit_node)
    assert isinstance(aircraft, Aircraft)


@pytest.mark.django_db
def test_create_aircraft_handles_missing_tailcode(unit_node, airframes):
    unit_node.onboard_num = None
    aircraft = tree_parser.create_aircraft(unit_node)
    assert aircraft.tailcode == None


@pytest.mark.django_db
def test_create_aircraft_throws_correct_error_when_airframe_not_linked(
    unit_node, airframes
):
    F18 = Airframe.objects.get(dcsname="FA-18C_hornet")
    F18.delete()
    with pytest.raises(ObjectDoesNotExist):
        aircraft = tree_parser.create_aircraft(unit_node)


@pytest.mark.django_db
def test_add_to_package_creates_flights(package, full_tree, airframes):
    tree_parser.add_to_package(full_tree, ['F18 Carrier Group'], package)
    assert Flight.objects.filter(callsign="Colt12").exists()


@pytest.mark.django_db
def test_add_to_package_creates_aircraft(package, full_tree, airframes):
    tree_parser.add_to_package(full_tree, ["airframe-9"], package)
    assert Aircraft.objects.filter(tailcode="212").exists()


@pytest.mark.django_db
def test_add_to_package_creates_waypoints(package, full_tree, airframes):
    tree_parser.add_to_package(full_tree, ["A10 Group"], package)
    assert Waypoint.objects.filter(text="wp 1 - Turning Point").exists()


@pytest.mark.django_db
def test_add_to_package_handles_coalition(full_tree, package, red_airframes):
    tree_parser.add_to_package(full_tree, ["blue"], package)
    '''
   
    
    
    '''
    # Assert flights created
    # assert Flight.objects.filter(callsign="CVN-71 F/A-18C #001").exists()
    assert Flight.objects.filter(callsign="Kuznetsov Su-33").exists()

    # Assert units created
    assert Aircraft.objects.filter(tailcode="180").exists()
    assert Aircraft.objects.filter(tailcode="183").exists()

    # Assert waypoints created
    assert Waypoint.objects.filter(name="TakeOffParking").exists()

    # Assert all linked to package
    for flight in Flight.objects.all():
        assert flight.package == package


@pytest.mark.django_db
def test_add_to_package_handles_country(full_tree, package, red_airframes):
    tree_parser.add_to_package(full_tree, ["USA"], package)

    # Assert flights, units, waypoints created and linked to package

    # Assert flights created
    assert Flight.objects.filter(callsign="Kuznetsov Su-33").exists()

    # Assert units created
    assert Aircraft.objects.filter(tailcode="180").exists()
    assert Aircraft.objects.filter(tailcode="183").exists()

    # Assert waypoints created
    assert Waypoint.objects.filter(name="TakeOffParking").exists()

    # Assert all linked to package
    for flight in Flight.objects.all():
        assert flight.package == package


@pytest.mark.django_db
def test_add_to_package_handles_waypoints(full_tree, package, airframes):
    tree_parser.add_to_package(full_tree, ["waypoints376"], package)

    flight = Flight.objects.get(callsign="CVN-71 F/A-18C (HOT)")

    # Assert waypoints created
    assert Waypoint.objects.filter(name="TakeOffParkingHot").exists()
    assert Waypoint.objects.filter(name="Turning Point").exists()

    # Assert linked to flight
    for wp in flight.waypoint_set.all():
        assert wp.flight == flight

    # Assert flight linked to package
    assert flight.package == package


@pytest.mark.django_db
def test_add_to_package_handles_units(full_tree, package, airframes):
    tree_parser.add_to_package(full_tree, ["units376"], package)

    flight = Flight.objects.get(callsign="CVN-71 F/A-18C (HOT)")

    # Assert units created
    assert Aircraft.objects.filter(tailcode="142").exists()
    assert Aircraft.objects.filter(tailcode="143").exists()

    # Assert linked to flight
    for ac in flight.aircraft_set.all():
        assert ac.flight == flight

    # Assert flight linked to package
    assert flight.package == package


@pytest.mark.django_db
def test_add_to_package_handles_multiple_nodes(full_tree, package, airframes):
    nodes = ["flight376", "units376", "waypoints376"]
    tree_parser.add_to_package(full_tree, nodes, package)

    flight = Flight.objects.get(callsign="CVN-71 F/A-18C (HOT)")

    # Assert flight created
    assert Flight.objects.filter(callsign="CVN-71 F/A-18C (HOT)").exists()

    # Assert waypoints created
    assert Waypoint.objects.filter(name="TakeOffParkingHot").exists()
    assert Waypoint.objects.filter(name="Turning Point").exists()

    # Assert waypoints linked to flight
    for wp in flight.waypoint_set.all():
        assert wp.flight == flight

    # Assert units created
    assert Aircraft.objects.filter(tailcode="142").exists()
    assert Aircraft.objects.filter(tailcode="143").exists()

    # Assert units linked to flight
    for ac in flight.aircraft_set.all():
        assert ac.flight == flight

    # Assert flight linked to package
    assert flight.package == package

    # Assert waypoints linked to package via flight
    for wp in flight.waypoint_set.all():
        assert wp.flight.package == package

    # Assert units linked to package via flight
    for ac in flight.aircraft_set.all():
        assert ac.flight.package == package
