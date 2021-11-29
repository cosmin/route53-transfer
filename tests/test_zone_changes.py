from boto.route53.record import Record

from helpers import assert_changes_eq, assert_change_eq, diff_zone


TEST_ZONE_ID = 1
TEST_ZONE_NAME = "test.dev"
TEST_ZONE = {"id": TEST_ZONE_ID, "name": TEST_ZONE_NAME}


def test_empty_source_and_destination_zones():
    rrset_before = []
    rrset_after = []
    changes = diff_zone(rrset_before, rrset_after)
    assert len(changes) == 0


def test_soa_and_ns_records_are_ignored():
    """
    SOA and NS records are ignored when computing zone changes
    """

    soa_rr = Record()
    soa_rr.type = "SOA"
    soa_rr.name = TEST_ZONE_NAME

    rrset_before = []
    rrset_after = [soa_rr]

    changes = diff_zone(rrset_before, rrset_after)
    assert len(changes) == 0

    ns_rr = Record()
    ns_rr.type = "NS"
    ns_rr.name = TEST_ZONE_NAME

    rrset_before = []
    rrset_after = [ns_rr]

    changes = diff_zone(rrset_before, rrset_after)
    assert len(changes) == 0

    rrset_after = [soa_rr, ns_rr]

    changes = diff_zone(rrset_before, rrset_after)
    assert len(changes) == 0


def test_add_one_simple_a_record():
    a_ptr = Record()
    a_ptr.type = "A"
    a_ptr.name = "server1"
    a_ptr.resource_records = ["1.2.3.4"]

    rrset_before = []
    rrset_after = [a_ptr]

    changes = diff_zone(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": a_ptr,
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


def test_add_a_record_to_existing_zone():
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

    changes = diff_zone(rrset_before, rrset_after)

    assert_changes_eq(changes, [
        {
            "operation": "CREATE",
            "zone": TEST_ZONE,
            "record": server2_ptr,
        }
    ])

