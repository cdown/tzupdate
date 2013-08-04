#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "tzupdate",
    version = "0.2.1",
    description = "Set the local timezone based on IP geolocation.",
    author = "Chris Down",
    author_email = "chris@chrisdown.name",
    url = "http://chrisdown.name",
    scripts = [ "tzupdate" ],
)
