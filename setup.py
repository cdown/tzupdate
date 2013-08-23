#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "tzupdate",
    version = "0.3.0",
    description = "Set the system timezone based on IP geolocation.",
    author = "Chris Down",
    author_email = "chris@chrisdown.name",
    url = "https://github.com/cdown/tzupdate",
    scripts = [ "tzupdate" ],
)
