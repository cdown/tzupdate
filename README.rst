|PyPI|

tzupdate is a simple, fully automated utility to set the system time
based upon IP geolocation. It uses your IP to geolocate you, and then
links the appropriate timezone file for your location (unless you pass
``-p`` or ``--print-only``, in which case it only prints the timezone).

You can also pass ``-a``/``--ip`` to get information about a specific IP
instead of using the one that you are making HTTP requests from.

.. |PyPI| image:: https://pypip.in/v/tzupdate/badge.png
   :target: https://pypi.python.org/pypi/tzupdate
