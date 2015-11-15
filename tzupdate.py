#!/usr/bin/env python

'''
Set the system timezone based on IP geolocation.
'''

from __future__ import print_function

import argparse
import os
import sys
import requests
import errno
import logging

log = logging.getLogger(__name__)

DEFAULT_ZONEINFO_PATH = '/usr/share/zoneinfo'
DEFAULT_LOCALTIME_PATH = '/etc/localtime'


class TimezoneUpdateException(Exception): exit_code = None
class TimezoneNotLocallyAvailableError(TimezoneUpdateException): exit_code = 1
class NoTimezoneAvailableError(TimezoneUpdateException): exit_code = 2
class DirectoryTraversalError(TimezoneUpdateException): exit_code = 3
class IPAPIError(TimezoneUpdateException): exit_code = 4
class LocaltimePermissionError(TimezoneUpdateException): exit_code = 5


def get_timezone_for_ip(ip_addr=None):
    '''
    Return the timezone for the specified IP, or if no IP is specified, use the
    current public IP address.
    '''

    api_url = 'http://ip-api.com/json/{ip}'.format(ip=ip_addr or '')
    log.debug('Making request to %s', api_url)
    api_response = requests.get(api_url).json()
    log.debug('API response: %r', api_response)
    try:
        return api_response['timezone']
    except KeyError:
        if api_response.get('status') == 'success':
            raise NoTimezoneAvailableError('No timezone found for this IP.')
        else:
            raise IPAPIError(
                api_response.get('message', 'Unspecified API error.'),
            )


def check_directory_traversal(base_dir, requested_path):
    '''
    Check for directory traversal, and raise an exception if it was detected.

    Since we are linking based upon the output of some data we retrieved over
    the internet, we should check that it doesn't attempt to do something
    naughty with local path traversal.

    This function checks that the base directory of the zoneinfo database
    shares a common prefix with the absolute path of the requested zoneinfo
    file.
    '''
    log.debug('Checking for traversal in path %s', requested_path)
    requested_path_abs = os.path.abspath(requested_path)
    log.debug('Absolute path of requested path is %s', requested_path_abs)
    if os.path.commonprefix([base_dir, requested_path_abs]) != base_dir:
        raise DirectoryTraversalError(
            '%r (%r) is outside base directory %r, refusing to run' % (
                requested_path, requested_path_abs, base_dir,
            )
        )


def link_localtime(timezone, zoneinfo_path, localtime_path):
    '''
    Link a timezone file from the zoneinfo database to /etc/localtime.

    Since we may be retrieving the timezone file's relative path from an
    untrusted source, we also do checks to make sure that no directory
    traversal is going on. See `check_directory_traversal` for information
    about how that works.
    '''
    zoneinfo_tz_path = os.path.join(zoneinfo_path, timezone)
    check_directory_traversal(zoneinfo_path, zoneinfo_tz_path)

    if not os.path.isfile(zoneinfo_tz_path):
        raise TimezoneNotLocallyAvailableError(
            'Geolocation succeeded, returning timezone "%s", but this '
            'timezone is not available on your operating system.' % timezone
        )

    try:
        os.unlink(localtime_path)
    except OSError as thrown_exc:
        # If we don't have permission to unlink /etc/localtime, we probably
        # need to be root.
        if thrown_exc.errno == errno.EACCES:
            raise LocaltimePermissionError(
                'Could not link "%s" (%s). Are you root?' % (
                    localtime_path, thrown_exc,
                )
            )
        else:
            raise

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
        '-t', '--timezone',
        help='use this timezone instead of automatically detecting it'
    )
    parser.add_argument(
        "-z", "--zoneinfo-path",
        default=DEFAULT_ZONEINFO_PATH,
        help="path to root of the zoneinfo database (default: %(default)s)"
    )
    parser.add_argument(
        '-l', '--localtime-path',
        default=DEFAULT_LOCALTIME_PATH,
        help='path to localtime symlink (default: %(default)s)'
    )
    parser.add_argument(
        '--debug',
        action="store_const", dest='log_level',
        const=logging.DEBUG, default=logging.WARNING,
        help='enable debug logging',
    )
    args = parser.parse_args(argv)
    return args


def run(args):
    if args.timezone:
        timezone = args.timezone
        print('Using explicitly passed timezone: %s' % timezone)
    else:
        timezone = get_timezone_for_ip(args.ip)
        print('Detected timezone is %s.' % timezone)

    if not args.print_only:
        zoneinfo_tz_path = link_localtime(
            timezone, args.zoneinfo_path, args.localtime_path,
        )
        print('Linked %s to %s.' % (args.localtime_path, zoneinfo_tz_path))


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    logging.basicConfig(level=args.log_level)

    try:
        run(args)
    except TimezoneUpdateException as thrown_exc:
        if args.log_level == logging.DEBUG:
            # Give the full traceback if we are in debug mode
            raise
        else:
            print('fatal: {0!s}'.format(thrown_exc), file=sys.stderr)
            sys.exit(thrown_exc.exit_code)


if __name__ == '__main__':
    main()
