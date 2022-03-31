from __future__ import print_function
from collections import defaultdict

import sys
import time
from datetime import datetime
from os import environ

import boto3

from route53_transfer.serialization import read_records, write_records
from route53_transfer.change_batch import ChangeBatch


class ComparableRecord:
    def __init__(self, obj):
        print(obj)
        for k, v in obj.items():
            self.__dict__[k] = v

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __hash__(self):
        # TODO massively incomplete
        it = (self.Name, self.Type,  # self.alias_hosted_zone_id,
              #self.alias_dns_name, tuple(sorted(self.resource_records)),
              tuple(sorted(map(lambda r: r['Value'], self.ResourceRecords))),
              self.TTL,
              #self.ttl, self.region, self.weight, self.identifier,
              #self.failover, self.alias_evaluate_target_health)
              )
        return it.__hash__()

    def to_change_dict(self):
        # TODO massively incomplete and a mess
        data = {}
        for k, v in self.__dict__.items():
            if k == 'ResourceRecords':
                continue
            elif k == 'Name':
                data['name'] = v
            elif k == 'TTL':
                data['ttl'] = v
            elif k == 'Id':
                data['id'] = v
            elif k == 'Type':
                data['type'] = v
            else:
                data[k] = v
        return data

    def __repr__(self):
        rr = " ".join(map(lambda r: r['Value'], self.ResourceRecords))
        extra_info = f"{self.TTL}:{rr}"

        if hasattr(self, 'AliasDnsName') and self.AliasDnsName:
            extra_info = f"ALIAS {self.alias_hosted_zone_id} {self.alias_dns_name} " \
                         f"(EvalTarget {self.alias_evaluate_target_health})"

        return f"<ComparableRecord:{self.Name}:{self.Type}:{extra_info}>"


def exit_with_error(error):
    sys.stderr.write(error)
    sys.exit(1)


def get_zone(r53_client, zone_name, vpc):
    """
    {
        "HostedZones": [
            {
                "CallerReference": "7C1E9645-5350-B96B-B1E8-095AD8017ABA",
                "Config": {
                    "Comment": "Experimental",
                    "PrivateZone": false
                },
                "Id": "/hostedzone/ZA3FSFWA1ZAVE",
                "Name": "kahoot-experimental.it.",
                "ResourceRecordSetCount": 100
            },
            {
                "CallerReference": "7AB28767-96B5-E3B8-A2D2-C893278F2CEE",
                "Config": {
                    "PrivateZone": false
                },
                "Id": "/hostedzone/Z1HK9LVYEVER1Y",
                "Name": "kahoot-experimental.com.",
                "ResourceRecordSetCount": 21
            },
            {
                "CallerReference": "06a1fc06-f139-479b-b61b-f115302e130d",
                "Config": {
                    "Comment": "",
                    "PrivateZone": false
                },
                "Id": "/hostedzone/Z099621627HY07FUO9ACG",
                "Name": "geotest.kahoot-experimental.it.",
                "ResourceRecordSetCount": 14
            }
        ],
        "IsTruncated": false,
        "MaxItems": "100",
        "ResponseMetadata": {
            "HTTPHeaders": {
                "content-length": "1077",
                "content-type": "text/xml",
                "date": "Tue, 22 Mar 2022 13:18:00 GMT",
                "x-amzn-requestid": "61554652-b58d-4918-9024-697e4eb51cf2"
            },
            "HTTPStatusCode": 200,
            "RequestId": "61554652-b58d-4918-9024-697e4eb51cf2",
            "RetryAttempts": 0
        }
    }
    """
    paginator = r53_client.get_paginator('list_hosted_zones')
    hosted_zones = []

    for page in paginator.paginate():
        hosted_zones.extend(page['HostedZones'])

    list_private_zones = vpc is not None and vpc.get('is_private')
    requested_vpc_id = vpc.get('id') if vpc else None
    matching_zones = []

    for zone in hosted_zones:
        is_private = zone['Config']['PrivateZone']
        if zone['Name'] != zone_name + '.':
            continue

        if (is_private and list_private_zones) \
                or (not is_private and not list_private_zones):
            matching_zones.append(zone)

    for zone in matching_zones:
        data = {
            'id': zone.get('Id', '').replace('/hostedzone/', ''),
            'name': zone.get('Name'),
        }
        if not list_private_zones:
            return data

        zone_id = data.get('id')
        z = r53_client.get_hosted_zone(Id=zone_id)
        # TODO validate
        z_vpc_id = z.get('HostedZone', {}) \
            .get('VPCs', {}) \
            .get('VPC', {}) \
            .get('VPCId', '')
        if requested_vpc_id and z_vpc_id == requested_vpc_id:
            return data
    else:
        return None


def create_zone(r53_client, zone_name, vpc):
    print('/// Create zone disabled ///')
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", datetime.utcnow().utctimetuple())
    # r53_client.create_hosted_zone(domain_name=zone_name,
    #                              private_zone=vpc.get('is_private'),
    #                              vpc_region=vpc.get('region'),
    #                              vpc_id=vpc.get('id'),
    #                              comment='autogenerated by route53-transfer @ {}'.format(ts))
    # return get_zone(r53_client, zone_name, vpc)
    return


def skip_apex_soa_ns(zone, records):
    """
    Name: kahoot-experimental-2703.com.
    ResourceRecords:
    - Value: ns-550.awsdns-04.net.
    - Value: ns-1248.awsdns-28.org.
    - Value: ns-176.awsdns-22.com.
    - Value: ns-1929.awsdns-49.co.uk.
    TTL: 172800
    Type: NS
    """
    for record in records:
        rec_name = record['Name']
        rec_type = record['Type']
        if rec_name == zone['name'] and rec_type in ('SOA', 'NS'):
            continue
        else:
            yield record


def comparable(records):
    return {ComparableRecord(record) for record in records}


def get_file(filename, mode):
    ''' Get a file-like object for a filename and mode.

        If filename is "-" return one of stdin or stdout.
    '''
    if filename == '-':
        if mode.startswith('r'):
            return sys.stdin
        elif mode.startswith('w'):
            return sys.stdout
        else:
            raise ValueError('Unknown mode "{}"'.format(mode))
    else:
        return open(filename, mode)


def get_hosted_zone_record_sets(r53_client, zone_id):
    paginator = r53_client.get_paginator('list_resource_record_sets')
    resource_record_sets = []
    for resource_record_set in paginator.paginate(HostedZoneId=zone_id):
        resource_record_sets.extend(resource_record_set['ResourceRecordSets'])
    return resource_record_sets


def load(r53, zone_name, file_in, **kwargs):
    """
    Send DNS records from input file to Route 53.

    Arguments are Route53 connection, zone name, vpc info, and file to open for reading.
    """
    dry_run = kwargs.get('dry_run', False)
    use_upsert = kwargs.get('use_upsert', False)
    vpc = kwargs.get('vpc', {})

    zone = get_zone(r53, zone_name, vpc)
    if not zone:
        if dry_run:
            print('CREATE ZONE:', zone_name)
        else:
            zone = create_zone(r53, zone_name, vpc)

    existing_records = get_hosted_zone_record_sets(r53, zone['id'])
    desired_records = read_records(file_in)

    changes = compute_changes(zone, existing_records, desired_records,
                              use_upsert=use_upsert)

    if dry_run:
        print("Dry-run requested. No changes are going to be applied")
    else:
        print("Applying changes...")

    n = 1
    for update_batch in changes_to_r53_updates(zone, changes):

        print(f"* Update batch {n} ({len(update_batch.changes)} changes)")
        if dry_run:
            for change in update_batch.changes:
                print("    -", change['operation'], change['change_dict'])
        else:
            update_batch.commit(r53, zone)
        n += 1

    else:
        print("No changes.")

    print("Done.")


def assign_change_priority(zone: dict, change_operations: list) -> None:
    """
    Given a list of change operations derived from the difference of two zones
    files, assign a priority integer to each change operation.

    The priority integer serves two purposes:

    1. Identify the relative order the changes. The target of an alias record
       will have a higher priority, since it needs to be present when we
       commit our change transaction.

    2. Group together all change operations that can be committed together
       in the same ResourceRecordSet change transaction.
    """
    rr_prio = defaultdict(int)

    def is_same_zone(change: dict) -> bool:
        return change["zone"]["id"] == zone["id"]

    def is_alias(change: ComparableRecord) -> bool:
        record = change["record"]
        return hasattr(record, 'alias_dns_name') and record.AliasDnsName is not None and is_same_zone(change)

    def is_new_alias(change: ComparableRecord) -> bool:
        return is_alias(change) and change["operation"] in ("CREATE", "UPSERT")

    for change in change_operations:
        if is_new_alias(change):
            record = change["record"]
            rr_prio[record.alias_dns_name] += 1

    for change in change_operations:
        if is_new_alias(change):
            record = change["record"]
            rr_prio[record.alias_dns_name] += rr_prio[record.name]

    for change in change_operations:
        record = change["record"]
        change["prio"] = rr_prio[record.Name]


def changes_to_r53_updates(zone, change_operations):
    """
    Given a list of zone change operations as computed by `compute_changes()`,
    returns a list of R53 update batches. Normally one update batch, that is,
    a `ResourceRecordSets` object, will suffice for all updates. In certain
    cases, when records are aliases and their target records do not already
    exist in a zone, it's necessary to split the zone updates in different
    batches, which have to be committed in two separate operations.

    :param zone: Route53 zone object (dict with `id` and `name`)
    :param change_operations: list of zone change operations as returned by
           `compute_changes()`
    :return: r53_updates: list of ChangeBatch objects
    """

    assign_change_priority(zone, change_operations)

    r53_update_batches = []
    current_batch = ChangeBatch()
    current_prio = None

    for change in sorted(change_operations, key=lambda c: c["prio"], reverse=True):
        order = change["prio"]

        if current_prio is None:
            current_prio = order

        if order != current_prio:
            if current_batch.changes:
                r53_update_batches.append(current_batch)
            current_batch = ChangeBatch()

        current_batch.add_change(change)
        current_prio = order

    if current_batch.changes:
        r53_update_batches.append(current_batch)

    return r53_update_batches


def compute_changes(zone, existing_records, desired_records, use_upsert=False):
    """
    Given two sets of existing and desired resource records, compute the
    list of transactions (ResourceRecordSets changes) that will bring us
    from the existing state to the desired state.

    We need to take into account that we can't commit our changes in a single
    transaction in certain cases. One such cases is when we introduce records
    that are aliases to existing records. Route53 will reject our updates
    if the target record for the alias does not exist yet. The workaround is
    to execute the change in two distinct transactions (ResourceRecordSet
    changes), the first to commit the target resources of all the new aliases
    and the second one for all the other resource records.

    :param zone: Route53 zone object
    :param existing_records: list of rrsets that exist in the r53 zone
    :param desired_records: list of rrsets that we desire as final state
    :param use_upsert: if True, prefers UPSERT operations to CREATE and DELETE
    :return: list of ResourceRecordSet changes to be applied
    """

    existing_records = comparable(skip_apex_soa_ns(zone, existing_records))
    desired_records = comparable(skip_apex_soa_ns(zone, desired_records))

    print("existing:", existing_records)
    print("desired:", desired_records)

    to_delete = existing_records.difference(desired_records)
    to_add = desired_records.difference(existing_records)
    changes = list()

    def is_in_set(record: ComparableRecord, s: set) -> bool:
        for entry in s:
            if entry.to_change_dict()["Name"] == record.to_change_dict()["Name"]:
                return True
        return False

    def sort_by_name(s: set):
        return sorted(s, key=lambda comparable_record: comparable_record.Name)

    if to_add or to_delete:
        for record in sort_by_name(to_add):
            op_type = "UPSERT" if use_upsert and is_in_set(record, to_delete) else "CREATE"
            changes.append({"zone": zone,
                            "operation": op_type,
                            "record": record})

        for record in sort_by_name(to_delete):
            if not (use_upsert and is_in_set(record, to_add)):
                changes.insert(0, {"zone": zone,
                                   "operation": "DELETE",
                                   "record": record})

    return changes


def dump(r53_client, zone_name, output_file, **kwargs):
    """
    Receive DNS records from Route 53 to output file.

    Arguments are Route53 connection, zone name, vpc info, and file to open for writing.
    """
    vpc = kwargs.get('vpc', {})

    zone = get_zone(r53_client, zone_name, vpc)
    if not zone:
        exit_with_error("ERROR: {} zone {} not found!".format(
            'Private' if vpc.get('is_private') else 'Public',
            zone_name))

    records = get_hosted_zone_record_sets(r53_client, zone['id'])

    output_file.write(write_records(records, format='yaml'))
    output_file.flush()


"""
DelegationSet:
  NameServers:
  - ns-1864.awsdns-41.co.uk
  - ns-1525.awsdns-62.org
  - ns-864.awsdns-44.net
  - ns-28.awsdns-03.com
HostedZone:
  CallerReference: 06a1fc06-f139-479b-b61b-f115302e130d
  Config:
    Comment: ''
    PrivateZone: false
  Id: /hostedzone/Z099621627HY07FUO9ACG
  Name: geotest.kahoot-experimental.it.
  ResourceRecordSetCount: 14
ResponseMetadata:
  HTTPHeaders:
    content-length: '665'
    content-type: text/xml
    date: Tue, 22 Mar 2022 14:35:43 GMT
    x-amzn-requestid: af722f7d-7e79-47ca-8922-3691913dc78a
  HTTPStatusCode: 200
  RequestId: af722f7d-7e79-47ca-8922-3691913dc78a
  RetryAttempts: 0
"""
# print(yaml.safe_dump(r53_client.get_hosted_zone(Id='Z099621627HY07FUO9ACG')))


def run(params):
    r53_client = boto3.client('route53')
    zone_name = params['<zone>']
    filename = params['<file>']

    vpc = {}
    if params.get('--private'):
        vpc['is_private'] = True
        vpc['region'] = params.get('--vpc-region') or environ.get('AWS_DEFAULT_REGION')
        vpc['id'] = params.get('--vpc-id')
        if not vpc.get('region') or not vpc.get('id'):
            exit_with_error("ERROR: Private zones require associated VPC Region and ID "
                            "(--vpc-region, --vpc-id)".format(zone_name))
    else:
        vpc['is_private'] = False

    if params.get('dump'):
        dump(r53_client, zone_name, get_file(filename, 'w'), vpc=vpc)
        if params.get('--s3-bucket'):
            # TODO
            # s3_client = boto3.client('s3')
            # up_to_s3(s3_client, params.get('<file>'), params.get('--s3-bucket'))
            pass

    elif params.get('load'):
        dry_run = params.get('--dry-run', False)
        use_upsert = params.get('--use-upsert', False)

        load(r53_client, zone_name, get_file(filename, 'r'), vpc=vpc,
             dry_run=dry_run, use_upsert=use_upsert)
    else:
        return 1