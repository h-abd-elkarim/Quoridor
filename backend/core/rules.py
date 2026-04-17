from __future__ import annotations
from dataclasses import dataclass
from typing import Union
from .board import Board, Position, Wall, WallOrientation, Direction, BOARD_SIZE
from .player import Player, PlayerID
from .game import GameState, GameStatus
from .pathfinding import bfs_has_path


# ---------------------------------------------------------------------------
# Types de coups
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class MoveAction:
    """Déplacement du pion vers une position cible."""
    destination: Position


@dataclass(frozen=True)
class WallAction:
    """Pose d'une barrière."""
    wall: Wall


Action = Union[MoveAction, WallAction]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class InvalidActionError(Exception):
    pass


def get_valid_moves(state: GameState) -> list[MoveAction]:
    """
    Retourne tous les déplacements valides pour le joueur courant.
    Gère les cas :
      1. Déplacement simple (case adjacente libre)
      2. Saut direct (adversaire adjacent, case derrière libre)
      3. Saut bifurqué (adversaire adjacent, barrière derrière → bifurcation latérale)
    """
    player = state.current_player
    opponent = state.opponent
    board = state.board
    moves: list[MoveAction] = []

    for direction in Direction:
        neighbor = player.position.neighbor(direction)

        if not neighbor.is_valid():
            continue
        if board.is_edge_blocked(player.position, neighbor):
            continue

        if neighbor == opponent.position:
            # L'adversaire est sur cette case → règles de saut
            jump_moves = _get_jump_moves(board, player.position, neighbor, direction)
            moves.extend(jump_moves)
        else:
            moves.append(MoveAction(destination=neighbor))

    return moves


def _get_jump_moves(
    board: Board,
    pawn: Position,
    opp: Position,
    direction: Direction,
) -> list[MoveAction]:
    """
    Calcule les cases atteignables après un saut par-dessus l'adversaire.
    - Si la case derrière l'adversaire est libre : saut direct.
    - Sinon (barrière ou bord) : bifurcation vers les cases latérales.
    """
    jump_moves: list[MoveAction] = []
    behind = opp.neighbor(direction)

    # Saut direct
    if behind.is_valid() and not board.is_edge_blocked(opp, behind):
        jump_moves.append(MoveAction(destination=behind))
        return jump_moves  # saut direct prioritaire, pas de bifurcation

    # Bifurcation latérale
    lateral_dirs = _lateral_directions(direction)
    for lat_dir in lateral_dirs:
        lateral = opp.neighbor(lat_dir)
        if lateral.is_valid() and not board.is_edge_blocked(opp, lateral):
            jump_moves.append(MoveAction(destination=lateral))

    return jump_moves


def _lateral_directions(direction: Direction) -> list[Direction]:
    """Retourne les deux directions perpendiculaires à `direction`."""
    if direction in (Direction.NORTH, Direction.SOUTH):
        return [Direction.EAST, Direction.WEST]
    return [Direction.NORTH, Direction.SOUTH]


def get_valid_walls(state: GameState) -> list[WallAction]:
    """
    Retourne toutes les poses de barrières valides pour le joueur courant.
    Conditions :
      1. Le joueur a encore des barrières
      2. La position est dans les limites du plateau
      3. La barrière ne chevauche pas une barrière existante
      4. Après pose, les deux joueurs ont encore un chemin vers leur objectif (BFS)
    """
    if state.current_player.walls_remaining == 0:
        return []

    valid_walls: list[WallAction] = []

    for row in range(BOARD_SIZE - 1):
        for col in range(BOARD_SIZE - 1):
            for orientation in WallOrientation:
                wall = Wall(Position(row, col), orientation)
                if not wall.is_valid():
                    continue
                if _wall_overlaps(wall, state.board):
                    continue

                # Test BFS sur une copie temporaire du board
                test_board = _board_with_wall(state.board, wall)
                p1 = state.players[PlayerID.ONE]
                p2 = state.players[PlayerID.TWO]

                if (
                    bfs_has_path(test_board, p1.position, p1.goal_row)
                    and bfs_has_path(test_board, p2.position, p2.goal_row)
                ):
                    valid_walls.append(WallAction(wall=wall))

    return valid_walls


def _wall_overlaps(wall: Wall, board: Board) -> bool:
    """
    Vérifie si les arêtes bloquées par `wall` sont déjà bloquées
    (chevauchement ou croisement de barrières).
    """
    new_edges = set(Board._wall_to_edges(wall))
    return bool(new_edges & board._blocked_edges)


def _board_with_wall(board: Board, wall: Wall) -> Board:
    """
    Retourne une copie légère du Board avec la barrière ajoutée.
    Évite un deepcopy complet — on ne copie que les ensembles de données.
    """
    from copy import copy
    new_board = copy(board)
    new_board.walls = set(board.walls)
    new_board._blocked_edges = set(board._blocked_edges)
    new_board.place_wall(wall)
    return new_board


# ---------------------------------------------------------------------------
# Application d'un coup
# ---------------------------------------------------------------------------

def apply_action(state: GameState, action: Action) -> GameState:
    """
    Applique une action validée sur un clone du GameState.
    Lève InvalidActionError si le coup est illégal.
    Retourne le nouvel état (immuable-friendly).
    """
    new_state = state.clone()

    if isinstance(action, MoveAction):
        valid_moves = get_valid_moves(state)
        if action not in valid_moves:
            raise InvalidActionError(f"Déplacement invalide : {action.destination}")
        new_state.current_player.position = action.destination
        new_state.current_player.move_history.append(
            _pos_to_notation(action.destination)
        )

    elif isinstance(action, WallAction):
        valid_walls = get_valid_walls(state)
        if action not in valid_walls:
            raise InvalidActionError(f"Barrière invalide : {action.wall}")
        new_state.board.place_wall(action.wall)
        new_state.current_player.walls_remaining -= 1
        new_state.current_player.move_history.append(
            _wall_to_notation(action.wall)
        )

    else:
        raise InvalidActionError(f"Type d'action inconnu : {type(action)}")

    new_state.check_victory()
    new_state.switch_turn()
    return new_state


def get_all_valid_actions(state: GameState) -> list[Action]:
    """
    Point d'entrée unique pour l'IA — retourne tous les coups légaux.
    Les mouvements sont listés en premier (priorité naturelle dans l'arbre).
    """
    if state.is_terminal():
        return []
    actions: list[Action] = []
    actions.extend(get_valid_moves(state))
    actions.extend(get_valid_walls(state))
    return actions


# ---------------------------------------------------------------------------
# Notation algébrique (pour move_history et logs)
# ---------------------------------------------------------------------------

def _pos_to_notation(pos: Position) -> str:
    """Convertit une position en notation Quoridor standard : e5, a1, i9..."""
    col_letter = chr(ord('a') + pos.col)
    row_number = pos.row + 1
    return f"{col_letter}{row_number}"


def _wall_to_notation(wall: Wall) -> str:
    """Notation : e5h (horizontal) ou e5v (vertical)."""
    base = _pos_to_notation(wall.position)
    suffix = "h" if wall.orientation == WallOrientation.HORIZONTAL else "v"
    return f"{base}{suffix}"
