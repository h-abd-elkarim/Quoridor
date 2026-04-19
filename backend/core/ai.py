"""
Implementations des algorithmes de recherche adversariale pour Quoridor :
  1. Minimax          - pseudo-code du cours
  2. Negamax          - pseudo-code du cours
  3. Alpha-Beta (ab)  - avec TT Zobrist + move ordering + max_walls adaptatif
  4. Nega-Beta (Nab)  - avec TT Zobrist + move ordering + max_walls adaptatif
  5. SSS*             - avec fallback automatique sur Alpha-Beta

Tous les algorithmes utilisent :
  - apply_action_trusted  : pas de re-validation (elimine 2 BFS/noeud)
  - get_all_valid_actions_ordered : move ordering + limite de murs adaptative
  - clone() rapide : pas de deepcopy

Point d'entree unifie : get_ai_move(state, difficulty)
"""
from __future__ import annotations

import heapq
import logging
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from .evaluation import evaluate, WIN_SCORE, LOSE_SCORE
from .game import GameState
from .player import PlayerID
from .rules import (
    Action,
    apply_action,
    apply_action_trusted,
    get_all_valid_actions,
    get_all_valid_actions_ordered,
)
from .zobrist import compute_hash

INF = float('inf')

logger = logging.getLogger("quoridor.ai")

# ---------------------------------------------------------------------------
# Profilage (desactivable via PROFILING_ENABLED = False)
# ---------------------------------------------------------------------------

PROFILING_ENABLED = True

_profile_stats: dict = {
    "evaluate_calls":     0,
    "evaluate_total_ms":  0.0,
    "get_actions_calls":  0,
    "get_actions_total_ms": 0.0,
    "tt_hits":   0,
    "tt_misses": 0,
}


def _timed_evaluate(state: GameState, player_id: PlayerID) -> float:
    if not PROFILING_ENABLED:
        return evaluate(state, player_id)
    t0 = time.perf_counter()
    result = evaluate(state, player_id)
    _profile_stats["evaluate_calls"] += 1
    _profile_stats["evaluate_total_ms"] += (time.perf_counter() - t0) * 1000
    return result


def _timed_get_actions(state: GameState, max_walls: int = 12) -> list:
    if not PROFILING_ENABLED:
        return get_all_valid_actions_ordered(state, max_walls=max_walls)
    t0 = time.perf_counter()
    result = get_all_valid_actions_ordered(state, max_walls=max_walls)
    _profile_stats["get_actions_calls"] += 1
    _profile_stats["get_actions_total_ms"] += (time.perf_counter() - t0) * 1000
    return result


def log_profile_stats(label: str = "") -> None:
    s = _profile_stats
    n_eval    = max(1, s["evaluate_calls"])
    n_actions = max(1, s["get_actions_calls"])
    logger.info(
        f"[PROFIL {label}] "
        f"evaluate={s['evaluate_calls']}x avg={s['evaluate_total_ms']/n_eval:.3f}ms | "
        f"get_actions={s['get_actions_calls']}x avg={s['get_actions_total_ms']/n_actions:.3f}ms | "
        f"TT hits={s['tt_hits']} misses={s['tt_misses']}"
    )
    for k in s:
        s[k] = 0 if isinstance(s[k], int) else 0.0


# ---------------------------------------------------------------------------
# Configuration de l'IA
# ---------------------------------------------------------------------------

class Difficulty(Enum):
    EASY   = 1   # Minimax  depth=1
    MEDIUM = 2   # Negamax  depth=2
    HARD   = 3   # Alpha-Beta depth=3
    EXPERT = 4   # Nega-Beta  depth=4 (avec iterative deepening si > 4s)
    MASTER = 5   # SSS*       depth=3 (avec fallback ab)


@dataclass
class AIResult:
    """Resultat retourne par tous les algorithmes — interface uniforme."""
    best_action: Optional[Action]
    score: float
    nodes_explored: int = 0
    algorithm: str = ""
    depth: int = 0


# ---------------------------------------------------------------------------
# Table de transposition (partagee ab / Nab)
# ---------------------------------------------------------------------------

@dataclass
class TTEntry:
    score: float
    depth: int
    flag: str            # "EXACT" | "LOWER" | "UPPER"
    best_action: Optional[Action] = None


class TranspositionTable:
    def __init__(self) -> None:
        self._table: dict[int, TTEntry] = {}
        self.hits   = 0
        self.misses = 0

    def get(self, h: int) -> Optional[TTEntry]:
        entry = self._table.get(h)
        if entry:
            self.hits += 1
            _profile_stats["tt_hits"] += 1
        else:
            self.misses += 1
            _profile_stats["tt_misses"] += 1
        return entry

    def store(self, h: int, entry: TTEntry) -> None:
        self._table[h] = entry

    def clear(self) -> None:
        self._table.clear()
        self.hits = self.misses = 0


# ---------------------------------------------------------------------------
# Helpers : max_walls adaptatif par profondeur
# ---------------------------------------------------------------------------

def _max_walls_for_depth(depth: int) -> int:
    """
    Retourne le nombre max de murs a generer selon la profondeur restante.
    Plus on est en profondeur, moins de murs sont necessaires car :
      - L'elagage coupe rapidement les branches sous-optimales
      - Les murs lointains sont rarement joues en pratique
    
    Calibrage empirique (Python pur, board 9x9) :
      depth>=4 : 4  murs  -> branching ~7,  7^4 ~2400 noeuds max
      depth=3  : 6  murs  -> branching ~9,  9^3  ~730 noeuds max
      depth=2  : 8  murs  -> branching ~11, 11^2 ~121 noeuds max
      depth=1  : 12 murs  -> branching ~15,  15  noeuds
    """
    if depth >= 4:
        return 4
    if depth == 3:
        return 6
    if depth == 2:
        return 8
    return 12   # depth=1 ou racine


# ---------------------------------------------------------------------------
# 1. MINIMAX  (fidelement au pseudo-code du cours)
# ---------------------------------------------------------------------------

def minimax(
    state: GameState,
    depth: int,
    is_max: bool,
    maximizing_player_id: PlayerID,
    counter: list,
) -> float:
    """Minimax recursif pur sans elagage."""
    counter[0] += 1
    if depth == 0 or state.is_terminal():
        return evaluate(state, maximizing_player_id)

    mw      = _max_walls_for_depth(depth)
    actions = _timed_get_actions(state, max_walls=mw)

    if is_max:
        val = -INF
        for action in actions:
            child = apply_action_trusted(state, action)
            val = max(val, minimax(child, depth - 1, False, maximizing_player_id, counter))
    else:
        val = +INF
        for action in actions:
            child = apply_action_trusted(state, action)
            val = min(val, minimax(child, depth - 1, True, maximizing_player_id, counter))
    return val


def minimax_decision(state: GameState, depth: int = 1) -> AIResult:
    player_id   = state.current_player_id
    counter     = [0]
    best_action = None
    best_val    = -INF
    mw          = _max_walls_for_depth(depth)

    for action in _timed_get_actions(state, max_walls=mw):
        child = apply_action_trusted(state, action)
        val   = minimax(child, depth - 1, False, player_id, counter)
        if val > best_val:
            best_val    = val
            best_action = action

    return AIResult(
        best_action=best_action, score=best_val,
        nodes_explored=counter[0], algorithm="Minimax", depth=depth,
    )


# ---------------------------------------------------------------------------
# 2. NEGAMAX  (fidelement au pseudo-code du cours)
# ---------------------------------------------------------------------------

def negamax(
    state: GameState,
    depth: int,
    maximizing_player_id: PlayerID,
    counter: list,
) -> float:
    """Negamax recursif. Score du point de vue du joueur courant."""
    counter[0] += 1
    if depth == 0 or state.is_terminal():
        sign = 1 if state.current_player_id == maximizing_player_id else -1
        return sign * evaluate(state, maximizing_player_id)

    mw  = _max_walls_for_depth(depth)
    val = -INF
    for action in _timed_get_actions(state, max_walls=mw):
        child = apply_action_trusted(state, action)
        val   = max(val, -negamax(child, depth - 1, maximizing_player_id, counter))
    return val


def negamax_decision(state: GameState, depth: int = 2) -> AIResult:
    player_id   = state.current_player_id
    counter     = [0]
    best_action = None
    best_val    = -INF
    mw          = _max_walls_for_depth(depth)

    for action in _timed_get_actions(state, max_walls=mw):
        child = apply_action_trusted(state, action)
        val   = -negamax(child, depth - 1, player_id, counter)
        if val > best_val:
            best_val    = val
            best_action = action

    return AIResult(
        best_action=best_action, score=best_val,
        nodes_explored=counter[0], algorithm="Negamax", depth=depth,
    )


# ---------------------------------------------------------------------------
# 3. ALPHA-BETA  avec TT Zobrist + move ordering
# ---------------------------------------------------------------------------

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
    Alpha-Beta avec :
    - Table de transposition Zobrist
    - apply_action_trusted (sans re-validation)
    - Move ordering + max_walls adaptatif par profondeur
    """
    counter[0] += 1

    h        = compute_hash(state)
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
        return _timed_evaluate(state, maximizing_player_id)

    mw      = _max_walls_for_depth(depth)
    actions = _timed_get_actions(state, max_walls=mw)

    # Move ordering : essayer d'abord le meilleur coup stocke en TT
    if tt_entry and tt_entry.best_action and tt_entry.best_action in actions:
        actions = [tt_entry.best_action] + [a for a in actions if a != tt_entry.best_action]

    original_alpha = alpha
    best_action    = None

    if is_max:
        k = 0
        while alpha < beta and k < len(actions):
            child = apply_action_trusted(state, actions[k])
            val   = alphabeta(child, depth - 1, alpha, beta, False,
                              maximizing_player_id, counter, tt)
            if val > alpha:
                alpha       = val
                best_action = actions[k]
            k += 1
        result = alpha
    else:
        k = 0
        while alpha < beta and k < len(actions):
            child = apply_action_trusted(state, actions[k])
            val   = alphabeta(child, depth - 1, alpha, beta, True,
                              maximizing_player_id, counter, tt)
            if val < beta:
                beta        = val
                best_action = actions[k]
            k += 1
        result = beta

    flag = "UPPER" if result <= original_alpha else ("LOWER" if result >= beta else "EXACT")
    tt.store(h, TTEntry(score=result, depth=depth, flag=flag, best_action=best_action))
    return result


def alphabeta_decision(
    state: GameState, depth: int = 3, tt: Optional[TranspositionTable] = None
) -> AIResult:
    if tt is None:
        tt = TranspositionTable()
    player_id   = state.current_player_id
    counter     = [0]
    best_action = None
    alpha       = -INF
    beta        = +INF
    mw          = _max_walls_for_depth(depth)

    for action in _timed_get_actions(state, max_walls=mw):
        child = apply_action_trusted(state, action)
        val   = alphabeta(child, depth - 1, alpha, beta, False,
                          player_id, counter, tt)
        if val > alpha:
            alpha       = val
            best_action = action

    return AIResult(
        best_action=best_action, score=alpha,
        nodes_explored=counter[0], algorithm="Alpha-Beta", depth=depth,
    )


# ---------------------------------------------------------------------------
# 4. NEGA-BETA  avec TT Zobrist + move ordering
# ---------------------------------------------------------------------------

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
    Nega-Beta avec :
    - Table de transposition Zobrist
    - apply_action_trusted (sans re-validation)
    - Move ordering + max_walls adaptatif par profondeur
    """
    counter[0] += 1

    h        = compute_hash(state)
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
        return sign * _timed_evaluate(state, maximizing_player_id)

    mw      = _max_walls_for_depth(depth)
    actions = _timed_get_actions(state, max_walls=mw)

    if tt_entry and tt_entry.best_action and tt_entry.best_action in actions:
        actions = [tt_entry.best_action] + [a for a in actions if a != tt_entry.best_action]

    original_alpha = alpha
    val            = -INF
    best_action    = None
    k              = 0

    while alpha < beta and k < len(actions):
        child     = apply_action_trusted(state, actions[k])
        child_val = -negalphabeta(
            child, depth - 1, -beta, -alpha,
            maximizing_player_id, counter, tt
        )
        val = max(val, child_val)
        if child_val > alpha:
            alpha       = max(alpha, val)
            best_action = actions[k]
        k += 1

    flag = "UPPER" if val <= original_alpha else ("LOWER" if val >= beta else "EXACT")
    tt.store(h, TTEntry(score=val, depth=depth, flag=flag, best_action=best_action))
    return val


def negalphabeta_decision(
    state: GameState, depth: int = 4, tt: Optional[TranspositionTable] = None
) -> AIResult:
    if tt is None:
        tt = TranspositionTable()
    player_id   = state.current_player_id
    counter     = [0]
    best_action = None
    best_val    = -INF
    alpha       = -INF
    mw          = _max_walls_for_depth(depth)

    for action in _timed_get_actions(state, max_walls=mw):
        child = apply_action_trusted(state, action)
        val   = -negalphabeta(child, depth - 1, -INF, -alpha,
                               player_id, counter, tt)
        if val > best_val:
            best_val    = val
            best_action = action
            alpha       = max(alpha, val)

    return AIResult(
        best_action=best_action, score=best_val,
        nodes_explored=counter[0], algorithm="Nega-Beta", depth=depth,
    )


# ---------------------------------------------------------------------------
# Iterative Deepening avec time limit
# Utilise pour EXPERT (depth=4) : si depth=4 depasse TIME_LIMIT_EXPERT secondes,
# on retourne le meilleur resultat trouve a la profondeur precedente.
# ---------------------------------------------------------------------------

TIME_LIMIT_EXPERT = 4.0   # secondes max pour EXPERT
TIME_LIMIT_MASTER = 4.0   # secondes max pour MASTER


def negalphabeta_with_time_limit(state: GameState, max_depth: int = 4) -> AIResult:
    """
    Iterative Deepening + time limit pour Nega-Beta.
    Lance depth=1, 2, 3, ... jusqu'a max_depth ou jusqu'a TIME_LIMIT_EXPERT secondes.
    Retourne toujours le meilleur resultat complet de la derniere profondeur terminee.
    """
    t_start     = time.perf_counter()
    best_result = None
    tt          = TranspositionTable()

    for d in range(1, max_depth + 1):
        elapsed = time.perf_counter() - t_start
        # Si on a deja depasse la moitie du temps, on ne peut pas finir depth=d
        if elapsed > TIME_LIMIT_EXPERT * 0.85:
            logger.info(f"[EXPERT] Iterative deepening stoppe a depth={d-1} ({elapsed*1000:.0f}ms)")
            break

        try:
            result = negalphabeta_decision(state, depth=d, tt=tt)
            best_result = result
            logger.info(
                f"[EXPERT] depth={d} OK | nodes={result.nodes_explored} | "
                f"elapsed={( time.perf_counter()-t_start)*1000:.0f}ms"
            )
        except Exception as e:
            logger.warning(f"[EXPERT] depth={d} erreur : {e}")
            break

        if time.perf_counter() - t_start > TIME_LIMIT_EXPERT:
            break

    if best_result is None:
        # Fallback minimal
        best_result = negalphabeta_decision(state, depth=1, tt=tt)

    best_result.algorithm = f"Nega-Beta (ID depth={best_result.depth})"
    return best_result


# ---------------------------------------------------------------------------
# 5. SSS*  avec fallback automatique sur Alpha-Beta
# ---------------------------------------------------------------------------

@dataclass(order=True)
class _SSSEntry:
    """Entree de la file G triee par score decroissant (max-heap via negation)."""
    neg_score:  float
    node_id:    int
    status:     str        = field(compare=False)   # "vivant" | "resolu"
    game_state: GameState  = field(compare=False)
    depth:      int        = field(compare=False)
    parent_id:  Optional[int]    = field(compare=False, default=None)
    action:     Optional[Action] = field(compare=False, default=None)


def sss_star(state: GameState, depth: int = 3, max_nodes: int = 5000) -> AIResult:
    """
    SSS* adapte pour Quoridor.

    Estimation de l'espace de recherche : si depasse max_nodes,
    bascule sur Alpha-Beta (meme qualite, garantie de terminaison).

    Optimisations conservees :
    - apply_action_trusted  : pas de re-validation dans l'arbre
    - get_all_valid_actions_ordered : move ordering + max_walls adaptatif
    - is_max_map            : propagation MAX/MIN correcte
    - _max_walls_for_depth  : branching factor adaptatif par profondeur

    CORRECTION BUG (resolved_actions supprime) :
    L'ancien code stockait resolved_actions[p_id] = best_act, ou best_act
    etait l'action d'un noeud enfant (profondeur k+1). En remontant, chaque
    niveau ecrasait l'action par celle de ses fils, si bien que la racine
    finissait par recevoir une action de profondeur 2 ou 3, illegale dans
    l'etat initial.

    Correction : on supprime resolved_actions. Pour retrouver l'action a
    jouer depuis la racine, on remonte parent_map depuis le meilleur enfant
    jusqu'a trouver le fils direct de root_id. C'est l'unique action legale
    a retourner.
    """
    player_id = state.current_player_id
    mw        = _max_walls_for_depth(depth)

    # Estimation du branching factor → fallback si trop grand
    test_actions    = get_all_valid_actions_ordered(state, max_walls=mw)
    branching       = len(test_actions)
    estimated_nodes = branching ** depth

    if estimated_nodes > max_nodes:
        logger.warning(
            f"[SSS*] Espace estime trop grand ({estimated_nodes} >= {max_nodes}), "
            f"fallback Alpha-Beta depth={depth}"
        )
        tt     = TranspositionTable()
        result = alphabeta_decision(state, depth=depth, tt=tt)
        result.algorithm = "SSS* (via Alpha-Beta)"
        return result

    counter      = [0]
    node_counter = [0]

    def new_id() -> int:
        node_counter[0] += 1
        return node_counter[0]

    root_id = new_id()

    heap:            list                                                = []
    children_map:    dict[int, set]                                      = {}
    resolved_scores: dict[int, float]                                    = {}
    # resolved_actions SUPPRIME : dangereux (voir docstring)
    parent_map:      dict[int, tuple[Optional[int], Optional[Action]]]   = {
        root_id: (None, None)
    }
    is_max_map:      dict[int, bool]                                     = {}

    heapq.heappush(heap, _SSSEntry(
        neg_score=-INF, node_id=root_id, status="vivant",
        game_state=state, depth=depth
    ))

    best_action: Optional[Action] = None

    # ── Helper : retrouver l'action du fils direct de root_id ─────────────────
    def root_action_for(node_id: int) -> Optional[Action]:
        """
        Remonte parent_map depuis node_id jusqu'a trouver le fils direct
        de root_id, et retourne l'action qui y mene.

        Exemple pour depth=3 :
          feuille → enfant_B → enfant_A → root_id
        On s'arrete quand parent_map[current][0] == root_id,
        et on retourne parent_map[current][1] (l'action qui va de root a current).

        Complexite : O(depth), negligeable.
        """
        current = node_id
        while True:
            p_id, act = parent_map.get(current, (None, None))
            if p_id is None:
                # current EST la racine — ne devrait pas arriver en pratique
                return None
            if p_id == root_id:
                # current est le fils direct de la racine : act est l'action
                return act
            current = p_id

    # ── Boucle principale SSS* ────────────────────────────────────────────────
    while heap:
        entry   = heapq.heappop(heap)
        counter[0] += 1
        n_id    = entry.node_id
        n_state = entry.game_state
        n_depth = entry.depth
        e       = -entry.neg_score

        if entry.status == "vivant":
            if n_depth == 0 or n_state.is_terminal():
                h_val = evaluate(n_state, player_id)
                heapq.heappush(heap, _SSSEntry(
                    neg_score=-min(e, h_val), node_id=n_id,
                    status="resolu", game_state=n_state, depth=n_depth,
                    parent_id=entry.parent_id, action=entry.action
                ))
            else:
                is_max  = (n_state.current_player_id == player_id)
                is_max_map[n_id] = is_max
                node_mw = _max_walls_for_depth(n_depth)
                actions = get_all_valid_actions_ordered(n_state, max_walls=node_mw)

                if not actions:
                    h_val = evaluate(n_state, player_id)
                    heapq.heappush(heap, _SSSEntry(
                        neg_score=-min(e, h_val), node_id=n_id,
                        status="resolu", game_state=n_state, depth=n_depth,
                        parent_id=entry.parent_id, action=entry.action
                    ))
                    continue

                children_map[n_id] = set()

                if is_max:
                    # Noeud MAX : generer tous les fils
                    for act in actions:
                        kid_id    = new_id()
                        kid_state = apply_action_trusted(n_state, act)
                        children_map[n_id].add(kid_id)
                        parent_map[kid_id] = (n_id, act)
                        heapq.heappush(heap, _SSSEntry(
                            neg_score=-e, node_id=kid_id, status="vivant",
                            game_state=kid_state, depth=n_depth - 1,
                            parent_id=n_id, action=act
                        ))
                else:
                    # Noeud MIN : generer uniquement le fils aine
                    act       = actions[0]
                    kid_id    = new_id()
                    kid_state = apply_action_trusted(n_state, act)
                    children_map[n_id].add(kid_id)
                    parent_map[kid_id] = (n_id, act)
                    heapq.heappush(heap, _SSSEntry(
                        neg_score=-e, node_id=kid_id, status="vivant",
                        game_state=kid_state, depth=n_depth - 1,
                        parent_id=n_id, action=act
                    ))

        else:  # resolu
            resolved_scores[n_id] = e

            p_id, _ = parent_map.get(n_id, (None, None))

            # ── Cas 1 : le noeud resolu EST la racine ─────────────────────────
            # (arrive si depth=0 ou partie terminee des le premier noeud)
            if p_id is None:
                best_action = entry.action  # action directe, correcte
                break

            # ── Cas 2 : le parent de n_id est la racine ───────────────────────
            # Tous les fils de root_id sont-ils resolus ?
            root_children = children_map.get(root_id, set())
            if root_children and all(s in resolved_scores for s in root_children):
                parent_is_max = is_max_map.get(root_id, True)
                agg           = max if parent_is_max else min
                # Trouver le meilleur fils direct de la racine par score
                best_child_id = agg(root_children, key=lambda s: resolved_scores[s])
                # L'action legale = parent_map[best_child_id][1]
                _, best_action = parent_map[best_child_id]
                resolved_scores[root_id] = resolved_scores[best_child_id]
                break

            # ── Cas 3 : propagation vers le parent (non-racine) ───────────────
            siblings = children_map.get(p_id, set())
            if not siblings or not all(s in resolved_scores for s in siblings):
                continue  # Le parent attend encore d'autres fils

            # Tous les fils de p_id sont resolus : resoudre p_id
            parent_is_max = is_max_map.get(p_id, True)
            agg           = max if parent_is_max else min
            best_sib_id   = agg(siblings, key=lambda s: resolved_scores[s])
            resolved_scores[p_id] = resolved_scores[best_sib_id]
            # NE PAS ecrire resolved_actions[p_id] = ...
            # L'action sera recuperee via root_action_for() si besoin

            # Le parent vient d'etre resolu : verifier si son propre parent
            # est root_id, ce qui declencherait la resolution finale
            gp_id, _ = parent_map.get(p_id, (None, None))
            if gp_id is None:
                # p_id EST la racine (resolution directe)
                best_action = root_action_for(best_sib_id)
                break

            if gp_id == root_id:
                # p_id est un fils direct de la racine, peut-etre pas le seul
                # → on re-verifie si tous les fils de root_id sont resolus
                root_children = children_map.get(root_id, set())
                if root_children and all(s in resolved_scores for s in root_children):
                    root_is_max   = is_max_map.get(root_id, True)
                    root_agg      = max if root_is_max else min
                    best_child_id = root_agg(root_children, key=lambda s: resolved_scores[s])
                    _, best_action = parent_map[best_child_id]
                    resolved_scores[root_id] = resolved_scores[best_child_id]
                    break

    # ── Fallback de securite (ne doit pas etre atteint en pratique) ───────────
    if best_action is None:
        logger.warning("[SSS*] Aucun coup resolu, fallback sur premier coup valide")
        fallback    = get_all_valid_actions_ordered(state, max_walls=mw)
        best_action = fallback[0] if fallback else None

    return AIResult(
        best_action    = best_action,
        score          = resolved_scores.get(root_id, 0.0),
        nodes_explored = counter[0],
        algorithm      = "SSS*",
        depth          = depth,
    )


def get_ai_move(state: GameState, difficulty: Difficulty) -> AIResult:
    """
    Dispatche vers l'algorithme approprie selon la difficulte.
    Interface unique utilisee par le routeur API.

    EXPERT utilise l'iterative deepening avec time limit (4s max).
    MASTER utilise SSS* avec fallback Alpha-Beta si espace trop grand.
    Tous les niveaux utilisent les optimisations : clone rapide,
    apply_action_trusted, move ordering, max_walls adaptatif.
    """
    # Reset compteurs profil
    for k in _profile_stats:
        _profile_stats[k] = 0 if isinstance(_profile_stats[k], int) else 0.0

    _tt     = TranspositionTable()
    t_start = time.perf_counter()

    dispatch = {
        Difficulty.EASY:   lambda: minimax_decision(state, depth=1),
        Difficulty.MEDIUM: lambda: negamax_decision(state, depth=2),
        Difficulty.HARD:   lambda: alphabeta_decision(state, depth=3, tt=_tt),
        Difficulty.EXPERT: lambda: negalphabeta_with_time_limit(state, max_depth=4),
        Difficulty.MASTER: lambda: sss_star(state, depth=3),
    }

    result  = dispatch[difficulty]()
    elapsed = time.perf_counter() - t_start

    logger.info(
        f"[AI] {difficulty.name} | algo={result.algorithm} | "
        f"depth={result.depth} | nodes={result.nodes_explored} | "
        f"score={result.score:.1f} | {elapsed*1000:.0f}ms"
    )
    log_profile_stats(label=difficulty.name)

    if elapsed > 5.0:
        logger.error(
            f"[AI] TIMEOUT {elapsed:.1f}s pour {difficulty.name} — "
            f"verifier les optimisations ou reduire la profondeur"
        )

    return result