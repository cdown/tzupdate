#!/usr/bin/env python

import tzupdate
import httpretty
import os
import errno
import mock
import pytest
from tests._test_utils import (
    IP_ADDRESSES,
    FAKE_SERVICES,
    FAKE_TIMEZONE,
    FAKE_ZONEINFO_PATH,
    setup_basic_api_response,
)
from hypothesis import given, settings, HealthCheck, assume
from hypothesis.strategies import sampled_from, none, one_of, text, integers


ERROR_STATUSES = [s for s in httpretty.http.STATUSES if 400 <= s <= 599]
SUPPRESSED_CHECKS = [HealthCheck.too_slow]

settings.register_profile("base", settings(suppress_health_check=SUPPRESSED_CHECKS))
settings.register_profile(
    "release", settings(max_examples=1000, suppress_health_check=SUPPRESSED_CHECKS)
)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "base"))


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()), sampled_from(FAKE_SERVICES))
def test_get_timezone_for_ip(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response()
    tzupdate.get_timezone_for_ip(ip_addr=ip, service=service, queue_obj=fake_queue)

    if ip is not None:
        assert ip in httpretty.last_request().path

    fake_queue.put.assert_called_once_with(FAKE_TIMEZONE)


def test_get_sys_timezone():
    systz = tzupdate.get_sys_timezone(
        FAKE_ZONEINFO_PATH, FAKE_ZONEINFO_PATH + "/" + FAKE_TIMEZONE
    )
    assert systz == FAKE_TIMEZONE


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()), sampled_from(FAKE_SERVICES))
def test_get_timezone_for_ip_empty_resp(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response(empty_resp=True)
    assert (
        tzupdate.get_timezone_for_ip(ip_addr=ip, service=service, queue_obj=fake_queue)
        is None
    )


@httpretty.activate
@given(one_of(IP_ADDRESSES, none()), sampled_from(FAKE_SERVICES))
def test_get_timezone_for_ip_empty_val(ip, service):
    fake_queue = mock.Mock()
    setup_basic_api_response(empty_val=True)
    assert (
        tzupdate.get_timezone_for_ip(ip_addr=ip, service=service, queue_obj=fake_queue)
        is None
    )


@httpretty.activate
@given(
    one_of(IP_ADDRESSES, none()),
    sampled_from(FAKE_SERVICES),
    sampled_from(ERROR_STATUSES),
)
def test_get_timezone_for_ip_doesnt_raise(ip, service, status):
    fake_queue = mock.Mock()
    setup_basic_api_response(status=status)
    assert (
        tzupdate.get_timezone_for_ip(ip_addr=ip, service=service, queue_obj=fake_queue)
        is None
    )


@mock.patch("tzupdate.os.replace")
@mock.patch("tzupdate.os.symlink")
@mock.patch("tzupdate.os.path.isfile")
@mock.patch("tzupdate.os.path.exists")
def test_link_localtime(exists_mock, isfile_mock, symlink_mock, replace_mock):
    isfile_mock.return_value = True

    # Don't check st_dev
    exists_mock.return_value = False

    expected = os.path.join(tzupdate.DEFAULT_ZONEINFO_PATH, FAKE_TIMEZONE)

    zoneinfo_tz_path = tzupdate.link_localtime(
        FAKE_TIMEZONE, tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH
    )

    assert replace_mock.called_once_with(
        [tzupdate.DEFAULT_LOCALTIME_PATH + "~", tzupdate.DEFAULT_LOCALTIME_PATH]
    )
    assert symlink_mock.called_once_with(
        [expected, tzupdate.DEFAULT_LOCALTIME_PATH + "~"]
    )

    assert zoneinfo_tz_path == expected


@mock.patch("tzupdate.os.replace")
@mock.patch("tzupdate.os.path.isfile")
@mock.patch("tzupdate.os.path.exists")
@mock.patch("tzupdate.os.stat")
@mock.patch("tzupdate.os.symlink")
def test_link_localtime_mounts_different(
    symlink_mock, stat_mock, exists_mock, isfile_mock, replace_mock
):
    isfile_mock.return_value = True

    # Check st_dev
    exists_mock.return_value = True

    # It should fail since devices are not the same
    first = os.stat_result((0, 0, 123, 0, 0, 0, 0, 0, 0, 0))
    second = os.stat_result((0, 0, 456, 0, 0, 0, 0, 0, 0, 0))
    stat_mock.side_effect = [first, second]

    with pytest.raises(tzupdate.TimezoneUpdateException):
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch("tzupdate.os.replace")
@mock.patch("tzupdate.os.path.isfile")
@mock.patch("tzupdate.os.path.exists")
@mock.patch("tzupdate.os.stat")
@mock.patch("tzupdate.os.symlink")
def test_link_localtime_mounts_same(
    symlink_mock, stat_mock, exists_mock, isfile_mock, replace_mock
):
    isfile_mock.return_value = True

    # Check st_dev
    exists_mock.return_value = True

    # It shouldn't fail since devices are the same
    first = os.stat_result((0, 0, 123, 0, 0, 0, 0, 0, 0, 0))
    second = os.stat_result((0, 0, 123, 0, 0, 0, 0, 0, 0, 0))
    stat_mock.side_effect = [first, second]

    expected = os.path.join(tzupdate.DEFAULT_ZONEINFO_PATH, FAKE_TIMEZONE)

    zoneinfo_tz_path = tzupdate.link_localtime(
        FAKE_TIMEZONE, tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH
    )

    assert zoneinfo_tz_path == expected


@given(text())
def test_link_localtime_traversal_attack_root(questionable_timezone):
    assume(tzupdate.DEFAULT_ZONEINFO_PATH not in questionable_timezone)
    questionable_timezone = "/" + questionable_timezone

    with pytest.raises(tzupdate.DirectoryTraversalError):
        tzupdate.link_localtime(
            questionable_timezone,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@given(text())
def test_link_localtime_traversal_attack_dotdot(questionable_timezone):
    assume(tzupdate.DEFAULT_ZONEINFO_PATH not in questionable_timezone)
    questionable_timezone = "../../../" + questionable_timezone

    with pytest.raises(tzupdate.DirectoryTraversalError):
        tzupdate.link_localtime(
            questionable_timezone,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch("tzupdate.os.path.isfile")
def test_link_localtime_timezone_not_available(isfile_mock):
    isfile_mock.return_value = False
    with pytest.raises(tzupdate.TimezoneNotLocallyAvailableError):
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )


@mock.patch("tzupdate.os.symlink")
@mock.patch("tzupdate.os.path.isfile")
def test_link_localtime_permission_denied(isfile_mock, symlink_mock):
    isfile_mock.return_value = True
    symlink_mock.side_effect = OSError(errno.EACCES, "Permission denied yo")
    with pytest.raises(OSError) as raise_cm:
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )

    assert raise_cm.value.errno == errno.EACCES


@mock.patch("tzupdate.os.symlink")
@mock.patch("tzupdate.os.path.isfile")
def test_link_localtime_oserror_not_permission(isfile_mock, symlink_mock):
    isfile_mock.return_value = True
    code = errno.ENOSPC
    symlink_mock.side_effect = OSError(code, "No space yo")

    with pytest.raises(OSError) as thrown_exc:
        tzupdate.link_localtime(
            FAKE_TIMEZONE,
            tzupdate.DEFAULT_ZONEINFO_PATH,
            tzupdate.DEFAULT_LOCALTIME_PATH,
        )

    assert thrown_exc.value.errno == code


@given(text(), text())
def test_debian_tz_path_exists_not_forced(timezone, tz_path):
    mo = mock.mock_open()
    with mock.patch("tzupdate.open", mo, create=True):
        tzupdate.write_debian_timezone(timezone, tz_path, must_exist=True)
        mo.assert_called_once_with(tz_path, "r+")
        mo().seek.assert_called_once_with(0)
        mo().write.assert_called_once_with(timezone + "\n")


@given(text(), text())
def test_debian_tz_path_doesnt_exist_not_forced(timezone, tz_path):
    mo = mock.mock_open()
    mo.side_effect = OSError(errno.ENOENT, "")
    with mock.patch("tzupdate.open", mo, create=True):
        tzupdate.write_debian_timezone(timezone, tz_path, must_exist=True)
        mo.assert_called_once_with(tz_path, "r+")


@given(text(), text())
def test_debian_tz_path_other_error_raises(timezone, tz_path):
    mo = mock.mock_open()
    code = errno.EPERM
    mo.side_effect = OSError(code, "")
    with mock.patch("tzupdate.open", mo, create=True):
        with pytest.raises(OSError) as thrown_exc:
            tzupdate.write_debian_timezone(timezone, tz_path, must_exist=True)
        assert thrown_exc.value.errno == code


@given(text(), text())
def test_debian_tz_path_doesnt_exist_forced(timezone, tz_path):
    mo = mock.mock_open()
    with mock.patch("tzupdate.open", mo, create=True):
        tzupdate.write_debian_timezone(timezone, tz_path, must_exist=False)
        mo.assert_called_once_with(tz_path, "w")
        mo().seek.assert_called_once_with(0)
        mo().write.assert_called_once_with(timezone + "\n")
