# original source code
# https://github.com/adafruit/micropython-adafruit-ht16k33

from micropython import const
import framebuf


_HT16K33_BLINK_CMD = const(0x80)
_HT16K33_BLINK_DISPLAYON = const(0x01)
_HT16K33_CMD_BRIGHTNESS = const(0xE0)
_HT16K33_OSCILATOR_ON = const(0x21)


class HT16K33:
    def __init__(self, i2c, address=0x70):
        self.i2c = i2c
        self.address = address
        self._temp = bytearray(1)

        self.buffer = bytearray(16)
        self._write_cmd(_HT16K33_OSCILATOR_ON)
        self.blink_rate(0)
        self.brightness(15)

    def _write_cmd(self, byte):
        self._temp[0] = byte
        self.i2c.writeto(self.address, self._temp)

    def blink_rate(self, rate=None):
        if rate is None:
            return self._blink_rate
        rate = rate & 0x03
        self._blink_rate = rate
        self._write_cmd(_HT16K33_BLINK_CMD |
                        _HT16K33_BLINK_DISPLAYON | rate << 1)

    def brightness(self, brightness):
        if brightness is None:
            return self._brightness
        brightness = brightness & 0x0F
        self._brightness = brightness
        self._write_cmd(_HT16K33_CMD_BRIGHTNESS | brightness)

    def show(self):
        self.i2c.writeto_mem(self.address, 0x00, self.buffer)


NUMBERS = {
    ' ': 0x00, # space
    '-': 0x40, # -
    '0': 0x3F, # 0
    '1': 0x06, # 1
    '2': 0x5B, # 2
    '3': 0x4F, # 3
    '4': 0x66, # 4
    '5': 0x6D, # 5
    '6': 0x7D, # 6
    '7': 0x07, # 7
    '8': 0x7F, # 8
    '9': 0x6F, # 9
    'a': 0x77, # A
    'b': 0x7C, # b
    'c': 0x39, # C
    'd': 0x5E, # d
    'e': 0x79, # E
    'f': 0x71, # F
    'g': 0x3D, # G
    'h': 0x74, # h
    'i': 0x30, # i
    'j': 0x1E, # J
    'k': 0x75, # K
    'l': 0x38, # L
    'm': 0x15, # M
    'n': 0x54, # n
    'o': 0x5C, # o
    'p': 0x73, # P
    'q': 0x67, # q
    'r': 0x50, # r
    's': 0x6D, # 5
    't': 0x78, # t
    'u': 0x1C, # u
    'v': 0x3E, # U
    'w': 0x2A, # W
    'x': 0x76, # H
    'y': 0x6E, # y
    'z': 0x5B, # 2
}



class Seg7x4(HT16K33):
    P = [0, 2, 6, 8] #  The positions of characters.

    def scroll(self):
        for i in range(3):
            self.buffer[self.P[i]] = self.buffer[self.P[i + 1]]
        self.put(' ', 3)

    def push(self, char):
        if char in ':;':
            self.put(char)
        else:
            if char != '.' or self.buffer[8] & 0b10000000:
                self.scroll()
            self.put(char, 3)

    def put(self, char, index=0):
        if not 0 <= index <= 3:
            return
        char = char.lower()
        if char in NUMBERS:
            self.buffer[self.P[index]] = NUMBERS[char]
            return
        elif char == '.':
            self.buffer[self.P[index]] |= 0b10000000
            return
        elif char == ':':
            self.buffer[4] = 0x02
            return
        elif char == ';':
            self.buffer[4] = 0x00
            return

    def text(self, text):
        for c in text:
            self.push(c)
        return self
