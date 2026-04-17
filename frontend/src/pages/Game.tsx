import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useGameStore } from "../store/useGameStore";
import Board from "../components/Board";
import HUD from "../components/HUD";

export default function Game() {
  const { createGame, gameState, error, isAIThinking } = useGameStore();

  useEffect(() => {
    createGame();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen bg-abyss-950 text-zinc-200 flex flex-col relative overflow-hidden">
      {/* --- Fond abyssal : grille holographique + glow --- */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.04]"
        style={{
          backgroundImage: `
            linear-gradient(rgba(192,132,252,0.25) 1px, transparent 1px),
            linear-gradient(90deg, rgba(192,132,252,0.25) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
        }}
      />
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 50% at 50% 0%, rgba(192,132,252,0.08), transparent 60%), radial-gradient(ellipse 60% 40% at 50% 100%, rgba(217,70,239,0.05), transparent 60%)",
        }}
      />

      {/* --- Cadre IA pulsant --- */}
      <AnimatePresence>
        {isAIThinking && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 pointer-events-none z-50"
          >
            <motion.div
              className="absolute inset-0"
              style={{
                boxShadow:
                  "inset 0 0 0 1px rgba(192,132,252,0.3), inset 0 0 120px rgba(192,132,252,0.08)",
              }}
              animate={{
                boxShadow: [
                  "inset 0 0 0 1px rgba(192,132,252,0.2), inset 0 0 60px rgba(192,132,252,0.05)",
                  "inset 0 0 0 2px rgba(217,70,239,0.45), inset 0 0 160px rgba(192,132,252,0.14)",
                  "inset 0 0 0 1px rgba(192,132,252,0.2), inset 0 0 60px rgba(192,132,252,0.05)",
                ],
              }}
              transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
            />
          </motion.div>
        )}
      </AnimatePresence>

      {/* --- Header --- */}
      <header className="relative z-10 flex items-center justify-between px-8 py-5 border-b border-white/5">
        <div className="flex items-center gap-4">
          <motion.div
            className="w-9 h-9 rounded-lg glass flex items-center justify-center relative"
            animate={isAIThinking ? { rotate: 360 } : { rotate: 0 }}
            transition={{
              duration: 4,
              repeat: isAIThinking ? Infinity : 0,
              ease: "linear",
            }}
          >
            <div className="w-4 h-4 border border-neon-violet rounded-sm" />
            <div className="absolute inset-1 border border-fuchsia-400/30 rounded" />
          </motion.div>
          <div>
            <h1 className="text-lg font-mono font-medium tracking-tight">
              <span className="text-neon-violet">Q</span>
              <span className="text-zinc-100">uoridor</span>
              <span className="text-zinc-600 mx-2">/</span>
              <span className="text-zinc-500 text-xs tracking-[0.28em] uppercase">
                Telemetry
              </span>
            </h1>
            <p className="text-[9px] font-mono text-zinc-600 tracking-[0.28em] uppercase mt-0.5">
              Algorithm Dashboard · Master Thesis
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {gameState && (
            <span className="text-[10px] font-mono text-zinc-600 tracking-wider hidden md:block tabular">
              ID {gameState.game_id.slice(0, 8)}
            </span>
          )}
          <button
            onClick={createGame}
            className="px-3 py-1.5 text-[10px] font-mono uppercase tracking-[0.2em] rounded-lg glass text-zinc-400 hover:text-white hover:border-neon-violet/50 transition-all"
          >
            Nouvelle partie
          </button>
        </div>
      </header>

      {/* --- Bandeau erreur --- */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="relative z-10 bg-red-950/30 border-b border-red-500/30 overflow-hidden"
          >
            <p className="text-red-300 text-[10px] font-mono uppercase tracking-widest px-8 py-2 flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-400 animate-pulse" />
              {error}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* --- Contenu principal --- */}
      <main className="relative z-10 flex-1 flex items-center justify-center p-6 lg:p-10">
        {gameState ? (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="flex flex-col lg:flex-row gap-8 items-center lg:items-start"
          >
            <Board />
            <HUD />
          </motion.div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className="w-8 h-8 border-2 border-neon-violet/30 border-t-neon-violet rounded-full animate-spin" />
            <p className="text-[10px] font-mono text-zinc-500 uppercase tracking-widest">
              Initialisation…
            </p>
          </div>
        )}
      </main>

      {/* --- Footer pédagogique --- */}
      <footer className="relative z-10 border-t border-white/5 px-8 py-3 flex justify-between text-[9px] font-mono text-zinc-600 tracking-widest uppercase">
        <span>BFS · A* · Minimax · Négamax · αβ · Négαβ · SSS*</span>
        <span>Zobrist · Tables de transposition</span>
      </footer>
    </div>
  );
}