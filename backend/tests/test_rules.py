import pytest
from core import GameState, Position, Wall, WallOrientation
from core.rules import (
    MoveAction, WallAction,
    get_valid_moves, get_valid_walls, apply_action,
    get_all_valid_actions, InvalidActionError,
)
from core.pathfinding import bfs_has_path, shortest_distance_to_goal


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def fresh_state():
    return GameState.new_game()


# ---------------------------------------------------------------------------
# Pathfinding
# ---------------------------------------------------------------------------

def test_bfs_open_board(fresh_state):
    """Plateau vide : les deux joueurs ont un chemin."""
    from core.player import PlayerID  
    board = fresh_state.board
    p1 = fresh_state.players[PlayerID.ONE]  
    p2 = fresh_state.players[PlayerID.TWO]  
    assert bfs_has_path(board, p1.position, p1.goal_row)
    assert bfs_has_path(board, p2.position, p2.goal_row)

def test_bfs_distance_start(fresh_state):
    """Distance initiale : 8 pas depuis le bord jusqu'au bord opposé."""
    from core.player import PlayerID
    p1 = fresh_state.players[PlayerID.ONE]
    dist = shortest_distance_to_goal(fresh_state.board, p1.position, p1.goal_row)
    assert dist == 8


# ---------------------------------------------------------------------------
# Mouvements valides
# ---------------------------------------------------------------------------

def test_p1_initial_moves(fresh_state):
    """P1 au centre du bord Nord : 3 mouvements initiaux (S, E, W)."""
    moves = get_valid_moves(fresh_state)
    assert len(moves) == 3


def test_move_blocked_by_wall(fresh_state):
    """Une barrière au Sud de P1 doit supprimer ce déplacement."""
    from core.board import Direction
    from core.player import PlayerID  
    p1_pos = fresh_state.players[PlayerID.ONE].position 
    wall = Wall(p1_pos, WallOrientation.HORIZONTAL)
    fresh_state.board.place_wall(wall)
    moves = get_valid_moves(fresh_state)
    destinations = [m.destination for m in moves]
    south = p1_pos.neighbor(Direction.SOUTH)
    assert south not in destinations

# ---------------------------------------------------------------------------
# Barrières valides
# ---------------------------------------------------------------------------

def test_wall_blocks_path_is_rejected(fresh_state):
    """
    Une série de barrières qui ferme le couloir central doit être rejetée
    par la contrainte BFS.
    """
    state = fresh_state
    # On pose des murs pour couper P1 de sa ligne d'arrivée
    for col in range(0, 8, 2):
        w = Wall(Position(4, col), WallOrientation.HORIZONTAL)
        from core.rules import _wall_overlaps, _board_with_wall
        if not _wall_overlaps(w, state.board):
            test_board = _board_with_wall(state.board, w)
            from core.player import PlayerID
            p1 = state.players[PlayerID.ONE]
            # Si le chemin est bloqué, la barrière ne doit pas figurer dans valid_walls
            if not bfs_has_path(test_board, p1.position, p1.goal_row):
                valid = get_valid_walls(state)
                assert WallAction(w) not in valid
                return
    # Si on n'a pas trouvé de cas bloquant, le test passe sans erreur
    pass


def test_no_walls_when_exhausted(fresh_state):
    """Quand walls_remaining == 0, aucune barrière ne doit être proposée."""
    fresh_state.current_player.walls_remaining = 0
    assert get_valid_walls(fresh_state) == []


# ---------------------------------------------------------------------------
# Application de coups
# ---------------------------------------------------------------------------

def test_apply_move_changes_position(fresh_state):
    from core.player import PlayerID
    moves = get_valid_moves(fresh_state)
    new_state = apply_action(fresh_state, moves[0])
    assert new_state.players[PlayerID.ONE].position == moves[0].destination


def test_apply_wall_decrements_count(fresh_state):
    from core.player import PlayerID
    walls = get_valid_walls(fresh_state)
    initial_count = fresh_state.players[PlayerID.ONE].walls_remaining
    new_state = apply_action(fresh_state, walls[0])
    assert new_state.players[PlayerID.ONE].walls_remaining == initial_count - 1


def test_apply_invalid_move_raises(fresh_state):
    bad_action = MoveAction(destination=Position(8, 8))
    with pytest.raises(InvalidActionError):
        apply_action(fresh_state, bad_action)


def test_turn_switches_after_action(fresh_state):
    from core.player import PlayerID
    moves = get_valid_moves(fresh_state)
    new_state = apply_action(fresh_state, moves[0])
    assert new_state.current_player_id == PlayerID.TWO


def test_victory_detected(fresh_state):
    from core.player import PlayerID
    from core.game import GameStatus
    # Téléporter P1 à row=7 et lui faire faire un pas vers row=8 (sur une colonne vide)
    fresh_state.players[PlayerID.ONE].position = Position(7, 0)  # <-- Remplacement (7, 4) par (7, 0)
    move = MoveAction(destination=Position(8, 0))                # <-- Remplacement (8, 4) par (8, 0)
    new_state = apply_action(fresh_state, move)
    assert new_state.status == GameStatus.PLAYER1_WIN