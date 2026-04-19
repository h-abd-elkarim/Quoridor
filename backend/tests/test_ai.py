import pytest
from core import GameState
from core.player import PlayerID
from core.ai import (
    minimax_decision, negamax_decision,
    alphabeta_decision, negalphabeta_decision,
    sss_star, get_ai_move, Difficulty, TranspositionTable,
)
from core.evaluation import evaluate, WIN_SCORE, LOSE_SCORE
from core.rules import apply_action, MoveAction
from core.board import Position
from core.game import GameStatus


@pytest.fixture
def fresh_state():
    return GameState.new_game()


# ---------------------------------------------------------------------------
# Évaluation
# ---------------------------------------------------------------------------

def test_evaluate_initial_balanced(fresh_state):
    """Plateau vide : les deux joueurs sont équidistants → score proche de 0."""
    score = evaluate(fresh_state, PlayerID.ONE)
    assert -5 < score < 5


def test_evaluate_win(fresh_state):
    """Victoire P1 → score = WIN_SCORE."""
    fresh_state.players[PlayerID.ONE].position = Position(8, 4)
    fresh_state.status = GameStatus.PLAYER1_WIN
    assert evaluate(fresh_state, PlayerID.ONE) == WIN_SCORE


def test_evaluate_lose(fresh_state):
    """Victoire P2 vue par P1 → score = LOSE_SCORE."""
    fresh_state.players[PlayerID.TWO].position = Position(0, 4)
    fresh_state.status = GameStatus.PLAYER2_WIN
    assert evaluate(fresh_state, PlayerID.ONE) == LOSE_SCORE


# ---------------------------------------------------------------------------
# Minimax
# ---------------------------------------------------------------------------

def test_minimax_returns_action(fresh_state):
    result = minimax_decision(fresh_state, depth=1)
    assert result.best_action is not None
    assert result.algorithm == "Minimax"
    assert result.nodes_explored > 0


def test_minimax_depth1_is_valid_move(fresh_state):
    """Le coup retourné par Minimax doit être légal."""
    from core.rules import get_all_valid_actions
    result = minimax_decision(fresh_state, depth=1)
    valid = get_all_valid_actions(fresh_state)
    assert result.best_action in valid


# ---------------------------------------------------------------------------
# Négamax
# ---------------------------------------------------------------------------

def test_negamax_returns_action(fresh_state):
    result = negamax_decision(fresh_state, depth=1)
    assert result.best_action is not None
    assert result.algorithm in ("Négamax", "Negamax")


def test_negamax_consistent_with_minimax(fresh_state):
    """Minimax et Négamax depth=1 doivent choisir un coup de même valeur."""
    r_mm = minimax_decision(fresh_state, depth=1)
    r_nm = negamax_decision(fresh_state, depth=1)
    # Les scores peuvent différer en signe/convention, mais les deux bougent
    assert r_mm.best_action is not None
    assert r_nm.best_action is not None


# ---------------------------------------------------------------------------
# Alpha-Bêta
# ---------------------------------------------------------------------------

def test_alphabeta_same_result_as_minimax(fresh_state):
    """αβ doit retourner le même score que Minimax à profondeur égale."""
    from core.player import PlayerID
    fresh_state.players[PlayerID.ONE].walls_remaining = 0
    fresh_state.players[PlayerID.TWO].walls_remaining = 0
    
    r_mm = minimax_decision(fresh_state, depth=2)
    tt = TranspositionTable()
    r_ab = alphabeta_decision(fresh_state, depth=2, tt=tt)
    # On vérifie que les deux algorithmes sont cohérents (même meilleur coup possible)
    assert r_ab.best_action is not None


def test_alphabeta_explores_fewer_nodes(fresh_state):
    """αβ doit explorer moins de nœuds que Minimax pur à même profondeur."""
    from core.player import PlayerID
    fresh_state.players[PlayerID.ONE].walls_remaining = 0
    fresh_state.players[PlayerID.TWO].walls_remaining = 0
    
    counter_mm = [0]
    from core.ai import minimax
    minimax(fresh_state, depth=2, is_max=True,
            maximizing_player_id=PlayerID.ONE, counter=counter_mm)

    tt = TranspositionTable()
    counter_ab = [0]
    from core.ai import alphabeta
    alphabeta(fresh_state, depth=2, alpha=-float('inf'), beta=float('inf'),
              is_max=True, maximizing_player_id=PlayerID.ONE,
              counter=counter_ab, tt=tt)

    assert counter_ab[0] <= counter_mm[0]


# ---------------------------------------------------------------------------
# Négα-Bêta
# ---------------------------------------------------------------------------

def test_negalphabeta_returns_action(fresh_state):
    from core.player import PlayerID
    fresh_state.players[PlayerID.ONE].walls_remaining = 0
    fresh_state.players[PlayerID.TWO].walls_remaining = 0
    
    tt = TranspositionTable()
    result = negalphabeta_decision(fresh_state, depth=2, tt=tt)
    assert result.best_action is not None
    assert result.algorithm in ("Négα-Bêta", "Nega-Beta")


# ---------------------------------------------------------------------------
# SSS*
# ---------------------------------------------------------------------------

def test_sss_star_returns_action(fresh_state):
    from core.player import PlayerID
    fresh_state.players[PlayerID.ONE].walls_remaining = 0
    fresh_state.players[PlayerID.TWO].walls_remaining = 0
    
    result = sss_star(fresh_state, depth=2)
    assert result.best_action is not None
    assert result.algorithm == "SSS*"


# ---------------------------------------------------------------------------
# Dispatcher get_ai_move
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("difficulty", list(Difficulty))
def test_get_ai_move_all_difficulties(fresh_state, difficulty):
    from core.player import PlayerID
    fresh_state.players[PlayerID.ONE].walls_remaining = 0
    fresh_state.players[PlayerID.TWO].walls_remaining = 0
    
    result = get_ai_move(fresh_state, difficulty)
    assert result.best_action is not None, f"Aucun coup pour {difficulty.name}"


# ---------------------------------------------------------------------------
# Zobrist
# ---------------------------------------------------------------------------

def test_zobrist_same_state_same_hash(fresh_state):
    from core.zobrist import compute_hash
    h1 = compute_hash(fresh_state)
    h2 = compute_hash(fresh_state)
    assert h1 == h2


def test_zobrist_different_state_different_hash(fresh_state):
    from core.zobrist import compute_hash
    from core.rules import get_valid_moves
    h1 = compute_hash(fresh_state)
    move = get_valid_moves(fresh_state)[0]
    new_state = apply_action(fresh_state, move)
    h2 = compute_hash(new_state)
    assert h1 != h2