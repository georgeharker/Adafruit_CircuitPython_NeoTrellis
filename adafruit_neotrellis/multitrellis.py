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
interface for connecting together multiple NeoTrellis boards.
"""

# imports

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/georgeharker/Adafruit_CircuitPython_neotrellis.git"

from dataclasses import dataclass
from typing import Callable, List, Optional, Sequence

from adafruit_seesaw.neopixel import ColorType

from adafruit_neotrellis.neotrellis import KeyEvent as SeesawKeyEvent
from adafruit_neotrellis.neotrellis import (
    KeypadEdge,  # noqa: F401
    NeoTrellis,
)


@dataclass
class KeyEvent:
    x: int
    y: int
    edge: int  # KeypadEdge


type CallbackType = Callable[[KeyEvent], None]


class MultiTrellis:
    """Driver for multiple connected Adafruit NeoTrellis boards."""

    _trelli: List[List[NeoTrellis]]
    _rows: int
    _cols: int
    _key_pads: List[List[NeoTrellis]]
    _callbacks: List[List[Optional[CallbackType]]]

    def __init__(self, neotrellis_array: List[List[NeoTrellis]]):
        self._trelli = neotrellis_array
        self._rows = len(neotrellis_array)
        self._cols = len(neotrellis_array[0])
        col_size_sum = [0 for _ in range(self._cols)]
        row_size_sum = [0 for _ in range(self._rows)]
        for py in range(self._rows):
            for px in range(self._cols):
                assert len(self._trelli[py]) == self._cols

                tr0 = self._trelli[0][px]
                tc0 = self._trelli[py][0]
                t = self._trelli[py][px]

                # All columns must have similar shape
                assert t.height == tc0.height
                # All rows must have similar shape
                assert t.width == tr0.width

                y_base = row_size_sum[py - 1] if py > 0 else 0
                x_base = col_size_sum[px - 1] if px > 0 else 0
                row_size_sum[py] = t.height + y_base
                col_size_sum[px] = t.width + x_base

                t.x_base = x_base
                t.y_base = y_base
                t.pad_x = px
                t.pad_y = py

        self._width = col_size_sum[self._cols - 1]
        self._height = row_size_sum[self._rows - 1]
        self._key_pads: List[List[NeoTrellis]] = []
        self._callbacks: List[List[Optional[CallbackType]]] = [
            [None for _ in range(self._width)] for _ in range(self._height)
        ]

        for _y in range(self._height):
            self._key_pads.append([])
        for py in range(self._rows):
            for px in range(self._cols):
                t = self._trelli[py][px]
                for ky in range(t.height):
                    y = t.y_base + ky
                    for _kx in range(t.width):
                        self._key_pads[y].append(t)

    @staticmethod
    def _callback_wrapper(t: NeoTrellis,
                          event: SeesawKeyEvent,
                          cb: CallbackType) -> None:
        x, y = t.key_xy(event.number)
        cb(KeyEvent(x=x, y=y, edge=event.edge))

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def rows(self):
        return self._rows

    @property
    def cols(self):
        return self._cols

    def __len__(self) -> int:
        return self._rows

    def __getitem__(self, subscript: int) -> Sequence[NeoTrellis]:
        return self._trelli[subscript]

    def get_keypad(self, x: int, y: int) -> NeoTrellis:
        return self._key_pads[y][x]

    @property
    def interrupt_enabled(self) -> bool:
        for py in range(self._rows):
            for px in range(self._cols):
                if not self._trelli[py][px].interrupt_enabled:
                    return False
        return True

    @interrupt_enabled.setter
    def interrupt_enabled(self, enabled: bool) -> None:
        for py in range(self._rows):
            for px in range(self._cols):
                self._trelli[py][px].interrupt_enabled = enabled

    def activate_key(self, x: int, y:
                     int, edge:  # KeypadEdge
                     int, enable: bool = True):
        """Activate or deactivate a key on the trellis. x and y are the index
        of the key measured from the top lefthand corner. Edge specifies what
        edge to register an event on and can be NeoTrellis.EDGE_FALLING or
        NeoTrellis.EDGE_RISING. enable should be set to True if the event is
        to be enabled, or False if the event is to be disabled."""
        pad = self._key_pads[y][x]
        pad.activate_key(pad.key_index(x, y), edge, enable)

    def set_callback(self, x: int, y: int, function: CallbackType):
        """Set a callback function for when an event for the key at index x, y
        (measured from the top lefthand corner) is detected."""
        pad = self._key_pads[y][x]
        self._callbacks[y][x] = function
        pad.callbacks[pad.key_index(x, y)] = lambda t, e: self._callback_wrapper(t, e, function)

    def get_callback(self, x: int, y: int) -> Optional[CallbackType]:
        """Get a callback function for when an event for the key at index x, y
        (measured from the top lefthand corner) is detected."""
        return self._callbacks[y][x]

    def color(self, x: int, y: int, color: ColorType):
        """Set the color of the pixel at index x, y measured from the top
        lefthand corner of the matrix"""
        pad = self._key_pads[y][x]
        pad.pixels[pad.key_index(x, y)] = color

    @property
    def data_pending(self) -> bool:
        for py in range(self._rows):
            for px in range(self._cols):
                available = self._trelli[py][px].count
                if available > 0:
                    return True
        return False

    def sync(self) -> None:
        """Read all trellis boards in the matrix and call any callbacks"""
        for py in range(self._rows):
            for px in range(self._cols):
                self._trelli[py][px].sync()

    def pixels_updated(self) -> None:
        """To be called after pixels are updated"""
        pass
