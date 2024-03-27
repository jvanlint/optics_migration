import os
from datetime import timedelta
from enum import Enum

from anytree import AnyNode
from dcs.mission import Mission


class NodeType(str, Enum):
    ROOT = "root"
    COALITION = "coalition"
    COUNTRY = "country"
    FLIGHT = "flight"
    WAYPOINTS = "waypoints"
    WAYPOINT = "waypoint"
    UNITS = "units"
    UNIT = "unit"


def load_external_mission(filename: str) -> tuple:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} does not exist")
    mission = Mission()
    results = mission.load_file(filename)
    return (mission, results)


"""Builds a tree of air units in the mission organized by coalition and country.

The tree root will be a node with type 'root'. The first level children 
will be nodes for each coalition in the mission with type 'coalition'.
The second level children will be nodes for each country in that coalition
with type 'country'. The third level children will be nodes for each flight 
in that country with type 'flight'. The fourth level children will be nodes
for each waypoint for that flight with type 'waypoint'and nodes for each 
unit in that flight with type 'unit'.

Args:
    mission: The loaded PyDCS mission object

Returns:
    The root node of the built tree
"""


def build_client_air_units_tree(mission: Mission) -> AnyNode:

    opened = {"opened": True}  # open this node in jtree
    disabled = {"disabled": True}  # disable this node in jtree
    selected = {"selected": True}  # select this node in jtree

    rootNode = AnyNode(
        id=NodeType.ROOT,
        text=mission.sortie_text(),
        state=opened,
        start_time=mission.start_time.isoformat(),
        type=NodeType.ROOT,
    )

    for index, coalition in enumerate(mission.coalition.values()):
        coalition_node = AnyNode(
            id=NodeType.COALITION + str(index),
            parent=rootNode,
            text=f'{coalition.name} coalition',
            state=opened,
            type=NodeType.COALITION,
        )

        countries = coalition.countries
        for country in countries.values():
            country_node = AnyNode(
                id=NodeType.COUNTRY + str(country.id),
                parent=coalition_node,
                text=country.name,
                state=opened,
                type=NodeType.COUNTRY,
            )
            client_plane_groups = [
                pg for pg in country.plane_group if pg.units[0].skill.value == "Client"
            ]
            for plane_group in client_plane_groups:

                plane_group_node = AnyNode(
                    id=NodeType.FLIGHT + str(plane_group.id),
                    parent=country_node,
                    text=plane_group.name,
                    frequency=plane_group.frequency,
                    task=plane_group.task,
                    type=NodeType.FLIGHT.value,
                )

                points_parent = AnyNode(
                    id=NodeType.WAYPOINTS + str(plane_group.id),
                    parent=plane_group_node,
                    text=f"{plane_group.name} Waypoints",
                    type=NodeType.WAYPOINTS,
                )

                for point_index, point in enumerate(plane_group.points):
                    point_node = AnyNode(
                        id=NodeType.WAYPOINT
                        + str(plane_group.id)
                        + str(point_index).zfill(2),
                        parent=points_parent,
                        latlng=point.position.latlng().format_dms(),
                        lat=point.position.latlng()._format_component(
                            point.position.latlng().lat, ("N", "S"), 2
                        ),
                        long=point.position.latlng()._format_component(
                            point.position.latlng().lng, ("E", "W"), 2
                        ),
                        waypoint_type=point.type,
                        alt=point.alt,
                        ETA=(mission.start_time + timedelta(seconds=point.ETA))
                        .time()
                        .isoformat(),
                        type=NodeType.WAYPOINT,
                        action=point.action.name,
                        text=point.type,
                    )

                units_list = AnyNode(
                    id=NodeType.UNITS + str(plane_group.id),
                    parent=plane_group_node,
                    text=f"{plane_group.name} Aircraft",
                    type=NodeType.UNITS,
                )

                for unit in plane_group.units:
                    name = f"{unit.onboard_num} - {unit.name} - {unit.type}"
                    unit_node = AnyNode(
                        id=NodeType.UNIT + str(unit.id),
                        parent=units_list,
                        unit_type=unit.type,
                        text=name,
                        name=unit.name,
                        onboard_num=unit.onboard_num,
                        type=NodeType.UNIT,
                    )

    return rootNode
