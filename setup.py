#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "tzupdate",
    version = "0.001",
    description = "Automatically determine and set localtime based on IP.",
    author = "Chris Down",
    author_email = "chris@illco.de",
    url = "http://illco.de",
    packages = (
        ""
    ),
    scripts = ( "tzupdate", ),
    long_description = """
tzupdate is a utility to automatically determine and set your computer's
localtime based upon a geolocation of your WAN IP.
"""
)
