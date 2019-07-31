#!/usr/bin/env python

"""
Set the system timezone based on IP geolocation.
"""

from __future__ import print_function

from multiprocessing import Queue, Process
import argparse
import collections
import errno
import logging
import os
import sys

import requests

try:
    from queue import Empty
except ImportError:  # Python 2 fallback
    from Queue import Empty

log = logging.getLogger(__name__)

DEFAULT_ZONEINFO_PATH = "/usr/share/zoneinfo"
DEFAULT_LOCALTIME_PATH = "/etc/localtime"
DEFAULT_DEBIAN_TIMEZONE_PATH = "/etc/timezone"


# url: A url with an "ip" key to be replaced with an optional IP
# tz_keys: The key hierarchy to get the timezone from
# error_keys: Optionally, where to get error messages from
GeoIPService = collections.namedtuple("GeoIPService", ["url", "tz_keys", "error_keys"])

SERVICES = frozenset(
    [
        GeoIPService("http://ip-api.com/json/{ip}", ("timezone",), ("message",)),
        GeoIPService("https://freegeoip.app/json/{ip}", ("time_zone",), None),
        GeoIPService("https://ipapi.co/{ip}/json/", ("timezone",), ("reason",)),
        GeoIPService("http://worldtimeapi.org/api/ip/{ip}", ("timezone",), ("error",)),
    ]
)


def get_deep(item, keys):
    tmp = item
    for key in keys:
        tmp = tmp[key]
    return tmp


def get_timezone(ip, timeout=5.0, services=SERVICES):
    q = Queue()

    threads = [
        Process(target=get_timezone_for_ip, args=(ip, svc, q)) for svc in services
    ]

    for t in threads:
        t.start()

    try:
        timezone = q.get(block=True, timeout=timeout)
    except Empty:
        raise TimezoneAcquisitionError(
            "No usable response from any API in {} seconds".format(timeout)
        )
    finally:
        for t in threads:
            t.terminate()

    return timezone


def get_timezone_for_ip(ip, service, queue_obj):
    api_url = service.url.format(ip=ip or "")
    api_response_obj = requests.get(api_url)

    if not api_response_obj.ok:
        log.warning("%s returned %d, ignoring", api_url, api_response_obj.status_code)
        return

    api_response = requests.get(api_url).json()
    log.debug("API response from %s: %r", api_url, api_response)

    try:
        tz = get_deep(api_response, service.tz_keys)
        if not tz:
            raise KeyError
    except KeyError:
        msg = "Unspecified API error for {}.".format(service.url)
        if service.error_keys is not None:
            try:
                msg = get_deep(api_response, service.error_keys)
            except KeyError:
                pass
        log.warning("%s failed: %s", api_url, msg)
    else:
        queue_obj.put(tz)


def write_debian_timezone(timezone, debian_timezone_path, must_exist=True):
    """
    Debian and derivatives also have /etc/timezone, which is used for a human
    readable timezone. Without this, dpkg-reconfigure will nuke /etc/localtime
    on reconfigure.

    If must_exist is True, we won't create debian_timezone_path if it doesn't
    already exist.
    """
    old_umask = os.umask(0o133)
    mode = "w"

    if must_exist:
        mode = "r+"

    try:
        with open(debian_timezone_path, mode) as debian_tz_f:
            debian_tz_f.seek(0)
            debian_tz_f.write(timezone + "\n")
    except OSError as thrown_exc:
        if must_exist and thrown_exc.errno == errno.ENOENT:
            return
        raise
    finally:
        os.umask(old_umask)


def check_directory_traversal(base_dir, requested_path):
    """
    Check for directory traversal, and raise an exception if it was detected.

    Since we are linking based upon the output of some data we retrieved over
    the internet, we should check that it doesn't attempt to do something
    naughty with local path traversal.

    This function checks that the base directory of the zoneinfo database
    shares a common prefix with the absolute path of the requested zoneinfo
    file.
    """
    log.debug("Checking for traversal in path %s", requested_path)
    requested_path_abs = os.path.abspath(requested_path)
    log.debug("Absolute path of requested path is %s", requested_path_abs)
    if os.path.commonprefix([base_dir, requested_path_abs]) != base_dir:
        raise DirectoryTraversalError(
            "%r (%r) is outside base directory %r, refusing to run"
            % (requested_path, requested_path_abs, base_dir)
        )


def link_localtime(timezone, zoneinfo_path, localtime_path):
    """
    Link a timezone file from the zoneinfo database to /etc/localtime.

    Since we may be retrieving the timezone file's relative path from an
    untrusted source, we also do checks to make sure that no directory
    traversal is going on. See `check_directory_traversal` for information
    about how that works.
    """
    zoneinfo_tz_path = os.path.join(zoneinfo_path, timezone)
    check_directory_traversal(zoneinfo_path, zoneinfo_tz_path)

    if not os.path.isfile(zoneinfo_tz_path):
        raise TimezoneNotLocallyAvailableError(
            'Timezone "%s" requested, but this timezone is not available on '
            "your operating system." % timezone
        )

    try:
        os.unlink(localtime_path)
    except OSError as thrown_exc:
        # If we don't have permission to unlink /etc/localtime, we probably
        # need to be root.
        if thrown_exc.errno == errno.EACCES:
            raise OSError(
                thrown_exc.errno,
                'Could not link "%s" (%s). Are you root?'
                % (localtime_path, thrown_exc),
            )
        if thrown_exc.errno != errno.ENOENT:
            raise

    os.symlink(zoneinfo_tz_path, localtime_path)

    return zoneinfo_tz_path


def get_sys_timezone(zoneinfo_abspath, localtime_abspath):
    return localtime_abspath.replace(
        os.path.commonprefix([zoneinfo_abspath, localtime_abspath]) + os.path.sep, "", 1
    )


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-p",
        "--print-only",
        action="store_true",
        help="print the timezone, but don't update the localtime file",
    )
    parser.add_argument(
        "--print-system-timezone",
        action="store_true",
        help="print the current system timezone",
    )
    parser.add_argument(
        "-a", "--ip", help="use this IP instead of automatically detecting it"
    )
    parser.add_argument(
        "-t",
        "--timezone",
        help="use this timezone instead of automatically detecting it",
    )
    parser.add_argument(
        "-z",
        "--zoneinfo-path",
        default=DEFAULT_ZONEINFO_PATH,
        help="path to root of the zoneinfo database (default: %(default)s)",
    )
    parser.add_argument(
        "-l",
        "--localtime-path",
        default=DEFAULT_LOCALTIME_PATH,
        help="path to localtime symlink (default: %(default)s)",
    )
    parser.add_argument(
        "-d",
        "--debian-timezone-path",
        default=DEFAULT_DEBIAN_TIMEZONE_PATH,
        help="path to Debian timezone name file (default: %(default)s)",
    )
    parser.add_argument(
        "--always-write-debian-timezone",
        action="store_true",
        help="create debian timezone file even if it doesn't exist (default: %(default)s)",
    )
    parser.add_argument(
        "-s",
        "--timeout",
        help="maximum number of seconds to wait for APIs to return (default: "
        "%(default)s)",
        type=float,
        default=5.0,
    )
    parser.add_argument(
        "--debug",
        action="store_const",
        dest="log_level",
        const=logging.DEBUG,
        default=logging.WARNING,
        help="enable debug logging",
    )
    args = parser.parse_args(argv)
    return args


def main(argv=None, services=SERVICES):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    logging.basicConfig(level=args.log_level)

    if args.print_system_timezone:
        print(
            get_sys_timezone(
                os.path.realpath(args.zoneinfo_path),
                os.path.realpath(args.localtime_path),
            )
        )
        return

    if args.timezone:
        timezone = args.timezone
        log.debug("Using explicitly passed timezone: %s", timezone)
    else:
        timezone = get_timezone(args.ip, timeout=args.timeout, services=services)

    if args.print_only:
        print(timezone)
    else:
        link_localtime(timezone, args.zoneinfo_path, args.localtime_path)
        write_debian_timezone(
            timezone, args.debian_timezone_path, not args.always_write_debian_timezone
        )
        print("Set system timezone to %s." % timezone)


class TimezoneUpdateException(Exception):
    """
    Base class for exceptions raised by tzupdate.
    """


class TimezoneNotLocallyAvailableError(TimezoneUpdateException):
    """
    Raised when the API returned a timezone, but we don't have it locally.
    """


class DirectoryTraversalError(TimezoneUpdateException):
    """
    Raised when the timezone path returned by the API would result in directory
    traversal when concatenated with the zoneinfo path.
    """


class TimezoneAcquisitionError(TimezoneUpdateException):
    """
    Raised when all timezone APIs do not return in a timely manner.
    """


if __name__ == "__main__":
    main()
