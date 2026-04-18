from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

BOARD_SIZE = 9  # plateau 9x9


class Direction(Enum):
    NORTH = "N"
    SOUTH = "S"
    EAST  = "E"
    WEST  = "W"


class WallOrientation(Enum):
    HORIZONTAL = "H"  # bloque déplacements N/S
    VERTICAL   = "V"  # bloque déplacements E/W


@dataclass(frozen=True)
class Position:
    """Coordonnées (row, col) sur le plateau, 0-indexées."""
    row: int
    col: int

    def is_valid(self) -> bool:
        return 0 <= self.row < BOARD_SIZE and 0 <= self.col < BOARD_SIZE

    def neighbor(self, direction: Direction) -> "Position":
        deltas = {
            Direction.NORTH: (-1,  0),
            Direction.SOUTH: ( 1,  0),
            Direction.EAST:  ( 0,  1),
            Direction.WEST:  ( 0, -1),
        }
        dr, dc = deltas[direction]
        return Position(self.row + dr, self.col + dc)

    def __repr__(self) -> str:
        return f"({self.row},{self.col})"


@dataclass(frozen=True)
class Wall:
    """
    Une barrière couvre 2 segments d'arêtes.
    Position = coin supérieur-gauche de la barrière.
    - HORIZONTAL : bloque les arêtes S entre (row,col)-(row,col+1)
                   et entre (row,col+1)-(row,col+2)
    - VERTICAL   : bloque les arêtes E entre (row,col)-(row+1,col)
                   et entre (row+1,col)-(row+2,col)
    """
    position: Position
    orientation: WallOrientation

    def is_valid(self) -> bool:
        """Vérifie que la barrière tient dans le plateau (max index 7)."""
        r, c = self.position.row, self.position.col
        if self.orientation == WallOrientation.HORIZONTAL:
            return 0 <= r < BOARD_SIZE - 1 and 0 <= c < BOARD_SIZE - 1
        else:
            return 0 <= r < BOARD_SIZE - 1 and 0 <= c < BOARD_SIZE - 1


@dataclass
class Board:
    """
    Représente l'état du plateau.
    
    Stocke les barrières sous forme de frozensets d'arêtes bloquées.
    Une arête = tuple (Position_A, Position_B) avec A < B (ordre canonique).
    Cette structure est directement exploitable par les algos de graphe (BFS/A*).
    """
    size: int = BOARD_SIZE
    walls: set[Wall] = field(default_factory=set)
    _blocked_edges: set[tuple[Position, Position]] = field(
        default_factory=set, repr=False
    )

    def place_wall(self, wall: Wall) -> None:
        """Enregistre une barrière et marque les arêtes bloquées."""
        if not wall.is_valid():
            raise ValueError(f"Barrière invalide : {wall}")
        self.walls.add(wall)
        for edge in self._wall_to_edges(wall):
            self._blocked_edges.add(edge)

    def is_edge_blocked(self, a: Position, b: Position) -> bool:
        """Vérifie si l'arête entre deux cases adjacentes est bloquée."""
        edge = (a, b) if (a.row, a.col) < (b.row, b.col) else (b, a)
        return edge in self._blocked_edges

    def get_neighbors(self, pos: Position) -> list[Position]:
        """
        Retourne les voisins accessibles depuis pos (sans barrière entre eux).
        Utilisé directement par BFS, A*, Dijkstra.
        """
        neighbors = []
        for direction in Direction:
            neighbor = pos.neighbor(direction)
            if neighbor.is_valid() and not self.is_edge_blocked(pos, neighbor):
                neighbors.append(neighbor)
        return neighbors

    @staticmethod
    def _wall_to_edges(wall: Wall) -> list[tuple[Position, Position]]:
        """Convertit une Wall en liste de 2 arêtes bloquées (format canonique)."""
        r, c = wall.position.row, wall.position.col
        edges = []
        if wall.orientation == WallOrientation.HORIZONTAL:
            for dc in range(2):
                a = Position(r, c + dc)
                b = Position(r + 1, c + dc)
                edges.append((a, b) if (a.row, a.col) < (b.row, b.col) else (b, a))
        else:  # VERTICAL
            for dr in range(2):
                a = Position(r + dr, c)
                b = Position(r + dr, c + 1)
                edges.append((a, b) if (a.row, a.col) < (b.row, b.col) else (b, a))
        return edges

    def to_adjacency_dict(self) -> dict[Position, list[Position]]:
        """
        Export du graphe complet du plateau en dict d'adjacence.
        Format attendu par les algorithmes d'exploration (UCS, A*).
        """
        graph: dict[Position, list[Position]] = {}
        for r in range(self.size):
            for c in range(self.size):
                pos = Position(r, c)
                graph[pos] = self.get_neighbors(pos)
        return graph
