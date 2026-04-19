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
    """Deplacement du pion vers une position cible."""
    destination: Position


@dataclass(frozen=True)
class WallAction:
    """Pose d'une barriere."""
    wall: Wall


Action = Union[MoveAction, WallAction]


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

class InvalidActionError(Exception):
    pass


def get_valid_moves(state: GameState) -> list[MoveAction]:
    """
    Retourne tous les deplacements valides pour le joueur courant.
    Gere les cas :
      1. Deplacement simple (case adjacente libre)
      2. Saut direct (adversaire adjacent, case derriere libre)
      3. Saut bifurque (adversaire adjacent, barriere derriere -> bifurcation laterale)
    """
    player   = state.current_player
    opponent = state.opponent
    board    = state.board
    moves: list[MoveAction] = []

    for direction in Direction:
        neighbor = player.position.neighbor(direction)
        if not neighbor.is_valid():
            continue
        if board.is_edge_blocked(player.position, neighbor):
            continue
        if neighbor == opponent.position:
            moves.extend(_get_jump_moves(board, player.position, neighbor, direction))
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
    Calcule les cases atteignables apres un saut par-dessus l'adversaire.
    - Si la case derriere l'adversaire est libre : saut direct.
    - Sinon (barriere ou bord) : bifurcation vers les cases laterales.
    """
    jump_moves: list[MoveAction] = []
    behind = opp.neighbor(direction)

    if behind.is_valid() and not board.is_edge_blocked(opp, behind):
        jump_moves.append(MoveAction(destination=behind))
        return jump_moves

    for lat_dir in _lateral_directions(direction):
        lateral = opp.neighbor(lat_dir)
        if lateral.is_valid() and not board.is_edge_blocked(opp, lateral):
            jump_moves.append(MoveAction(destination=lateral))

    return jump_moves


def _lateral_directions(direction: Direction) -> list[Direction]:
    """Retourne les deux directions perpendiculaires a direction."""
    if direction in (Direction.NORTH, Direction.SOUTH):
        return [Direction.EAST, Direction.WEST]
    return [Direction.NORTH, Direction.SOUTH]


# ---------------------------------------------------------------------------
# Cache pour get_valid_walls
# Le calcul des murs valides est identique pour toute la duree ou le plateau
# ne change pas. On le cache par configuration du board.
# ---------------------------------------------------------------------------

_walls_cache: dict[tuple, list] = {}
_WALLS_CACHE_MAX = 60_000


def _board_cache_key(state: GameState) -> tuple:
    """
    Cle de cache : uniquement le frozenset des murs places.
    Les positions des pions ne changent pas la validite des murs.
    """
    return (frozenset(state.board.walls),)


def get_valid_walls(state: GameState) -> list[WallAction]:
    """
    Retourne toutes les poses de barrieres valides pour le joueur courant.

    Conditions :
      1. Le joueur a encore des barrieres
      2. La barriere ne chevauche pas une barriere existante
      3. Apres pose, les deux joueurs ont encore un chemin vers leur objectif (BFS)

    OPTIMISATION : cache par configuration du board.
    Le calcul (128 BFS) n'est fait qu'une seule fois par configuration unique.
    """
    if state.current_player.walls_remaining == 0:
        return []

    key = _board_cache_key(state)
    if key in _walls_cache:
        return _walls_cache[key]

    if len(_walls_cache) >= _WALLS_CACHE_MAX:
        _walls_cache.clear()

    p1 = state.players[PlayerID.ONE]
    p2 = state.players[PlayerID.TWO]
    valid_walls: list[WallAction] = []

    for row in range(BOARD_SIZE - 1):
        for col in range(BOARD_SIZE - 1):
            for orientation in WallOrientation:
                wall = Wall(Position(row, col), orientation)
                if _wall_overlaps(wall, state.board):
                    continue
                test_board = _board_with_wall(state.board, wall)
                if (
                    bfs_has_path(test_board, p1.position, p1.goal_row)
                    and bfs_has_path(test_board, p2.position, p2.goal_row)
                ):
                    valid_walls.append(WallAction(wall=wall))

    _walls_cache[key] = valid_walls
    return valid_walls


def get_valid_walls_for_ai(state: GameState, max_walls: int = 20) -> list[WallAction]:
    """
    Version pour l'IA : retourne les murs valides PRE-FILTRES et LIMITES.

    Strategie :
      1. Recuperer tous les murs valides (depuis le cache si possible)
      2. Trier par pertinence strategique (proximite des deux joueurs)
      3. Retourner uniquement les max_walls meilleurs

    Pourquoi ca marche :
      - Les murs lointains des deux joueurs sont rarement utiles
      - Limiter a 20 murs reduit le branching factor de 128 a ~23
      - L'elagage Alpha-Beta devient x5 a x10 plus efficace
      - Perte de qualite negligeable : les "bons" murs sont proches des pions

    max_walls=0 desactive le filtrage (comportement complet).
    """
    all_walls = get_valid_walls(state)
    if max_walls == 0 or len(all_walls) <= max_walls:
        return all_walls

    p1_pos = state.players[PlayerID.ONE].position
    p2_pos = state.players[PlayerID.TWO].position

    def wall_score(wa: WallAction) -> int:
        r, c = wa.wall.position.row, wa.wall.position.col
        # Distance Manhattan aux deux joueurs — on veut les murs les plus proches
        d1 = abs(r - p1_pos.row) + abs(c - p1_pos.col)
        d2 = abs(r - p2_pos.row) + abs(c - p2_pos.col)
        return min(d1, d2)  # proximite au joueur le plus proche

    return sorted(all_walls, key=wall_score)[:max_walls]


def _wall_overlaps(wall: Wall, board: Board) -> bool:
    """
    Verifie si les aretes bloquees par wall sont deja bloquees
    (chevauchement ou croisement de barrieres).
    """
    new_edges = set(Board._wall_to_edges(wall))
    return bool(new_edges & board._blocked_edges)


def _board_with_wall(board: Board, wall: Wall) -> Board:
    """
    Retourne une copie legere du Board avec la barriere ajoutee.
    Evite un deepcopy complet.
    """
    new_board = object.__new__(Board)
    new_board.walls = set(board.walls)
    new_board._blocked_edges = set(board._blocked_edges)
    new_board.place_wall(wall)
    return new_board


# ---------------------------------------------------------------------------
# Application d'un coup — version avec validation (API / joueur humain)
# ---------------------------------------------------------------------------

def apply_action(state: GameState, action: Action) -> GameState:
    """
    Applique une action en validant qu'elle est legale.
    Utiliser apply_action_trusted() dans l'IA pour eviter la re-validation.
    """
    new_state = state.clone()

    if isinstance(action, MoveAction):
        valid_moves = get_valid_moves(state)
        if action not in valid_moves:
            raise InvalidActionError(f"Deplacement invalide : {action.destination}")
        new_state.current_player.position = action.destination
        new_state.current_player.move_history.append(
            _pos_to_notation(action.destination)
        )

    elif isinstance(action, WallAction):
        valid_walls = get_valid_walls(state)
        if action not in valid_walls:
            raise InvalidActionError(f"Barriere invalide : {action.wall}")
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


# ---------------------------------------------------------------------------
# Application d'un coup — fast path pour l'IA (sans re-validation)
# ---------------------------------------------------------------------------

def apply_action_trusted(state: GameState, action: Action) -> GameState:
    """
    Version rapide d'apply_action SANS re-validation.
    A utiliser UNIQUEMENT quand l'action vient de get_all_valid_actions*().

    Gain : supprime les BFS de re-validation a chaque noeud de l'arbre.
    """
    new_state = state.clone()

    if isinstance(action, MoveAction):
        new_state.current_player.position = action.destination
        new_state.current_player.move_history.append(
            _pos_to_notation(action.destination)
        )
    elif isinstance(action, WallAction):
        new_state.board.place_wall(action.wall)
        new_state.current_player.walls_remaining -= 1
        new_state.current_player.move_history.append(
            _wall_to_notation(action.wall)
        )

    new_state.check_victory()
    new_state.switch_turn()
    return new_state


# ---------------------------------------------------------------------------
# Listes d'actions pour l'IA
# ---------------------------------------------------------------------------

def get_all_valid_actions(state: GameState) -> list[Action]:
    """
    Retourne tous les coups legaux (mouvements en premier).
    Version non-triee, utilisee par Minimax/Negamax purs.
    """
    if state.is_terminal():
        return []
    actions: list[Action] = []
    actions.extend(get_valid_moves(state))
    actions.extend(get_valid_walls(state))
    return actions


def get_all_valid_actions_ordered(state: GameState, max_walls: int = 20) -> list[Action]:
    """
    Retourne les actions valides TRIEES et LIMITEES pour un meilleur elagage Alpha-Beta.

    Ordre :
      1. Mouvements vers la ligne d'arrivee (priorite aux cases proches du but)
      2. Murs tries par pertinence strategique, limites a max_walls

    Le parametre max_walls (defaut 20) reduit le branching factor de ~131 a ~23,
    ce qui rend l'elagage Alpha-Beta x5 a x10 plus efficace en profondeur.

    max_walls=0 desactive la limite (comportement complet, plus lent).
    """
    if state.is_terminal():
        return []

    player   = state.current_player
    goal_row = player.goal_row
    opp_pos  = state.opponent.position

    moves = get_valid_moves(state)
    walls = get_valid_walls_for_ai(state, max_walls=max_walls) if player.walls_remaining > 0 else []

    # Mouvements : priorite aux cases qui rapprochent du but
    if goal_row == 0:
        moves_sorted = sorted(moves, key=lambda m: m.destination.row)
    else:
        moves_sorted = sorted(moves, key=lambda m: -m.destination.row)

    # Murs : deja tries par get_valid_walls_for_ai, on les retrie par cote adversaire
    walls_sorted = sorted(
        walls,
        key=lambda w: abs(w.wall.position.row - opp_pos.row)
                    + abs(w.wall.position.col - opp_pos.col)
    )

    return moves_sorted + walls_sorted


# ---------------------------------------------------------------------------
# Notation algebrique (pour move_history et logs)
# ---------------------------------------------------------------------------

def _pos_to_notation(pos: Position) -> str:
    """Convertit une position en notation Quoridor : e5, a1, i9..."""
    col_letter = chr(ord('a') + pos.col)
    row_number = pos.row + 1
    return f"{col_letter}{row_number}"


def _wall_to_notation(wall: Wall) -> str:
    """Notation : e5h (horizontal) ou e5v (vertical)."""
    base   = _pos_to_notation(wall.position)
    suffix = "h" if wall.orientation == WallOrientation.HORIZONTAL else "v"
    return f"{base}{suffix}"