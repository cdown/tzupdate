Automatic timezone change detection with NetworkManager
=======================================================

The ``09-timezone`` script can be placed in the
``/etc/NetworkManager/dispatcher.d/`` folder. This script will automatically
launch tzupdate upon network connection. The user will therefore be prompted to
change the system timezone whenever the system connects to a network in a
different timezone. You also need a notification server with action support
like ``xfce4-notifyd`` for instance.
