from __future__ import annotations
from collections import deque
from typing import Optional
from .board import Board, Position, BOARD_SIZE


def bfs_has_path(board: Board, start: Position, goal_row: int) -> bool:
    """
    BFS (exploration de graphe sans bouclage) depuis `start` vers n'importe
    quelle case de `goal_row`.

    Implémentation directe de l'algorithme ExplorationDeGraphe du cours :
      Frontière ← {start}
      Générés   ← {start}
      Tant que Frontière ≠ ∅ :
          s ← retirer(Frontière)
          Si s ∈ Finaux → Solution = Vrai
          Pour tout successeur t de s :
              Si t ∉ Générés : ajouter(t, Frontière ∪ Générés)

    Complexity : O(N²) avec N = BOARD_SIZE (81 cases max).
    """
    if start.row == goal_row:
        return True

    frontier: deque[Position] = deque([start])
    generated: set[Position] = {start}

    while frontier:
        current = frontier.popleft()

        for neighbor in board.get_neighbors(current):
            if neighbor.row == goal_row:
                return True
            if neighbor not in generated:
                generated.add(neighbor)
                frontier.append(neighbor)

    return False


def bfs_shortest_path(
    board: Board, start: Position, goal_row: int
) -> Optional[list[Position]]:
    """
    BFS avec reconstruction de chemin.
    Retourne la liste de positions du chemin le plus court, ou None si bloqué.
    Utilisé pour la visualisation pédagogique (PathOverlay frontend).
    """
    if start.row == goal_row:
        return [start]

    frontier: deque[Position] = deque([start])
    generated: set[Position] = {start}
    parent: dict[Position, Optional[Position]] = {start: None}

    while frontier:
        current = frontier.popleft()

        for neighbor in board.get_neighbors(current):
            if neighbor not in generated:
                generated.add(neighbor)
                parent[neighbor] = current
                frontier.append(neighbor)

                if neighbor.row == goal_row:
                    return _reconstruct_path(parent, neighbor)

    return None


def _reconstruct_path(
    parent: dict[Position, Optional[Position]], end: Position
) -> list[Position]:
    path = []
    node: Optional[Position] = end
    while node is not None:
        path.append(node)
        node = parent[node]
    path.reverse()
    return path


def shortest_distance_to_goal(board: Board, start: Position, goal_row: int) -> int:
    """
    Retourne la distance BFS minimale. Retourne float('inf') si bloqué.
    Guard ajouté : path peut être None (cas théorique hors contrainte BFS).
    """
    path = bfs_shortest_path(board, start, goal_row)
    if path is None:
        return float('inf')
    return len(path) - 1