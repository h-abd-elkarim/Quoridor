/**
 * PATCH HUD.tsx — Ajout des boutons "Règles" et "Démos"
 * ═══════════════════════════════════════════════════════
 *
 * Ce fichier montre les modifications à apporter à votre HUD.tsx existant
 * pour intégrer les deux nouvelles fonctionnalités requises par la consigne.
 *
 * INSTRUCTIONS D'INTÉGRATION :
 * 1. Copier RulesModal.tsx et DemoPlayer.tsx dans src/components/
 * 2. Copier demo_games.ts dans src/data/
 * 3. Appliquer les modifications ci-dessous dans votre HUD.tsx existant.
 *
 * ─────────────────────────────────────────────────────────────────────────
 * MODIFICATION 1 : Ajouter les imports en haut de HUD.tsx
 * ─────────────────────────────────────────────────────────────────────────
 */

// Ajouter ces deux imports après les imports existants :
//
//   import RulesModal from "./RulesModal";
//   import DemoPlayer from "./DemoPlayer";

/*
 * ─────────────────────────────────────────────────────────────────────────
 * MODIFICATION 2 : Ajouter les états dans le composant HUD
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Ajouter ces deux lignes useState après les états existants dans HUD() :
 *
 *   const [showRules, setShowRules] = useState(false);
 *   const [showDemo, setShowDemo]   = useState(false);
 *
 * ─────────────────────────────────────────────────────────────────────────
 * MODIFICATION 3 : Insérer les boutons dans la section de contrôle du HUD
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Ajouter ce bloc JSX dans la section des boutons de contrôle,
 * par exemple juste après le bouton de sélection PvP/PvE :
 *
 *   <div className="flex gap-2 mt-2">
 *     <button
 *       onClick={() => setShowRules(true)}
 *       className="flex-1 px-3 py-1.5 text-[10px] font-mono uppercase
 *                  tracking-[0.2em] rounded-lg glass text-zinc-400
 *                  hover:text-white hover:border-violet-400/50 transition-all"
 *     >
 *       📖 Règles
 *     </button>
 *     <button
 *       onClick={() => setShowDemo(true)}
 *       className="flex-1 px-3 py-1.5 text-[10px] font-mono uppercase
 *                  tracking-[0.2em] rounded-lg glass text-zinc-400
 *                  hover:text-white hover:border-violet-400/50 transition-all"
 *     >
 *       🎬 Démos
 *     </button>
 *   </div>
 *
 * ─────────────────────────────────────────────────────────────────────────
 * MODIFICATION 4 : Monter les modaux à la fin du return() de HUD
 * ─────────────────────────────────────────────────────────────────────────
 *
 * Ajouter ces deux lignes juste avant le </> de fermeture du return() :
 *
 *   {showRules && <RulesModal onClose={() => setShowRules(false)} />}
 *   {showDemo  && <DemoPlayer onClose={() => setShowDemo(false)}  />}
 *
 * ─────────────────────────────────────────────────────────────────────────
 * VERSION COMPLÈTE (copier-coller le composant HUD minimal avec les ajouts)
 * ─────────────────────────────────────────────────────────────────────────
 */

import React, { useState } from "react";
import { useGameStore } from "../store/useGameStore";
import RulesModal from "./RulesModal";
import DemoPlayer from "./DemoPlayer";

/**
 * HUD — Panneau de télémétrie et de contrôle de la partie.
 *
 * Fonctionnalités intégrées (conformément à la consigne) :
 *  - Sélecteur PvP / PvE
 *  - Sélecteur de difficulté (EASY → MASTER)
 *  - Bouton "Règles" → RulesModal
 *  - Bouton "Démos"  → DemoPlayer
 *  - Métriques IA (algorithme, nœuds, profondeur, hash Zobrist)
 */
export default function HUD() {
  const {
    gameState,
    difficulty,
    setDifficulty,
    gameMode,
    setGameMode,
    isAIThinking,
    lastAIMetrics,
    createGame,
  } = useGameStore();

  // ── États locaux pour les modaux ─────────────────────────────────────
  /** Affichage du modal des règles */
  const [showRules, setShowRules] = useState(false);
  /** Affichage du lecteur de démos */
  const [showDemo, setShowDemo] = useState(false);

  if (!gameState) return null;

  const { players, current_player, status, turn } = gameState;
  const p1 = players["1"];
  const p2 = players["2"];

  // ── Rendu ─────────────────────────────────────────────────────────────
  return (
    <div className="w-72 flex flex-col gap-3 font-mono">

      {/* ── Statut de la partie ────────────────────────────────────────── */}
      <div className="glass rounded-xl p-4 border border-white/10">
        <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-2">
          Statut — Tour {turn}
        </p>
        <p className={`text-xs font-bold ${status === "ongoing" ? "text-emerald-400" : "text-amber-400"}`}>
          {status === "ongoing"
            ? `Joueur ${current_player} joue`
            : `Joueur ${status === "player1_wins" ? "1" : "2"} gagne !`}
        </p>
      </div>

      {/* ── Barrières restantes ────────────────────────────────────────── */}
      <div className="glass rounded-xl p-4 border border-white/10">
        <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-3">
          Barrières restantes
        </p>
        <div className="flex justify-between">
          {[
            { label: "Joueur 1", count: p1.walls_remaining, color: "bg-violet-500" },
            { label: "Joueur 2", count: p2.walls_remaining, color: "bg-amber-500" },
          ].map(({ label, count, color }) => (
            <div key={label}>
              <p className="text-[9px] text-zinc-500 mb-1">{label}</p>
              <div className="flex gap-0.5 flex-wrap w-28">
                {Array.from({ length: 10 }).map((_, i) => (
                  <div
                    key={i}
                    className={`w-2 h-2 rounded-sm transition-all ${i < count ? color : "bg-zinc-800"}`}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Mode de jeu ────────────────────────────────────────────────── */}
      <div className="glass rounded-xl p-4 border border-white/10">
        <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-2">
          Mode de jeu
        </p>
        <div className="flex gap-2">
          {(["PvP", "PvE"] as const).map((mode) => (
            <button
              key={mode}
              onClick={() => setGameMode(mode)}
              className={`flex-1 py-1.5 text-[10px] uppercase tracking-wider rounded-lg transition-all
                ${gameMode === mode
                  ? "bg-violet-600/40 border border-violet-500/50 text-violet-200"
                  : "glass text-zinc-500 hover:text-zinc-300"}`}
            >
              {mode === "PvP" ? "⚔ 1 vs 1" : "🤖 vs IA"}
            </button>
          ))}
        </div>
      </div>

      {/* ── Difficulté ─────────────────────────────────────────────────── */}
      {gameMode === "PvE" && (
        <div className="glass rounded-xl p-4 border border-white/10">
          <p className="text-[9px] text-zinc-500 uppercase tracking-widest mb-2">
            Niveau de difficulté
          </p>
          <div className="flex flex-col gap-1">
            {(["EASY", "MEDIUM", "HARD", "EXPERT", "MASTER"] as const).map((d) => (
              <button
                key={d}
                onClick={() => setDifficulty(d)}
                className={`py-1 text-[10px] uppercase tracking-wider rounded transition-all
                  ${difficulty === d
                    ? "bg-violet-600/30 text-violet-300 border border-violet-500/40"
                    : "text-zinc-500 hover:text-zinc-300"}`}
              >
                {d}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* ── Métriques IA ───────────────────────────────────────────────── */}
      {lastAIMetrics && (
        <div className="glass rounded-xl p-4 border border-violet-500/20">
          <p className="text-[9px] text-violet-400 uppercase tracking-widest mb-2 flex items-center gap-2">
            <span className={`w-1.5 h-1.5 rounded-full ${isAIThinking ? "bg-violet-400 animate-pulse" : "bg-zinc-600"}`} />
            Télémétrie IA
          </p>
          <div className="space-y-1">
            <MetricRow label="Algorithme" value={lastAIMetrics.algorithm} />
            <MetricRow label="Nœuds explorés" value={lastAIMetrics.nodes_explored?.toLocaleString()} />
            <MetricRow label="Profondeur" value={String(lastAIMetrics.depth)} />
            <MetricRow label="Durée" value={`${(lastAIMetrics.time_ms ?? 0).toFixed(0)} ms`} />
          </div>
        </div>
      )}

      {/* ── Boutons pédagogiques : Règles + Démos ──────────────────────── */}
      <div className="flex gap-2">
        {/* Bouton Règles — ouvre RulesModal */}
        <button
          onClick={() => setShowRules(true)}
          className="flex-1 px-3 py-2 text-[10px] font-mono uppercase tracking-[0.2em]
                     rounded-lg glass text-zinc-400 hover:text-white
                     hover:border-violet-400/50 transition-all"
          title="Consulter les règles du Quoridor"
        >
          📖 Règles
        </button>

        {/* Bouton Démos — ouvre DemoPlayer */}
        <button
          onClick={() => setShowDemo(true)}
          className="flex-1 px-3 py-2 text-[10px] font-mono uppercase tracking-[0.2em]
                     rounded-lg glass text-zinc-400 hover:text-white
                     hover:border-violet-400/50 transition-all"
          title="Voir des exemples de parties commentées"
        >
          🎬 Démos
        </button>
      </div>

      {/* Bouton nouvelle partie */}
      <button
        onClick={createGame}
        className="w-full py-2 text-[10px] uppercase tracking-widest rounded-lg
                   glass text-zinc-500 hover:text-white transition-all"
      >
        ↺ Nouvelle partie
      </button>

      {/* ── Modaux montés ici ──────────────────────────────────────────── */}
      {/* RulesModal : affiché quand showRules est vrai */}
      {showRules && <RulesModal onClose={() => setShowRules(false)} />}

      {/* DemoPlayer : affiché quand showDemo est vrai */}
      {showDemo && <DemoPlayer onClose={() => setShowDemo(false)} />}
    </div>
  );
}

// ── Sous-composant utilitaire ─────────────────────────────────────────────

/** Ligne de métrique clé/valeur dans le panneau de télémétrie. */
function MetricRow({ label, value }: { label: string; value?: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="text-[9px] text-zinc-600 uppercase tracking-wider">{label}</span>
      <span className="text-[9px] text-zinc-300 tabular-nums">{value ?? "—"}</span>
    </div>
  );
}
