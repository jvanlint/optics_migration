import os
from datetime import timedelta
from enum import Enum

from anytree import AnyNode, Node, RenderTree
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


def parse_mission_to_tree(mission: Mission):
    opened = {"opened": True}  # open this node in jtree
    disabled = {"disabled": True}  # disable this node in jtree
    selected = {"selected": True}  # select this node in jtree
    # "text" field is what is shown on jstree rendering on page
    root = AnyNode(
        id=NodeType.ROOT.value,
        text=mission.sortie_text(),
        state=opened,
        start_time=mission.start_time.isoformat(),
        type=NodeType.ROOT,
    )
    for coalition in mission.coalition.values():
        for country in coalition.countries.values():
            human_plane_groups = [pg for pg in country.plane_group if pg.has_human()]
            if human_plane_groups:
                coalition_node = AnyNode(
                    id=coalition.name,
                    state=opened,
                    type=NodeType.COALITION,
                    parent=root,
                )

                country_node = AnyNode(
                    id=country.shortname,
                    text=country.name,
                    state=opened,
                    type=NodeType.COUNTRY,
                    parent=coalition_node,
                )
            for plane_group in human_plane_groups:
                plane_group_name = plane_group.name
                plane_group_node = AnyNode(
                    id=plane_group.name,
                    frequency=plane_group.frequency,
                    task=plane_group.task,
                    type=NodeType.FLIGHT,
                    parent=country_node,
                    state={"opened": True},
                )

                human_units = [unit for unit in plane_group.units if unit.is_human()]
                for unit in human_units:
                    unit_node = AnyNode(
                        id=f"airframe-{unit.id}",
                        parent=plane_group_node,
                        airframe_type=unit.type,
                        callsign=unit.callsign_dict['name'],
                        type=NodeType.UNIT,
                        state={"opened": True},
                        text=unit.name,
                        onboard_num=unit.onboard_num,
                    )
                for point_index, point in enumerate(plane_group.points):
                    point_node = AnyNode(
                        id=f'{plane_group_name}-wp-{point_index:02d}',
                        parent=plane_group_node,
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
                        text=f"wp {point_index} - {point.action.value}",
                    )
            human_helo_groups = [
                hg for hg in country.helicopter_group if hg.has_human()
            ]
            for helo_group in human_helo_groups:
                helo_group_name = helo_group.name
                helo_group_node = AnyNode(
                    id=helo_group.name,
                    frequency=helo_group.frequency,
                    task=helo_group.task,
                    type=NodeType.FLIGHT,
                    parent=country_node,
                    state={"opened": True},
                )
                human_units = [unit for unit in helo_group.units if unit.is_human()]
                for unit in human_units:
                    unit_node = AnyNode(
                        id=f"airframe-{unit.id}",
                        parent=helo_group_node,
                        airframe_type=unit.type,
                        callsign=unit.callsign_dict['name'],
                        type=NodeType.UNIT,
                        state={"opened": True},
                        text=unit.name,
                        onboard_num=unit.onboard_num,
                    )
                for point_index, point in enumerate(helo_group.points):
                    point_node = AnyNode(
                        id=f'{helo_group_name}-wp-{point_index:02d}',
                        parent=helo_group_node,
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
                        text=f"wp {point_index} - {point.action.value}",
                    )
    # print(RenderTree(root))
    return root
