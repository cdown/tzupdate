#!/usr/bin/env python

import tzupdate
import httpretty
import json
import re
import ipaddress
from hypothesis.strategies import integers, builds


IP_ADDRESSES = builds(
    ipaddress.IPv4Address,
    integers(min_value=0, max_value=(2**32 - 1))
).map(str)

FAKE_TIMEZONE = 'Fake/Timezone'
FAKE_ERROR = 'Virus = very yes'

FAKE_SERVICES = set([
    tzupdate.GeoIPService(
        'http://example.com/json/{ip}', ('timezone',), 'message',
    ),
    tzupdate.GeoIPService(
        'https://doesnotexistreally.com/{ip}', ('time_zone',), None,
    ),
    tzupdate.GeoIPService(
        'http://tzupdate.com/foo/bar/{ip}', ('location', 'time_zone'), 'msg',
    ),
])


def setup_basic_api_response(services=None, empty_resp=False, empty_val=False):
    '''
    If `empty_resp', we return a totally empty API response, except for any
    error message.

    If `empty_val', the tz_key is an empty string.
    '''
    if services is None:
        services = FAKE_SERVICES

    for service in services:
        url_regex = re.compile(service.url.format(ip=r'.*'))
        api_body = {}

        if not empty_resp:
            cur_level = api_body

            for i, key in enumerate(service.tz_keys, start=1):
                if i == len(service.tz_keys):
                    if empty_val:
                        cur_level[key] = ''
                    else:
                        cur_level[key] = FAKE_TIMEZONE
                else:
                    cur_level[key] = {}
                    cur_level = cur_level[key]

        # If this already exists, it means that service.tz_keys is
        # (service.error_key,), which makes no sense...
        assert service.error_key not in api_body

        if service.error_key is not None:
            api_body[service.error_key] = FAKE_ERROR

        httpretty.register_uri(
            httpretty.GET, url_regex,
            body=json.dumps(api_body), content_type='application/json',
        )
