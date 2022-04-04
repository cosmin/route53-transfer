"""
Unit tests for the route53 change batch computation
"""

from route53_transfer.app import changes_to_r53_updates
from route53_transfer.models import R53Record, ResourceRecord, AliasTargetModel

TEST_ZONE_ID = 1
TEST_ZONE_NAME = "test.dev"
TEST_ZONE = {"id": TEST_ZONE_ID, "name": TEST_ZONE_NAME}


def test_empty_changes_list():
    zone = TEST_ZONE
    r53_change_batches = changes_to_r53_updates(zone, [])
    assert len(r53_change_batches) == 0


def test_single_change():
    zone = TEST_ZONE

    ptr = R53Record(Type="A",
                    Name="server1.",
                    ResourceRecords=[
                        ResourceRecord(Value="1.2.3.4")
                    ])

    change_operations = [
        {"zone": zone,
         "operation": "CREATE",
         "record": ptr}
    ]

    r53_change_batches = changes_to_r53_updates(zone, change_operations)
    assert len(r53_change_batches) == 1


def test_alias_change_in_separate_updates():
    zone = TEST_ZONE

    srv1 = R53Record(Type="A",
                     Name="server1",
                     ResourceRecords=[
                         ResourceRecord(Value="1.2.3.4")
                     ])

    srv2_alias = R53Record(Type="A",
                           Name="server2",
                           AliasTarget=AliasTargetModel(
                               HostedZoneId=str(TEST_ZONE_ID),
                               DNSName="server1",
                               EvaluateTargetHealth=False
                           ))

    change_operations = [
        {"zone": zone,
         "operation": "CREATE",
         "record": srv2_alias},

        {"zone": zone,
         "operation": "CREATE",
         "record": srv1},
    ]

    r53_change_batches = changes_to_r53_updates(zone, change_operations)
    assert len(r53_change_batches) == 2, \
        "Two update batches expected since there is a record that is an alias"

    first_update = r53_change_batches[0]
    record: R53Record = first_update.changes[0]["record"]
    assert record.Name == "server1"
    assert record.is_alias() is False

    second_update = r53_change_batches[1]
    record = second_update.changes[0]["record"]
    assert record.Name == "server2"
    assert record.is_alias() and record.AliasTarget.DNSName == "server1"


def test_two_chained_aliases_resolved_in_three_updates():
    zone = TEST_ZONE

    srv1 = R53Record(Type="A",
                     Name="server1",
                     ResourceRecords=[
                         ResourceRecord(Value="1.2.3.4")
                     ])

    srv2_alias = R53Record(Type="A",
                           Name="server2",
                           AliasTarget=AliasTargetModel(
                               HostedZoneId=str(TEST_ZONE_ID),
                               DNSName="server1",
                               EvaluateTargetHealth=False
                           ))

    srv3_alias = R53Record(Type="A",
                           Name="server3",
                           AliasTarget=AliasTargetModel(
                               HostedZoneId=str(TEST_ZONE_ID),
                               DNSName="server2",
                               EvaluateTargetHealth=False
                           ))

    change_operations = [
        {"zone": zone,
         "operation": "CREATE",
         "record": srv2_alias},

        {"zone": zone,
         "operation": "CREATE",
         "record": srv3_alias},

        {"zone": zone,
         "operation": "CREATE",
         "record": srv1},
    ]

    r53_change_batches = changes_to_r53_updates(zone, change_operations)
    assert len(r53_change_batches) == 3, \
        "Three update batches expected since there are two record aliases in a chain"

    first_update = r53_change_batches[0]
    r: R53Record = first_update.changes[0]["record"]
    assert r.Name == "server1"
    assert r.is_alias() is False

    second_update = r53_change_batches[1]
    r = second_update.changes[0]["record"]
    assert r.Name == "server2"
    assert r.is_alias() and r.alias_target() == "server1"

    third_update = r53_change_batches[2]
    r = third_update.changes[0]["record"]
    assert r.Name == "server3"
    assert r.alias_target() == "server2"
