from __future__ import annotations
from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field, model_validator


# ---------------------------------------------------------------------------
# Requêtes entrantes
# ---------------------------------------------------------------------------

class MoveRequest(BaseModel):
    """Déplacement de pion."""
    type: Literal["move"]
    row: int = Field(..., ge=0, le=8)
    col: int = Field(..., ge=0, le=8)


class WallRequest(BaseModel):
    """Pose de barrière."""
    type: Literal["wall"]
    row: int = Field(..., ge=0, le=7)
    col: int = Field(..., ge=0, le=7)
    orientation: Literal["H", "V"]


# Union discriminée sur le champ `type`
ActionRequest = Annotated[
    Union[MoveRequest, WallRequest],
    Field(discriminator="type"),
]


class ActionPayload(BaseModel):
    """Corps de POST /games/{game_id}/play"""
    action: ActionRequest


# ---------------------------------------------------------------------------
# Réponses sortantes
# ---------------------------------------------------------------------------

class PositionOut(BaseModel):
    row: int
    col: int


class PlayerOut(BaseModel):
    position: PositionOut
    walls_remaining: int


class WallOut(BaseModel):
    row: int
    col: int
    orientation: str


class GameStateOut(BaseModel):
    """
    Réponse complète de l'état du jeu.
    Conçu pour inclure le Zobrist hash (ticket IA) sans changement de contrat.
    """
    game_id: str
    turn: int
    status: str
    current_player: int
    players: dict[str, PlayerOut]
    walls_placed: list[WallOut]
    # Champ réservé pour le hash Zobrist (sera peuplé au ticket IA)
    zobrist_hash: int | None = None


class ValidActionsOut(BaseModel):
    game_id: str
    current_player: int
    moves: list[PositionOut]
    walls: list[WallOut]
    total_count: int


class ErrorOut(BaseModel):
    detail: str


class CreateGameOut(BaseModel):
    game_id: str
    message: str


# ---------------------------------------------------------------------------
# Helpers de conversion (GameState → schémas Pydantic)
# ---------------------------------------------------------------------------

def game_state_to_out(game_id: str, state) -> GameStateOut:
    """
    Convertit un GameState en réponse API.
    Découple la couche web de la représentation interne.
    """
    raw = state.to_dict()
    return GameStateOut(
        game_id=game_id,
        turn=raw["turn"],
        status=raw["status"],
        current_player=raw["current_player"],
        players={
            str(pid): PlayerOut(
                position=PositionOut(**p["position"]),
                walls_remaining=p["walls_remaining"],
            )
            for pid, p in raw["players"].items()
        },
        walls_placed=[
            WallOut(row=w["row"], col=w["col"], orientation=w["orientation"])
            for w in raw["walls_placed"]
        ],
    )


def valid_actions_to_out(game_id: str, state, actions) -> ValidActionsOut:
    """
    Sépare les actions légales en deux listes (moves / walls)
    pour faciliter le rendu côté React (PathOverlay, WallGhost, etc.).
    """
    from core.rules import MoveAction, WallAction

    moves = []
    walls = []

    for action in actions:
        if isinstance(action, MoveAction):
            moves.append(PositionOut(
                row=action.destination.row,
                col=action.destination.col,
            ))
        elif isinstance(action, WallAction):
            walls.append(WallOut(
                row=action.wall.position.row,
                col=action.wall.position.col,
                orientation=action.wall.orientation.value,
            ))

    return ValidActionsOut(
        game_id=game_id,
        current_player=state.current_player_id.value,
        moves=moves,
        walls=walls,
        total_count=len(moves) + len(walls),
    )
