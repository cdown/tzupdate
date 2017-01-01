|travis| |coveralls|

.. |travis| image:: https://travis-ci.org/cdown/tzupdate.svg?branch=develop
  :target: https://travis-ci.org/cdown/tzupdate
  :alt: Test status

.. |coveralls| image:: https://coveralls.io/repos/cdown/tzupdate/badge.svg?branch=develop&service=github
  :target: https://coveralls.io/github/cdown/tzupdate?branch=develop
  :alt: Coverage

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

    pip install -U tzupdate

To install the latest development version directly from GitHub:

.. code::

    pip install -U git+https://github.com/cdown/tzupdate.git@develop

Testing
-------

.. code::

   tox -e quick

.. _Tox: https://tox.readthedocs.org
