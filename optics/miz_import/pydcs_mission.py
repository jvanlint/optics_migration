import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from anytree import AnyNode
from anytree import search as tree_search
from pyproj import CRS, Transformer

from .slpp import slpp as lua


@dataclass(frozen=True)
class Projection:
    central_meridian: int
    false_easting: float
    false_northing: float
    scale_factor: float

    def to_crs(self) -> CRS:
        return CRS.from_proj4(
            " ".join(
                [
                    "+proj=tmerc",
                    "+lat_0=0",
                    f"+lon_0={self.central_meridian}",
                    f"+k_0={self.scale_factor}",
                    f"+x_0={self.false_easting}",
                    f"+y_0={self.false_northing}",
                    "+towgs84=0,0,0,0,0,0,0",
                    "+units=m",
                    "+vunits=m",
                    "+ellps=WGS84",
                    "+no_defs",
                    "+axis=neu",
                ]
            )
        )


class TerrainProjection(Enum):
    # central_meridian, false_easting, false_northing, scale_factor
    Caucasus = Projection(33, -99516.9999999732, -4998114.999999984, 0.9996)
    PersianGulf = Projection(57, 75755.99999999645, -2894933.0000000377, 0.9996)
    Normandy = Projection(-3, -1995526.00000000204, -5484812.999999951, 0.9996)
    Nevada = Projection(-117, -193996.80999964548, -4410028.063999966, 0.9996)
    MarianaIslands = Projection(147, 238417.99999989968, -1491840.000000048, 0.9996)
    Falklands = Projection(-57, 147639.99999997593, 5815417.000000032, 0.9996)
    TheChannel = Projection(3, 99376.00000000288, -5636889.00000001, 0.9996)
    SinaiMap = Projection(33, 169221.9999999585, -3325312.9999999693, 0.9996)
    Syria = Projection(39, 282801.00000003993, -3879865.9999999935, 0.9996)


class DCSMission:

    TERRAIN_MAP = {
        'Caucasus': TerrainProjection.Caucasus,
        'Nevada': TerrainProjection.Nevada,
        'PersianGulf': TerrainProjection.PersianGulf,
        'Normandy': TerrainProjection.Normandy,
        'TheChannel': TerrainProjection.TheChannel,
        'SinaiMap': TerrainProjection.SinaiMap,
        'Syria': TerrainProjection.Syria,
        'MarianaIslands': TerrainProjection.MarianaIslands,
        'Falklands': TerrainProjection.Falklands,
    }

    def __init__(self) -> None:
        self.terrain = TerrainProjection.Caucasus
        self.filename: Optional[str] = None
        self.description_text = ""
        self.description_bluetask = ""
        self.description_redtask = ""
        self.sortie = ""
        self.start_time = datetime.fromtimestamp(
            1306886400 + 43200, timezone.utc
        )  # 01-06-2011 12:00:00 UTC
        # self.terrain = terrain
        self.bullseye_blue = Point()
        self.bullseye_red = Point()
        self.weather = None
        self.aircraft_groups = []

    def load_file(self, filename: str):
        self.filename = filename
        mission_dict, text_dict = self._extract_mission_dictionaries(filename)
        self._setup_terrain(mission_dict)
        self._import_base_values(mission_dict, text_dict)
        self._load_bullseye(mission_dict)
        self._import_weather(mission_dict)
        self._load_planegroups(mission_dict)
        self._load_helogroups(mission_dict)

    def _extract_mission_dictionaries(
        self, filename: str
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        with zipfile.ZipFile(filename, 'r') as miz:
            # reserved_files: List[str] = []
            mission_dict = self._loadDictFromMizFile(
                'mission', miz
            )  # , reserved_files)
            text_dict = self._loadDictFromMizFile(
                'l10n/DEFAULT/dictionary', miz
            )  # , reserved_files)
        return mission_dict, text_dict

    def _setup_terrain(self, mission_dict: dict) -> None:
        self.terrain = self.TERRAIN_MAP.get(mission_dict["theatre"])
        if self.terrain is None:
            raise RuntimeError(f"Unknown theatre: '{mission_dict["theatre"]}'")
        else:
            self.terrain = self.terrain.value

    def _import_base_values(
        self, mission_dict: Dict[str, Any], dictionary_dict: Dict[str, Any]
    ) -> None:
        self.description_text = dictionary_dict[mission_dict["descriptionText"]]
        self.description_bluetask = dictionary_dict[mission_dict["descriptionBlueTask"]]
        self.description_redtask = dictionary_dict[mission_dict["descriptionRedTask"]]
        self.sortie = dictionary_dict[mission_dict["sortie"]]
        self._set_mission_time(mission_dict)
        self.usedModules = mission_dict.get("usedModules", None)

    def _load_bullseye(self, mission_dict: Dict[str, Any]):
        self.bullseye_blue.name = "Blue Bullseye"
        self.bullseye_blue.x = mission_dict['coalition']['blue']['bullseye']["x"]
        self.bullseye_blue.y = mission_dict['coalition']['blue']['bullseye']["y"]
        self.bullseye_red.name = "Red Bullseye"
        self.bullseye_red.x = mission_dict['coalition']['red']['bullseye']["x"]
        self.bullseye_red.y = mission_dict['coalition']['red']['bullseye']["y"]

    def _load_planegroups(self, mission_dict: Dict[str, Any]) -> None:
        for coalition_name, coalition in mission_dict['coalition'].items():
            for country in coalition['country'].values():
                if 'plane' in country and 'group' in country['plane']:
                    for plane_group in country['plane']['group'].values():
                        pg = AircraftGroup(plane_group)
                        self.aircraft_groups.append(pg)

    def _load_helogroups(self, mission_dict: Dict[str, Any]) -> None:
        for coalition_name, coalition in mission_dict['coalition'].items():
            for country in coalition['country'].values():
                if 'helicopter' in country and 'group' in country['helicopter']:
                    for plane_group in country['helicopter']['group'].values():
                        pg = AircraftGroup(plane_group)
                        self.aircraft_groups.append(pg)

    def _loadDictFromMizFile(
        self, fname: str, mizfile: zipfile.ZipFile
    ) -> Dict[str, Any]:
        # reserved_files.append(fname)
        with mizfile.open(fname) as mfile:
            data = mfile.read().decode()
            # clean the file description from the start and end of the lua data
            start_index = data.find('{')
            end_index = data.rfind('}')
            if start_index != -1 and end_index != -1:
                data = data[start_index : end_index + 1]
            data_table = lua.decode(data)
            if not isinstance(data_table, dict):
                raise ValueError(
                    f"Expected dictionary from {fname}, got {type(data_table)}"
                )
            data_dict = {key: value for key, value in data_table.items()}
            return data_dict

    def _set_mission_time(self, mission_dict: Dict[str, Any]) -> None:
        imp_date = mission_dict.get("date", {"Year": 2011, "Month": 6, "Day": 1})
        hour = int(mission_dict["start_time"] / 3600)
        minutes = int(mission_dict["start_time"] / 60) - hour * 60
        self.start_time = datetime(
            year=imp_date["Year"],
            month=imp_date["Month"],
            day=imp_date["Day"],
            hour=hour,
            minute=minutes,
            second=mission_dict["start_time"] % 60,
        )

    def _import_weather(self, mission_dict: Dict[str, Any]) -> None:
        self.weather = Weather(mission_dict["weather"])

    def to_tree(self) -> AnyNode:

        opened = {"opened": True}  # open this node in jtree
        # disabled = {"disabled": True}  # disable this node in jtree
        # selected = {"selected": True}  # select this node in jtree

        rootNode = AnyNode(
            id=NodeType.ROOT,
            text=self.sortie,
            state=opened,
            start_time=self.start_time.isoformat(),
            type=NodeType.ROOT,
        )

        for aircraft_group in self.aircraft_groups:

            plane_group_node = AnyNode(
                id=NodeType.FLIGHT + str(aircraft_group.group_ID),
                parent=rootNode,
                text=aircraft_group.name,
                frequency=aircraft_group.frequency,
                task=aircraft_group.task,
                type=NodeType.FLIGHT.value,
            )

            points_parent = AnyNode(
                id=NodeType.WAYPOINTS + str(aircraft_group.name),
                parent=plane_group_node,
                text=f"{aircraft_group.name} Waypoints",
                type=NodeType.WAYPOINTS,
            )

            for point_index, waypoint in enumerate(aircraft_group.waypoints):
                text = f"{waypoint.type} - Alt {waypoint.alt}"
                point_node = AnyNode(
                    id=NodeType.WAYPOINT
                    + str(aircraft_group.group_ID)
                    + str(point_index).zfill(2),
                    parent=points_parent,
                    lat=waypoint.latlng(self.terrain).format_lattitude(),
                    lon=waypoint.latlng(self.terrain).format_longitude(),
                    latlng=waypoint.latlng(self.terrain).format_dms(),
                    waypoint_type=waypoint.type,
                    alt=waypoint.alt,
                    ETA=(self.start_time + timedelta(seconds=waypoint.ETA))
                    .time()
                    .isoformat(),
                    type=NodeType.WAYPOINT,
                    action=waypoint.action,
                    text=text,
                )

            units_list = AnyNode(
                id=NodeType.UNITS + str(aircraft_group.group_ID),
                parent=plane_group_node,
                text=f"{aircraft_group.name} Aircraft",
                type=NodeType.UNITS,
            )

            for aircraft in aircraft_group.air_units:
                name = f" {aircraft.type} - {aircraft.name} - {aircraft.callsign}"
                unit_node = AnyNode(
                    id=NodeType.UNIT + str(aircraft.unit_id),
                    parent=units_list,
                    unit_type=aircraft.type,
                    text=name,
                    name=aircraft.name,
                    onboard_num=aircraft.onboard_number,
                    player=aircraft.player,
                    type=NodeType.UNIT,
                )

        return rootNode


@dataclass
class Point:
    x: float = 0
    y: float = 0
    name: str = ""
   
    
    def latlng(self, projection: Projection):
        lat, lon = Transformer.from_crs(projection.to_crs(), CRS("WGS84")).transform(
            self.x, self.y
        )
        return LatLng(lat, lon)
    


@dataclass
class Waypoint(Point):
    alt: int = 0
    type: str = ""
    action: str = ""
    ETA: int = 0
    

@dataclass(frozen=True)
class LatLng:
    lat: float
    lng: float

    def as_list(self) -> List[float]:
        return [self.lat, self.lng]

    @staticmethod
    def _components(dimension: float) -> Tuple[int, int, float]:
        degrees = int(dimension)
        minutes = int(dimension * 60 % 60)
        seconds = dimension * 3600 % 60
        return degrees, minutes, seconds

    def _format_component(
        self, dimension: float, hemispheres: Tuple[str, str], seconds_precision: int
    ) -> str:
        hemisphere = hemispheres[0] if dimension >= 0 else hemispheres[1]
        degrees, minutes, seconds = self._components(dimension)
        return f'{degrees}°{minutes:02}\'{seconds:02.{seconds_precision}f}"{hemisphere}'

    def format_dms(self, include_decimal_seconds: bool = False) -> str:
        # print(ll.format_dms()) == 45°07'46"N 34°15'56"E
        # print(ll.format_dms(True)) == 45°07'46.19"N 34°15'55.85"E
        precision = 2 if include_decimal_seconds else 0
        return " ".join(
            [
                self.format_lattitude(include_decimal_seconds),
                self.format_longitude(include_decimal_seconds),
            ]
        )

    def format_lattitude(self, include_decimal_seconds: bool = False) -> str:
        # print(ll.format_latitude()) == 45°07'46"N
        # print(ll.format_latitude(True)) == 45°07'46.19"N
        precision = 2 if include_decimal_seconds else 0
        return self._format_component(self.lat, ("N", "S"), precision)

    def format_longitude(self, include_decimal_seconds: bool = False) -> str:
        # print(ll.format_longitude()) == 34°15'56"E
        # print(ll.format_longitude(True)) == 34°15'55.85"E
        precision = 2 if include_decimal_seconds else 0
        return self._format_component(self.lng, ("E", "W"), precision)
    
@dataclass
class AirUnit:
    type: str
    callsign: str
    unit_id: int
    name: str
    player: bool
    onboard_number: str


class Weather:
    def __init__(self, weather_dict: Dict[str, Any]) -> None:
        self.name = weather_dict["name"]
        self.visibility = weather_dict["visibility"]["distance"]
        self.qnh = weather_dict["qnh"]
        self.temperature = weather_dict["season"]["temperature"]
        self.wind_at_ground = {
            "speed": weather_dict["wind"]["atGround"]["speed"],
            "direction": weather_dict["wind"]["atGround"]["dir"],
        }
        self.wind_at_2k = {
            "speed": weather_dict["wind"]["at2000"]["speed"],
            "direction": weather_dict["wind"]["at2000"]["dir"],
        }
        self.wind_at_8k = {
            "speed": weather_dict["wind"]["at8000"]["speed"],
            "direction": weather_dict["wind"]["at8000"]["dir"],
        }


class AircraftGroup:
    def __init__(self, data_dict: Dict[str, Any] = {}) -> None:
        self.waypoints = []
        self.air_units = []

        if data_dict:
            self.name = data_dict.get("name", "Unknown")
            self.group_ID = data_dict.get("groupId", None)
            self.frequency = data_dict.get("frequency", None)
            self.task = data_dict.get("task", "")
            self.waypoints = self.create_waypoint_objects(data_dict)
            self.air_units = self.create_unit_objects(data_dict)

    def create_waypoint_objects(self, group_dict: Dict[str, Any]) -> List[Waypoint]:
        self.waypoints = []
        if "route" in group_dict and "points" in group_dict["route"]:
            for point_data in group_dict["route"]["points"].values():
                new_point = Waypoint(
                    ETA=point_data.get("ETA", 0),
                    alt=point_data.get("alt", 0),
                    x=point_data.get("x", 0),
                    y=point_data.get("y", 0),
                    type=point_data.get("type", ""),
                    name=point_data.get("name", ""),
                    action=point_data.get("action", ""),
                )
                self.waypoints.append(new_point)
        return self.waypoints

    def create_unit_objects(self, group_dict: Dict[str, Any]) -> List[AirUnit]:
        self.air_units = []
        if "units" in group_dict:
            for unit_data in group_dict["units"].values():
                new_unit = AirUnit(
                    type=unit_data.get("type", ""),
                    callsign=unit_data["callsign"].get("name", ""),
                    unit_id=unit_data.get("unitId", 0),
                    name=unit_data.get("name", ""),
                    player=True if unit_data.get("skill") == "Player" else False,
                    onboard_number=unit_data.get("onboard_num", ""),
                )
                self.air_units.append(new_unit)
        return self.air_units


class NodeType(str, Enum):
    ROOT = "root"
    # COALITION = "coalition"
    # COUNTRY = "country"
    FLIGHT = "flight"
    WAYPOINTS = "waypoints"
    WAYPOINT = "waypoint"
    UNITS = "units"
    UNIT = "unit"
