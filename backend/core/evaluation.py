"""
Fonction d'évaluation heuristique pour Quoridor.
Utilisée comme s.e (valeur de feuille) dans Minimax/Négamax/αβ.

Heuristique principale : différence de distances BFS aux objectifs.
  eval = dist(adversaire → son_but) - dist(joueur_courant → son_but)
  → Plus le joueur courant est proche ET l'adversaire est loin, meilleur c'est.

Bonus/malus additionnels :
  - Barrières restantes (ressource stratégique)
  - Victoire/défaite : ±INF
"""
from __future__ import annotations
from .game import GameState, GameStatus
from .pathfinding import shortest_distance_to_goal

INF = float('inf')
WIN_SCORE  =  100_000
LOSE_SCORE = -100_000

# Poids des composantes de l'heuristique
W_DISTANCE = 10   # distance BFS (composante principale)
W_WALLS    =  1   # barrières restantes (composante secondaire)


def evaluate(state: GameState, maximizing_player_id) -> float:
    """
    Évalue state du point de vue de `maximizing_player_id`.
    Retourne un score réel ∈ [LOSE_SCORE, WIN_SCORE].

    Correspond à s.e dans le pseudo-code Minimax du cours.
    """
    from .player import PlayerID

    if state.status == GameStatus.PLAYER1_WIN:
        winner = PlayerID.ONE
    elif state.status == GameStatus.PLAYER2_WIN:
        winner = PlayerID.TWO
    else:
        winner = None

    if winner is not None:
        return WIN_SCORE if winner == maximizing_player_id else LOSE_SCORE

    # Joueur MAX et adversaire
    max_player = state.players[maximizing_player_id]
    opp_id = PlayerID.TWO if maximizing_player_id == PlayerID.ONE else PlayerID.ONE
    opp_player = state.players[opp_id]

    dist_max = shortest_distance_to_goal(
        state.board, max_player.position, max_player.goal_row
    )
    dist_opp = shortest_distance_to_goal(
        state.board, opp_player.position, opp_player.goal_row
    )

    if dist_max == INF:
        return LOSE_SCORE
    if dist_opp == INF:
        return WIN_SCORE

    score = (
        W_DISTANCE * (dist_opp - dist_max)
        + W_WALLS * (max_player.walls_remaining - opp_player.walls_remaining)
    )
    return float(score)
