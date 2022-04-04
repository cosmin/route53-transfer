"""
Unit tests for models (R53Record) hashing and comparison
"""

from route53_transfer.models import *


def test_equality_of_simple_a_records():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    assert r1 == r2
    assert r1.__hash__() == r2.__hash__()


def test_equality_of_record_copy():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = r1.copy()

    assert r1 == r2
    assert r1.__hash__() == r2.__hash__()


def test_inequality_of_record_copy():
    """
    `model.copy()` is a shallow copy! Be careful how you treat models that have
    been copied! Modifying object members like `ResourceRecords` is likely to
    cause surprising results.
    """
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = r1.copy()

    # WARNING: Modifying the copied model like the following is going to modify
    # the source object as well, thus producing equal hashes, so don't do it!
    # r2.ResourceRecords[0].Value = "127.0.0.3"

    r2.ResourceRecords = [
        ResourceRecord(Value="127.0.0.3")
    ]

    assert r1 != r2
    assert r1.__hash__() != r2.__hash__()


def test_inequality_of_simple_a_records():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=299,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    assert r1 != r2


def test_inequality_of_resource_record_value():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.2")
                   ])

    assert r1.__hash__() != r2.__hash__()
    assert r1 != r2, \
        "Differences in ResourceRecords values should be detected"


def test_inequality_of_type_value():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=300,
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = r1.copy()
    r2.Type = "AAAA"

    assert r1 != r2, \
        "Differences in record Type should be detected"


def test_hashing_of_geolocation_attribute():
    r1 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=60,
                   GeoLocation=GeoLocationModel(CountryCode="US"),
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    r2 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=60,
                   GeoLocation=GeoLocationModel(CountryCode="US"),
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    assert r1 == r2, \
        "Hashing of GeoLocation attribute is based on its attributes"
    assert r1.__hash__() == r2.__hash__()

    r3 = R53Record(Name="test1.example.com.",
                   Type="A",
                   TTL=60,
                   GeoLocation=GeoLocationModel(CountryCode="*"),
                   ResourceRecords=[
                       ResourceRecord(Value="127.0.0.1")
                   ])

    assert r1 != r3
    assert r1.__hash__() != r3.__hash__()


def test_hashing_of_region_attribute():
    r1 = R53Record(Name="rp-latency.example.com.",
                   Type="A",
                   TTL=60,
                   Region=RegionEnum.ap_southeast_2)

    r2 = R53Record(Name="rp-latency.example.com.",
                   Type="A",
                   TTL=60,
                   Region=RegionEnum.ap_southeast_2)

    assert r1 == r2, "Region attribute has consistent hashing"
    assert r1.__hash__() == r2.__hash__()

    r3 = R53Record(Name="rp-latency.example.com.",
                   Type="A",
                   TTL=60,
                   Region=RegionEnum.eu_west_1)

    assert r1 != r3
    assert r1.__hash__() != r3.__hash__()
