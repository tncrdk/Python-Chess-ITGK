from dataclasses import dataclass
import typing
import enum

Point: typing.TypeAlias = tuple[int, int]
Index: typing.TypeAlias = tuple[int, int]
AbstractPoint: typing.TypeAlias = typing.Union[Point, Index]


class Color(enum.Enum):
    white = 1
    black = -1


@dataclass
class Direction:
    x: int
    y: int
    is_capture_direction: bool = True
    must_capture: bool = False
    reach: int = 0

    def __add__(self, other):
        return Direction(self.x + other.x, self.y + other.y)

    def __mul__(self, other: int):
        return Direction(self.x * other, self.y * other)


UP = Direction(0, 1)
DOWN = UP * (-1)
RIGHT = Direction(1, 0)
LEFT = RIGHT * (-1)
