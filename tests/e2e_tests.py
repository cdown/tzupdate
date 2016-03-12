#!/usr/bin/env python2

import tzupdate
import mock
from nose.tools import assert_true, assert_false


FAKE_TIMEZONE = 'E2E'


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
@mock.patch('tzupdate.export_etc_timezone')
def test_end_to_end_no_args(export_etc_timezone_mock,
                        link_localtime_mock,
                        get_timezone_for_ip_mock):

    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = []
    tzupdate.main(args)
    assert_true(link_localtime_mock.called)
    assert_true(export_etc_timezone_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_print_only_no_link(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = ['-p']
    tzupdate.main(args)
    assert_false(link_localtime_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.export_etc_timezone')
@mock.patch('tzupdate.link_localtime')
def test_explicit_paths(link_localtime_mock, export_etc_timezone_mock, get_timezone_for_ip_mock):
    localtime_path = '/l'
    zoneinfo_path = '/z'
    etc_timezone_path = '/e'
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = ['-l', localtime_path, '-z', zoneinfo_path]
    tzupdate.main(args)
    assert_true(
        link_localtime_mock.called_once_with(
            FAKE_TIMEZONE, zoneinfo_path, localtime_path,
        ),
    )
    assert_true(
        export_etc_timezone_mock.called_once_with(
            FAKE_TIMEZONE, etc_timezone_path,
        ),
    )


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.export_etc_timezone')
@mock.patch('tzupdate.link_localtime')
def test_explicit_ip(_, export_etc_timezone_mock, get_timezone_for_ip_mock):
    ip_addr = '1.2.3.4'
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = ['-a', ip_addr]
    tzupdate.main(args)
    assert_true(get_timezone_for_ip_mock.called_once_with(ip_addr))
    assert_true(export_etc_timezone_mock.called)


@mock.patch('tzupdate.link_localtime')
@mock.patch('tzupdate.export_etc_timezone')
def test_explicit_timezone(export_etc_timezone_mock, link_localtime_mock):
    timezone = 'Foo/Bar'
    args = ['-t', timezone]
    tzupdate.main(args)
    assert_true(
        link_localtime_mock.called_once_with(
            timezone,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )
    )
    assert_true(
        export_etc_timezone_mock.called_once_with(
            timezone,
            tzupdate.DEFAULT_ETC_TIMEZONE_PATH,
        )
    )
