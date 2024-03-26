from dcs.helicopters import helicopter_map
from dcs.planes import plane_map


def convert_dicts():
    plane_list = list(key for key, value in plane_map.items())
    helicopter_list = list(key for key, value in helicopter_map.items())
    # print("-" * 80)
    # print("    class DCSAirframes(models.TextChoices):")
    # print("        Not_Mapped = 'Not Mapped'")
    for plane in sorted(plane_list):
        db_value = (
            plane.replace(" ", "_").replace("/", "").replace("-", "_").replace(".", "_")
        )
        # print(f"        {db_value} = '{plane}'")
        print(f"{db_value},{plane}")
    for helicopter in sorted(helicopter_list):
        db_value = (
            helicopter.replace(" ", "_")
            .replace("/", "")
            .replace("-", "_")
            .replace(".", "_")
        )
        # print(f"        {db_value} = '{helicopter}'")
        print(f"{db_value},{helicopter}")
    # print("-" * 80)
    # print("Cut and paste the output to models/Airframe.py")


if __name__ == "__main__":
    print('building airframe and waypoint type choices from pydcs')
    convert_dicts()
