from objects import (
    Board,
    AbstractPiece,
    Player,
    King,
    Pawn,
    Queen,
    Bishop,
    Knight,
    Rook,
)
from abstract_types import Color, Point
from typing import Callable
from returns.maybe import Maybe, Some, Nothing
from returns.pointfree import bind
from returns.result import Result, Success, Failure
from returns import pipeline
from functools import partial
import sys
import os


def run_chess(board: Board = Board()):
    check_mate = False
    name1 = input("Player1 navn? ")
    name2 = input("Player2 navn? ")
    players = [Player(name1, Color.white), Player(name2, Color.black)]
    captured_pieces: dict[Color, list[AbstractPiece]] = {Color.black: [], Color.white: []}

    while not check_mate:
        for player in players:
            os.system("cls")
            print(board)
            print(f"{player.name} sitt trekk:".upper())
            take_turn(board, player, captured_pieces)
            check_mate = is_check_mate(board, players)
            if check_mate:
                break

    return players


def is_check_mate(board: Board, players: list[Player]) -> bool:
    for player in players:
        in_check = player.is_in_check(board, player.king_position)
        no_moves = get_legal_moves(board, player.king_position, player) == []
        if in_check and no_moves:
            player.check_mate = True
            return True
    return False


def take_turn(
    board: Board, player: Player, captured_pieces: dict[Color, list[AbstractPiece]]
) -> None:
    old_position, new_position = get_player_move(board, player)

    captured_piece = board.get(new_position)
    if captured_piece != Nothing:
        update_captured_pieces(captured_piece.unwrap(), captured_pieces, player)
    move_piece(board, old_position, new_position, player)


def take_player_input(
    prompt_string: str, validation_func: Callable[[Point], Result[Point, str]]
) -> Point:
    while True:
        player_input: Result[Point, str] = pipeline.flow(
            input(prompt_string),
            check_input_string,
            bind(convert_input),
            bind(validation_func),
        )
        match player_input:
            case Failure(err):
                print(err)
            case Success(input_position):
                return input_position


def get_player_move(board: Board, player: Player) -> tuple[Point, Point]:
    validate_piece = partial(validate_piece_to_move, board=board, player=player)
    old_position = take_player_input("Hvilken brikke vil du flytte? ", validate_piece)

    validate_new_pos = partial(
        validate_place_to_move_to, old_position=old_position, board=board, player=player
    )
    new_position = take_player_input("Hvor vil du flytte brikken? ", validate_new_pos)

    return old_position, new_position


def validate_place_to_move_to(
    position: Point,
    old_position: Point,
    board: Board,
    player: Player,
) -> Result[Point, str]:
    valid, err = board.index_within_board(position)
    if not valid:
        return Failure(err)

    match get_legal_moves(board, old_position, player):
        case []:
            return Failure("Brikken må kunne flyttes.")
        case other:
            legal_moves: list[Point] = other

    if not position in legal_moves:
        return Failure("Du må velge en gyldig rute å flytte til.")
    return Success(position)


def validate_piece_to_move(
    position: Point, board: Board, player: Player
) -> Result[Point, str]:
    valid, err = board.index_within_board(position)
    if not valid:
        return Failure(err)

    square_value = board.get(position)
    match square_value:
        case Maybe.empty:
            return Failure("Du må velge en rute med en brikke på.")
        case Some(piece):
            legal_piece: AbstractPiece = piece

    if legal_piece.color != player.color:
        return Failure("Brikken må være din egen.")
    if get_legal_moves(board, position, player) == []:
        return Failure("Brikken må kunne flyttes.")
    return Success(position)


def convert_input(player_input: tuple[str, str]) -> Result[Point, str]:
    string_x, y = player_input
    if string_x not in "abcdefgh":
        return Failure(f"Denne indeksen, {string_x}, er ikke gyldig.")

    x = "abcdefgh".find(string_x.lower()) + 1
    return Success((x, int(y)))


def check_input_string(input_string: str) -> Result[tuple[str, str], str]:
    match input_string.lower():
        case "quit" | "q" | "exit":
            sys.exit(0)
    if len(input_string) != 2:
        return Failure(f"Inputen kan ikke være {len(input_string)} lang.")
    string_x, y = tuple(input_string)
    if not y.isdigit():
        return Failure("Siste delen må være et tall.")
    return Success((string_x, y))


def get_legal_moves(board: Board, position: Point, player: Player) -> list[Point]:
    piece = board.get(position).unwrap()
    legal_movements = piece.get_movements(
        board, position, piece.directions, piece.color
    )
    legal_moves = [
        move
        for move in legal_movements
        if move_escapes_check(board, player, move, position)
    ]
    print(legal_moves)
    return legal_moves


def move_piece(
    board: Board, position: Point, new_position: Point, player: Player
) -> None:
    square_value = board.get(position)
    board.update_square(square_value, new_position)
    moved_piece = remove_piece(board, position)
    apply_effects(board, position, new_position, player, moved_piece)


def apply_effects(
    board: Board,
    position: Point,
    new_position: Point,
    player: Player,
    moved_piece: Maybe[AbstractPiece],
):
    match moved_piece:
        case Some(Pawn()):
            pawn = moved_piece.unwrap()
            pawn.change_reach(1)
            if pawn.color == Color.black and new_position[1] == 1:
                promote_piece(board, pawn.color, new_position)
            elif pawn.color == Color.white and new_position[1] == 8:
                promote_piece(board, pawn.color, new_position)
        case Some(King()):
            player.king_position = new_position


def promote_piece(board: Board, color: Color, position) -> None:
    while True:
        p = input(
            "Til hvilken brikke ønsker du å promotere brikken din? [q, b, r, n, p]: "
        )
        if not len(p) == 1:
            continue
        match p.lower():
            case "q":
                board.update_square(Some(Queen(color)), position)
                return
            case "b":
                board.update_square(Some(Bishop(color)), position)
                return
            case "r":
                board.update_square(Some(Rook(color)), position)
                return
            case "n":
                board.update_square(Some(Knight(color)), position)
                return
            case "p":
                board.update_square(Some(Pawn(color)), position)
                return
            case other:
                print(f"{other} er ikke et gyldig alternativ")


def update_captured_pieces(
    captured_piece: AbstractPiece,
    captured_pieces: dict[Color, list[AbstractPiece]],
    player: Player,
) -> None:
    match captured_piece:
        case AbstractPiece(color=Color.white):
            captured_pieces[Color.black].append(captured_piece)
        case AbstractPiece(color=Color.black):
            captured_pieces[Color.white].append(captured_piece)
        case _:
            raise ValueError("Denne brikken er ikke gyldig")


def remove_piece(board: Board, position: Point) -> Maybe[AbstractPiece]:
    square_value = board.get(position)
    board.update_square(Nothing, position)
    return square_value


def move_escapes_check(
    board: Board, player: Player, new_position: Point, old_position: Point
) -> bool:
    """Sjekker om et trekk kan redde kongen"""
    escapes_check = True
    # Apply simulation changes
    blocking_piece = remove_piece(board, new_position)
    piece = remove_piece(board, old_position)
    board.update_square(piece, new_position)

    # Check simulation
    match piece:
        case Some(King()):
            player.king_position = new_position
            if player.is_in_check(board, player.king_position):
                escapes_check = False
            player.king_position = old_position
        case _:
            if player.is_in_check(board, player.king_position):
                escapes_check = False

    # Reset changes
    remove_piece(board, new_position)
    board.update_square(blocking_piece, new_position)
    board.update_square(piece, old_position)
    return escapes_check


if __name__ == "__main__":
    board = Board()
