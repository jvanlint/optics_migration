from dcs.helicopters import helicopter_map
from dcs.planes import plane_map


def convert_dicts():
    plane_list = list(key for key, value in plane_map.items())
    helicopter_list = list(key for key, value in helicopter_map.items())

    print("dcsname")
    for idx1, plane in enumerate(sorted(plane_list)):
        db_value = (
            plane.replace(" ", "_").replace("/", "").replace("-", "_").replace(".", "_")
        )
        # print(f"        {db_value} = '{plane}'")
        print(f"{db_value}")
    for idx2, helicopter in enumerate(sorted(helicopter_list)):
        db_value = (
            helicopter.replace(" ", "_")
            .replace("/", "")
            .replace("-", "_")
            .replace(".", "_")
        )
        print(f"{db_value}")


if __name__ == "__main__":
    convert_dicts()
    print("-" * 80)
    print('Built airframe type choices from pydcs')
    print("-" * 80)
    print("Cut and paste the output above the --- to a file.")
    print("and import to the DCS Airframes table using the admin site.")
    print("Import as type csv.")
