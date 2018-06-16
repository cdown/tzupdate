#!/usr/bin/env python2

import tzupdate
import httpretty
import os
import errno
import mock
from tests._test_utils import (IP_ADDRESSES, FAKE_SERVICES, FAKE_TIMEZONE,
                               setup_basic_api_response)
from nose.tools import (assert_raises, eq_ as eq, assert_true, assert_is_none,
                        assert_in)
from nose_parameterized import parameterized
from hypothesis import given, settings
from hypothesis.strategies import sampled_from, none, one_of, text


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()))
@given(sampled_from(FAKE_SERVICES))
@settings(max_examples=20)
def test_get_timezone_for_ip(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response()
    tzupdate.get_timezone_for_ip(
        ip=ip, service=service, queue_obj=fake_queue,
    )

    if ip is not None:
        assert_in(ip, httpretty.last_request().path)

    fake_queue.put.assert_called_once_with(FAKE_TIMEZONE)


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()))
@given(sampled_from(FAKE_SERVICES))
@settings(max_examples=20)
def test_get_timezone_for_ip_empty_resp(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response(empty_resp=True)
    assert_is_none(tzupdate.get_timezone_for_ip(
            ip=ip, service=service, queue_obj=fake_queue,
    ))


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()))
@given(sampled_from(FAKE_SERVICES))
@settings(max_examples=20)
def test_get_timezone_for_ip_empty_val(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response(empty_val=True)
    assert_is_none(tzupdate.get_timezone_for_ip(
            ip=ip, service=service, queue_obj=fake_queue,
    ))


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
    with assert_raises(OSError) as raise_cm:
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH,
        )

    eq(raise_cm.exception.errno, errno.EACCES)


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


@given(text())
@given(text())
@settings(max_examples=20)
def test_debian_tz_path(timezone, tz_path):
    mo = mock.mock_open()
    with mock.patch('tzupdate.open', mo, create=True):
        tzupdate.write_debian_timezone(timezone, tz_path)
        mo.assert_called_once_with(tz_path, 'w')
        mo().write.assert_called_once_with(timezone + '\n')
