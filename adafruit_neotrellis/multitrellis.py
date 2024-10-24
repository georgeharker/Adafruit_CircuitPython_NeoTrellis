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
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_neotrellis.git"

from typing import List, Dict, Tuple, Sequence
from time import sleep
from micropython import const
from adafruit_neotrellis.neotrellis import NeoTrellis
from adafruit_seesaw.keypad import KeyEvent


class MultiTrellis:
    """Driver for multiple connected Adafruit NeoTrellis boards."""

    _trelli: List[List[NeoTrellis]]
    _rows: int
    _cols: int
    _key_pads: List[List[NeoTrellis]]

    def __init__(self, neotrellis_array):
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

        self._width = col_size_sum[self._cols - 1]
        self._height = row_size_sum[self._rows - 1]
        self._key_pads : List[List[NeoTrellis]] = [[None for _ in range(self._width)]
            for _ in range(self._height)]

        for py in range(self._rows):
            for px in range(self._cols):
                t = self._trelli[py][px]
                for ky in range(t.height):
                    for kx in range(t.width):
                        x = t.x_base + kx
                        y = t.y_base + ky
                        self._key_pads[y][x] = t

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def rows(self):
        return self._rowa

    @property
    def cols(self):
        return self._cols

    def __len__(self) -> int:
        return self._rows

    def __getitem__(self, subscript: int) -> Sequence[NeoTrellis]:
        return self._trelli[subscript]

    def get_key_pad(self, x: int, y: int) -> NeoTrellis:
        return self._key_pads[y][x]

    def activate_key(self, x, y, edge, enable=True):
        """Activate or deactivate a key on the trellis. x and y are the index
        of the key measured from the top lefthand corner. Edge specifies what
        edge to register an event on and can be NeoTrellis.EDGE_FALLING or
        NeoTrellis.EDGE_RISING. enable should be set to True if the event is
        to be enabled, or False if the event is to be disabled."""
        pad = self._key_pads[y][x]
        pad.activate_key(pad.key_index(x, y), enable)

    def set_callback(self, x, y, function):
        """Set a callback function for when an event for the key at index x, y
        (measured from the top lefthand corner) is detected."""
        pad = self._key_pads[y][x]
        pad.callbacks[pad.key_index(x, y)] = function

    def color(self, x, y, color):
        """Set the color of the pixel at index x, y measured from the top
        lefthand corner of the matrix"""
        pad = self._key_pads[y][x]
        pad.pixels[pad.key_index(x, y)] = color

    def sync(self):
        """Read all trellis boards in the matrix and call any callbacks"""
        for _n in range(self._rows):
            for _m in range(self._cols):

                _t = self._trelli[_n][_m]
                _t.sync()
