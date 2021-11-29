import pytest
from boto.route53.record import Record

from helpers import (
    assert_changes_eq,
    diff_zone,
    diff_zone_upsert)


TEST_ZONE_ID = 1
TEST_ZONE_NAME = "test.dev"
TEST_ZONE = {"id": TEST_ZONE_ID, "name": TEST_ZONE_NAME}

diff_functions = [
    diff_zone,
    diff_zone_upsert
]


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_empty_source_and_destination_zones(diff_fn):
    rrset_before = []
    rrset_after = []
    changes = diff_fn(rrset_before, rrset_after)
    assert len(changes) == 0


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_soa_and_ns_records_are_ignored(diff_fn):
    """
    SOA and NS records are ignored when computing zone changes
    """

    soa_rr = Record()
    soa_rr.type = "SOA"
    soa_rr.name = TEST_ZONE_NAME

    rrset_before = []
    rrset_after = [soa_rr]

    changes = diff_fn(rrset_before, rrset_after)
    assert len(changes) == 0

    ns_rr = Record()
    ns_rr.type = "NS"
    ns_rr.name = TEST_ZONE_NAME

    rrset_before = []
    rrset_after = [ns_rr]

    changes = diff_fn(rrset_before, rrset_after)
    assert len(changes) == 0

    rrset_after = [soa_rr, ns_rr]

    changes = diff_fn(rrset_before, rrset_after)
    assert len(changes) == 0


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_add_one_simple_a_record(diff_fn):
    a_ptr = Record()
    a_ptr.type = "A"
    a_ptr.name = "server1"
    a_ptr.resource_records = ["1.2.3.4"]

    rrset_before = []
    rrset_after = [a_ptr]

    changes = diff_fn(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": a_ptr,
        }
    ])


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_add_a_record_to_existing_zone(diff_fn):
    server1_ptr = Record()
    server1_ptr.type = "A"
    server1_ptr.name = "server1"
    server1_ptr.resource_records = ["1.2.3.4"]

    rrset_before = [server1_ptr]

    server2_ptr = Record()
    server2_ptr.type = "CNAME"
    server2_ptr.name = "server2"
    server2_ptr.resource_records = ["server2.another.zone.dev"]

    rrset_after = [server1_ptr, server2_ptr]

    changes = diff_fn(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": server2_ptr,
        }
    ])


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_add_alias_to_existing_record(diff_fn):
    server1_ptr = Record()
    server1_ptr.type = "A"
    server1_ptr.name = "server1"
    server1_ptr.resource_records = ["10.2.3.4"]

    server2_ptr = Record()
    server2_ptr.type = "A"
    server2_ptr.name = "server2"
    server2_ptr.resource_records = ["10.2.3.5"]

    rrset_before = [server1_ptr, server2_ptr]

    server3_alias = Record()
    server3_alias.type = "A"
    server3_alias.name = "server3"
    server3_alias.alias_hosted_zone_id = str(TEST_ZONE_ID)
    server3_alias.alias_dns_name = "server2"
    server3_alias.alias_evaluate_target_health = False

    rrset_after = [server1_ptr, server2_ptr, server3_alias]

    changes = diff_fn(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": server3_alias,
        }
    ])


@pytest.mark.parametrize('diff_fn', diff_functions)
def test_add_alias_to_a_new_record(diff_fn):
    """
    Verify that when adding an alias to a record that is not previously
    existing in the zone (it's going to be added by the zone change), that
    we can correctly handle this and generate two distinct route53 updates.

    Failing to do that would results in route53 rejecting our update.
    Records that are alias targets must exist before the update request
    is submitted.
    """
    server1_ptr = Record()
    server1_ptr.type = "A"
    server1_ptr.name = "server1"
    server1_ptr.resource_records = ["10.2.3.4"]

    rrset_before = [server1_ptr]

    server2_ptr = Record()
    server2_ptr.type = "A"
    server2_ptr.name = "server2"
    server2_ptr.resource_records = ["10.2.3.5"]

    server3_alias = Record()
    server3_alias.type = "A"
    server3_alias.name = "server3"
    server3_alias.alias_hosted_zone_id = str(TEST_ZONE_ID)
    server3_alias.alias_dns_name = "server2"
    server3_alias.alias_evaluate_target_health = False

    rrset_after = [server1_ptr, server2_ptr, server3_alias]

    changes = diff_fn(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": server2_ptr,
        },
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": server3_alias,
        }
    ])


def test_replace_simple_a_record():
    server1_ptr = Record()
    server1_ptr.type = "A"
    server1_ptr.name = "server1"
    server1_ptr.resource_records = ["1.2.3.4"]

    modified_server1_ptr = Record()
    modified_server1_ptr.type = "A"
    modified_server1_ptr.name = "server1"
    modified_server1_ptr.resource_records = ["1.2.3.5"]

    rrset_before = [server1_ptr]
    rrset_after = [modified_server1_ptr]

    changes = diff_zone(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "DELETE",
            "zone": TEST_ZONE,
            "record": server1_ptr,
        },

        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": modified_server1_ptr,
        }
    ])


def test_replace_simple_a_record_with_upsert():
    server1_ptr = Record()
    server1_ptr.type = "A"
    server1_ptr.name = "server1"
    server1_ptr.resource_records = ["1.2.3.4"]

    modified_server1_ptr = Record()
    modified_server1_ptr.type = "A"
    modified_server1_ptr.name = "server1"
    modified_server1_ptr.resource_records = ["1.2.3.5"]

    rrset_before = [server1_ptr]
    rrset_after = [modified_server1_ptr]

    changes = diff_zone(rrset_before, rrset_after, use_upsert=True)

    assert_changes_eq(changes, [{
        "operation": "UPSERT",
        "zone": TEST_ZONE,
        "record": modified_server1_ptr,
    }])


