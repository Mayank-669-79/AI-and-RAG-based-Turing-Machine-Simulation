"""Mutable, finite representation of a two-way-infinite TM tape."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Tape:
    """Tape cells with automatic blank expansion at either boundary.

    ``head_position`` is an index into ``cells`` and is always kept in range.
    Moving left from index zero prepends a blank and leaves the head at zero.
    """

    input_string: str = ""
    blank_symbol: str = "B"
    cells: list[str] = field(init=False)
    head_position: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.blank_symbol, str) or not self.blank_symbol:
            raise ValueError("blank_symbol must be a non-empty string")
        if not isinstance(self.input_string, str):
            raise TypeError("input_string must be a string")
        self.cells = list(self.input_string) or [self.blank_symbol]

    def read(self) -> str:
        return self.cells[self.head_position]

    def write(self, symbol: str) -> None:
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("symbol must be a non-empty string")
        self.cells[self.head_position] = symbol

    def move(self, direction: str) -> None:
        direction = direction.upper()
        if direction == "L":
            if self.head_position == 0:
                self.cells.insert(0, self.blank_symbol)
            else:
                self.head_position -= 1
        elif direction == "R":
            self.head_position += 1
            if self.head_position == len(self.cells):
                self.cells.append(self.blank_symbol)
        elif direction != "S":
            raise ValueError("direction must be 'L', 'R', or 'S'")

    def snapshot(self) -> list[str]:
        """Return a copy safe to include in a JSON trace."""
        return self.cells.copy()
