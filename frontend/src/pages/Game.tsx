import { useEffect } from "react";
import { useGameStore } from "../store/useGameStore";
import Board from "../components/Board";
import HUD from "../components/HUD";
import { motion } from "framer-motion";

export default function Game() {
  const { createGame, gameState, error } = useGameStore();

  useEffect(() => {
    createGame();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white flex flex-col items-center justify-center gap-8 p-8">
      <motion.h1
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-4xl font-bold tracking-tight bg-gradient-to-r from-amber-400 to-purple-400 bg-clip-text text-transparent"
      >
        Quoridor
      </motion.h1>

      {error && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-red-400 text-sm bg-red-950/30 px-4 py-2 rounded-lg border border-red-800"
        >
          {error}
        </motion.div>
      )}

      {gameState ? (
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          animate={{ opacity: 1, scale: 1 }}
          className="flex gap-8 items-start"
        >
          <Board />
          <HUD />
        </motion.div>
      ) : (
        <div className="text-gray-400 animate-pulse">Chargement…</div>
      )}
    </div>
  );
}
