from enum import Enum
from anytree import AnyNode, search as tree_search
from dcs import Mission
from apps.airops.models import (
    Flight,
    Waypoint,
    WaypointType,
    Aircraft,
    Package,
    Airframe,
)
from datetime import timedelta


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
    m = Mission()
    results = m.load_file(filename)
    return (m, results)


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
                    text = f"{point.type} - Alt {point.alt}"
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
                        text=text,
                    )
                    print(point.type)

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


def create_waypoints(full_tree: AnyNode, waypoint_node_ids: list) -> list:
    waypoints = []
    for id in waypoint_node_ids:
        waypoints.append(create_waypoint(full_tree, id))
    return waypoints  # list of waypoint objects


def create_waypoint(full_tree: AnyNode, waypoint_node_id: str) -> Waypoint:
    wp_node = tree_search.find_by_attr(full_tree, waypoint_node_id, name='id')
    if wp_node is not None:
        # wp = Waypoint()
        wp = Waypoint.objects.create(
            number=int(waypoint_node_id[-2:]),
            name=wp_node.text,
            lat=wp_node.lat,
            long=wp_node.long,
            elevation=wp_node.alt,
            tot=wp_node.ETA,
            waypoint_type=WaypointType.objects.filter(
                dcs_mapping=wp_node.waypoint_type
            ).first(),
        )
        return wp
        # wp.number = int(id[-2:])
        # wp.name = wp_node.text
        # wp.lat = wp_node.lat
        # wp.long = wp_node.long
        # wp.elevation = wp_node.alt
        # wp.tot = wp_node.ETA
        # wp.waypoint_type = WaypointType.objects.filter(
        #     dcs_mapping=wp_node.waypoint_type
        # ).first()
        # return wp
    else:
        return None


def create_units(full_tree: AnyNode, unit_node_ids: list) -> list:
    """create selected units from a full_tree.

    Args:
        full_tree (AnyNode): The full AnyNode tree of mission info.
        unit_node_ids (list): The list of tree node IDs selected to add.

    Returns:
        list of units.
    """
    units = []
    for id in unit_node_ids:
        units.append(create_unit(full_tree, id))
    return units


def create_unit(full_tree: AnyNode, unit_node_id: str) -> Aircraft:
    unit_node = tree_search.find_by_attr(full_tree, unit_node_id, name='id')
    if unit_node is not None:
        aircraft = Aircraft.objects.create(tailcode=unit_node.onboard_num)
        aircraft.type = Airframe.objects.filter(dcs_mapping=unit_node.unit_type).first()
        aircraft.save()
        return aircraft
    else:
        return None


def build_full_flight(full_tree: AnyNode, flight_node_id: str) -> Flight:
    flight = build_flight(full_tree, flight_node_id)
    if flight is not None:
        flight_node = tree_search.find_by_attr(full_tree, flight_node_id, name='id')
        waypoints = []
        units = []
        for node in flight_node.descendants:
            if node.type == NodeType.WAYPOINT:
                waypoint = create_waypoint(full_tree, node.id)
                waypoint.copyToFlight(flight)
            if node.type == NodeType.UNIT:
                unit = create_unit(full_tree, node.id)
                unit.copyToFlight(flight)
        flight.save()
        return flight
    else:
        return None


def build_flight(full_tree: AnyNode, flight_node_id: str) -> Flight:
    """Build a basic Flight object from full_tree and the nodeID of a flight
    Args:
        full_tree (AnyNode): The full AnyNode tree of mission info.
        flight_node_id (str): The node_ID of the flight node.
    Returns:
        Flight: Flight
    """
    flight_node = tree_search.find_by_attr(full_tree, flight_node_id, name='id')
    if flight_node is not None:
        flight = Flight.objects.create(
            callsign=flight_node.text,
            radio_frequency=flight_node.frequency,
        )
        return flight
    else:
        return None


def copy_flight_to_package(flight: Flight, package: Package) -> int:
    flight.package = package
    flight.save()
    return flight.package.id


def set_package(items: list, package: Package):
    for item in items:
        item.copyToPackage(package)


def add_to_package(
    full_tree: AnyNode, selected_items: list, package: Package
) -> Package:
    flight = None
    for item in selected_items:
        item_node = tree_search.find_by_attr(full_tree, item, name='id')
        item_type = item_node.type

        if item_type == NodeType.COALITION or item_type == NodeType.COUNTRY:
            for child in item_node.descendants:
                if child.type == NodeType.FLIGHT:
                    flight = build_full_flight(full_tree, child.id)
                    copy_flight_to_package(flight, package)

        elif item_type == NodeType.FLIGHT:
            flight_node = item_node
            flight = build_full_flight(full_tree, item_node.id)

        elif item_type == NodeType.UNITS:
            # infer and build Parent Flight
            flight_node = item_node.parent
            flight = build_flight(full_tree, flight_node.id)
            for child in item_node.children:
                unit = create_unit(full_tree, item_node.id)
                unit.copyToFlight(flight)

        elif item_type == NodeType.WAYPOINTS:
            flight_node = item_node.parent
            flight = build_flight(full_tree, flight_node.id)
            for child in item_node.children:
                waypoint = create_waypoint(full_tree, item_node.id)
                waypoint.copyToFlight(flight)

        elif item_type == NodeType.WAYPOINT:
            flight_node = item_node.parent.parent
            flight = build_flight(full_tree, flight_node.id)
            waypoint = create_waypoint(full_tree, item_node.id)
            waypoint.copyToFlight(flight)

        elif item_node.type == NodeType.UNIT:
            flight_node = item_node.parent.parent
            flight = build_flight(full_tree, flight_node.id)
            unit = create_unit(full_tree, item_node.id)
            unit.copyToFlight(flight)

        copy_flight_to_package(flight, package)

    return package
