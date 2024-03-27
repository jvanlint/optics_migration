from enum import Enum
from unittest.mock import patch

import dcs
import pytest
from anytree import AnyNode, Node, RenderTree, Resolver, search
from anytree.exporter import JsonExporter
from dcs.mapping import Point
from dcs.mission import Mission

from optics.miz_import.new_mission_parser import parse_mission_to_tree


class NodeType(str, Enum):
    ROOT = "root"
    COALITION = "coalition"
    COUNTRY = "country"
    FLIGHT = "flight"
    WAYPOINTS = "waypoints"
    WAYPOINT = "waypoint"
    UNITS = "units"
    UNIT = "unit"


@pytest.fixture
def mission() -> Mission:
    m = dcs.mission.Mission()
    kobuleti = m.terrain.airports["Kobuleti"]
    kobuleti.set_blue()
    batumi = m.terrain.airports["Batumi"]
    batumi.set_blue()
    usa = m.coalition["blue"].country("USA")

    # Player A10 Group of 1 a/c
    A10_Group = m.flight_group_from_airport(
        usa,
        "A10 Group",
        dcs.planes.A_10C_2,
        kobuleti,
        start_type=dcs.mission.StartType.Warm,
    )
    A10_Group.units[0].set_player()
    A10_Group.add_runway_waypoint(kobuleti)
    A10_Group.add_runway_waypoint(batumi, batumi.runways[0], 8000)
    wp1 = Point(batumi.position.x + 1000, batumi.position.y + 1000, m.terrain)
    wp2 = Point(batumi.position.x + 2000, batumi.position.y + 2000, m.terrain)

    A10_Group.add_waypoint(wp1, 5000, 250, "waypoint_one")
    A10_Group.add_waypoint(wp2, 6000, 300, "waypoint_two")
    A10_Group.land_at(batumi)

    # Non player group
    awacs = m.awacs_flight(
        usa,
        "AWACS",
        dcs.planes.E_3A,
        batumi,
        batumi.position,
        race_distance=120 * 1000,
        heading=90,
    )

    # Non player Helo group
    heli = m.flight_group_inflight(
        usa,
        "Non_player Helo group",
        dcs.helicopters.UH_60A,
        dcs.mapping.Point(batumi.position.x + 1000 * 5, batumi.position.y, m.terrain),
        300,
        speed=150,
    )
    heli.add_runway_waypoint(kobuleti)
    heli.land_at(kobuleti)

    # Player Helo Group
    apache = m.flight_group_from_airport(
        usa, "Apache Group", dcs.helicopters.AH_64D_BLK_II, kobuleti, group_size=2
    )
    apache.add_runway_waypoint(kobuleti)
    [unit.set_player() for unit in apache.units]

    # carrier with aircraft
    seapoint = batumi.unit_zones[0].random_point()
    seapoint.y -= 10 * 1000
    sg = m.ship_group(usa, "CVN", dcs.countries.USA.Ship.Stennis, seapoint)
    F18 = m.flight_group_from_unit(
        usa, "F18 Carrier Group", dcs.planes.FA_18C_hornet, sg, group_size=4
    )
    [unit.set_player() for unit in F18.units]

    return m


def test_parse_mission_to_tree_adds_plane_group(mission):
    tree = parse_mission_to_tree(mission)
    plane_group = search.find_by_attr(tree, name="id", value="A10 Group")
    mission_ref = mission.coalition["blue"].country("USA").find_group("A10 Group")
    assert plane_group.type == NodeType.FLIGHT
    assert plane_group.frequency == mission_ref.frequency
    assert plane_group.task == mission_ref.task
    assert plane_group.state == {"opened": True}
    assert plane_group.parent.id == "USA"
    waypoint = search.find_by_attr(tree, name="id", value="A10 Group-wp-00")
    assert waypoint.text == 'wp 0 - From Parking Area Hot'
    assert waypoint.action == 'FromParkingAreaHot'
    assert waypoint.ETA == '12:00:00'
    assert waypoint.lat == '41°55\'41.68"N'
    assert waypoint.long == '41°52\'13.10"E'
    assert waypoint.type == NodeType.WAYPOINT
    assert waypoint.waypoint_type == 'TakeOffParkingHot'
    # we need to check against the fixture object as pydcs will change things like onboard num and callsign
    # each time we generate a mission.
    unit = search.find_by_attr(tree, name="id", value="airframe-1")
    airframe = mission.coalition["blue"].country("USA").find_group("A10 Group").units[0]
    assert unit.airframe_type == airframe.type
    assert unit.callsign == airframe.callsign_dict['name']
    assert unit.onboard_num == airframe.onboard_num
    assert unit.text == airframe.name


def test_parse_mission_to_tree_adds_helo_group(mission):
    tree = parse_mission_to_tree(mission)

    helo_group = search.find_by_attr(tree, name="id", value="Apache Group")
    mission_ref = mission.coalition["blue"].country("USA").find_group("Apache Group")

    assert helo_group.type == NodeType.FLIGHT
    assert helo_group.frequency == mission_ref.frequency
    assert helo_group.task == mission_ref.task
    assert helo_group.state == {"opened": True}
    assert helo_group.parent.id == "USA"
    waypoint = search.find_by_attr(tree, name="id", value='Apache Group-wp-01')
    miz_wp = mission.coalition['blue'].countries['USA'].helicopter_group[1].points[1]
    assert waypoint.text == 'wp 1 - Turning Point'
    assert waypoint.action == 'TurningPoint'
    assert waypoint.ETA == '12:00:00'
    assert waypoint.latlng == miz_wp.position.latlng().format_dms()
    unit = search.find_by_attr(tree, name="id", value="airframe-4")
    airframe = (
        mission.coalition["blue"].country("USA").find_group("Apache Group").units[0]
    )
    assert unit.airframe_type == airframe.type
    assert unit.callsign == airframe.callsign_dict['name']
    assert unit.onboard_num == airframe.onboard_num
    assert unit.text == airframe.name


# @pytest.mark.skip("Only used to build test data")
def test_build_tree_for_testing(mission):
    tree = parse_mission_to_tree(mission)
    exporter = JsonExporter()
    tree_dump = exporter.export(tree)
    print("should pause here")
    # ** Pause at the line above **
    # Save this data to conftest if necessary
    # Note that the unit tests are very tightly coupled to this data.
    assert True
