# encoding: utf-8

import yaml
import json
import sys

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
    return reader(filename)


def write_records(records, format='yaml'):
    default_writer = FORMAT_WRITER[DEFAULT_FORMAT]
    writer = FORMAT_WRITER.get(format, default_writer)
    return writer(records)

