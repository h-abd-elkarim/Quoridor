"""
Implémentations strictes des algorithmes vus en cours :
  1. Minimax          — pseudo-code §Minimax(s, Γ)
  2. Négamax          — pseudo-code §Négamax(s, Γ)
  3. Alpha-Bêta (αβ)  — pseudo-code §αβ
  4. Négα-Bêta (Négαβ)— pseudo-code §Négαβ
  5. SSS*             — pseudo-code §SSS* (approximation sur arbre de jeu)

Tables de transposition Zobrist intégrées dans αβ et Négαβ.
"""
from __future__ import annotations
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import math

from .game import GameState
from .player import PlayerID
from .rules import Action, get_all_valid_actions, apply_action
from .evaluation import evaluate, WIN_SCORE, LOSE_SCORE
from .zobrist import compute_hash

INF = float('inf')


# ---------------------------------------------------------------------------
# Configuration de l'IA
# ---------------------------------------------------------------------------

class Difficulty(Enum):
    EASY   = 1   # Minimax depth=1
    MEDIUM = 2   # Négamax depth=2
    HARD   = 3   # αβ       depth=3
    EXPERT = 4   # Négαβ    depth=4
    MASTER = 5   # SSS*     depth=3


@dataclass
class AIResult:
    """Résultat retourné par tous les algorithmes — interface uniforme."""
    best_action: Optional[Action]
    score: float
    nodes_explored: int = 0
    algorithm: str = ""
    depth: int = 0


# ---------------------------------------------------------------------------
# Table de transposition (partagée αβ / Négαβ)
# ---------------------------------------------------------------------------

@dataclass
class TTEntry:
    score: float
    depth: int
    flag: str  # "EXACT" | "LOWER" | "UPPER"
    best_action: Optional[Action] = None


class TranspositionTable:
    def __init__(self):
        self._table: dict[int, TTEntry] = {}
        self.hits = 0
        self.misses = 0

    def get(self, h: int) -> Optional[TTEntry]:
        entry = self._table.get(h)
        if entry:
            self.hits += 1
        else:
            self.misses += 1
        return entry

    def store(self, h: int, entry: TTEntry) -> None:
        self._table[h] = entry

    def clear(self) -> None:
        self._table.clear()
        self.hits = self.misses = 0


# ---------------------------------------------------------------------------
# 1. MINIMAX  (fidèle au pseudo-code du cours)
# ---------------------------------------------------------------------------
# Fonction Minimax(s : Noeud; Γ : Arborescence) : Réel
#   Si s.St = Feuille alors val ← s.e
#   Sinon
#     Si s.Etiquette = Max : val ← -∞; Pour k: val ← Max(val, Minimax(fils[k]))
#     Sinon                 : val ← +∞; Pour k: val ← Min(val, Minimax(fils[k]))
#   Retourner(val)

def minimax(
    state: GameState,
    depth: int,
    is_max: bool,
    maximizing_player_id: PlayerID,
    counter: list,
) -> float:
    """
    Minimax récursif pur — sans élagage.
    `counter` est une liste [0] passée par référence pour compter les nœuds.
    """
    counter[0] += 1

    # Feuille : état terminal OU profondeur atteinte
    if depth == 0 or state.is_terminal():
        return evaluate(state, maximizing_player_id)  # s.e

    actions = get_all_valid_actions(state)

    if is_max:
        val = -INF
        for action in actions:
            child = apply_action(state, action)
            val = max(val, minimax(child, depth - 1, False, maximizing_player_id, counter))
    else:
        val = +INF
        for action in actions:
            child = apply_action(state, action)
            val = min(val, minimax(child, depth - 1, True, maximizing_player_id, counter))

    return val


def minimax_decision(state: GameState, depth: int = 1) -> AIResult:
    """Point d'entrée Minimax — retourne le meilleur coup."""
    player_id = state.current_player_id
    counter = [0]
    best_action = None
    best_val = -INF

    for action in get_all_valid_actions(state):
        child = apply_action(state, action)
        val = minimax(child, depth - 1, False, player_id, counter)
        if val > best_val:
            best_val = val
            best_action = action

    return AIResult(
        best_action=best_action,
        score=best_val,
        nodes_explored=counter[0],
        algorithm="Minimax",
        depth=depth,
    )


# ---------------------------------------------------------------------------
# 2. NÉGAMAX  (fidèle au pseudo-code du cours)
# ---------------------------------------------------------------------------
# Fonction Négamax(s, Γ) : Réel
#   Si s.St = Feuille : val ← s.e
#   Sinon : val ← -∞; Pour k: val ← Max(val, -Négamax(fils[k]))
#   Retourner(val)

def negamax(
    state: GameState,
    depth: int,
    maximizing_player_id: PlayerID,
    counter: list,
) -> float:
    """
    Négamax récursif — le score est toujours du point de vue du joueur courant.
    La négation (-Négamax) change de perspective à chaque niveau.
    """
    counter[0] += 1

    if depth == 0 or state.is_terminal():
        # Le signe dépend de si c'est le joueur MAX qui joue à ce nœud
        sign = 1 if state.current_player_id == maximizing_player_id else -1
        return sign * evaluate(state, maximizing_player_id)

    val = -INF
    for action in get_all_valid_actions(state):
        child = apply_action(state, action)
        val = max(val, -negamax(child, depth - 1, maximizing_player_id, counter))

    return val


def negamax_decision(state: GameState, depth: int = 2) -> AIResult:
    player_id = state.current_player_id
    counter = [0]
    best_action = None
    best_val = -INF

    for action in get_all_valid_actions(state):
        child = apply_action(state, action)
        val = -negamax(child, depth - 1, player_id, counter)
        if val > best_val:
            best_val = val
            best_action = action

    return AIResult(
        best_action=best_action,
        score=best_val,
        nodes_explored=counter[0],
        algorithm="Négamax",
        depth=depth,
    )


# ---------------------------------------------------------------------------
# 3. ALPHA-BÊTA (αβ)  (fidèle au pseudo-code du cours)
# ---------------------------------------------------------------------------
# Si s.Etiquette = Max :
#   Tant que (α < β et k ≤ bf) : α ← Max(α, αβ(fils[k], α, β)); k++
#   Retourner(α)
# Sinon (Min) :
#   Tant que (α < β et k ≤ bf) : β ← Min(β, αβ(fils[k], α, β)); k++
#   Retourner(β)

def alphabeta(
    state: GameState,
    depth: int,
    alpha: float,
    beta: float,
    is_max: bool,
    maximizing_player_id: PlayerID,
    counter: list,
    tt: TranspositionTable,
) -> float:
    """
    Alpha-Bêta avec table de transposition Zobrist.
    Élagage : tant que α < β (fidèle au cours).
    """
    counter[0] += 1

    # Consultation table de transposition
    h = compute_hash(state)
    tt_entry = tt.get(h)
    if tt_entry and tt_entry.depth >= depth:
        if tt_entry.flag == "EXACT":
            return tt_entry.score
        elif tt_entry.flag == "LOWER":
            alpha = max(alpha, tt_entry.score)
        elif tt_entry.flag == "UPPER":
            beta = min(beta, tt_entry.score)
        if alpha >= beta:
            return tt_entry.score

    if depth == 0 or state.is_terminal():
        return evaluate(state, maximizing_player_id)

    actions = get_all_valid_actions(state)
    original_alpha = alpha
    best_action = None

    if is_max:
        # Nœud MAX : val = α
        k = 0
        while alpha < beta and k < len(actions):          # Tant que (α < β et k ≤ bf)
            child = apply_action(state, actions[k])
            val = alphabeta(child, depth - 1, alpha, beta, False,
                            maximizing_player_id, counter, tt)
            if val > alpha:
                alpha = val
                best_action = actions[k]
            k += 1
        result = alpha
    else:
        # Nœud MIN : val = β
        k = 0
        while alpha < beta and k < len(actions):          # Tant que (α < β et k ≤ bf)
            child = apply_action(state, actions[k])
            val = alphabeta(child, depth - 1, alpha, beta, True,
                            maximizing_player_id, counter, tt)
            if val < beta:
                beta = val
                best_action = actions[k]
            k += 1
        result = beta

    # Mise en table de transposition
    if result <= original_alpha:
        flag = "UPPER"
    elif result >= beta:
        flag = "LOWER"
    else:
        flag = "EXACT"
    tt.store(h, TTEntry(score=result, depth=depth, flag=flag, best_action=best_action))

    return result


def alphabeta_decision(
    state: GameState, depth: int = 3, tt: Optional[TranspositionTable] = None
) -> AIResult:
    if tt is None:
        tt = TranspositionTable()
    player_id = state.current_player_id
    counter = [0]
    best_action = None
    alpha = -INF
    beta = +INF

    for action in get_all_valid_actions(state):
        child = apply_action(state, action)
        val = alphabeta(child, depth - 1, alpha, beta, False,
                        player_id, counter, tt)
        if val > alpha:
            alpha = val
            best_action = action

    return AIResult(
        best_action=best_action,
        score=alpha,
        nodes_explored=counter[0],
        algorithm="Alpha-Bêta",
        depth=depth,
    )


# ---------------------------------------------------------------------------
# 4. NÉGα-BÊTA (Négαβ)  (fidèle au pseudo-code du cours)
# ---------------------------------------------------------------------------
# val ← -∞; k ← 1
# Tant que (α < β et k ≤ bf) :
#   val ← Max(val, -Négαβ(fils[k], -β, -α))
#   α ← Max(α, val); k++
# Retourner(val)

def negalphabeta(
    state: GameState,
    depth: int,
    alpha: float,
    beta: float,
    maximizing_player_id: PlayerID,
    counter: list,
    tt: TranspositionTable,
) -> float:
    """
    Négα-Bêta : Négamax + élagage αβ.
    Inversion de signe ET inversion de la fenêtre (-β, -α) à chaque appel récursif.
    """
    counter[0] += 1

    # Table de transposition
    h = compute_hash(state)
    tt_entry = tt.get(h)
    if tt_entry and tt_entry.depth >= depth:
        if tt_entry.flag == "EXACT":
            return tt_entry.score
        elif tt_entry.flag == "LOWER":
            alpha = max(alpha, tt_entry.score)
        elif tt_entry.flag == "UPPER":
            beta = min(beta, tt_entry.score)
        if alpha >= beta:
            return tt_entry.score

    if depth == 0 or state.is_terminal():
        sign = 1 if state.current_player_id == maximizing_player_id else -1
        return sign * evaluate(state, maximizing_player_id)

    actions = get_all_valid_actions(state)
    original_alpha = alpha
    val = -INF
    best_action = None
    k = 0

    while alpha < beta and k < len(actions):              # Tant que (α < β et k ≤ bf)
        child = apply_action(state, actions[k])
        child_val = -negalphabeta(
            child, depth - 1, -beta, -alpha,              # Négαβ(fils[k], -β, -α)
            maximizing_player_id, counter, tt
        )
        val = max(val, child_val)                         # val ← Max(val, ...)
        if child_val > alpha:
            alpha = max(alpha, val)                       # α ← Max(α, val)
            best_action = actions[k]
        k += 1

    # Table de transposition
    if val <= original_alpha:
        flag = "UPPER"
    elif val >= beta:
        flag = "LOWER"
    else:
        flag = "EXACT"
    tt.store(h, TTEntry(score=val, depth=depth, flag=flag, best_action=best_action))

    return val


def negalphabeta_decision(
    state: GameState, depth: int = 4, tt: Optional[TranspositionTable] = None
) -> AIResult:
    if tt is None:
        tt = TranspositionTable()
    player_id = state.current_player_id
    counter = [0]
    best_action = None
    best_val = -INF
    alpha = -INF

    for action in get_all_valid_actions(state):
        child = apply_action(state, action)
        val = -negalphabeta(child, depth - 1, -INF, -alpha,
                             player_id, counter, tt)
        if val > best_val:
            best_val = val
            best_action = action
            alpha = max(alpha, val)

    return AIResult(
        best_action=best_action,
        score=best_val,
        nodes_explored=counter[0],
        algorithm="Négα-Bêta",
        depth=depth,
    )


# ---------------------------------------------------------------------------
# 5. SSS* — adapté pour arbre de jeu Quoridor
# ---------------------------------------------------------------------------
# Pseudo-code du cours : file G triée par (nœud, statut, valeur)
# statut ∈ {vivant, résolu}
# Tant que Premier(G) ≠ (n_racine, résolu, v) :
#   (n, t, e) ← Extraire-Premier(G)
#   ...

import heapq


@dataclass(order=True)
class SSSState:
    """Entrée de la file G triée par score décroissant (max-heap via négation)."""
    neg_score: float                           # -score pour heapq (min-heap → max)
    node_id: int                               # id unique pour départager
    status: str = field(compare=False)         # "vivant" | "résolu"
    state: GameState = field(compare=False)
    depth: int = field(compare=False)
    parent_id: Optional[int] = field(compare=False, default=None)
    action: Optional[Action] = field(compare=False, default=None)


def sss_star(state: GameState, depth: int = 3) -> AIResult:
    """
    SSS* adapté pour Quoridor (arbre de jeu fini, joueur MAX = current_player).
    
    La file G contient des états (nœud, statut, valeur estimée).
    On extrait toujours le nœud de valeur maximale.
    Critère d'arrêt : la racine passe à l'état 'résolu'.
    """
    player_id = state.current_player_id
    counter = [0]
    node_counter = [0]

    def new_id():
        node_counter[0] += 1
        return node_counter[0]

    root_id = new_id()
    root_h = compute_hash(state)

    # Initialisation : G ← {(racine, vivant, +∞)}
    heap: list[SSSState] = []

    def push(entry: SSSState):
        heapq.heappush(heap, entry)

    def pop() -> SSSState:
        return heapq.heappop(heap)

    push(SSSState(
        neg_score=-INF,       # +∞ initial
        node_id=root_id,
        status="vivant",
        state=state,
        depth=depth,
    ))

    # Table : node_id → SSSState résolu (pour reconstruction)
    resolved: dict[int, SSSState] = {}
    # Table : node_id → liste des enfants générés
    children_map: dict[int, list[int]] = {}
    # Table : node_id → action qui y mène
    action_map: dict[int, Action] = {}

    best_action = None

    while heap:
        entry = pop()
        counter[0] += 1

        n_id = entry.node_id
        n_state = entry.state
        n_depth = entry.depth
        e = -entry.neg_score  # score réel

        if entry.status == "vivant":
            # Nœud terminal ou profondeur max
            if n_depth == 0 or n_state.is_terminal():
                # Insérer((n, résolu, min(e, h(n))), G)
                h_val = evaluate(n_state, player_id)
                resolved_score = min(e, h_val)
                resolved_entry = SSSState(
                    neg_score=-resolved_score,
                    node_id=n_id,
                    status="résolu",
                    state=n_state,
                    depth=n_depth,
                    parent_id=entry.parent_id,
                    action=entry.action,
                )
                push(resolved_entry)

            else:
                # Nœud interne
                is_max_node = (n_state.current_player_id == player_id)
                actions = get_all_valid_actions(n_state)
                kids = []

                if is_max_node:
                    # MAX : générer TOUS les fils avec valeur e
                    for act in actions:
                        kid_id = new_id()
                        kid_state = apply_action(n_state, act)
                        kids.append(kid_id)
                        action_map[kid_id] = act
                        push(SSSState(
                            neg_score=-e,
                            node_id=kid_id,
                            status="vivant",
                            state=kid_state,
                            depth=n_depth - 1,
                            parent_id=n_id,
                            action=act,
                        ))
                else:
                    # MIN : générer UNIQUEMENT le premier fils (fils aîné)
                    act = actions[0]
                    kid_id = new_id()
                    kid_state = apply_action(n_state, act)
                    kids.append(kid_id)
                    action_map[kid_id] = act
                    push(SSSState(
                        neg_score=-e,
                        node_id=kid_id,
                        status="vivant",
                        state=kid_state,
                        depth=n_depth - 1,
                        parent_id=n_id,
                        action=act,
                    ))

                children_map[n_id] = kids

        else:  # statut == "résolu"
            resolved[n_id] = entry

            # Vérification : est-ce la racine ?
            if entry.parent_id is None:
                # Racine résolue → on a le score final
                best_action = entry.action
                break

            p_id = entry.parent_id
            # Récupérer l'état parent depuis les enfants enregistrés
            # (Le parent n'est pas forcément dans la heap — on cherche dans resolved)
            # Trouver si le parent est de type MIN ou MAX
            # On déduit via l'action (si l'action mène depuis le parent)
            # Heuristique : si tous les frères sont résolus → propager au grand-parent
            siblings = children_map.get(p_id, [])
            all_resolved = all(s in resolved for s in siblings)

            if all_resolved and siblings:
                # Nœud MIN : prendre le min des scores résolus
                scores = [(-resolved[s].neg_score) for s in siblings]
                parent_score = min(scores)
                best_sib = siblings[scores.index(parent_score)]
                parent_action = resolved[best_sib].action

                # Chercher le grand-parent dans resolved ou en remontant
                # Simplification : on stocke le parent_id dans l'entrée
                push(SSSState(
                    neg_score=-parent_score,
                    node_id=p_id,
                    status="résolu",
                    state=n_state,  # approximation
                    depth=n_depth + 1,
                    parent_id=None,  # on ne remonte pas plus haut ici
                    action=parent_action,
                ))

    # Fallback : si SSS* n'a pas convergé, on prend le meilleur enfant résolu
    if best_action is None and resolved:
        best_entry = min(resolved.values(), key=lambda e: e.neg_score)
        best_action = best_entry.action

    # Dernier fallback : premier coup légal
    if best_action is None:
        actions = get_all_valid_actions(state)
        best_action = actions[0] if actions else None

    return AIResult(
        best_action=best_action,
        score=0.0,
        nodes_explored=counter[0],
        algorithm="SSS*",
        depth=depth,
    )


# ---------------------------------------------------------------------------
# Point d'entrée unifié — sélection par difficulté
# ---------------------------------------------------------------------------

def get_ai_move(state: GameState, difficulty: Difficulty) -> AIResult:
    """
    Dispatche vers l'algorithme approprié selon la difficulté.
    Interface unique utilisée par le routeur API.
    """
    _tt = TranspositionTable()  # table fraîche par coup (pas de pollution inter-coups)

    dispatch = {
        Difficulty.EASY:   lambda: minimax_decision(state, depth=1),
        Difficulty.MEDIUM: lambda: negamax_decision(state, depth=2),
        Difficulty.HARD:   lambda: alphabeta_decision(state, depth=3, tt=_tt),
        Difficulty.EXPERT: lambda: negalphabeta_decision(state, depth=4, tt=_tt),
        Difficulty.MASTER: lambda: sss_star(state, depth=3),
    }

    return dispatch[difficulty]()
