"""
Helper and custom assert methods to test dns zone updates
"""

from route53_transfer import app
from route53_transfer.serialization import read_records

from pathlib import Path


TEST_ZONE_ID = 1
TEST_ZONE_NAME = "test.dev"
TEST_ZONE = {"id": TEST_ZONE_ID, "name": TEST_ZONE_NAME}


def diff_zone(rrset_before, rrset_after, use_upsert=False):
    return app.compute_changes(TEST_ZONE, rrset_before, rrset_after,
                               use_upsert=use_upsert)


def diff_zone_upsert(rrset_before, rrset_after):
    return diff_zone(rrset_before, rrset_after, use_upsert=True)


def assert_change_eq(c1: dict, c2: dict):
    assert c1["operation"] == c2["operation"], \
        f"Expected operation type to be {c2['operation']} but was {c1['operation']}"

    assert c1["zone"]["id"] == c2["zone"]["id"], \
        f"Expected zone id to be {c2['zone']['id']} but was {c1['zone']['id']}"

    assert c1["zone"]["name"] == c2["zone"]["name"], \
        f"Expected zone name to be {c2['zone']['name']} but was {c1['zone']['name']}"

    assert c1["record"] == c2["record"]
    assert c1["record"].__hash__() == c2["record"].__hash__()


def assert_resource_records_eq(r1, r2):
    rr1 = r1.ResourceRecords
    rr2 = r2.ResourceRecords

    if rr1 is None and rr2 is None:
        return

    assert len(rr1) == len(rr2), \
        f"Expected resource_records length to be the same, but was {len(rr1)} instead of {len(rr2)}"

    for i in range(len(rr1)):
        assert rr1[i] == rr2[i], \
            "Expected resource_records element {i} to be {rr2[i]} but was {rr1[i]}"


def assert_changes_eq(cl1: list, cl2: list):
    assert len(cl1) == len(cl2), \
        f"Expected changes list length to be the same, but was {len(cl1)} instead of {len(cl2)}"

    for i in range(len(cl1)):
        assert_change_eq(cl1[i], cl2[i])


def load_fixture(fixture_filename):
    """
    Load a fixture file with test records from disk

    :param fixture_filename: The filename of the fixture to load, relative to
        the fixtures directory. The format is automatically detected.
    :return: A list of route53 records, each a simple dictionary
    """
    fixture_path = Path(__file__).parent / "fixtures" / fixture_filename
    fixture_format = "json" if fixture_filename.endswith(".json") else ".yaml"

    with open(fixture_path, "rb") as fixture_file:
        return read_records(fixture_file, format=fixture_format)


def fixtures_for(test_name):
    return test_name + ".yaml", test_name + ".json"
