from dcs.helicopters import helicopter_map
from dcs.planes import plane_map


def get_flyable_aircraft():
    flyable_planes = [(id, plane) for id, plane in plane_map.items() if plane.flyable]
    flyable_helos = [(id, helo) for id, helo in helicopter_map.items() if helo.flyable]
    print('id,dcsname')
    for idx, plane in enumerate(flyable_planes, start=1):
        print(f"{idx},{plane[0]}")
    for idx, helicopter in enumerate(flyable_helos, start=idx + 1):
        print(f'{idx},{helicopter[0]}')


if __name__ == "__main__":
    get_flyable_aircraft()
    print("-" * 80)
    print('Built airframe type choices from pydcs')
    print("-" * 80)
    print("Cut and paste the output above the --- to a file.")
    print("and import to the DCS Airframes table using the admin site.")
    print("Import as type csv.")
