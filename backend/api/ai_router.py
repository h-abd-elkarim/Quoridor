from __future__ import annotations
from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel

from core import GameState
from core.ai import get_ai_move, Difficulty, AIResult
from core.rules import MoveAction, WallAction
from api.schemas import GameStateOut, WallOut, game_state_to_out
from api.game_router import _games   # store partagé

router = APIRouter(prefix="/games", tags=["ai"])


class AIPlayResponse(BaseModel):
    """Réponse enrichie après un coup IA — inclut les métadonnées pédagogiques."""
    game_state: GameStateOut
    algorithm: str
    nodes_explored: int
    depth: int
    action_played: dict


@router.post("/{game_id}/ai-play", response_model=AIPlayResponse)
def ai_play(
    game_id: str = Path(...),
    difficulty: str = Query(default="HARD", description="EASY|MEDIUM|HARD|EXPERT|MASTER"),
) -> AIPlayResponse:
    """
    L'IA joue le meilleur coup pour le joueur courant.
    
    Retourne l'état après le coup + métadonnées pédagogiques :
    quel algorithme, combien de nœuds explorés, quelle profondeur.
    """
    state = _games.get(game_id)
    if state is None:
        raise HTTPException(status_code=404, detail=f"Partie '{game_id}' introuvable.")

    if state.is_terminal():
        raise HTTPException(status_code=400, detail="La partie est déjà terminée.")

    try:
        diff = Difficulty[difficulty.upper()]
    except KeyError:
        raise HTTPException(
            status_code=400,
            detail=f"Difficulté inconnue : '{difficulty}'. "
                   f"Valeurs : {[d.name for d in Difficulty]}",
        )

    result = get_ai_move(state, diff)

    if result.best_action is None:
        raise HTTPException(status_code=500, detail="L'IA n'a trouvé aucun coup valide.")

    from core.rules import apply_action
    new_state = apply_action(state, result.best_action)
    _games[game_id] = new_state

    # Sérialisation de l'action jouée pour l'affichage frontend
    action_played = _action_to_dict(result.best_action)

    return AIPlayResponse(
        game_state=game_state_to_out(game_id, new_state),
        algorithm=result.algorithm,
        nodes_explored=result.nodes_explored,
        depth=result.depth,
        action_played=action_played,
    )


def _action_to_dict(action) -> dict:
    if isinstance(action, MoveAction):
        return {
            "type": "move",
            "row": action.destination.row,
            "col": action.destination.col,
        }
    if isinstance(action, WallAction):
        return {
            "type": "wall",
            "row": action.wall.position.row,
            "col": action.wall.position.col,
            "orientation": action.wall.orientation.value,
        }
    return {}
