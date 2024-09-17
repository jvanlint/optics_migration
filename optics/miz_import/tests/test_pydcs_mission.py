import os
import pickle
import sys

import pytest

# Get the absolute path of the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Add the project root to the Python path
sys.path.append(project_root)
from optics.miz_import.pydcs_mission import AircraftGroup, DCSMission, Point, Projection

TEST_MIZ_FILE = "optics/miz_import/tests/missions/test.miz"
TEST_MISSION_DATA = 'optics/miz_import/tests/missions/mission_dict.pickle'
TEST_MISSION_TEXT = 'optics/miz_import/tests/missions/text_dict.pickle'


@pytest.fixture
def mission_dict():
    with open(TEST_MISSION_DATA, 'rb') as f:
        return pickle.load(f)


@pytest.fixture
def text_dict():
    with open(TEST_MISSION_TEXT, 'rb') as f:
        return pickle.load(f)


def test_load_file():
    mission = DCSMission()
    # optics/miz_import/tests/missions/test.miz
    result = mission.load_file(TEST_MIZ_FILE)
    assert len(mission.aircraft_groups) != 0


def test_extract_mission_dictionaries():
    mission = DCSMission()
    mission_dict, text_dict = mission._extract_mission_dictionaries(TEST_MIZ_FILE)
    assert isinstance(mission_dict, dict)
    assert isinstance(text_dict, dict)


def test_setup_terrain(mission_dict: dict):
    mission = DCSMission()
    mission._setup_terrain(mission_dict)
    assert mission.terrain is not None


def test_import_base_values(mission_dict: dict, text_dict: dict):
    mission = DCSMission()
    mission._import_base_values(mission_dict, text_dict)
    assert mission.description_text == "Test Mission description text"
    assert mission.description_bluetask == "Test Mission bluetask text"
    assert mission.description_redtask == "Test Mission redtask text"
    assert mission.sortie == "Test Mission sortie"


def test_set_mission_time(mission_dict: dict):
    mission = DCSMission()
    mission._set_mission_time(mission_dict)
    assert mission.start_time is not None


def test_import_weather(mission_dict: dict):
    mission = DCSMission()
    mission._import_weather(mission_dict)
    assert mission.weather is not None
    assert mission.weather.name == "Summer, clean sky"
    assert mission.weather.visibility == 80000
    assert mission.weather.qnh == 760
    assert mission.weather.temperature == 20
    assert mission.weather.wind_at_ground["speed"] == 0
    assert mission.weather.wind_at_ground["direction"] == 0
    assert mission.weather.wind_at_2k["speed"] == 0
    assert mission.weather.wind_at_2k["direction"] == 0
    assert mission.weather.wind_at_8k["speed"] == 0
    assert mission.weather.wind_at_8k["direction"] == 0


def test_load_bullseye(mission_dict: dict):
    mission = DCSMission()
    mission._load_bullseye(mission_dict)
    assert mission.bullseye_blue is not None
    assert mission.bullseye_red is not None
    assert mission.bullseye_blue.x == mission_dict['coalition']['blue']['bullseye']["x"]
    assert mission.bullseye_blue.y == mission_dict['coalition']['blue']['bullseye']["y"]
    assert mission.bullseye_red.x == mission_dict['coalition']['red']['bullseye']["x"]
    assert mission.bullseye_red.y == mission_dict['coalition']['red']['bullseye']["y"]


def test_create_waypoint_objects(mission_dict: dict):
    for coalition_name, coalition in mission_dict['coalition'].items():
        for country in coalition['country'].values():
            if 'plane' in country and 'group' in country['plane']:
                for plane_group in country['plane']['group'].values():
                    pg = AircraftGroup()
                    points = pg.create_waypoint_objects(plane_group)

                    assert points is not None
                    assert len(points) > 0
                    # Test the first point
                    first_point = points[0]
                    assert hasattr(first_point, 'x')
                    assert hasattr(first_point, 'y')
                    assert hasattr(first_point, 'alt')
                    assert hasattr(first_point, 'type')

                    # Test if the number of points matches the route points
                    assert len(points) == len(plane_group['route']['points'])
                    # Test if the coordinates match
                    for i, point in enumerate(points):
                        original_point = plane_group['route']['points'][i + 1]
                        assert point.x == original_point['x']
                        assert point.y == original_point['y']
                        assert point.alt == original_point['alt']
                        assert point.type == original_point['type']
                        # Test if the number of units matches the original data
                    assert len(points) == len(plane_group['route']['points'])


def test_create_unit_object(mission_dict: dict):
    # group_1 = mission_dict['coalition']['blue']['country'][19]['plane']['group'][1]
    pg = AircraftGroup()
    coalition = mission_dict['coalition']['blue']
    country = next(
        country
        for country in coalition['country'].values()
        if 'plane' in country and 'group' in country['plane']
    )
    plane_group = next(iter(country['plane']['group'].values()))

    pg = AircraftGroup()
    units = pg.create_unit_objects(plane_group)

    assert units is not None
    assert len(units) > 0

    # Test the first unit
    first_unit = units[0]
    assert hasattr(first_unit, 'type')
    assert hasattr(first_unit, 'name')
    assert hasattr(first_unit, 'player')
    assert hasattr(first_unit, 'callsign')

    # Test if the number of units matches the original data
    assert len(units) == len(plane_group['units'])

    # Test if the unit data matches
    for i, unit in enumerate(units):
        original_unit = plane_group['units'][i + 1]
        assert unit.type == original_unit['type']
        assert unit.name == original_unit['name']
        assert unit.player == (
            True if original_unit.get("skill") == "Player" else False
        )
        assert unit.callsign == original_unit['callsign']['name']


def test_create_unit_object_for_planes(mission_dict: dict):
    for coalition_name, coalition in mission_dict['coalition'].items():
        for country in coalition['country'].values():
            if 'plane' in country and 'group' in country['plane']:
                for plane_group in country['plane']['group'].values():
                    pg = AircraftGroup()
                    units = pg.create_unit_objects(plane_group)

                    assert units is not None
                    assert len(units) > 0

                    # Test each unit
                    for i, unit in enumerate(units):
                        original_unit = plane_group['units'][i + 1]
                        assert unit.type == original_unit['type']
                        assert unit.name == original_unit['name']
                        assert unit.player == (
                            True if original_unit.get("skill") == "Player" else False
                        )
                        assert unit.callsign == original_unit['callsign']['name']
                        assert unit.onboard_number == original_unit['onboard_num']

                    # Test if the number of units matches the original data
                    assert len(units) == len(plane_group['units'])


def test_create_unit_object_for_helos(mission_dict: dict):
    for coalition_name, coalition in mission_dict['coalition'].items():
        for country in coalition['country'].values():
            if 'helicopter' in country and 'group' in country['plane']:
                for helo_group in country['helicopter']['group'].values():
                    pg = AircraftGroup()
                    units = pg.create_unit_objects(helo_group)

                    assert units is not None
                    assert len(units) > 0

                    # Test each unit
                    for i, unit in enumerate(units):
                        original_unit = helo_group['units'][i + 1]
                        assert unit.type == original_unit['type']
                        assert unit.name == original_unit['name']
                        assert unit.player == (
                            True if original_unit.get("skill") == "Player" else False
                        )
                        assert unit.callsign == original_unit['callsign']['name']
                        assert unit.onboard_number == original_unit['onboard_num']

                    # Test if the number of units matches the original data
                    assert len(units) == len(helo_group['units'])


def test_DCSMission_to_tree(mission_dict: dict):
    mission = DCSMission()
    mission.load_file(TEST_MIZ_FILE)
    tree = mission.to_tree()
    assert tree is not None


def test_point_latlng() -> None:
    caucasus = Projection(33, -99516.9999999732, -4998114.999999984, 0.9996)
    p = Point(0, 0, "test zero point")
    ll = p.latlng(caucasus)
    pytest.approx(ll.lat, 45.129497060328966)
    pytest.approx(ll.lng, 34.265515188456)
    assert ll.format_dms() == '45°07\'46"N 34°15\'56"E'
    # print(ll.format_dms()) == 45°07'46"N 34°15'56"E
    assert ll.format_dms(True) == '45°07\'46.19"N 34°15\'55.85"E'
