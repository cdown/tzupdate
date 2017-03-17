|travis| |coveralls| |libraries|

.. |travis| image:: https://img.shields.io/travis/cdown/tzupdate/develop.svg?label=tests
  :target: https://travis-ci.org/cdown/tzupdate
  :alt: Tests

.. |coveralls| image:: https://img.shields.io/coveralls/cdown/tzupdate/develop.svg?label=test%20coverage
  :target: https://coveralls.io/github/cdown/tzupdate?branch=develop
  :alt: Coverage

.. |libraries| image:: https://img.shields.io/librariesio/github/cdown/tzupdate.svg?label=dependencies
  :target: https://libraries.io/github/cdown/tzupdate
  :alt: Dependencies

tzupdate is a fully automated utility to set the system time using geolocation.

Usage
-----

By default, tzupdate will geolocate you, get the timezone for that geolocation,
and then attempt to link that timezone to ``/etc/localtime``. You can pass
``-p`` to print the detected timezone without linking. You can also pass ``-a``
to pass an IP address to use, instead of geolocating you.

::

    $ sudo tzupdate
    Set system timezone to Europe/London.

Installation
------------

To install the latest stable version from PyPi:

.. code::

    $ pip install -U tzupdate

To install the latest development version directly from GitHub:

.. code::

    $ pip install -U git+https://github.com/cdown/tzupdate.git@develop

Testing
-------

.. code::

    $ pip install tox
    $ tox
    ..........
    ----------------------------------------------------------------------
    Ran 10 tests in 4.088s
    OK
