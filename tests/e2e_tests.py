#!/usr/bin/env python2

import tzupdate
import os
import mock
from nose.tools import assert_raises, eq_ as eq, assert_true, assert_false


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_end_to_end_no_args(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = 'Fake/Timezone'
    tzupdate.run([])
    assert_true(link_localtime_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_print_only_no_link(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = 'Fake/Timezone'
    tzupdate.run(['-p'])
    assert_false(link_localtime_mock.called)


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_explicit_paths(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = 'Fake/Timezone'
    tzupdate.run(['-l', '/l', '-z', '/z'])
    assert_true(
        link_localtime_mock.called_once_with('Fake/Timezone', '/z', '/l'),
    )


@mock.patch('tzupdate.get_timezone_for_ip')
@mock.patch('tzupdate.link_localtime')
def test_explicit_ip(link_localtime_mock, get_timezone_for_ip_mock):
    get_timezone_for_ip_mock.return_value = 'Fake/Timezone'
    tzupdate.run(['-a', '1.2.3.4'])
    assert_true(get_timezone_for_ip_mock.called_once_with('1.2.3.4'))
