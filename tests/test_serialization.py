"""
Unit tests for DNS records serialization/deserialization
"""

import pytest

from helpers import (
    load_fixture,
    fixtures_for,
)

from route53_transfer.models import ContinentCodeEnum


@pytest.mark.parametrize('fixture', fixtures_for('test1'))
def test_deserialize_simple_record(fixture):
    """
    Test deserialization of a simple A record from YAML/JSON files
    """
    records = load_fixture(fixture_filename=fixture)
    assert len(records) == 1

    simple_a_record = records[0]

    name = simple_a_record.Name
    assert name == "test1.example.com."
    assert name.endswith(".")

    assert simple_a_record.Type == "A"

    assert simple_a_record.TTL == 65

    rr = simple_a_record.ResourceRecords
    assert len(rr) == 1

    rr0_value = rr[0].Value
    assert rr0_value == "127.0.0.99"


def test_deserialize_geolocation_routing_policy():
    records = load_fixture(fixture_filename="geolocation.yaml")
    assert len(records) == 3

    geo_rp_default, geo_rp_se, geo_rp_africa = records

    assert geo_rp_default.Name == "geo1.example.com."
    assert geo_rp_default.TTL is None
    assert geo_rp_default.Type == "A"
    assert len(geo_rp_default.ResourceRecords) == 1
    assert geo_rp_default.GeoLocation.CountryCode == "*"

    assert geo_rp_se.Name == "geo2.example.com."
    assert geo_rp_se.TTL is None
    assert geo_rp_se.Type == "A"
    assert geo_rp_se.ResourceRecords[0].Value == "127.0.0.3"
    assert geo_rp_se.GeoLocation.CountryCode == "SE"

    assert geo_rp_africa.Name == "geo3.example.com."
    assert geo_rp_africa.TTL is None
    assert geo_rp_africa.Type == "A"
    assert geo_rp_africa.ResourceRecords[0].Value == "127.0.0.4"
    assert geo_rp_africa.GeoLocation.CountryCode is None
    assert geo_rp_africa.GeoLocation.ContinentCode == ContinentCodeEnum.Africa