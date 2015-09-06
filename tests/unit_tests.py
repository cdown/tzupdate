#!/usr/bin/env python2

import tzupdate
import httpretty
import json
import re
from nose.tools import assert_raises, eq_ as eq, assert_true, with_setup
from hypothesis import given, assume
from hypothesis.strategies import integers, tuples


IP_OCTET = integers(min_value=0, max_value=255)
IP_ADDRESSES = tuples(IP_OCTET, IP_OCTET, IP_OCTET, IP_OCTET)
FAKE_TIMEZONE = 'Fake/Timezone'
FAKE_API_BODY = json.dumps({'timezone': FAKE_TIMEZONE})


def setup_basic_api_response(body=FAKE_API_BODY):
    uri_regex = re.compile(r'^http://ip-api\.com/json/')
    httpretty.register_uri(
        httpretty.GET, uri_regex,
        body=body, content_type='application/json',
    )


@httpretty.activate
def test_get_timezone_for_ip_none():
    setup_basic_api_response()
    got_timezone = tzupdate.get_timezone_for_ip()
    eq(got_timezone, FAKE_TIMEZONE)


@httpretty.activate
@given(IP_ADDRESSES)
def test_get_timezone_for_ip_explicit(ip_octets):
    setup_basic_api_response()
    ip = '.'.join(map(str, ip_octets))
    got_timezone = tzupdate.get_timezone_for_ip(ip)
    eq(got_timezone, FAKE_TIMEZONE)
