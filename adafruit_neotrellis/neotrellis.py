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
from typing import List, Callable
from micropython import const
from adafruit_seesaw.keypad import Keypad, KeyEvent, SeesawKeyResponse, ResponseType
from adafruit_seesaw.neopixel import NeoPixel

_NEO_TRELLIS_ADDR = const(0x2E)

_NEO_TRELLIS_NEOPIX_PIN = const(3)

_NEO_TRELLIS_NUM_ROWS = const(8)
_NEO_TRELLIS_NUM_COLS = const(8)
_NEO_TRELLIS_NUM_KEYS = const(64)

class NeoTrellis(Keypad):
    """Driver for the Adafruit NeoTrellis."""

    width: int
    height: int
    x_base: int
    y_base: int
    interrupt_enabled: bool
    callbacks: List[Callable[[KeyEvent], None]]
    pixels: List[NeoPixel]

    def __init__(self, i2c_bus, interrupt=False,
                 addr=_NEO_TRELLIS_ADDR, drdy=None,
                 width=_NEO_TRELLIS_NUM_COLS,
                 height=_NEO_TRELLIS_NUM_ROWS,
                 x_base = 0, y_base = 0):
        super().__init__(i2c_bus, addr, drdy)
        self.width = width
        self.height = height
        self.x_base = x_base
        self.y_base = y_base
        self.interrupt_enabled = interrupt
        self.callbacks = [None] * _NEO_TRELLIS_NUM_KEYS
        self.pixels = NeoPixel(self, _NEO_TRELLIS_NEOPIX_PIN, _NEO_TRELLIS_NUM_KEYS)

    def activate_key(self, key, edge, enable=True):
        """Activate or deactivate a key on the trellis. Key is the key number from
           0 to 16. Edge specifies what edge to register an event on and can be
           NeoTrellis.EDGE_FALLING or NeoTrellis.EDGE_RISING. enable should be set
           to True if the event is to be enabled, or False if the event is to be
           disabled."""
        self.set_event(key, edge, enable)

    def clear(self):
        self.pixels.fill((0, 0, 0))

    def sync(self):
        """read any events from the Trellis hardware and call associated
           callbacks"""
        available = self.count
        sleep(0.0005)       # FIXME: resolve
        if available > 0:
            buf = self.read_keypad(available)
            for r in buf:
                if r.response_type == ResponseType.TYPE_KEY:
                    (e, n) = r.data_edge_num()
                    evt = KeyEvent(n, e)
                    if (
                        evt.number < _NEO_TRELLIS_NUM_KEYS
                        and self.callbacks[evt.number] is not None
                    ):
                        self.callbacks[evt.number](evt)

    def local_key_index(self, x, y):
        return int(y * self.width + x)

    def key_index(self, x, y):
        return int((y - self.y_base) * self.width + (x - self.x_base))

