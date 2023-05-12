# tzupdate | [![Tests](https://img.shields.io/github/actions/workflow/status/cdown/tzupdate/ci.yml?branch=master)](https://github.com/cdown/tzupdate/actions?query=branch%3Amaster)

tzupdate is a fully automated utility to set the system time using geolocation.

## Features

- Small, easy to understand codebase
- Queries multiple geolocation services in parallel and returns the first with
  a successful result
- Protects against directory traversal and invalid results when linking
  /etc/localtime

## Installation

    cargo install tzupdate

## Usage

    # tzupdate
    Set system timezone to Europe/London.

Internally, this geolocates you, gets the timezone for that geolocation, and
then updates the system's local time zone.

You can see what tzupdate would do without actually doing it by passing `-p`,
and specify an alternative IP address by using `-i`. This is not an exhaustive
list of options, see `tzupdate --help` for that.
