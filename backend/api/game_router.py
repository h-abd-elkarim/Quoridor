from __future__ import annotations
import uuid
from fastapi import APIRouter, HTTPException, Path, Response
from fastapi.responses import JSONResponse

from core import GameState
from core.board import Position, Wall, WallOrientation
from core.rules import (
    MoveAction, WallAction,
    apply_action, get_all_valid_actions,
    InvalidActionError,
)
from api.schemas import (
    ActionPayload, MoveRequest, WallRequest,
    GameStateOut, ValidActionsOut, CreateGameOut,
    game_state_to_out, valid_actions_to_out,
)

router = APIRouter(prefix="/games", tags=["game"])

# ---------------------------------------------------------------------------
# Stockage en mémoire (remplacé par Redis/DB à terme)
# ---------------------------------------------------------------------------
# Clé   : game_id (str UUID)
# Valeur: GameState
_games: dict[str, GameState] = {}


# ---------------------------------------------------------------------------
# POST /games  — créer une partie
# ---------------------------------------------------------------------------

@router.post("", response_model=CreateGameOut, status_code=201)
def create_game() -> CreateGameOut:
    """
    Initialise un nouveau GameState et le stocke en mémoire.
    Retourne un UUID stable que le frontend utilisera pour toutes les requêtes.
    """
    game_id = str(uuid.uuid4())
    _games[game_id] = GameState.new_game()
    return CreateGameOut(game_id=game_id, message="Partie créée avec succès.")


# ---------------------------------------------------------------------------
# GET /games/{game_id}  — état complet
# ---------------------------------------------------------------------------

@router.get("/{game_id}", response_model=GameStateOut)
def get_game(game_id: str = Path(...)) -> GameStateOut:
    state = _get_or_404(game_id)
    return game_state_to_out(game_id, state)


# ---------------------------------------------------------------------------
# GET /games/{game_id}/valid-actions  — coups légaux
# ---------------------------------------------------------------------------

@router.get("/{game_id}/valid-actions", response_model=ValidActionsOut)
def get_valid_actions(game_id: str = Path(...)) -> ValidActionsOut:
    """
    Retourne les mouvements et barrières légaux pour le joueur courant.
    Utilisé par le frontend pour afficher PathOverlay et les cases cliquables.

    Note : get_valid_walls() est O(N²×BFS) — acceptable en dev,
    on ajoutera un cache Zobrist au ticket IA.
    """
    state = _get_or_404(game_id)
    actions = get_all_valid_actions(state)
    return valid_actions_to_out(game_id, state, actions)


# ---------------------------------------------------------------------------
# POST /games/{game_id}/play  — jouer un coup
# ---------------------------------------------------------------------------

@router.post("/{game_id}/play", response_model=GameStateOut)
def play_action(
    payload: ActionPayload,
    game_id: str = Path(...),
) -> GameStateOut:
    """
    Valide et applique une action.
    Retourne le nouvel état complet après le coup.

    Codes HTTP :
      200 — coup appliqué, état mis à jour
      400 — coup illégal (InvalidActionError)
      404 — partie introuvable
      422 — payload malformé (Pydantic)
    """
    state = _get_or_404(game_id)

    if state.is_terminal():
        raise HTTPException(
            status_code=400,
            detail=f"La partie est terminée : {state.status.value}",
        )

    action = _parse_action(payload)

    try:
        new_state = apply_action(state, action)
    except InvalidActionError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    _games[game_id] = new_state
    return game_state_to_out(game_id, new_state)


# ---------------------------------------------------------------------------
# DELETE /games/{game_id}  — supprimer une partie (utile pour les tests)
# ---------------------------------------------------------------------------

@router.delete("/{game_id}", status_code=204, response_class=Response)
def delete_game(game_id: str = Path(...)):
    _get_or_404(game_id)
    del _games[game_id]
    
# ---------------------------------------------------------------------------
# Helpers privés
# ---------------------------------------------------------------------------

def _get_or_404(game_id: str) -> GameState:
    state = _games.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Partie '{game_id}' introuvable.")
    return state


def _parse_action(payload: ActionPayload):
    """
    Convertit un ActionRequest Pydantic en objet Action du domaine métier.
    Centralise la conversion pour ne pas polluer le routeur.
    """
    req = payload.action

    if isinstance(req, MoveRequest):
        return MoveAction(destination=Position(row=req.row, col=req.col))

    if isinstance(req, WallRequest):
        return WallAction(
            wall=Wall(
                position=Position(row=req.row, col=req.col),
                orientation=WallOrientation(req.orientation),
            )
        )

    raise HTTPException(status_code=422, detail="Type d'action inconnu.")
