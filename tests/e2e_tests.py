#!/usr/bin/env python2

import tzupdate
import mock
from nose.tools import assert_true, assert_false


FAKE_TIMEZONE = 'E2E'


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_end_to_end_no_args(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = tzupdate.parse_args([])
    tzupdate.run(args)
    assert_true(link_localtime_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_print_only_no_link(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = tzupdate.parse_args(['-p'])
    tzupdate.run(args)
    assert_false(link_localtime_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_explicit_paths(link_localtime_mock, get_timezone_for_ip_mock):
    localtime_path = '/l'
    zoneinfo_path = '/z'
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = tzupdate.parse_args(['-l', localtime_path, '-z', zoneinfo_path])
    tzupdate.run(args)
    assert_true(
        link_localtime_mock.called_once_with(
            FAKE_TIMEZONE, zoneinfo_path, localtime_path,
        ),
    )


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_explicit_ip(_, get_timezone_for_ip_mock):
    ip_addr = '1.2.3.4'
    get_timezone_for_ip_mock.return_value = FAKE_TIMEZONE
    args = tzupdate.parse_args(['-a', ip_addr])
    tzupdate.run(args)
    assert_true(get_timezone_for_ip_mock.called_once_with(ip_addr))
