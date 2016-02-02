#!/usr/bin/env python2

import tzupdate
import httpretty
import os
import errno
import json
import re
import mock
from nose.tools import assert_raises, eq_ as eq, assert_true
from nose_parameterized import parameterized
from hypothesis import given
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
    ip_addr = '.'.join(map(str, ip_octets))
    got_timezone = tzupdate.get_timezone_for_ip(ip_addr)
    eq(got_timezone, FAKE_TIMEZONE)


@parameterized([
    ({'status': 'success'}, tzupdate.NoTimezoneAvailableError),
    ({'status': 'fail'}, tzupdate.IPAPIError),
    ({'status': 'fail', 'message': 'lolno'}, tzupdate.IPAPIError),
])
@httpretty.activate
def test_get_timezone_for_ip_api_error_types(error_body, expected_exception):
    setup_basic_api_response(body=json.dumps(error_body))
    with assert_raises(expected_exception):
        tzupdate.get_timezone_for_ip()


@mock.patch('tzupdate.os.unlink')
@mock.patch('tzupdate.os.symlink')
@mock.patch('tzupdate.os.path.isfile')
def test_link_localtime(isfile_mock, symlink_mock, unlink_mock):
    isfile_mock.return_value = True
    expected = os.path.join(tzupdate.DEFAULT_ZONEINFO_PATH, FAKE_TIMEZONE)

    zoneinfo_tz_path = tzupdate.link_localtime(
        FAKE_TIMEZONE,
        tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
    )

    assert_true(unlink_mock.called_once_with([expected]))
    assert_true(symlink_mock.called_once_with([
        expected, tzupdate.DEFAULT_LOCALTIME_PATH
    ]))

    eq(zoneinfo_tz_path, expected)


@parameterized([
    '/foo/bar',
    '../../../../foo/bar',
])
def test_link_localtime_traversal_attack(questionable_timezone):
    with assert_raises(tzupdate.DirectoryTraversalError):
        tzupdate.link_localtime(
            questionable_timezone,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch('tzupdate.os.path.isfile')
def test_link_localtime_timezone_not_available(isfile_mock):
    isfile_mock.return_value = False
    with assert_raises(tzupdate.TimezoneNotLocallyAvailableError):
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch('tzupdate.os.unlink')
@mock.patch('tzupdate.os.path.isfile')
def test_link_localtime_permission_denied(isfile_mock, unlink_mock):
    isfile_mock.return_value = True
    unlink_mock.side_effect = OSError(errno.EACCES, 'Permission denied yo')
    with assert_raises(tzupdate.LocaltimePermissionError):
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch('tzupdate.os.unlink')
@mock.patch('tzupdate.os.path.isfile')
def test_link_localtime_oserror_not_permission(isfile_mock, unlink_mock):
    isfile_mock.return_value = True
    code = errno.ENOSPC
    unlink_mock.side_effect = OSError(code, 'No space yo')

    with assert_raises(OSError) as thrown_exc:
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )

    eq(thrown_exc.exception.errno, code)


@mock.patch('tzupdate.os.unlink')
@mock.patch('tzupdate.os.path.isfile')
@mock.patch('tzupdate.os.symlink')
def test_link_localtime_localtime_missing_no_raise(symlink_mock, isfile_mock,
                                                   unlink_mock):
    isfile_mock.return_value = True
    code = errno.ENOENT
    unlink_mock.side_effect = OSError(code, 'No such file or directory')

    # This should handle OSError and not raise further
    tzupdate.link_localtime(
        FAKE_TIMEZONE,
        tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
    )
