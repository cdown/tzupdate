|travis| |lgtm| |coveralls| |libraries|

.. |travis| image:: https://img.shields.io/travis/cdown/tzupdate/develop.svg?label=tests
  :target: https://travis-ci.org/cdown/tzupdate
  :alt: Tests

.. |lgtm| image:: https://img.shields.io/lgtm/grade/python/github/cdown/tzupdate.svg?label=code%20quality
  :target: https://lgtm.com/projects/g/cdown/tzupdate/overview/
  :alt: LGTM

.. |coveralls| image:: https://img.shields.io/coveralls/cdown/tzupdate/develop.svg?label=test%20coverage
  :target: https://coveralls.io/github/cdown/tzupdate?branch=develop
  :alt: Coverage

.. |libraries| image:: https://img.shields.io/librariesio/github/cdown/tzupdate.svg?label=dependencies
  :target: https://libraries.io/github/cdown/tzupdate
  :alt: Dependencies

tzupdate is a fully automated utility to set the system time using geolocation.

Usage
-----

::

    $ sudo tzupdate
    Set system timezone to Europe/London.

Internally, this geolocates you, gets the timezone for that geolocation, and
then updates the system's local time zone.

You can also see what tzupdate would do without actually doing it by passing
``-p``, and specify an alternative IP address by using ``-a``. This is not an
exhaustive list of options, see ``tzupdate --help`` for that.

Installation
------------

To install the latest stable version from PyPi (recommended):

.. code::

    $ pip install -U tzupdate

To install the latest development code from GitHub:

.. code::

    $ pip install -U git+https://github.com/cdown/tzupdate.git@develop

Testing
-------

.. code::

    $ tox
    Ran 18 tests in 1.109s
