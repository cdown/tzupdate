#!/usr/bin/env python

'''
Set the system timezone based on IP geolocation.
'''

from __future__ import print_function

import argparse
import os
import sys
import requests
from geolite2 import geolite2


class TimezoneUpdateException(Exception): pass
class TimezoneNotLocallyAvailableError(TimezoneUpdateException): exit_code = 1
class NoTimezoneAvailableError(TimezoneUpdateException): exit_code = 2


def get_public_ip():
    ipify_handle = requests.get('https://api.ipify.org')
    return ipify_handle.text


def get_timezone_for_ip(ip):
    geoip = geolite2.reader()
    ip_info = geoip.get(ip)
    timezone = ip_info['location'].get('time_zone')

    if timezone is None:
        raise NoTimezoneAvailableError('No timezone found for this IP.')

    return timezone


def link_localtime(timezone, zoneinfo_path, localtime_path):
    zoneinfo_tz_path = os.path.join(zoneinfo_path, timezone)

    if not os.path.isfile(zoneinfo_tz_path):
        raise TimezoneNotLocallyAvailableError(
            'Geolocation succeeded, returning timezone "%s", but this '
            'timezone is not available on your operating system.' % timezone
        )

    os.unlink(localtime_path)
    os.symlink(zoneinfo_tz_path, localtime_path)

    return zoneinfo_tz_path


def parse_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-p', '--print-only',
        action='store_true',
        help="print the timezone, but don't update the localtime file"
    )
    parser.add_argument(
        '-a', '--ip',
        help='use this IP instead of automatically detecting it'
    )
    parser.add_argument(
        "-z", "--zoneinfo-path",
        default='/usr/share/zoneinfo',
        help="path to root of the zoneinfo database (default: %(default)s)"
    )
    parser.add_argument(
        '-l', '--localtime-path',
        default='/etc/localtime',
        help='path to localtime symlink (default: %(default)s)'
    )
    args = parser.parse_args(argv)

    # We do this here instead of in "default" to avoid running it when we
    # already have an IP address manually specified.
    if args.ip is None:
        args.ip = get_public_ip()

    return args


def main(argv=sys.argv[1:]):
    args = parse_args(argv)

    timezone = get_timezone_for_ip(args.ip)
    print('Detected timezone is %s.' % timezone)

    if not args.print_only:
        zoneinfo_tz_path = link_localtime(
            timezone, args.zoneinfo_path, args.localtime_path,
        )
        print('Linked %s to %s.' % (args.localtime_path, zoneinfo_tz_path))


if __name__ == '__main__':
    try:
        main()
    except TimezoneUpdateException as thrown_exc:
        print(str(thrown_exc), file=sys.stderr)
        sys.exit(thrown_exc.exit_code)
