`tzupdate` is a simple, fully automated `/etc/localtime` update utility. It
uses your WAN IP to geolocate you, and then link the appropriate zoneinfo file
for your location. 

# GeoNames API username

If you know that you are going to be making a lot of requests, *please* use your
own API username (you can pass the `username` argument when calling
`getTimeZoneFromCoords`).
