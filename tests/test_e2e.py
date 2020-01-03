#!/usr/bin/env python

import httpretty
import tzupdate
import mock
import pytest
from tests._test_utils import FAKE_SERVICES, FAKE_TIMEZONE, setup_basic_api_response


@httpretty.activate
@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
def test_end_to_end_no_args(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    args = []
    tzupdate.main(args, services=FAKE_SERVICES)
    link_localtime_mock.assert_called_once_with(
        FAKE_TIMEZONE, tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH
    )
    deb_tz_mock.assert_called_once_with(
        FAKE_TIMEZONE, tzupdate.DEFAULT_DEBIAN_TIMEZONE_PATH, True
    )


@httpretty.activate
@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
def test_print_only_no_link(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    args = ["-p"]
    tzupdate.main(args, services=FAKE_SERVICES)
    assert not link_localtime_mock.called
    assert not deb_tz_mock.called


@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
def test_print_sys_tz_no_link(link_localtime_mock, deb_tz_mock):
    args = ["--print-system-timezone"]
    tzupdate.main(args, services=FAKE_SERVICES)
    assert not link_localtime_mock.called
    assert not deb_tz_mock.called


@httpretty.activate
@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
def test_explicit_paths(link_localtime_mock, deb_tz_mock):
    setup_basic_api_response()
    localtime_path = "/l"
    zoneinfo_path = "/z"
    deb_path = "/d"
    args = ["-l", localtime_path, "-z", zoneinfo_path, "-d", deb_path]
    tzupdate.main(args, services=FAKE_SERVICES)
    link_localtime_mock.assert_called_once_with(
        FAKE_TIMEZONE, zoneinfo_path, localtime_path
    )
    deb_tz_mock.assert_called_once_with(FAKE_TIMEZONE, deb_path, True)


@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
@mock.patch("tzupdate.get_timezone")
def test_explicit_ip(get_timezone_mock, _unused_ll, _unused_deb):
    ip_addr = "1.2.3.4"
    args = ["-a", ip_addr]
    tzupdate.main(args, services=FAKE_SERVICES)
    get_timezone_mock.assert_called_once_with(
        ip_addr, timeout=mock.ANY, services=FAKE_SERVICES
    )


@mock.patch("tzupdate.write_debian_timezone")
@mock.patch("tzupdate.link_localtime")
def test_explicit_timezone(link_localtime_mock, deb_tz_mock):
    timezone = "Foo/Bar"
    args = ["-t", timezone]
    tzupdate.main(args)
    link_localtime_mock.assert_called_once_with(
        timezone, tzupdate.DEFAULT_ZONEINFO_PATH, tzupdate.DEFAULT_LOCALTIME_PATH
    )
    deb_tz_mock.assert_called_once_with(
        timezone, tzupdate.DEFAULT_DEBIAN_TIMEZONE_PATH, True
    )


@httpretty.activate
@mock.patch("tzupdate.Process")
def test_timeout_results_in_exception(process_mock):
    # The process mock causes us to never run get_timezone_from_ip, so we
    # should time out
    setup_basic_api_response()
    args = ["-s", "0.01"]
    with pytest.raises(tzupdate.TimezoneAcquisitionError):
        tzupdate.main(args, services=FAKE_SERVICES)
