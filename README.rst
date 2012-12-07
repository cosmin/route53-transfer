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

    route53-transfer backup example.com backup.csv

Use STDOUT instead of a file

::

    route53-transfer backup example.com -

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

