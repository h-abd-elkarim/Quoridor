import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_game() -> str:
    resp = client.post("/games")
    assert resp.status_code == 201
    return resp.json()["game_id"]


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


# ---------------------------------------------------------------------------
# POST /games
# ---------------------------------------------------------------------------

def test_create_game_returns_id():
    resp = client.post("/games")
    assert resp.status_code == 201
    data = resp.json()
    assert "game_id" in data
    assert len(data["game_id"]) == 36  # UUID v4


def test_two_games_have_distinct_ids():
    id1 = create_game()
    id2 = create_game()
    assert id1 != id2


# ---------------------------------------------------------------------------
# GET /games/{game_id}
# ---------------------------------------------------------------------------

def test_get_game_initial_state():
    gid = create_game()
    resp = client.get(f"/games/{gid}")
    assert resp.status_code == 200
    data = resp.json()

    assert data["turn"] == 0
    assert data["status"] == "ongoing"
    assert data["current_player"] == 1
    # P1 au centre du bord Nord
    assert data["players"]["1"]["position"] == {"row": 0, "col": 4}
    # P2 au centre du bord Sud
    assert data["players"]["2"]["position"] == {"row": 8, "col": 4}
    assert data["players"]["1"]["walls_remaining"] == 10
    assert data["walls_placed"] == []


def test_get_game_not_found():
    resp = client.get("/games/inexistant-id")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /games/{game_id}/valid-actions
# ---------------------------------------------------------------------------

def test_valid_actions_initial():
    gid = create_game()
    resp = client.get(f"/games/{gid}/valid-actions")
    assert resp.status_code == 200
    data = resp.json()

    # P1 en (0,4) : 3 mouvements (S, E, W)
    assert len(data["moves"]) == 3
    # Beaucoup de barrières disponibles sur plateau vide
    assert len(data["walls"]) > 0
    assert data["total_count"] == len(data["moves"]) + len(data["walls"])


# ---------------------------------------------------------------------------
# POST /games/{game_id}/play — mouvement
# ---------------------------------------------------------------------------

def test_play_valid_move():
    gid = create_game()
    payload = {"action": {"type": "move", "row": 1, "col": 4}}
    resp = client.post(f"/games/{gid}/play", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["players"]["1"]["position"] == {"row": 1, "col": 4}
    assert data["current_player"] == 2
    assert data["turn"] == 1


def test_play_invalid_move_returns_400():
    gid = create_game()
    # Case (8,8) est valide géométriquement mais illégale depuis (0,4)
    payload = {"action": {"type": "move", "row": 8, "col": 8}}
    resp = client.post(f"/games/{gid}/play", json=payload)
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /games/{game_id}/play — barrière
# ---------------------------------------------------------------------------

def test_play_valid_wall():
    gid = create_game()
    payload = {"action": {"type": "wall", "row": 4, "col": 4, "orientation": "H"}}
    resp = client.post(f"/games/{gid}/play", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["walls_placed"]) == 1
    assert data["players"]["1"]["walls_remaining"] == 9
    assert data["current_player"] == 2


def test_play_wall_reduces_count():
    gid = create_game()
    for col in [0, 2]:  # deux barrières valides non chevauchantes
        payload = {"action": {"type": "wall", "row": 3, "col": col, "orientation": "H"}}
        resp = client.post(f"/games/{gid}/play", json=payload)
        assert resp.status_code == 200
        # Après chaque coup de P1, c'est P2 qui joue — on simule P2 aussi
        p2_moves = client.get(f"/games/{gid}/valid-actions").json()["moves"]
        p2_payload = {"action": {"type": "move", "row": p2_moves[0]["row"], "col": p2_moves[0]["col"]}}
        client.post(f"/games/{gid}/play", json=p2_payload)

    state = client.get(f"/games/{gid}").json()
    assert state["players"]["1"]["walls_remaining"] == 8


# ---------------------------------------------------------------------------
# Flux complet : Créer → Jouer → Vérifier → Supprimer
# ---------------------------------------------------------------------------

def test_full_game_flow():
    # 1. Créer
    gid = create_game()

    # 2. P1 avance
    resp = client.post(f"/games/{gid}/play", json={
        "action": {"type": "move", "row": 1, "col": 4}
    })
    assert resp.status_code == 200
    assert resp.json()["current_player"] == 2

    # 3. P2 avance
    resp = client.post(f"/games/{gid}/play", json={
        "action": {"type": "move", "row": 7, "col": 4}
    })
    assert resp.status_code == 200
    assert resp.json()["current_player"] == 1

    # 4. Vérifier l'état
    state = client.get(f"/games/{gid}").json()
    assert state["players"]["1"]["position"] == {"row": 1, "col": 4}
    assert state["players"]["2"]["position"] == {"row": 7, "col": 4}
    assert state["turn"] == 2

    # 5. Supprimer
    resp = client.delete(f"/games/{gid}")
    assert resp.status_code == 204
    assert client.get(f"/games/{gid}").status_code == 404


# ---------------------------------------------------------------------------
# Payload malformé → 422 Pydantic
# ---------------------------------------------------------------------------

def test_malformed_payload_returns_422():
    gid = create_game()
    # Champ `type` absent → Pydantic doit rejeter
    resp = client.post(f"/games/{gid}/play", json={"action": {"row": 1, "col": 4}})
    assert resp.status_code == 422


def test_wall_out_of_bounds_returns_422():
    gid = create_game()
    # row=8 est hors limite pour une barrière (max 7)
    resp = client.post(f"/games/{gid}/play", json={
        "action": {"type": "wall", "row": 8, "col": 4, "orientation": "H"}
    })
    assert resp.status_code == 422
