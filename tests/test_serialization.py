"""
Unit tests for DNS records serialization/deserialization
"""

import pytest

from helpers import (
    load_fixture,
    fixtures_for,
)

from route53_transfer.models import R53Record


@pytest.mark.parametrize('fixture', fixtures_for('test1'))
def test_deserialize_simple_record(fixture):
    """
    Test deserialization of a simple A record from YAML/JSON files
    """
    records = load_fixture(fixture_filename=fixture)
    assert len(records) == 1

    simple_a_record = records[0]

    name = simple_a_record["Name"]
    assert name == "test1.example.com."
    assert name.endswith(".")

    type_ = simple_a_record["Type"]
    assert type_ == "A"

    ttl = simple_a_record["TTL"]
    assert ttl == 65

    rr = simple_a_record["ResourceRecords"]
    assert len(rr) == 1
    rr0_value = rr[0]["Value"]
    assert rr0_value == "127.0.0.99"


@pytest.mark.parametrize('fixture', fixtures_for('test1'))
def test_deserialize_and_model_loading(fixture):
    """
    Test deserialization of a simple A record from YAML/JSON files,
    and then loading into a R53Record model instance.
    """
    records = load_fixture(fixture_filename=fixture)
    assert len(records) == 1

    simple_a_record = records[0]

    r = R53Record(**simple_a_record)

    assert r.Name == "test1.example.com."
    assert r.TTL == 65
    assert r.Type == "A"
    assert len(r.ResourceRecords) == 1
    assert r.ResourceRecords[0].Value == "127.0.0.99"
