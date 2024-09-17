import logging
from enum import Enum

from anytree import AnyNode
from anytree import search as tree_search
from django.core.exceptions import ObjectDoesNotExist

from optics.opticsapp.models import (
    Aircraft,
    Airframe,
    DCSAirframe,
    Flight,
    Package,
    Waypoint,
    WaypointType,
)

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    ROOT = "root"
    COALITION = "coalition"
    COUNTRY = "country"
    FLIGHT = "flight"
    WAYPOINTS = "waypoints"
    WAYPOINT = "waypoint"
    UNITS = "units"
    UNIT = "unit"


def add_to_package(full_tree: AnyNode, selected_items: list, package: Package):
    '''Entrypoint for importing assets from a miz file.
    .miz file has been parsed and stored as in a tree strucutre in full_tree.
    selected_items contains the list of items that need to be added to the package.
    '''
    flight = Flight()
    for item in selected_items:
        item_node = tree_search.find_by_attr(full_tree, value=item, name='id')
        if not item_node:
            logger.warning(f"Item {item} not found in tree")
            continue
        item_type = item_node.type
        if item_type == NodeType.COALITION or item_type == NodeType.COUNTRY:
            # Build all descendants, all flights including waypoints
            for child in item_node.descendants:
                if child.type == NodeType.FLIGHT:
                    flight = build_full_flight(child)
                    copy_flight_to_package(flight, package)

        elif item_type == NodeType.FLIGHT:
            # Build full flight including waypoints
            flight_node = item_node
            flight = build_full_flight(item_node)

        elif item_type == NodeType.UNITS:
            # infer and build Parent Flight
            flight_node = item_node.parent
            flight = build_flight(flight_node)
            # add all the units to the flight
            for child in item_node.children:
                unit = create_aircraft(child)
                unit.copyToFlight(flight)

        elif item_type == NodeType.WAYPOINTS:
            flight_node = item_node.parent
            flight = build_flight(flight_node)
            for child in item_node.children:
                waypoint = create_waypoint(child)
                waypoint.copyToFlight(flight)

        elif item_type == NodeType.WAYPOINT:
            flight_node = item_node.parent
            flight = build_flight(flight_node)
            waypoint = create_waypoint(item_node)
            waypoint.copyToFlight(flight)

        elif item_node.type == NodeType.UNIT:
            flight_node = item_node.parent
            flight = build_flight(flight_node)
            unit = create_aircraft(item_node)
            unit.copyToFlight(flight)

        copy_flight_to_package(flight, package)

    return package


def create_waypoints(full_tree: AnyNode, waypoint_node_ids: list) -> list:
    waypoints = []
    for id in waypoint_node_ids:
        waypoints.append(create_waypoint(full_tree, id))
    return waypoints  # list of waypoint objects


def create_waypoint(wp_node) -> Waypoint:
    if wp_node is not None:
        # wp = Waypoint()
        wp = Waypoint.objects.create(
            number=int(wp_node.id[-2:]),
            name=wp_node.text,
            lat=wp_node.lat,
            long=wp_node.lon,
            elevation=wp_node.alt,
            tot=wp_node.ETA,
            waypoint_type=WaypointType.objects.filter(
                dcs_mapping=wp_node.waypoint_type
            ).first(),
        )
        return wp
    else:
        return Waypoint.objects.create()


def create_aircraft(node) -> Aircraft:
    try:
        airframe = Airframe.objects.get(dcsname__dcsname=node.unit_type)
    except ObjectDoesNotExist as e:
        msg = (
            f"Unable to link {node.unit_type} with any aircraft in the optics database."
        )
        logger.warning(msg)
        raise ObjectDoesNotExist(msg)
    return Aircraft.objects.create(tailcode=node.onboard_num, type=airframe)


def build_full_flight(flight_node) -> Flight:
    flight = build_flight(flight_node)
    if flight is not None:
        for node in flight_node.descendants:
            if node.type == NodeType.WAYPOINT:
                waypoint = create_waypoint(node)
                waypoint.copyToFlight(flight)
            if node.type == NodeType.UNIT:
                aircraft = create_aircraft(node)
                aircraft.copyToFlight(flight)
        flight.save()
        return flight
    else:
        return Flight()


def build_flight(flight_node) -> Flight:
    return Flight.objects.create(
        callsign=f"{flight_node.id} - {flight_node.task}",
        radio_frequency=flight_node.frequency,
    )


def copy_flight_to_package(flight: Flight, package: Package) -> int:
    flight.package = package
    flight.save()
    return flight.package.id


def set_package(items: list, package: Package):
    for item in items:
        item.copyToPackage(package)
