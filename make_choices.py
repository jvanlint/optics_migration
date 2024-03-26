from .src.pydcs.dcs.helicopters import helicopters
from .src.pydcs.dcs.planes import planes


def convert_dicts():
    plane_list = list(key for key, value in planes.plane_map.items())
    helicopter_list = list(key for key, value in helicopters.helicopter_map.items())
    print("-" * 80)
    for plane in sorted(plane_list):
        db_value = (
            plane.replace(" ", "_").replace("/", "").replace("-", "_").replace(".", "_")
        )
        print(f"{db_value} = '{plane}'")
    for helicopter in sorted(helicopter_list):
        db_value = (
            helicopter.replace(" ", "_")
            .replace("/", "")
            .replace("-", "_")
            .replace(".", "_")
        )
        print(f"{db_value} = '{helicopter}'")
    print("-" * 80)
    print("Cut and paste the output to models/Airframe.py")


if __name__ == "__main__":
    print('building airframe and waypoint type choices from pydcs')
    convert_dicts()
