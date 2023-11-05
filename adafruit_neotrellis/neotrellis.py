# The MIT License (MIT)
#
# Copyright (c) 2018 Dean Miller for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
``adafruit_neotrellis``
====================================================

4x4 elastomer buttons and RGB LEDs

* Author(s): Dean Miller

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

* Adafruit Seesaw CircuitPython library
  https://github.com/adafruit/Adafruit_CircuitPython_seesaw/releases
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_neotrellis.git"

from time import sleep
from micropython import const
from adafruit_seesaw.keypad import Keypad, KeyEvent
from adafruit_seesaw.neopixel import NeoPixel

_NEO_TRELLIS_ADDR = const(0x2E)

_NEO_TRELLIS_NEOPIX_PIN = const(3)

_NEO_TRELLIS_NUM_ROWS = const(8)
_NEO_TRELLIS_NUM_COLS = const(8)
_NEO_TRELLIS_NUM_KEYS = const(64)

_NEO_TRELLIS_MAX_CALLBACKS = const(64)


def _key(xval):
    return int(int(xval / 8) * 8 + (xval % 8))


def _seesaw_key(xval):
    return int(int(xval / 8) * 8 + (xval % 8))

class NeoTrellis(Keypad):
    """Driver for the Adafruit NeoTrellis."""

    def __init__(self, i2c_bus, interrupt=False, addr=_NEO_TRELLIS_ADDR, drdy=None):
        super().__init__(i2c_bus, addr, drdy)
        self.interrupt_enabled = interrupt
        self.callbacks = [None] * _NEO_TRELLIS_NUM_KEYS
        self.pixels = NeoPixel(self, _NEO_TRELLIS_NEOPIX_PIN, _NEO_TRELLIS_NUM_KEYS)

    def activate_key(self, key, edge, enable=True):
        """Activate or deactivate a key on the trellis. Key is the key number from
           0 to 16. Edge specifies what edge to register an event on and can be
           NeoTrellis.EDGE_FALLING or NeoTrellis.EDGE_RISING. enable should be set
           to True if the event is to be enabled, or False if the event is to be
           disabled."""
        self.set_event(_key(key), edge, enable)

    def sync(self):
        """read any events from the Trellis hardware and call associated
           callbacks"""
        available = self.count
        sleep(0.0005)
        if available > 0:
            available = available + 2
            buf = self.read_keypad(available)
            for response in buf:
                raw = response.data
                evt = KeyEvent(_seesaw_key((raw >> 2) & 0x3F), raw & 0x3)
                if (evt.number < _NEO_TRELLIS_NUM_KEYS and
                        self.callbacks[evt.number] is not None):
                    self.callbacks[evt.number](evt)

