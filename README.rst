route53-transfer
================

Backup and restore Route53 zones, or transfer between AWS accounts.

Installation
------------

::

    pip install route53-transfer

Usage
-----

Backup a zone
~~~~~~~~~~~~~

Backup the ``example.com`` zone to a ``CSV`` file.

::

    route53-transfer dump example.com backup.csv

Use STDOUT instead of a file

::

    route53-transfer dump example.com -

Restore a zone
~~~~~~~~~~~~~~

Restore the ``example.com`` zone from a ``CSV`` file.

::

    route53-transfer load example.com backup.csv

Use ``-`` to load from STDIN instead.

Migrate between accounts
~~~~~~~~~~~~~~~~~~~~~~~~

Use the command line switches to override the access and secret keys.
Dump from one account, load into another.

::

    route53-transfer --access-key-id=ACCOUNT1 --secret-key=SECRET dump example.com
    route53-transfer --access-key-id=ACCOUNT2 --secret-key=SECRET load example.com

Working with private zones
~~~~~~~~~~~~~~~~~~~~~~~~~~
If hosting split-horizon zones, use --private to distinguish private domains.

::

    route53-transfer --private dump example.com example-private.csv
    route53-transfer dump example.com example-public.csv

When loading private zones, the target VPC region (--vpc-region)  and VPC id (--vpc-id) must be specified.

::

    route53-transfer --private --vpc-region {target vpc region} --vpc-id {target vpc id} load example.com example-private.csv

In Python
~~~~~~~~~

Use the `load` and `dump` functions to move data.

::

    from StringIO import StringIO
    from route53_transfer import load, dump
    from boto import route53
    
    out = StringIO()
    con = route53.connect_to_region('universal')
    dump(con, 'example.com', out)
