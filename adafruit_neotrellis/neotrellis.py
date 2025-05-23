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

from __future__ import annotations


# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/georgeharker/Adafruit_CircuitPython_neotrellis.git"


from time import sleep
from typing import Callable, List, Optional, Sequence, Tuple

from adafruit_seesaw.keypad import (
    KeyEvent,
    Keypad,
    KeypadEdge,  # noqa: F401
    ResponseType,
)
from adafruit_seesaw.neopixel import ColorType, NeoPixel
from micropython import const


_NEO_TRELLIS_ADDR = const(0x2E)

_NEO_TRELLIS_NEOPIX_PIN = const(3)

_NEO_TRELLIS_NUM_ROWS = const(8)
_NEO_TRELLIS_NUM_COLS = const(8)
_NEO_TRELLIS_NUM_KEYS = const(64)

SYNC_DELAY = const(0.0005)
INIT_DELAY = const(0.0005)

type CallbackType = Callable[['NeoTrellis', KeyEvent], None]


class NeoTrellis(Keypad):
    """Driver for the Adafruit NeoTrellis."""

    width: int
    height: int
    x_base: int
    y_base: int
    pad_x: int
    pad_y: int
    callbacks: List[Optional[CallbackType]]
    pixels: NeoPixel

    def __init__(self, i2c_bus, interrupt: bool = False,
                 addr: int = _NEO_TRELLIS_ADDR, drdy=None,
                 width: int = _NEO_TRELLIS_NUM_COLS,
                 height: int = _NEO_TRELLIS_NUM_ROWS,
                 x_base: int = 0, y_base: int = 0,
                 pad_x: int = 0, pad_y: int = 0):
        super().__init__(i2c_bus, addr, drdy)
        self.width = width
        self.height = height
        self.x_base = x_base
        self.y_base = y_base
        self.interrupt_enabled = interrupt
        self.callbacks = [None] * _NEO_TRELLIS_NUM_KEYS
        self.pixels = NeoPixel(self, _NEO_TRELLIS_NEOPIX_PIN, self.width * self.height)
        sleep(INIT_DELAY)

    def activate_key(self, key:
                     int, edge:  # KeypadEdge
                     int, enable: bool = True) -> None:
        """Activate or deactivate a key on the trellis. Key is the key number from
           0 to 16. Edge specifies what edge to register an event on and can be
           NeoTrellis.EDGE_FALLING or NeoTrellis.EDGE_RISING. enable should be set
           to True if the event is to be enabled, or False if the event is to be
           disabled."""
        self.set_event(key, edge, enable)

    def clear(self) -> None:
        self.pixels.fill((0, 0, 0))

    def color(self, key: int, color: ColorType) -> None:
        """Set the color of the specified key """
        self.pixels[key] = color

    def update(self, updates: Sequence[Tuple[int, ColorType]]) -> None:
        """Set the color of the specified keys """
        self.pixels.update(updates)

    def show(self) -> None:
        self.pixels.show()

    def sync(self) -> None:
        """read any events from the Trellis hardware and call associated
           callbacks"""
        available = self.count
        sleep(SYNC_DELAY)       # FIXME: resolve
        if available > 0:
            buf = self.read_keypad(available)
            for r in buf:
                if r.response_type == ResponseType.TYPE_KEY:
                    evt = r.data_keyevent()
                    callback = self.callbacks[evt.number]
                    if (
                        callback is not None and
                        evt.number < _NEO_TRELLIS_NUM_KEYS
                    ):
                        callback(self, evt)

    def local_key_index(self, x: int, y: int) -> int:
        return int(y * self.width + x)

    def key_index(self, x: int, y: int) -> int:
        return int((y - self.y_base) * self.width + (x - self.x_base))

    def local_key_xy(self, key: int) -> Tuple[int, int]:
        return key % self.width, key // self.width

    def key_xy(self, key: int) -> Tuple[int, int]:
        return self.x_base + key % self.width, self.y_base + key // self.width
