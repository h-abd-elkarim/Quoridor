"""
Table de hachage Zobrist pour Quoridor.
Permet de calculer un hash unique d'un GameState en O(1) par mise à jour
(XOR incrémental) — indispensable pour les tables de transposition Minimax.

Principe :
  hash = XOR de tous les tokens actifs
  Mise à jour : hash ^= TABLE[token_modifié]  (ajout ET retrait)
"""
from __future__ import annotations
import random
from functools import lru_cache
from .board import BOARD_SIZE, WallOrientation, Position, Wall

random.seed(0xDEADBEEF)  # Reproductible pour les tests


def _rand64() -> int:
    return random.getrandbits(64)


# ---------------------------------------------------------------------------
# Tables de valeurs aléatoires 64-bit
# ---------------------------------------------------------------------------

# Position de P1 : 81 cases
ZOBRIST_PLAYER1: list[list[int]] = [
    [_rand64() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
]

# Position de P2 : 81 cases
ZOBRIST_PLAYER2: list[list[int]] = [
    [_rand64() for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)
]

# Joueur courant : 2 valeurs
ZOBRIST_TURN: list[int] = [_rand64(), _rand64()]

# Barrières horizontales : (row, col) → 8×8 = 64 positions valides
ZOBRIST_WALL_H: list[list[int]] = [
    [_rand64() for _ in range(BOARD_SIZE - 1)] for _ in range(BOARD_SIZE - 1)
]

# Barrières verticales : idem
ZOBRIST_WALL_V: list[list[int]] = [
    [_rand64() for _ in range(BOARD_SIZE - 1)] for _ in range(BOARD_SIZE - 1)
]


# ---------------------------------------------------------------------------
# Calcul complet du hash (utilisé à l'initialisation du nœud racine)
# ---------------------------------------------------------------------------

def compute_hash(state) -> int:
    """
    Calcule le hash Zobrist complet d'un GameState.
    O(nb_murs) — utilisé une seule fois par partie (racine).
    Les mises à jour sont incrémentales via update_hash_*.
    """
    from .player import PlayerID

    h = 0

    # Positions des joueurs
    p1 = state.players[PlayerID.ONE].position
    p2 = state.players[PlayerID.TWO].position
    h ^= ZOBRIST_PLAYER1[p1.row][p1.col]
    h ^= ZOBRIST_PLAYER2[p2.row][p2.col]

    # Joueur courant
    h ^= ZOBRIST_TURN[state.current_player_id.value - 1]

    # Barrières posées
    for wall in state.board.walls:
        r, c = wall.position.row, wall.position.col
        if wall.orientation == WallOrientation.HORIZONTAL:
            h ^= ZOBRIST_WALL_H[r][c]
        else:
            h ^= ZOBRIST_WALL_V[r][c]

    return h


def update_hash_move(h: int, player_table, old_pos: Position, new_pos: Position) -> int:
    """Mise à jour XOR incrémentale après un déplacement de pion."""
    h ^= player_table[old_pos.row][old_pos.col]  # retire l'ancienne position
    h ^= player_table[new_pos.row][new_pos.col]  # ajoute la nouvelle
    return h


def update_hash_wall(h: int, wall: Wall) -> int:
    """Mise à jour XOR après pose d'une barrière."""
    r, c = wall.position.row, wall.position.col
    if wall.orientation == WallOrientation.HORIZONTAL:
        h ^= ZOBRIST_WALL_H[r][c]
    else:
        h ^= ZOBRIST_WALL_V[r][c]
    return h


def update_hash_turn(h: int, old_player_id_value: int, new_player_id_value: int) -> int:
    """Mise à jour XOR après changement de tour."""
    h ^= ZOBRIST_TURN[old_player_id_value - 1]
    h ^= ZOBRIST_TURN[new_player_id_value - 1]
    return h
