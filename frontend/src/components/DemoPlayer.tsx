/**
 * DemoPlayer.tsx
 * ──────────────
 * Lecteur interactif de parties de démonstration. Permet à l'utilisateur
 * de naviguer coup par coup dans 5 parties commentées, avec explication
 * tactique à chaque étape.
 *
 * Consigne universitaire : "L'utilisateur devra avoir la possibilité
 * d'avoir des exemples de parties."
 *
 * Props : onClose — callback de fermeture du lecteur.
 */

import React, { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { DEMO_GAMES, DemoGame, DemoMove } from "../data/demo_games";

// ── Constantes ─────────────────────────────────────────────────────────────

/** Taille du plateau (9×9) */
const BOARD_SIZE = 9;

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Reconstruit les positions des deux pions à partir d'une séquence de coups.
 * @param moves   Séquence de coups jusqu'à l'index `upTo` (exclus).
 * @returns       Positions actuelles des deux joueurs.
 */
function computePositions(
  moves: DemoMove[],
  upTo: number
): { p1: [number, number]; p2: [number, number] } {
  // Positions initiales (rangée 0 col 4 pour J1, rangée 8 col 4 pour J2)
  let p1: [number, number] = [0, 4];
  let p2: [number, number] = [8, 4];

  for (let i = 0; i < upTo; i++) {
    const m = moves[i];
    if (m.action.type === "move") {
      if (m.player === 1) p1 = [m.action.row, m.action.col];
      else p2 = [m.action.row, m.action.col];
    }
  }
  return { p1, p2 };
}

/**
 * Collecte toutes les barrières posées jusqu'à l'index `upTo`.
 */
function computeWalls(moves: DemoMove[], upTo: number) {
  return moves
    .slice(0, upTo)
    .filter((m) => m.action.type === "wall")
    .map((m) => m.action as { type: "wall"; row: number; col: number; orientation: "H" | "V" });
}

// ── Composant ──────────────────────────────────────────────────────────────

interface DemoPlayerProps {
  onClose: () => void;
}

export default function DemoPlayer({ onClose }: DemoPlayerProps) {
  // Indice de la partie de démo sélectionnée
  const [gameIdx, setGameIdx] = useState(0);
  // Indice du coup courant (0 = état initial)
  const [moveIdx, setMoveIdx] = useState(0);

  const game: DemoGame = DEMO_GAMES[gameIdx];
  const totalMoves = game.moves.length;

  /** Coup couramment affiché (null si état initial) */
  const currentMove: DemoMove | null =
    moveIdx > 0 ? game.moves[moveIdx - 1] : null;

  /** Positions reconstituées à l'étape courante */
  const { p1, p2 } = computePositions(game.moves, moveIdx);

  /** Barrières posées à l'étape courante */
  const walls = computeWalls(game.moves, moveIdx);

  // ── Handlers ─────────────────────────────────────────────────────────
  const goNext = useCallback(
    () => setMoveIdx((i) => Math.min(i + 1, totalMoves)),
    [totalMoves]
  );
  const goPrev = useCallback(
    () => setMoveIdx((i) => Math.max(i - 1, 0)),
    []
  );
  const selectGame = useCallback((idx: number) => {
    setGameIdx(idx);
    setMoveIdx(0);
  }, []);

  // ── Rendu ─────────────────────────────────────────────────────────────
  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        style={{ background: "rgba(10,6,20,0.88)" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      >
        <motion.div
          className="relative w-full max-w-3xl glass rounded-2xl border border-violet-500/30 overflow-hidden"
          initial={{ scale: 0.92, y: 24 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.92, y: 24 }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* En-tête */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <h2 className="font-mono text-sm font-bold uppercase tracking-widest text-violet-300">
              🎬 Exemples de parties
            </h2>
            <button
              onClick={onClose}
              className="text-zinc-500 hover:text-white transition-colors text-lg"
              aria-label="Fermer"
            >
              ✕
            </button>
          </div>

          {/* Sélecteur de parties */}
          <div className="flex overflow-x-auto gap-2 px-4 py-3 border-b border-white/10">
            {DEMO_GAMES.map((g, i) => (
              <button
                key={g.id}
                onClick={() => selectGame(i)}
                className={`
                  whitespace-nowrap px-3 py-1.5 rounded text-[10px] font-mono
                  uppercase tracking-wider transition-all
                  ${gameIdx === i
                    ? "bg-violet-600/40 text-violet-200 border border-violet-500/50"
                    : "text-zinc-500 hover:text-zinc-300 border border-transparent"}
                `}
              >
                {g.id}. {g.title}
              </button>
            ))}
          </div>

          {/* Corps : plateau + commentaire */}
          <div className="flex flex-col md:flex-row gap-4 p-5">
            {/* Mini-plateau de visualisation */}
            <div className="flex-shrink-0">
              <p className="text-[9px] font-mono text-zinc-600 uppercase tracking-widest mb-2">
                État du plateau — coup {moveIdx}/{totalMoves}
              </p>
              <MiniBoardView p1={p1} p2={p2} walls={walls} />
            </div>

            {/* Panneau d'information */}
            <div className="flex-1 flex flex-col gap-3">
              {/* Description de la partie */}
              <div className="p-3 rounded-lg bg-black/20 border border-white/10">
                <p className="text-[10px] font-mono text-violet-300 font-bold mb-1">
                  {game.title}
                </p>
                <p className="text-zinc-400 text-xs leading-4">{game.description}</p>
              </div>

              {/* Commentaire du coup courant */}
              <div className="flex-1 p-3 rounded-lg bg-violet-900/20 border border-violet-500/20 min-h-[80px]">
                {currentMove ? (
                  <>
                    <p className="text-[9px] font-mono text-violet-400 uppercase tracking-widest mb-1">
                      Coup {moveIdx} · Joueur {currentMove.player} ·{" "}
                      {currentMove.action.type === "move" ? "Déplacement" : "Barrière"}
                    </p>
                    <p className="text-zinc-200 text-xs leading-5">
                      {currentMove.comment}
                    </p>
                  </>
                ) : (
                  <p className="text-zinc-500 text-xs italic">
                    Appuyez sur <b>→</b> pour commencer la partie.
                  </p>
                )}
              </div>

              {/* Barre de progression */}
              <div className="w-full h-1 rounded-full bg-white/10 overflow-hidden">
                <div
                  className="h-full bg-violet-500 transition-all duration-300"
                  style={{ width: `${(moveIdx / totalMoves) * 100}%` }}
                />
              </div>

              {/* Contrôles */}
              <div className="flex justify-between items-center">
                <button
                  onClick={() => setMoveIdx(0)}
                  className="text-[10px] font-mono text-zinc-500 hover:text-white transition"
                >
                  ⏮ Début
                </button>
                <div className="flex gap-3">
                  <button
                    onClick={goPrev}
                    disabled={moveIdx === 0}
                    className="px-4 py-1.5 rounded glass text-[11px] font-mono disabled:opacity-30 hover:text-white transition"
                  >
                    ← Précédent
                  </button>
                  <button
                    onClick={goNext}
                    disabled={moveIdx === totalMoves}
                    className="px-4 py-1.5 rounded bg-violet-600/40 border border-violet-500/50 text-[11px] font-mono disabled:opacity-30 hover:bg-violet-600/60 transition"
                  >
                    Suivant →
                  </button>
                </div>
                <button
                  onClick={() => setMoveIdx(totalMoves)}
                  className="text-[10px] font-mono text-zinc-500 hover:text-white transition"
                >
                  Fin ⏭
                </button>
              </div>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ── Sous-composant : plateau miniature ────────────────────────────────────

interface MiniBoardViewProps {
  p1: [number, number];
  p2: [number, number];
  walls: Array<{ row: number; col: number; orientation: "H" | "V" }>;
}

/**
 * Représentation minimaliste du plateau 9×9.
 * Affiche les deux pions et les barrières posées.
 */
function MiniBoardView({ p1, p2, walls }: MiniBoardViewProps) {
  const CELL = 22; // Taille d'une cellule en pixels
  const SIZE = BOARD_SIZE * CELL;

  return (
    <svg
      width={SIZE + 2}
      height={SIZE + 2}
      className="rounded-lg border border-white/10"
      style={{ background: "rgba(10,6,20,0.8)" }}
    >
      {/* Grille de cellules */}
      {Array.from({ length: BOARD_SIZE }, (_, r) =>
        Array.from({ length: BOARD_SIZE }, (_, c) => {
          const isP1 = p1[0] === r && p1[1] === c;
          const isP2 = p2[0] === r && p2[1] === c;
          return (
            <rect
              key={`cell-${r}-${c}`}
              x={c * CELL + 1}
              y={r * CELL + 1}
              width={CELL - 1}
              height={CELL - 1}
              fill={isP1 ? "#7C3AED" : isP2 ? "#D97706" : "rgba(255,255,255,0.03)"}
              stroke="rgba(255,255,255,0.06)"
              strokeWidth={0.5}
              rx={1}
            />
          );
        })
      )}

      {/* Barrières */}
      {walls.map((w, i) => {
        const x = w.col * CELL + 1;
        const y = w.row * CELL + 1;
        if (w.orientation === "H") {
          return (
            <rect key={`wall-${i}`} x={x} y={y + CELL - 2} width={CELL * 2 - 1} height={3} fill="#D97706" rx={1} />
          );
        } else {
          return (
            <rect key={`wall-${i}`} x={x + CELL - 2} y={y} width={3} height={CELL * 2 - 1} fill="#D97706" rx={1} />
          );
        }
      })}

      {/* Labels des pions */}
      <text x={p1[1] * CELL + CELL / 2 + 1} y={p1[0] * CELL + CELL / 2 + 5} textAnchor="middle" fill="white" fontSize={10} fontWeight="bold">1</text>
      <text x={p2[1] * CELL + CELL / 2 + 1} y={p2[0] * CELL + CELL / 2 + 5} textAnchor="middle" fill="white" fontSize={10} fontWeight="bold">2</text>
    </svg>
  );
}
