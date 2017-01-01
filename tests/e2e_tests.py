#!/usr/bin/env python2

import httpretty
import tzupdate
import mock
from nose.tools import assert_false, assert_raises
from tests._test_utils import (FAKE_SERVICES, FAKE_TIMEZONE,
                               setup_basic_api_response)


@httpretty.activate
@mock.patch('tzupdate.write_debian_timezone')
@mock.patch('tzupdate.link_localtime')
def test_end_to_end_no_args(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    args = []
    tzupdate.main(args, services=FAKE_SERVICES)
    link_localtime_mock.assert_called_once_with(
        FAKE_TIMEZONE, tzupdate.DEFAULT_ZONEINFO_PATH,
        tzupdate.DEFAULT_LOCALTIME_PATH,
    )
    deb_tz_mock.assert_called_once_with(
        FAKE_TIMEZONE, tzupdate.DEFAULT_DEBIAN_TIMEZONE_PATH,
    )


@httpretty.activate
@mock.patch('tzupdate.write_debian_timezone')
@mock.patch('tzupdate.link_localtime')
def test_print_only_no_link(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    args = ['-p']
    tzupdate.main(args, services=FAKE_SERVICES)
    assert_false(link_localtime_mock.called)
    assert_false(deb_tz_mock.called)


@httpretty.activate
@mock.patch('tzupdate.write_debian_timezone')
@mock.patch('tzupdate.link_localtime')
def test_explicit_paths(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    localtime_path = '/l'
    zoneinfo_path = '/z'
    deb_path = '/d'
    args = ['-l', localtime_path, '-z', zoneinfo_path, '-d', deb_path]
    tzupdate.main(args, services=FAKE_SERVICES)
    link_localtime_mock.assert_called_once_with(
        FAKE_TIMEZONE, zoneinfo_path, localtime_path,
    )
    deb_tz_mock.assert_called_once_with(FAKE_TIMEZONE, deb_path)


@httpretty.activate
@mock.patch('tzupdate.write_debian_timezone')
@mock.patch('tzupdate.link_localtime')
def test_explicit_ip(_unused_ll, _unused_deb):
    setup_basic_api_response()
    ip_addr = '1.2.3.4'
    args = ['-a', ip_addr]
    tzupdate.main(args, services=FAKE_SERVICES)

    # TODO (#16): httpretty.last_request() and
    # get_timezone_for_ip.assert_called_once_with don't work for testing here
    # because of the threading we use. We need to work out a good solution for
    # this in


@mock.patch('tzupdate.write_debian_timezone')
@mock.patch('tzupdate.link_localtime')
def test_explicit_timezone(link_localtime_mock, deb_tz_mock):
    timezone = 'Foo/Bar'
    args = ['-t', timezone]
    tzupdate.main(args)
    link_localtime_mock.assert_called_once_with(
        timezone,
        tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
    )
    deb_tz_mock.assert_called_once_with(
        timezone, tzupdate.DEFAULT_DEBIAN_TIMEZONE_PATH
    )


@httpretty.activate
@mock.patch('tzupdate.Process')
def test_timeout_results_in_exception(process_mock):
    # The process mock causes us to never run get_timezone_from_ip, so we
    # should time out
    setup_basic_api_response()
    args = ['-s', '0.01']
    with assert_raises(tzupdate.TimezoneAcquisitionError):
        tzupdate.main(args, services=FAKE_SERVICES)
