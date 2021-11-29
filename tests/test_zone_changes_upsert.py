from boto.route53.record import Record

from route53_transfer import app
from route53_transfer.app import ComparableRecord

TEST_ZONE_ID = 1
TEST_ZONE_NAME = "test.dev"
TEST_ZONE = {"id": TEST_ZONE_ID, "name": TEST_ZONE_NAME}


def diff_zone(rrset_before, rrset_after):
    return app.compute_changes_upsert(TEST_ZONE, rrset_before, rrset_after)


def to_comparable(r):
    return r if type(r) == ComparableRecord else ComparableRecord(r)


def assert_change_eq(c1: dict, c2: dict):
    assert c1["operation"] == c2["operation"]
    assert c1["zone"]["id"] == c2["zone"]["id"]
    assert c1["zone"]["name"] == c2["zone"]["name"]

    c1_record = to_comparable(c1["record"])
    c2_record = to_comparable(c2["record"])

    assert_record_eq(c1_record, c2_record)


def assert_record_eq(r1, r2):
    rd1 = r1.to_change_dict()
    rd2 = r2.to_change_dict()

    for attr in ("type", "name", "ttl", "alias_hosted_zone_id",
                 "alias_dns_name", "identifier", "weight", "region",
                 "alias_evaluate_target_health", "health_check", "failover"):
        assert rd1[attr] == rd2[attr]

    assert_resource_records_eq(r1, r2)


def assert_resource_records_eq(r1, r2):
    rr1 = r1.resource_records
    rr2 = r2.resource_records

    assert len(rr1) == len(rr2)
    for i in range(len(rr1)):
        assert rr1[i] == rr2[i]


def assert_changes_eq(cl1: list, cl2: list):
    assert len(cl1) == len(cl2)
    for i in range(len(cl1)):
        assert_change_eq(cl1[i], cl2[i])


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

    assert_changes_eq(changes, [{
      "operation": "CREATE",
      "zone": TEST_ZONE,
      "record": a_ptr,
    }])


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

    assert_changes_eq(changes, [{
        "operation": "UPSERT",
        "zone": TEST_ZONE,
        "record": ComparableRecord(modified_server1_ptr),
    }])


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

