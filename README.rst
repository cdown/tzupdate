tzupdate is a fully automated utility to set the system time using geolocation.

Usage
=====

By default, tzupdate will geolocate you, get the timezone for that geolocation,
and then attempt to link that timezone to ``/etc/localtime``. You can pass
``-p`` to print the detected timezone without linking. You can also pass ``-a``
to pass an IP address to use, instead of geolocating you.

::

    $ sudo tzupdate
    Detected timezone is Europe/Dublin.
    Linked /etc/localtime to /usr/share/zoneinfo/Europe/Dublin.


Installation
============

Installation requires `setuptools`_.

.. _setuptools: https://pypi.python.org/pypi/setuptools

Stable version
--------------

::

    $ pip install tzupdate

Development version
-------------------

::

    $ git clone git://github.com/cdown/tzupdate.git
    $ cd tzupdate
    $ python setup.py install

Testing
=======

.. image:: https://travis-ci.org/cdown/tzupdate.svg?branch=develop
  :target: https://travis-ci.org/cdown/tzupdate
  :alt: Test status

::

    $ python setup.py test

License
=======

tzupdate is licensed under an `ISC license`_. Full information is in the
`LICENSE`_ file.

.. _ISC license: https://en.wikipedia.org/wiki/ISC_license
.. _LICENSE: LICENSE
