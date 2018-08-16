from micropython import const
import network
import time

import config


_TIMEOUT = const(30)


class STANetwork:
    def __init__(self):
        self._sta_if = network.WLAN(network.STA_IF)
        self._expires_at = None

    def __del__(self):
        if self._sta_if.active():
            self._sta_if.disconnect()
            self._sta_if.active(False)

    def safe_connect(self, timeout=None, progress=None):
        if self._sta_if.isconnected():
            # already connected
            self._expires_at = None
        elif self._expires_at is not None:
            # connecting
            pass
        else:
            # not connected
            if not timeout:
                timeout = _TIMEOUT
            self._connect(timeout=timeout, progress=progress)

    def _connect(self, timeout, progress=None):
        if not self._sta_if.active():
            self._sta_if.active(True)
        self._sta_if.connect(config.ESSID, config.PASSWORD)
        self._expires_at = time.time() + timeout

        if progress and callable(progress):
            while not self._sta_if.isconnected():
                if self.is_timeout():
                    break
                progress()
        if self._sta_if.isconnected():
            self._expires_at = None

    def disconnect(self):
        if self._sta_if.active():
            self._sta_if.disconnect()
            self._sta_if.active(False)
        self._expires_at = None

    def is_connected(self):
        connected = self._sta_if.isconnected()
        if connected:
            self._expires_at = None
        return connected

    def is_timeout(self):
        if self._expires_at is None:
            return False
        return self._expires_at < time.time()
