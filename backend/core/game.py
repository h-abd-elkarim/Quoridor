from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from .board import Board, Wall
from .player import Player, PlayerID, make_players


class GameStatus(Enum):
    ONGOING     = "ongoing"
    PLAYER1_WIN = "player1_win"
    PLAYER2_WIN = "player2_win"


@dataclass
class GameState:
    """
    État complet et immuable-friendly de la partie.

    Conçu pour être copié efficacement lors de la génération
    des nœuds fils dans Minimax / Négamax / αβ.
    """
    board: Board
    players: dict[PlayerID, Player]
    current_player_id: PlayerID = PlayerID.ONE
    turn_number: int = 0
    status: GameStatus = GameStatus.ONGOING

    @classmethod
    def new_game(cls) -> "GameState":
        """Point d'entrée principal — crée une partie fraîche."""
        p1, p2 = make_players()
        return cls(
            board=Board(),
            players={PlayerID.ONE: p1, PlayerID.TWO: p2},
            current_player_id=PlayerID.ONE,
        )

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_id]

    @property
    def opponent_id(self) -> PlayerID:
        return PlayerID.TWO if self.current_player_id == PlayerID.ONE else PlayerID.ONE

    @property
    def opponent(self) -> Player:
        return self.players[self.opponent_id]

    def clone(self) -> "GameState":
        """
        Clone manuel ultra-rapide — remplace deepcopy.
        Gain mesuré : x15 a x20 vs deepcopy.
        """
        new_board = object.__new__(Board)
        new_board.walls = set(self.board.walls)
        new_board._blocked_edges = set(self.board._blocked_edges)

        new_players = {}
        for pid, player in self.players.items():
            new_player = object.__new__(Player)
            new_player.id              = player.id
            new_player.position        = player.position
            # goal_row est une @property calculee depuis player.id, pas besoin de la copier
            new_player.walls_remaining = player.walls_remaining
            new_player.move_history    = list(player.move_history)
            new_players[pid] = new_player

        new_state = object.__new__(GameState)
        new_state.board             = new_board
        new_state.players           = new_players
        new_state.current_player_id = self.current_player_id
        new_state.turn_number       = self.turn_number
        new_state.status            = self.status

        return new_state

    def switch_turn(self) -> None:
        self.current_player_id = self.opponent_id
        self.turn_number += 1

    def check_victory(self) -> None:
        """Met a jour le statut si un joueur a atteint sa ligne d'arrivee."""
        if self.players[PlayerID.ONE].has_reached_goal():
            self.status = GameStatus.PLAYER1_WIN
        elif self.players[PlayerID.TWO].has_reached_goal():
            self.status = GameStatus.PLAYER2_WIN

    def is_terminal(self) -> bool:
        """Noeud terminal au sens Minimax — partie finie."""
        return self.status != GameStatus.ONGOING

    def to_dict(self) -> dict:
        """Serialisation legere pour l'API REST."""
        return {
            "turn": self.turn_number,
            "status": self.status.value,
            "current_player": self.current_player_id.value,
            "players": {
                pid.value: {
                    "position": {"row": p.position.row, "col": p.position.col},
                    "walls_remaining": p.walls_remaining,
                }
                for pid, p in self.players.items()
            },
            "walls_placed": [
                {
                    "row": w.position.row,
                    "col": w.position.col,
                    "orientation": w.orientation.value,
                }
                for w in self.board.walls
            ],
        }

    def get_all_valid_actions(self):
        """Proxy vers rules.get_all_valid_actions."""
        from .rules import get_all_valid_actions
        return get_all_valid_actions(self)

    def apply(self, action):
        """Proxy vers rules.apply_action."""
        from .rules import apply_action
        return apply_action(self, action)