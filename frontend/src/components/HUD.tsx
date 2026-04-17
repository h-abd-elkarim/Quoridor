import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useGameStore } from "../store/useGameStore";
import Counter from "./Counter";
import Tooltip from "./Tooltip";

interface Difficulty {
  key: string;
  label: string;
  algo: string;
  depth: number;
  color: string;
  explain: string;
}

const DIFFICULTIES: Difficulty[] = [
  {
    key: "EASY",
    label: "Facile",
    algo: "Minimax",
    depth: 1,
    color: "text-emerald-300",
    explain:
      "Minimax · exploration exhaustive de l'arbre de jeu à profondeur fixe. Maximise son score, minimise celui de l'adversaire.",
  },
  {
    key: "MEDIUM",
    label: "Moyen",
    algo: "Négamax",
    depth: 2,
    color: "text-cyan-300",
    explain:
      "Négamax · reformulation élégante de Minimax reposant sur max(a, b) = −min(−a, −b). Code unifié, même logique.",
  },
  {
    key: "HARD",
    label: "Difficile",
    algo: "α-β",
    depth: 3,
    color: "text-amber-300",
    explain:
      "Alpha-Bêta · Minimax enrichi d'un élagage : coupe les branches dont le score ne peut plus influencer la décision.",
  },
  {
    key: "EXPERT",
    label: "Expert",
    algo: "Négα-β",
    depth: 4,
    color: "text-orange-300",
    explain:
      "Négamax + Alpha-Bêta · combine la concision de Négamax et la puissance d'élagage d'α-β. Plus profond, plus vite.",
  },
  {
    key: "MASTER",
    label: "Maître",
    algo: "SSS*",
    depth: 3,
    color: "text-fuchsia-300",
    explain:
      "SSS* · algorithme best-first de Stockman. Explore les états les plus prometteurs d'abord via une file de priorité. Provablement ≤ α-β en nœuds visités.",
  },
];

export default function HUD() {
  const {
    gameState,
    isAIThinking,
    lastAIInfo,
    difficulty,
    setDifficulty,
    triggerAI,
    createGame,
  } = useGameStore();

  if (!gameState) return null;

  const p1 = gameState.players["1"];
  const p2 = gameState.players["2"];
  const isOver = gameState.status !== "ongoing";
  const currentDiff = DIFFICULTIES.find((d) => d.key === difficulty)!;

  return (
    <div className="flex flex-col gap-3 w-80">
      {/* Header télémétrie */}
      <div className="glass rounded-xl px-4 py-3 relative overflow-hidden">
        {isAIThinking && <div className="absolute inset-0 radar-sweep" />}
        <div className="relative flex items-center justify-between">
          <div>
            <p className="text-[9px] font-mono text-zinc-500 tracking-[0.28em] uppercase">
              Telemetry · Live
            </p>
            <p className="text-xs font-mono text-zinc-300 mt-1 tabular">
              Tour{" "}
              <span className="text-neon-violet">{gameState.turn}</span> · Joueur{" "}
              <span
                className={
                  gameState.current_player === 1
                    ? "text-blue-300"
                    : "text-red-300"
                }
              >
                {gameState.current_player}
              </span>
            </p>
          </div>
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-1.5">
              <motion.span
                className="w-1.5 h-1.5 rounded-full bg-neon-violet"
                animate={{ opacity: isAIThinking ? [0.3, 1, 0.3] : 1 }}
                transition={{
                  duration: 1,
                  repeat: isAIThinking ? Infinity : 0,
                }}
                style={{ boxShadow: "0 0 8px #c084fc" }}
              />
              <span className="text-[9px] font-mono uppercase tracking-widest text-zinc-500">
                {isAIThinking ? "compute" : "idle"}
              </span>
            </div>
            {gameState.zobrist_hash !== null && (
              <span className="text-[8px] font-mono text-zinc-700 tabular">
                0x{gameState.zobrist_hash.toString(16).slice(0, 8).toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Joueurs */}
      {([1, 2] as const).map((pid) => {
        const p = pid === 1 ? p1 : p2;
        const isActive = gameState.current_player === pid && !isOver;
        const palette =
          pid === 1
            ? {
                border: "border-blue-400/30",
                glow: "shadow-[0_0_24px_-8px_rgba(96,165,250,0.5)]",
                dot: "bg-blue-400",
                dotGlow: "0 0 8px #60a5fa",
                text: "text-blue-200",
                accent: "text-blue-300",
              }
            : {
                border: "border-red-400/30",
                glow: "shadow-[0_0_24px_-8px_rgba(248,113,113,0.5)]",
                dot: "bg-red-400",
                dotGlow: "0 0 8px #f87171",
                text: "text-red-200",
                accent: "text-red-300",
              };

        return (
          <motion.div
            key={pid}
            animate={{ opacity: isActive ? 1 : 0.55 }}
            transition={{ duration: 0.3 }}
            className={`glass rounded-xl p-4 border ${palette.border} ${
              isActive ? palette.glow : ""
            }`}
          >
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <motion.div
                  className={`w-2 h-2 rounded-full ${palette.dot}`}
                  animate={
                    isActive
                      ? { scale: [1, 1.4, 1], opacity: [0.7, 1, 0.7] }
                      : { opacity: 0.3 }
                  }
                  transition={{
                    duration: 1.4,
                    repeat: isActive ? Infinity : 0,
                    ease: "easeInOut",
                  }}
                  style={{
                    boxShadow: isActive ? palette.dotGlow : undefined,
                  }}
                />
                <span
                  className={`text-xs font-mono uppercase tracking-widest font-medium ${palette.text}`}
                >
                  Joueur {pid}
                </span>
              </div>
              <span className="text-[10px] font-mono text-zinc-500 tabular">
                ({p.position.row},{p.position.col})
              </span>
            </div>

            {/* Barre de barrières */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between text-[9px] font-mono text-zinc-500 uppercase tracking-wider">
                <span>Barrières</span>
                <span className="text-amber-300 tabular">
                  <Counter
                    value={p.walls_remaining}
                    format={(n) => `${n}/10`}
                    duration={400}
                  />
                </span>
              </div>
              <div className="flex gap-1">
                {Array.from({ length: 10 }, (_, i) => (
                  <motion.div
                    key={i}
                    className={`flex-1 h-1.5 rounded-full ${
                      i < p.walls_remaining
                        ? "bg-amber-400"
                        : "bg-white/[0.04]"
                    }`}
                    animate={{
                      scaleY: i < p.walls_remaining ? 1 : 0.5,
                      boxShadow:
                        i < p.walls_remaining
                          ? "0 0 6px rgba(251,191,36,0.45)"
                          : "none",
                    }}
                    transition={{ duration: 0.25, delay: i * 0.02 }}
                  />
                ))}
              </div>
            </div>
          </motion.div>
        );
      })}

      {/* Sélecteur difficulté */}
      <div className="glass rounded-xl p-3">
        <p className="text-[9px] font-mono text-zinc-500 tracking-[0.22em] uppercase mb-2">
          Algorithme IA
        </p>
        <div className="grid grid-cols-5 gap-1">
          {DIFFICULTIES.map((d) => {
            const active = difficulty === d.key;
            return (
              <Tooltip
                key={d.key}
                side="top"
                content={
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className={`font-semibold ${d.color}`}>
                        {d.algo}
                      </span>
                      <span className="text-[9px] text-zinc-500 tabular">
                        d={d.depth}
                      </span>
                    </div>
                    <p className="text-zinc-400 leading-snug">{d.explain}</p>
                  </div>
                }
              >
                <button
                  onClick={() => setDifficulty(d.key)}
                  className={`w-full py-2 text-[10px] font-mono uppercase tracking-wider rounded-lg border transition-all duration-200 ${
                    active
                      ? `${d.color} border-current bg-white/[0.04] shadow-[0_0_12px_-4px_currentColor]`
                      : "text-zinc-600 border-white/5 hover:border-white/15 hover:text-zinc-400"
                  }`}
                >
                  {d.label}
                </button>
              </Tooltip>
            );
          })}
        </div>
        <div className="mt-3 flex justify-between text-[9px] font-mono text-zinc-500 uppercase tracking-wider border-t border-white/5 pt-2">
          <span>
            Actif · <span className={currentDiff.color}>{currentDiff.algo}</span>
          </span>
          <span className="tabular">profondeur {currentDiff.depth}</span>
        </div>
      </div>

      {/* Bouton IA */}
      <motion.button
        whileHover={!isAIThinking && !isOver ? { scale: 1.015 } : {}}
        whileTap={!isAIThinking && !isOver ? { scale: 0.98 } : {}}
        onClick={triggerAI}
        disabled={isAIThinking || isOver}
        className={`relative rounded-xl py-3.5 text-xs font-mono uppercase tracking-[0.2em] font-semibold transition-all overflow-hidden border disabled:opacity-30 disabled:cursor-not-allowed ${
          isAIThinking
            ? "bg-fuchsia-500/10 text-fuchsia-200 border-fuchsia-400/50"
            : "bg-gradient-to-b from-violet-600 to-fuchsia-700 text-white border-violet-400/60 shadow-glow-violet hover:shadow-glow-fuchsia"
        }`}
      >
        {isAIThinking && (
          <>
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-fuchsia-400/25 to-transparent"
              animate={{ x: ["-100%", "200%"] }}
              transition={{ duration: 1.3, repeat: Infinity, ease: "linear" }}
            />
            <div className="absolute inset-0 flex items-center justify-start pl-4">
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.span
                    key={i}
                    className="w-1 h-1 rounded-full bg-fuchsia-300"
                    animate={{ opacity: [0.3, 1, 0.3] }}
                    transition={{
                      duration: 0.9,
                      repeat: Infinity,
                      delay: i * 0.15,
                    }}
                  />
                ))}
              </div>
            </div>
          </>
        )}
        <span className="relative z-10">
          {isAIThinking
            ? `${currentDiff.algo} compute…`
            : `▶  Coup IA · ${currentDiff.label}`}
        </span>
      </motion.button>

      {/* Télémétrie post-calcul */}
      <AnimatePresence mode="wait">
        {lastAIInfo && !isAIThinking && (
          <motion.div
            key={`${lastAIInfo.algorithm}-${lastAIInfo.nodes}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.3 }}
            className="glass rounded-xl p-3"
          >
            <p className="text-[9px] font-mono text-zinc-500 tracking-[0.22em] uppercase mb-2">
              Dernier calcul
            </p>
            <div className="grid grid-cols-3 gap-2">
              <TelemetryStat
                label="Algo"
                value={lastAIInfo.algorithm}
                color="text-fuchsia-300"
              />
              <TelemetryStat
                label="Nœuds"
                valueNode={
                  <Counter
                    value={lastAIInfo.nodes}
                    duration={900}
                    className="text-cyan-300 text-sm font-semibold"
                  />
                }
              />
              <TelemetryStat
                label="Prof."
                valueNode={
                  <span className="text-amber-300 text-sm font-semibold tabular">
                    d=
                    <Counter value={lastAIInfo.depth} duration={400} />
                  </span>
                }
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Victoire */}
      <AnimatePresence>
        {isOver && (
          <motion.div
            initial={{ scale: 0.85, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ type: "spring", stiffness: 280, damping: 22 }}
            className="glass-strong rounded-xl p-5 border border-emerald-400/40 text-center shadow-glow-emerald"
          >
            <p className="text-[9px] font-mono text-emerald-300/70 tracking-[0.3em] uppercase mb-2">
              Game Over
            </p>
            <p className="text-emerald-200 font-bold text-xl mb-1 tabular">
              {gameState.status === "player1_win"
                ? "Joueur 1 gagne"
                : "Joueur 2 gagne"}
            </p>
            <p className="text-zinc-500 text-[10px] font-mono mb-4 tabular">
              Terminé · tour {gameState.turn}
            </p>
            <button
              onClick={createGame}
              className="px-6 py-2.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 text-emerald-200 text-xs font-mono uppercase tracking-widest font-semibold border border-emerald-400/50 transition-all"
            >
              Nouvelle partie
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

/* --------- Micro-composant stat --------- */
function TelemetryStat({
  label,
  value,
  valueNode,
  color,
}: {
  label: string;
  value?: string;
  valueNode?: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="text-center px-1">
      <p className="text-[8px] font-mono text-zinc-600 uppercase tracking-widest">
        {label}
      </p>
      <div className="mt-1">
        {valueNode ?? (
          <span className={`text-sm font-semibold tabular ${color ?? ""}`}>
            {value}
          </span>
        )}
      </div>
    </div>
  );
}