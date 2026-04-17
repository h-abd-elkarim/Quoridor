from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .board import Position, BOARD_SIZE

INITIAL_WALLS = 10  # chaque joueur commence avec 10 barrières


class PlayerID(Enum):
    ONE = 1  # part du bord NORD (row=0), objectif : row=8
    TWO = 2  # part du bord SUD (row=8), objectif : row=0


@dataclass
class Player:
    id: PlayerID
    position: Position
    walls_remaining: int = INITIAL_WALLS
    move_history: list[str] = field(default_factory=list)  # notation algébrique

    @property
    def goal_row(self) -> int:
        """Ligne d'arrivée du joueur."""
        return BOARD_SIZE - 1 if self.id == PlayerID.ONE else 0

    @property
    def start_row(self) -> int:
        return 0 if self.id == PlayerID.ONE else BOARD_SIZE - 1

    def has_reached_goal(self) -> bool:
        return self.position.row == self.goal_row

    def goal_positions(self) -> list[Position]:
        """Toutes les cases de la ligne d'arrivée (pour A* multi-target)."""
        return [Position(self.goal_row, c) for c in range(BOARD_SIZE)]

    def __repr__(self) -> str:
        return (
            f"Player({self.id.name} @ {self.position}, "
            f"walls={self.walls_remaining})"
        )


def make_players() -> tuple[Player, Player]:
    """Factory : crée les deux joueurs à leur position de départ."""
    p1 = Player(
        id=PlayerID.ONE,
        position=Position(row=0, col=BOARD_SIZE // 2),
    )
    p2 = Player(
        id=PlayerID.TWO,
        position=Position(row=BOARD_SIZE - 1, col=BOARD_SIZE // 2),
    )
    return p1, p2
