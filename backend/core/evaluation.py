"""
Fonction d'évaluation heuristique pour Quoridor.
Utilisée comme s.e (valeur de feuille) dans Minimax/Negamax/ab.

Heuristique multi-composantes :
  1. Différence de distances A* aux objectifs        (composante principale)
  2. Progression absolue du joueur MAX vers son but   (anti-bouclage ← NEW)
  3. Barrières restantes                              (ressource stratégique)
  4. Pénalité de répétition d'état (Zobrist)          (anti-boucle ← NEW)

POURQUOI LE BOUCLAGE APPARAISSAIT :
  L'ancienne évaluation = W_DISTANCE * (dist_opp - dist_max)
  Ce score est STATIONNAIRE : si les deux joueurs reculent d'une case en même
  temps, la différence reste identique. L'IA peut donc faire des allers-retours
  sans jamais voir son score se dégrader.
  La composante W_PROGRESS casse cela : reculer d'une case coûte toujours
  W_PROGRESS points, même si l'adversaire recule aussi.
"""
from __future__ import annotations
from .game import GameState, GameStatus
from .pathfinding import astar

INF        = float('inf')
WIN_SCORE  =  100_000
LOSE_SCORE = -100_000

# ── Poids des composantes ────────────────────────────────────────────────────
W_DISTANCE = 10   # différence de distances A* (principal)
W_PROGRESS =  4   # progression absolue vers le but (anti-bouclage)
W_WALLS    =  1   # barrières restantes
W_REPEAT   = 15   # pénalité par répétition dans la partie réelle


def _distance_to_goal(board, position, goal_row: int) -> float:
    """Distance A* minimale de `position` vers `goal_row`."""
    if position.row == goal_row:
        return 0.0
    path = astar(board, position, goal_row)
    return float(len(path) - 1) if path is not None else INF


def _progress_score(position, goal_row: int) -> float:
    """
    Récompense la proximité absolue au but.

    Joueur 1 (goal_row=8) : progress = row (0→8, plus grand = mieux)
    Joueur 2 (goal_row=0) : progress = 8 - row (8→0, plus grand = mieux)

    Cette composante force l'IA à avancer : même si dist_opp - dist_max
    reste constant, reculer d'une case fait baisser progress_max de 1,
    ce qui coûte W_PROGRESS points dans le score final.
    """
    from .board import BOARD_SIZE
    if goal_row == BOARD_SIZE - 1:
        return float(position.row)
    else:
        return float(BOARD_SIZE - 1 - position.row)


def evaluate(
    state: GameState,
    maximizing_player_id,
    position_history: "dict[int, int] | None" = None,
) -> float:
    """
    Évalue state du point de vue de maximizing_player_id.
    Retourne un score réel dans [LOSE_SCORE, WIN_SCORE].

    position_history (optionnel) :
      dict {zobrist_hash -> nb_visites} des états vus dans la partie RÉELLE.
      Passé par ai_router via get_ai_move(). Permet de pénaliser les positions
      que l'IA a déjà visitées, sans toucher à l'arbre de recherche interne.
    """
    from .player import PlayerID

    # ── Cas terminal ─────────────────────────────────────────────────────────
    if state.status == GameStatus.PLAYER1_WIN:
        winner = PlayerID.ONE
    elif state.status == GameStatus.PLAYER2_WIN:
        winner = PlayerID.TWO
    else:
        winner = None

    if winner is not None:
        return WIN_SCORE if winner == maximizing_player_id else LOSE_SCORE

    # ── Joueurs ───────────────────────────────────────────────────────────────
    max_player = state.players[maximizing_player_id]
    opp_id     = PlayerID.TWO if maximizing_player_id == PlayerID.ONE else PlayerID.ONE
    opp_player = state.players[opp_id]

    # ── 1. Différence de distances A* ────────────────────────────────────────
    dist_max = _distance_to_goal(state.board, max_player.position, max_player.goal_row)
    dist_opp = _distance_to_goal(state.board, opp_player.position, opp_player.goal_row)

    if dist_max == INF:
        return LOSE_SCORE
    if dist_opp == INF:
        return WIN_SCORE

    # ── 2. Progression absolue (anti-bouclage) ───────────────────────────────
    progress_max = _progress_score(max_player.position, max_player.goal_row)
    progress_opp = _progress_score(opp_player.position, opp_player.goal_row)

    # ── 3. Barrières restantes ────────────────────────────────────────────────
    wall_delta = max_player.walls_remaining - opp_player.walls_remaining

    # ── 4. Pénalité de répétition de position (partie réelle uniquement) ──────
    repeat_penalty = 0.0
    if position_history is not None:
        from .zobrist import compute_hash
        h      = compute_hash(state)
        visits = position_history.get(h, 0)
        if visits > 0:
            # Pénalité croissante : 1 visite → -15, 2 → -45, 3 → -90…
            repeat_penalty = float(W_REPEAT * visits * (visits + 1) // 2)

    score = (
        W_DISTANCE * (dist_opp - dist_max)
        + W_PROGRESS * (progress_max - progress_opp)
        + W_WALLS    * wall_delta
        - repeat_penalty
    )
    return float(score)