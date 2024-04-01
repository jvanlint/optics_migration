from dcs.helicopters import helicopter_map
from dcs.planes import plane_map


def get_flyable_aircraft():
    flyable_planes = [(id, plane) for id, plane in plane_map.items() if plane.flyable]
    flyable_helos = [(id, helo) for id, helo in helicopter_map.items() if helo.flyable]

    for plane in flyable_planes:
        print(plane[1].id)
    for helicopter in flyable_helos:
        print(helicopter[1].id)


if __name__ == "__main__":
    get_flyable_aircraft()
    print("-" * 80)
    print('Built airframe type choices from pydcs')
    print("-" * 80)
    print("Cut and paste the output above the --- to a file.")
    print("and import to the DCS Airframes table using the admin site.")
    print("Import as type csv.")
