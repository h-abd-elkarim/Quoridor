import { useGameStore } from "../store/useGameStore";
import { motion, AnimatePresence } from "framer-motion";

export default function HUD() {
  const { gameState, isAIThinking, lastAIInfo, difficulty, setDifficulty, triggerAI } =
    useGameStore();

  if (!gameState) return null;

  const p1 = gameState.players["1"];
  const p2 = gameState.players["2"];
  const isOver = gameState.status !== "ongoing";

  return (
    <div className="flex flex-col gap-4 w-64">
      {/* Joueurs */}
      {[1, 2].map((pid) => {
        const p = pid === 1 ? p1 : p2;
        const isActive = gameState.current_player === pid && !isOver;
        return (
          <motion.div
            key={pid}
            animate={{ scale: isActive ? 1.03 : 1 }}
            className={`rounded-xl p-4 border ${
              pid === 1
                ? "border-blue-500/40 bg-blue-950/30"
                : "border-red-500/40 bg-red-950/30"
            }`}
          >
            <div className="flex justify-between items-center">
              <span className={`font-bold ${pid === 1 ? "text-blue-400" : "text-red-400"}`}>
                Joueur {pid}
              </span>
              {isActive && (
                <motion.span
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-xs text-emerald-400 font-medium"
                >
                  ● À toi
                </motion.span>
              )}
            </div>
            <div className="mt-2 text-sm text-gray-300">
              Murs restants :{" "}
              <span className="font-mono font-bold text-white">{p.walls_remaining}</span>
            </div>
            {/* Murs visuels */}
            <div className="flex gap-1 mt-2 flex-wrap">
              {Array.from({ length: 10 }, (_, i) => (
                <div
                  key={i}
                  className={`w-3 h-1 rounded-full transition-all ${
                    i < p.walls_remaining ? "bg-amber-400" : "bg-gray-700"
                  }`}
                />
              ))}
            </div>
          </motion.div>
        );
      })}

      {/* Sélecteur difficulté */}
      <div className="rounded-xl p-4 border border-gray-700 bg-gray-900/40">
        <p className="text-xs text-gray-400 mb-2 uppercase tracking-widest">Difficulté IA</p>
        {["EASY", "MEDIUM", "HARD", "EXPERT", "MASTER"].map((d) => (
          <button
            key={d}
            onClick={() => setDifficulty(d)}
            className={`mr-1 mb-1 px-2 py-1 text-xs rounded-md font-mono transition-all ${
              difficulty === d
                ? "bg-purple-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {d}
          </button>
        ))}
      </div>

      {/* Bouton IA */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.97 }}
        onClick={triggerAI}
        disabled={isAIThinking || isOver}
        className="rounded-xl py-3 bg-purple-600 hover:bg-purple-500 disabled:opacity-40
                   text-white font-bold tracking-wide transition-all"
      >
        {isAIThinking ? "IA réfléchit…" : "Faire jouer l'IA"}
      </motion.button>

      {/* Infos pédagogiques algo */}
      <AnimatePresence>
        {lastAIInfo && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            className="rounded-xl p-3 border border-purple-800/40 bg-purple-950/20 text-xs"
          >
            <p className="text-purple-300 font-mono">{lastAIInfo.algorithm}</p>
            <p className="text-gray-400">
              {lastAIInfo.nodes.toLocaleString()} nœuds · profondeur {lastAIInfo.depth}
            </p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Victoire */}
      <AnimatePresence>
        {isOver && (
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="rounded-xl p-4 bg-emerald-900/40 border border-emerald-500 text-center"
          >
            <p className="text-emerald-400 font-bold text-lg">
              {gameState.status === "player1_win" ? "Joueur 1 gagne !" : "Joueur 2 gagne !"}
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
