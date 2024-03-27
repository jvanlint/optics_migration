import pytest
from anytree import AnyNode
from model_bakery import baker

from optics.miz_import import tree_parser
from optics.opticsapp.models import Aircraft, Airframe, DCSAirframe


@pytest.fixture
def airframes2():
    af = baker.prepare('DCSAirframe')
    test = baker.prepare('Airframe')
    test.dcsname = af

    airframe_A10C = baker.make("Airframe", dcsname=baker.prepare('DCSAirframe'))

    airframe_A10C2 = baker.make("Airframe", dcsname="A-10C_2")
    airframe_F18 = baker.make("Airframe", dcsname="F/A-18C")
    airframe_AV8B = baker.make("Airframe", dcsname="AV8BNA")
    airframe_F15C = baker.make("Airframe", dcsname="F-15C")
    airframe_unmapped = baker.make("Airframe", dcsname="Not-Mapped")
    return airframe_A10C, airframe_F18


@pytest.fixture
def dcsnames():
    A10 = baker.prepare('DCSAirframe', dcsname="A-10C")
    F18 = baker.prepare('DCSAirframe', dcsname="F/A-18C")
    return A10, F18


@pytest.fixture
def airframes(dcsnames):
    airframe_A10C = Airframe()
    airframe_A10C.name = "A10"
    airframe_A10C.dcsname = dcsnames.A10
    # airframe_A10C.name = "A10"
    # airframe_A10C.dcsname = dcsnames.A10
    airframe_F18 = Airframe(dcsname=dcsnames.F18)
    return airframe_A10C, airframe_F18


@pytest.fixture
def tree():
    root = AnyNode(name="Root")
    unit1 = AnyNode(
        parent=root, name="unit1", id="123", unit_type="A-10C", onboard_num="ABC"
    )
    unit2 = AnyNode(
        parent=root, name="unit2", id="456", unit_type="F/A-18C", onboard_num="DEF"
    )
    return root


def test_create_unit_returns_aircraft_object(tree):
    aircraft = tree_parser.create_unit(tree, "123")
    assert isinstance(aircraft, Aircraft)
    assert aircraft.tailcode == "ABC"
    # assert aircraft.type == airframes[0]


def test_create_unit_returns_none_for_invalid_node(tree, airframes):
    aircraft = tree_parser.create_unit(tree, "invalid")
    assert aircraft is None


def test_create_unit_sets_correct_airframe(tree, airframes):
    aircraft = tree_parser.create_unit(tree, "456")
    assert aircraft.type == airframes[1]
