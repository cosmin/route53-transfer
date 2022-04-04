# encoding: utf-8

import yaml
import json
import sys

from typing import List
from route53_transfer.models import R53Record

DEFAULT_FORMAT = "yaml"

FORMAT_READER = {
    "yaml": yaml.safe_load,
    "json": json.load,
}

FORMAT_WRITER = {
    "yaml": yaml.safe_dump,
    "json": json.dumps,
}


def read_records(filename=sys.stdin, format='yaml'):
    default_reader = FORMAT_READER[DEFAULT_FORMAT]
    reader = FORMAT_READER.get(format, default_reader)
    records_dict_list = reader(filename)

    r53_records_list = map(R53Record.from_dict, records_dict_list)
    return list(r53_records_list)


def write_records(records: List[R53Record], format='yaml') -> str:
    default_writer = FORMAT_WRITER[DEFAULT_FORMAT]
    writer = FORMAT_WRITER.get(format, default_writer)

    records_dict_list = [record.dict(exclude_none=True)
                         for record in records]
    return writer(records_dict_list)
