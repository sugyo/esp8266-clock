import gc
from machine import I2C, Pin
from micropython import const
import ntptime
import time
import utime

import config

from HT16K33 import Seg7x4

from sta_network import STANetwork


ntptime.NTP_DELTA -= config.TIMEZONE
ntptime.host = config.NTPSERVER

TM_YEAR = const(0)
TM_MON = const(1)
TM_MDAY = const(2)
TM_HOUR = const(3)
TM_MIN = const(4)
TM_SEC = const(5)


class SevenSegmentDisplay:
    def __init__(self, scl=2, sda=0):
        self.i2c = I2C(scl=Pin(scl), sda=Pin(sda))
        self.seg7x4 = Seg7x4(self.i2c)
        self.seg7x4.brightness(1)
        self.clear()

    def text(self, s):
        self.seg7x4.put(';')  # colon off
        self.seg7x4.text(s)
        self.seg7x4.show()

    def time(self, now, sync_error=False):
        self.seg7x4.put(':' if now[TM_SEC] % 2 == 0 else ';')
        self.seg7x4.text('{:0>2d}{:0>2d}'.format(now[TM_HOUR], now[TM_MIN]))
        if sync_error:
            self.seg7x4.put('.', 3)

        # index = int(now[TM_SEC] / 15)
        # mod = now[TM_SEC] % 15
        # if mod < 12 or now[TM_SEC] % 2 == 0:
        #     self.seg7x4.put('.', index)

        n = now[TM_SEC] + 4
        for i in range(4):
            if n & (0b0100 << (3 - i)):
                self.seg7x4.put('.', i)

        self.seg7x4.show()

    def date(self, now):
        self.text('{:0>2d}.{:0>2d}'.format(now[TM_MON], now[TM_MDAY]))

    def year(self, now):
        self.text('{:0>4d}'.format(now[TM_YEAR]))

    def progress_bar(self, count):
        bar = '----    '[4 - (count % 5):]
        self.text(bar[:4])

    def clear(self):
        self.seg7x4.put(';')
        for i in range(3):
            self.seg7x4.put(' ', i)
        self.seg7x4.show()


class TimeSync:
    def __init__(self, display):
        self._display = display
        self._network = STANetwork()
        self._request_sync = False
        self.error = False

    def sync(self):
        self._progress_count = 0
        self._sync(progress=self._progress_bar)

    def _progress_bar(self):
        self._display.progress_bar(self._progress_count)
        time.sleep_ms(200)
        self._progress_count += 1

    def _sync(self, progress=None):
        self._network.safe_connect(progress=progress)
        if self._network.is_connected():
            self._display.text('sync')
            ntptime.settime()
            self._network.disconnect()
            self._request_sync = False
            self.error = False
        elif self._network.is_timeout():
            self._display.text('err ')
            self._network.disconnect()
            self._request_sync = False
            self.error = True
            time.sleep_ms(500)
        else:  # connecting
            self._request_sync = True
            self.error = False

    def request(self):
        self._request_sync = True

    def run(self):
        if self._request_sync:
            self._sync()


class Cron:
    def __init__(self):
        self._cron = []
        self._minutely_guard = False

    def add(self, cron):
       self._cron.append(cron)

    def run(self, now):
        # allow delay
        delay_max = 6
        if now[TM_SEC] < delay_max:
            if not self._minutely_guard:
                self._minutely(now)
                self._minutely_guard = True
        elif self._minutely_guard:
            self._minutely_guard = False

    def _minutely(self, now):
        for cron in self._cron:
            minutely = getattr(cron, 'minutely', None)
            if callable(minutely):
                cron.minutely(now)
        if now[TM_MIN] == 0:
            self._hourly(now)

    def _hourly(self, now):
        for cron in self._cron:
            hourly = getattr(cron, 'hourly', None)
            if callable(hourly):
                cron.hourly(now)
        if now[TM_HOUR] == 2:
            self._daily(now)

    def _daily(self, now):
        for cron in self._cron:
            daily = getattr(cron, 'daily', None)
            if callable(daily):
                cron.daily(now)


class DigitalClock:
    _DISPLAY_TIME = 0
    _DISPLAY_YEAR = 1
    _DISPLAY_DATE = 2
    _DISPLAY_GUARD = 3

    def __init__(self):
        self._display = SevenSegmentDisplay()
        self._cron = Cron()
        self._timesync = TimeSync(self._display)

    def start(self):
        self._cron.add(self)
        self._timesync.sync()

        self._next_run = self._DISPLAY_TIME
        while True:
            now = time.localtime()
            self._run(now)
            self._cron.run(now)
            self._timesync.run()
            time.sleep_ms(1000)

    def _run(self, now):
        interval = 5
        if self._next_run == self._DISPLAY_TIME:
            if now[TM_MIN] % interval == 0:
                self._display.year(now)
                self._next_run = self._DISPLAY_DATE
            else:
                self._display.time(now, self._timesync.error)

        elif self._next_run == self._DISPLAY_DATE:
            self._display.date(now)
            self._next_run = self._DISPLAY_GUARD

        elif self._next_run == self._DISPLAY_GUARD:
            self._display.time(now, self._timesync.error)
            if now[TM_MIN] % interval != 0:
                self._next_run = self._DISPLAY_TIME

    def hourly(self, now):
        if self._timesync.error:
            self._timesync.request()

    def daily(self, now):
        self._timesync.request()
        gc.collect()
