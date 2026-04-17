"""
Tests unitaires pour UCS et A*.
Couvre : plateau vide, barrières, détection de blocage complet.
"""
import pytest
from core.board import Board, Position, Wall, WallOrientation, BOARD_SIZE
from core.pathfinding import ucs, astar, bfs_shortest_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_board_with_walls(*walls: Wall) -> Board:
    b = Board()
    for w in walls:
        b.place_wall(w)
    return b


# ---------------------------------------------------------------------------
# 1. Plateau vide — les trois algos doivent donner le même résultat
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("algo", [ucs, astar, bfs_shortest_path])
def test_open_board_finds_path(algo):
    """Plateau vide : chemin trouvé en 8 pas depuis row=0 vers row=8."""
    board = Board()
    start = Position(0, 4)
    path = algo(board, start, goal_row=8)
    assert path is not None
    assert path[0] == start
    assert path[-1].row == 8
    assert len(path) == 9  # 8 pas = 9 nœuds


@pytest.mark.parametrize("algo", [ucs, astar])
def test_open_board_path_length_matches_bfs(algo):
    """UCS et A* doivent trouver un chemin de même longueur que BFS."""
    board = Board()
    start = Position(0, 4)
    ref    = bfs_shortest_path(board, start, goal_row=8)
    result = algo(board, start, goal_row=8)
    assert result is not None
    assert len(result) == len(ref)


# ---------------------------------------------------------------------------
# 2. Barrières partielles — chemin plus long mais toujours trouvé
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("algo", [ucs, astar])
def test_detour_around_wall(algo):
    """
    Barrière horizontale au milieu du couloir central :
    le chemin existe mais doit être plus long que 8 pas.
    """
    board = make_board_with_walls(
        Wall(Position(4, 3), WallOrientation.HORIZONTAL),
        Wall(Position(4, 5), WallOrientation.HORIZONTAL),
    )
    start = Position(0, 4)
    path = algo(board, start, goal_row=8)
    assert path is not None
    assert path[-1].row == 8
    assert len(path) > 9  # détour obligatoire


@pytest.mark.parametrize("algo", [ucs, astar])
def test_path_is_connected(algo):
    """Chaque pas du chemin retourné est bien un mouvement d'une case."""
    board = Board()
    start = Position(2, 2)
    path = algo(board, start, goal_row=8)
    assert path is not None
    for i in range(len(path) - 1):
        a, b = path[i], path[i + 1]
        manhattan = abs(a.row - b.row) + abs(a.col - b.col)
        assert manhattan == 1, f"Pas non adjacent : {a} → {b}"


# ---------------------------------------------------------------------------
# 3. Blocage total — les algos doivent retourner None
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("algo", [ucs, astar])
def test_full_block_returns_none(algo):
    """
    Blocage total : on injecte directement les 9 arêtes bloquées entre
    row=4 et row=5 dans _blocked_edges, sans passer par place_wall
    (qui refuse col > BOARD_SIZE-2 par design).
    Résultat : aucun passage possible entre row=4 et row=5 → None.
    """
    board = Board()
    # Bloquer manuellement les 9 arêtes horizontales entre row=4 et row=5
    for col in range(BOARD_SIZE):
        a = Position(4, col)
        b = Position(5, col)
        edge = (a, b)  # a < b car (4,x) < (5,x)
        board._blocked_edges.add(edge)

    start = Position(0, 4)
    path = algo(board, start, goal_row=8)
    assert path is None

# ---------------------------------------------------------------------------
# 4. Départ déjà sur la ligne d'arrivée
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("algo", [ucs, astar])
def test_start_is_goal(algo):
    """Si le départ est déjà sur la ligne but, retourne [start]."""
    board = Board()
    start = Position(8, 4)
    path = algo(board, start, goal_row=8)
    assert path is not None
    assert path == [start]


# ---------------------------------------------------------------------------
# 5. Cohérence UCS vs A* sur plateau avec barrières
# ---------------------------------------------------------------------------

def test_ucs_vs_astar_same_length():
    """UCS et A* doivent trouver des chemins de même longueur optimale."""
    board = make_board_with_walls(
        Wall(Position(2, 2), WallOrientation.VERTICAL),
        Wall(Position(5, 4), WallOrientation.HORIZONTAL),
        Wall(Position(3, 6), WallOrientation.VERTICAL),
    )
    start = Position(0, 4)
    p_ucs   = ucs(board, start, goal_row=8)
    p_astar = astar(board, start, goal_row=8)
    assert p_ucs is not None
    assert p_astar is not None
    assert len(p_ucs) == len(p_astar)