# encoding: utf-8

from pydantic import BaseModel, Field
from typing import List, Optional


class AliasTargetModel(BaseModel):

    DNSName: str = Field(
        None,
        description="DNS name of the target host",
        example="test1.example.com.")
    EvaluateTargetHealth: bool = Field(
        None,
        description="Whether or not to evaluate the health of the target",
        example=False)
    HostedZoneId: str = Field(
        None,
        description="Hosted zone ID of the target host",
        example="Z0992A3F3Q3HY06FU")


class ResourceRecord(BaseModel):

    Value: str = Field(
        None,
        description="Value of the resource record",
        example="test1.example.com.")


class GeoLocationModel(BaseModel):

    ContinentCode: Optional[str] = Field(
        None,
        description="Continent code of the location",
        example="NA")
    CountryCode: Optional[str] = Field(
        None,
        description="Country code of the location",
        example="US")
    SubdivisionCode: Optional[str] = Field(
        None,
        description="Subdivision code of the location",
        example="CA")


class R53Record(BaseModel):

    Name: str = Field(
        None,
        description="Name of the DNS record",
        example="test1.example.com.")
    Type: str = Field(
        None,
        description="Type of DNS record",
        example="A")
    TTL: int = Field(
        None,
        description="Time to leave of the DNS record in seconds",
        example=300)
    Region: Optional[str] = Field(
        None,
        description="If the record has latency routing policy, this field will indicate which AWS region is the record pointing to. Must be a valid AWS region name",
        example="eu-west-1")
    GeoLocation: Optional[GeoLocationModel]
    AliasTarget: Optional[AliasTargetModel]
    ResourceRecords: List[ResourceRecord]
    SetIdentifier: Optional[str] = Field(
        None,
        description="Assigns an arbitrary identifier to the record",
        example="rp-geo-default")
    Weight: Optional[int] = Field(
        None,
        description="If the record has weighted routing policy, this field will indicate the weight of the record.",
        example=100)
