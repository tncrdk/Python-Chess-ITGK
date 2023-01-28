from __future__ import annotations
from dataclasses import dataclass, field
from returns.maybe import Maybe, Some, Nothing
import copy
from typing import Type, Union
from abstract_types import (
    AbstractPoint,
    Color,
    Direction,
    UP,
    LEFT,
    DOWN,
    RIGHT,
    Index,
    Point,
)

OrthogonalDirections: list[Direction] = [
    UP,
    DOWN,
    RIGHT,
    LEFT,
]

DiagonalDirections: list[Direction] = [
    UP + RIGHT,
    UP + LEFT,
    DOWN + RIGHT,
    DOWN + LEFT,
]

JumpDirections: list[Direction] = [
    UP + UP + RIGHT,
    UP + UP + LEFT,
    DOWN + DOWN + RIGHT,
    DOWN + DOWN + LEFT,
    LEFT + LEFT + UP,
    LEFT + LEFT + DOWN,
    RIGHT + RIGHT + UP,
    RIGHT + RIGHT + DOWN,
]


class Board:
    def __init__(
        self,
        board_string: str = "RNBQKBNRPPPPPPPP".lower() + 32 * "." + "PPPPPPPPRNBQKBNR",
        length: int = 8,
        width: int = 8,
    ) -> None:
        self.width = width
        self.length = length
        self.board = self.create_board(board_string)

    def create_board(self, board_string: str) -> list[list[Maybe[AbstractPiece]]]:
        assert len(board_string) == self.length * self.width

        board = []
        for h in range(self.length):
            row = []
            for w in range(self.width):
                value = board_string[h * self.width + w]
                piece = self.string_to_piece(value)
                row.append(piece)

            board.append(row)

        return board

    def string_to_piece(self, value: str) -> Maybe[AbstractPiece]:
        color = Color.white if value.isupper() else Color.black
        match value.lower():
            case ".":
                return Nothing
            case "p":
                return Some(Pawn(color))
            case "r":
                return Some(Rook(color))
            case "n":
                return Some(Knight(color))
            case "b":
                return Some(Bishop(color))
            case "k":
                return Some(King(color))
            case "q":
                return Some(Queen(color))
            case _:
                raise ValueError(f"Dette representerer ikke en brikke: {value}")

    def is_empty_square(self, position: Point) -> bool:
        return self.get(position) == Nothing

    def get(self, position: Point) -> Maybe[AbstractPiece]:
        width_index, length_index = self.point_to_index(position)
        return self.board[length_index][width_index]

    def update_square(
        self,
        new_value: Maybe[AbstractPiece],
        position: Point,
    ) -> None:
        width_index, heigth_index = self.point_to_index(position)
        self.board[heigth_index][width_index] = new_value

    def point_to_index(self, position: Point) -> Index:
        sucess, err = self.index_within_board(position)
        if not sucess:
            raise ValueError(err)
        width = position[0] - 1
        height = self.length - position[1]
        return width, height

    def index_to_point(self, index: Index) -> Point:
        x = index[0] + 1
        y = self.length - index[1]
        valid, err = self.index_within_board((x, y))
        if not valid:
            raise ValueError(err)
        return (x, y)

    def index_within_board(self, position: Point) -> tuple[bool, str]:
        if not len(position) == 2:
            return (False, "Posisjonen må være nøyaktig to integers")
        width, length = position
        if not 1 <= width <= 8 or not 1 <= length <= self.length:
            return (False, f"Indeksen {position} er utenfor brettet")
        return (True, "")

    def __str__(self) -> str:
        horizontal_line = "  " + "-" * 33 + "\n"
        board_string = horizontal_line

        for row_num, row in enumerate(self.board):
            board_string += f"{self.length - row_num} |"

            for square_value in row:
                match square_value:
                    case Maybe.empty:
                        board_string += "   |"
                    case Some(piece):
                        board_string += f" {str(piece)} |"

            board_string += "\n"
            board_string += horizontal_line

        board_string += "    " + "   ".join(
            [i for i in "ABCDEFGH"],
        )
        return board_string


@dataclass
class AbstractPiece:
    color: Color
    symbol: str
    directions: list[Direction]
    has_moved: bool = False

    def __post_init__(self):
        if self.color == Color.white:
            self.symbol = self.symbol.upper()
        for direction in self.directions:
            direction.y *= self.color.value

    def __str__(self) -> str:
        return self.symbol

    @staticmethod
    def get_movements(
        board: Board, position: Point, directions: list[Direction], color: Color
    ) -> list[Point]:
        movements = []
        for direction in directions:
            beam = follow_direction(
                board,
                position,
                direction,
                color,
                max_distance=direction.reach,
                is_capture_direction=direction.is_capture_direction,
                must_capture=direction.must_capture,
            )
            movements += beam
        return movements

    def get_capture_movements(
        self, board: Board, position: Point, directions: list[Direction]
    ) -> list[Point]:
        capture_directions = [
            direction for direction in directions if direction.is_capture_direction
        ]
        return self.get_movements(board, position, capture_directions, self.color)

    def change_reach(self, new_reach: int):
        for direction in self.directions:
            direction.reach = new_reach


@dataclass
class Pawn(AbstractPiece):
    symbol: str = "p"
    directions: list[Direction] = field(
        default_factory=lambda: [
            Direction(0, 1, is_capture_direction=False, reach=2),
            Direction(1, 1, is_capture_direction=True, must_capture=True, reach=1),
            Direction(-1, 1, is_capture_direction=True, must_capture=True, reach=1),
        ]
    )


@dataclass
class Rook(AbstractPiece):
    symbol: str = "r"
    directions: list[Direction] = field(
        default_factory=lambda: copy.deepcopy(OrthogonalDirections)
    )


@dataclass
class Knight(AbstractPiece):
    symbol: str = "n"
    directions: list[Direction] = field(
        default_factory=lambda: copy.deepcopy(JumpDirections)
    )

    def __post_init__(self):
        super().__post_init__()
        self.change_reach(1)


@dataclass
class Bishop(AbstractPiece):
    symbol: str = "b"
    directions: list[Direction] = field(
        default_factory=lambda: copy.deepcopy(DiagonalDirections)
    )


@dataclass
class King(AbstractPiece):
    symbol: str = "k"
    directions: list[Direction] = field(
        default_factory=lambda: copy.deepcopy(DiagonalDirections + OrthogonalDirections)
    )

    def __post_init__(self):
        super().__post_init__()
        self.change_reach(1)


@dataclass
class Queen(AbstractPiece):
    symbol: str = "q"
    directions: list[Direction] = field(
        default_factory=lambda: copy.deepcopy(DiagonalDirections + OrthogonalDirections)
    )


ChessPieceType = Union[
    Type[Pawn], Type[King], Type[Queen], Type[Rook], Type[Knight], Type[Bishop]
]


@dataclass
class Player:
    name: str
    color: Color
    check_mate: bool = False

    def __post_init__(self):
        match self.color:
            case Color.white:
                self.king_position: Point = (5, 1)
            case Color.black:
                self.king_position: Point = (5, 8)

    def is_in_check(self, board: Board, king_position: Point) -> bool:
        ALL_PIECES: list[ChessPieceType] = [
            Pawn,
            King,
            Queen,
            Rook,
            Knight,
            Bishop,
        ]
        color = Color.white
        opp_color = Color.black

        match board.get(king_position):
            case Some(King(color=Color.white)):
                color = Color.white
                opp_color = Color.black
            case Some(King(color=Color.black)):
                color = Color.black
                opp_color = Color.white

        for piece_type in ALL_PIECES:
            piece = piece_type(color)
            for pos in piece.get_capture_movements(
                board, king_position, piece.directions
            ):
                square_value = board.get(pos)
                if square_value != Nothing:
                    opp_piece = square_value.unwrap()
                    if type(opp_piece) == type(piece) and opp_piece.color == opp_color:
                        return True
        return False


def follow_direction(
    board: Board,
    position: Point,
    direction: Direction,
    self_color: Color,
    max_distance: int = 0,
    is_capture_direction: bool = True,
    must_capture: bool = False,
) -> list[Point]:
    points: list[Point] = []
    i = 1
    while True:
        if max_distance != 0 and i > max_distance:
            return points

        position = add_direction(position, direction)
        valid_pos, _ = board.index_within_board(position)
        if not valid_pos:
            return points

        match board.get(position):
            case Some(piece):
                if piece.color == self_color or not is_capture_direction:
                    return points
                points.append(position)
                return points

            case Maybe.empty:
                if not must_capture:
                    points.append(position)
        i += 1


def add_direction(a: AbstractPoint, b: Direction) -> AbstractPoint:
    return (a[0] + b.x, a[1] + b.y)


if __name__ == "__main__":
    board = Board()
    print(board)
