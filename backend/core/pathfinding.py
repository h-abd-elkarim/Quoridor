from __future__ import annotations
from collections import deque
from typing import Optional
from itertools import count as _count
import heapq as _heapq
from .board import Board, Position, BOARD_SIZE


def bfs_has_path(board: Board, start: Position, goal_row: int) -> bool:
    """
    BFS optimise depuis start vers goal_row.

    Implémentation fidele au cours (ExplorationDeGraphe) avec
    optimisation : liste + index au lieu de deque, array 2D au lieu de set.
    Gain mesure : ~15% vs version deque+set.

    Complexity : O(N²) avec N = BOARD_SIZE (81 cases max).
    """
    if start.row == goal_row:
        return True

    visited = [[False] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    visited[start.row][start.col] = True
    queue: list[Position] = [start]
    head = 0

    while head < len(queue):
        current = queue[head]
        head += 1
        for neighbor in board.get_neighbors(current):
            r, c = neighbor.row, neighbor.col
            if r == goal_row:
                return True
            if not visited[r][c]:
                visited[r][c] = True
                queue.append(neighbor)

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
    """
    path = bfs_shortest_path(board, start, goal_row)
    if path is None:
        return float('inf')
    return len(path) - 1


# ===========================================================================
# UCS — Exploration à coût uniforme (pseudo-code du cours)
# ===========================================================================
# Procédure Init(G, s, ∆, π, O, F)
#   Pour tout x : ∆(x) ← +∞ ; π(x) ← 0 ; O(x) ← faux ; F(x) ← faux
#   ∆(s) ← 0 ; O(s) ← vrai
#
# Procédure Examiner(x, ∆, π, O, F)
#   Pour tout successeur y de x :
#     Si ∆(x) + g(x,y) < ∆(y) : ∆(y) ← … ; π(y) ← x ; Ouvrir(y)
#   Fermer(x)
# ===========================================================================

def ucs(board: Board, start: Position, goal_row: int) -> Optional[list[Position]]:
    """
    Exploration à coût uniforme — implémentation fidèle au pseudo-code du cours.

    Variables du cours :
      ∆  (delta)  : dict Position → coût minimal connu
      π  (pi)     : dict Position → prédécesseur sur le chemin optimal
      O  (open)   : ensemble des nœuds ouverts (file de priorité sur ∆)
      F  (closed) : ensemble des nœuds fermés

    Toutes les arêtes ont un coût g(x,y) = 1 (plateau unitaire).
    Retourne le chemin optimal ou None si but inaccessible.

    Fix : tuple (coût, tie_breaker, position) pour éviter la comparaison
    Position < Position dans heapq quand les coûts sont égaux.
    """
    if start.row == goal_row:
        return [start]

    INF = float('inf')
    _tie = _count()  # tie-breaker entier, jamais égaux → heapq ne compare jamais Position

    # --- Init(G, s, ∆, π, O, F) ---
    delta:      dict[Position, float]                = {}  # ∆
    pi:         dict[Position, Optional[Position]]   = {}  # π
    open_set:   set[Position]                        = set()  # O
    closed_set: set[Position]                        = set()  # F

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = Position(r, c)
            delta[p] = INF   # ∆(x) ← +∞
            pi[p]    = None  # π(x) ← 0

    delta[start] = 0        # ∆(s) ← 0
    open_set.add(start)     # O(s) ← vrai

    # File de priorité : (∆(x), tie, x)
    heap: list = [(0.0, next(_tie), start)]

    while heap:
        # Choisir dans O un sommet x de coût ∆ minimal
        cost_x, _, x = _heapq.heappop(heap)

        if x in closed_set:  # entrée périmée
            continue

        if x.row == goal_row:
            return _reconstruct_path(pi, x)

        # --- Examiner(x, ∆, π, O, F) ---
        for y in board.get_neighbors(x):       # Pour tout successeur y de x
            if y in closed_set:
                continue
            new_cost = delta[x] + 1.0          # ∆(x) + g(x,y),  g = 1

            if new_cost < delta[y]:            # Si ∆(x)+g(x,y) < ∆(y)
                delta[y] = new_cost            # ∆(y) ← ∆(x) + g(x,y)
                pi[y]    = x                   # π(y) ← x
                open_set.add(y)                # Ouvrir(y)
                _heapq.heappush(heap, (new_cost, next(_tie), y))

        # Fermer(x)
        open_set.discard(x)
        closed_set.add(x)                      # F(x) ← vrai

    return None  # Échec


# ===========================================================================
# A* — (pseudo-code du cours)
# ===========================================================================
# Procédure Init*(G, s, ∆, π, O, f)
#   Pour tout x : ∆(x) ← +∞ ; π(x) ← -1 ; O(x) ← faux ; f(x) ← Nil
#   ∆(s) ← 0 ; O(s) ← vrai ; f(s) ← h(s)
#
# Procédure Examiner*(x, ∆, π, f, O)
#   Pour tout successeur y de x :
#     Si ∆(x) + g(x,y) < ∆(y) :
#       ∆(y) ← … ; π(y) ← x ; f(y) ← ∆(y) + h(y) ; Ouvrir*(y)
#   Fermer*(x)
#
# Procédure A*(G, s, t, ∆, π, f)
#   Init*(G, s, …)
#   x ← s
#   Tant que (x ≠ t) et (O ≠ ∅) :
#     Choisir dans O le sommet x d'approximation f(x) minimale
#     Examiner*(x, …)
# ===========================================================================

def _heuristic(pos: Position, goal_row: int) -> float:
    """
    h(x) — heuristique admissible pour A* Quoridor.
    Distance de Manhattan vers la ligne d'arrivée (minore toujours le vrai coût).
    """
    return float(abs(pos.row - goal_row))


def astar(board: Board, start: Position, goal_row: int) -> Optional[list[Position]]:
    """
    A* — implémentation fidèle au pseudo-code du cours.

    Variables du cours :
      ∆  (delta) : coût g réel depuis la source
      π  (pi)    : prédécesseur sur le chemin optimal
      f          : approximation totale f(x) = ∆(x) + h(x)
      O          : ensemble des nœuds ouverts (file sur f)

    Heuristique h(x) = |row(x) - goal_row|  (Manhattan, admissible).

    Fix : tuple (f, tie_breaker, position) pour éviter la comparaison
    Position < Position dans heapq quand les f sont égaux.
    """
    if start.row == goal_row:
        return [start]

    INF = float('inf')
    _tie = _count()  # tie-breaker

    # --- Init*(G, s, ∆, π, O, f) ---
    delta:      dict[Position, float]                = {}  # ∆
    pi:         dict[Position, Optional[Position]]   = {}  # π
    f_val:      dict[Position, float]                = {}  # f
    open_set:   set[Position]                        = set()  # O
    closed_set: set[Position]                        = set()

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            p = Position(r, c)
            delta[p] = INF   # ∆(x) ← +∞
            pi[p]    = None  # π(x) ← -1
            f_val[p] = INF   # f(x) ← Nil

    delta[start] = 0                              # ∆(s) ← 0
    open_set.add(start)                           # O(s) ← vrai
    f_val[start] = _heuristic(start, goal_row)    # f(s) ← h(s)

    # File de priorité : (f(x), tie, x)
    heap: list = [(f_val[start], next(_tie), start)]

    # Procédure A* : x ← s ; Tant que (x ≠ t) et (O ≠ ∅)
    while heap:
        # Choisir dans O le sommet x d'approximation f(x) minimale
        _, _, x = _heapq.heappop(heap)

        if x in closed_set:
            continue

        if x.row == goal_row:                     # x = t
            return _reconstruct_path(pi, x)

        # --- Examiner*(x, ∆, π, f, O) ---
        for y in board.get_neighbors(x):          # Pour tout successeur y de x
            if y in closed_set:
                continue
            new_g = delta[x] + 1.0                # ∆(x) + g(x,y)

            if new_g < delta[y]:                  # Si ∆(x)+g(x,y) < ∆(y)
                delta[y] = new_g                  # ∆(y) ← ∆(x) + g(x,y)
                pi[y]    = x                      # π(y) ← x
                f_val[y] = new_g + _heuristic(y, goal_row)  # f(y) ← ∆(y) + h(y)
                open_set.add(y)                   # Ouvrir*(y)
                _heapq.heappush(heap, (f_val[y], next(_tie), y))

        # Fermer*(x)
        open_set.discard(x)
        closed_set.add(x)

    return None  # Échec