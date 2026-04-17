import React, { useState } from "react";
import { motion } from "framer-motion";
import { useGameStore } from "../store/useGameStore";
import { WallPlaced } from "../api/client";
import Wall from "./Wall";
import WallGhost from "./WallGhost";
import PathOverlay from "./PathOverlay";

const BOARD_SIZE = 9;
const CELL_SIZE = 54;
const GAP = 4;

export default function Board() {
  const { gameState, validActions, playMove, playWall, isAIThinking } =
    useGameStore();
  const [wallMode, setWallMode] = useState<"H" | "V" | null>(null);
  const [ghostWall, setGhostWall] = useState<WallPlaced | null>(null);

  if (!gameState) return null;

  const p1 = gameState.players["1"].position;
  const p2 = gameState.players["2"].position;
  const validMoves = validActions?.moves ?? [];
  const validWalls = validActions?.walls ?? [];
  const currentPlayer = gameState.current_player;
  const isOver = gameState.status !== "ongoing";

  const isValidMove = (r: number, c: number) =>
    validMoves.some((m) => m.row === r && m.col === c);

  const isValidWall = (r: number, c: number, o: "H" | "V") =>
    validWalls.some(
      (w) => w.row === r && w.col === c && w.orientation === o
    );

  const handleCellClick = (row: number, col: number) => {
    if (isOver || isAIThinking) return;
    if (wallMode) {
      if (row < BOARD_SIZE - 1 && col < BOARD_SIZE - 1) {
        playWall(row, col, wallMode);
        setWallMode(null);
        setGhostWall(null);
      }
      return;
    }
    if (isValidMove(row, col)) playMove(row, col);
  };

  const handleCellHover = (row: number, col: number) => {
    if (!wallMode || row >= BOARD_SIZE - 1 || col >= BOARD_SIZE - 1) {
      setGhostWall(null);
      return;
    }
    setGhostWall({ row, col, orientation: wallMode });
  };

  const boardPx = BOARD_SIZE * (CELL_SIZE + GAP) + GAP;

  return (
    <div className="flex flex-col items-center gap-5">
      {/* Contrôles mode mur */}
      <div className="flex gap-2">
        {(["H", "V"] as const).map((o) => (
          <button
            key={o}
            onClick={() => setWallMode(wallMode === o ? null : o)}
            disabled={isAIThinking}
            className={`px-4 py-2 text-[10px] font-mono uppercase tracking-[0.2em] rounded-lg border transition-all duration-200 ${
              wallMode === o
                ? "bg-amber-400/15 text-amber-300 border-amber-400/70 shadow-glow-amber"
                : "glass text-zinc-500 hover:text-zinc-300 hover:border-amber-400/40"
            } disabled:opacity-30 disabled:cursor-not-allowed`}
          >
            Mur {o === "H" ? "─ Horizontal" : "│ Vertical"}
          </button>
        ))}
        {wallMode && (
          <button
            onClick={() => {
              setWallMode(null);
              setGhostWall(null);
            }}
            className="px-4 py-2 text-[10px] font-mono uppercase tracking-[0.2em] rounded-lg glass text-zinc-500 hover:text-zinc-300"
          >
            ✕ Annuler
          </button>
        )}
      </div>

      {/* Cadre holographique */}
      <motion.div
        className={`relative glass-strong rounded-2xl p-3 ${
          isAIThinking ? "ai-thinking-frame" : ""
        }`}
        animate={
          isAIThinking
            ? {}
            : {
                boxShadow: [
                  "0 0 0 1px rgba(255,255,255,0.06), 0 0 40px -20px rgba(192,132,252,0.15)",
                  "0 0 0 1px rgba(255,255,255,0.06), 0 0 40px -20px rgba(192,132,252,0.15)",
                ],
              }
        }
      >
        {/* Glow interne */}
        <div
          className="absolute inset-0 rounded-2xl pointer-events-none opacity-60"
          style={{
            background:
              "radial-gradient(ellipse at 50% 0%, rgba(192,132,252,0.12), transparent 60%)",
          }}
        />

        {/* Plateau */}
        <div
          className="relative select-none rounded-lg overflow-hidden"
          style={{
            width: boardPx,
            height: boardPx,
            background:
              "linear-gradient(145deg, rgba(15,15,28,0.9), rgba(8,8,16,0.95))",
          }}
          onMouseLeave={() => setGhostWall(null)}
        >
          {/* Grille holographique SVG (fond) */}
          <svg
            className="absolute inset-0 pointer-events-none"
            width={boardPx}
            height={boardPx}
            style={{ opacity: 0.18 }}
          >
            <defs>
              <pattern
                id="holo-grid"
                width={CELL_SIZE + GAP}
                height={CELL_SIZE + GAP}
                patternUnits="userSpaceOnUse"
              >
                <path
                  d={`M ${CELL_SIZE + GAP} 0 L 0 0 0 ${CELL_SIZE + GAP}`}
                  fill="none"
                  stroke="#c084fc"
                  strokeWidth="0.5"
                />
              </pattern>
            </defs>
            <rect width={boardPx} height={boardPx} fill="url(#holo-grid)" />
          </svg>

          {/* Cases */}
          {Array.from({ length: BOARD_SIZE }, (_, row) =>
            Array.from({ length: BOARD_SIZE }, (_, col) => {
              const hasP1 = p1.row === row && p1.col === col;
              const hasP2 = p2.row === row && p2.col === col;
              const validMove = isValidMove(row, col);
              const isWallTarget =
                wallMode !== null &&
                row < BOARD_SIZE - 1 &&
                col < BOARD_SIZE - 1 &&
                isValidWall(row, col, wallMode);
              const isWallBlocked =
                wallMode !== null &&
                row < BOARD_SIZE - 1 &&
                col < BOARD_SIZE - 1 &&
                !isValidWall(row, col, wallMode);

              return (
                <motion.div
                  key={`cell-${row}-${col}`}
                  className={`absolute flex items-center justify-center cursor-pointer rounded-md transition-colors duration-150 ${
                    validMove
                      ? "bg-emerald-400/[0.04] ring-1 ring-emerald-400/20"
                      : isWallTarget
                      ? "bg-amber-400/[0.04] ring-1 ring-amber-400/20"
                      : "bg-white/[0.015] ring-1 ring-white/[0.04] hover:ring-white/10"
                  } ${isWallBlocked ? "hover:ring-red-500/30" : ""}`}
                  style={{
                    left: col * (CELL_SIZE + GAP) + GAP / 2,
                    top: row * (CELL_SIZE + GAP) + GAP / 2,
                    width: CELL_SIZE,
                    height: CELL_SIZE,
                  }}
                  onClick={() => handleCellClick(row, col)}
                  onMouseEnter={() => handleCellHover(row, col)}
                  whileHover={
                    validMove
                      ? {
                          backgroundColor: "rgba(52, 211, 153, 0.1)",
                          scale: 1.02,
                        }
                      : {}
                  }
                >
                  {/* Coordonnées discrètes */}
                  <span className="absolute top-0.5 left-1 text-[8px] text-zinc-700 font-mono select-none tabular">
                    {String.fromCharCode(97 + col)}
                    {row + 1}
                  </span>

                  {hasP1 && (
                    <Pawn color="blue" isActive={currentPlayer === 1 && !isOver} />
                  )}
                  {hasP2 && (
                    <Pawn color="red" isActive={currentPlayer === 2 && !isOver} />
                  )}
                </motion.div>
              );
            })
          )}

          {/* PathOverlay BFS */}
          {!wallMode && !isAIThinking && (
            <PathOverlay
              validMoves={validMoves}
              playerRow={currentPlayer === 1 ? p1.row : p2.row}
              playerCol={currentPlayer === 1 ? p1.col : p2.col}
              cellSize={CELL_SIZE}
              gap={GAP}
            />
          )}

          {/* Barrières posées */}
          {gameState.walls_placed.map((w, i) => (
            <Wall
              key={`wall-${i}-${w.row}-${w.col}-${w.orientation}`}
              wall={w}
              cellSize={CELL_SIZE}
              gap={GAP}
            />
          ))}

          {/* Ghost wall */}
          <WallGhost
            ghost={ghostWall}
            cellSize={CELL_SIZE}
            gap={GAP}
            isValid={
              ghostWall !== null &&
              isValidWall(ghostWall.row, ghostWall.col, ghostWall.orientation)
            }
          />

          {/* Voile de réflexion IA */}
          {isAIThinking && (
            <motion.div
              className="absolute inset-0 pointer-events-none rounded-lg"
              style={{
                background:
                  "radial-gradient(circle at 50% 50%, rgba(192,132,252,0.08), transparent 70%)",
              }}
              animate={{ opacity: [0.4, 0.8, 0.4] }}
              transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
            />
          )}
        </div>

        {/* Légende coordonnées */}
        <div
          className="flex mt-2 text-[9px] font-mono text-zinc-700 tabular"
          style={{ paddingLeft: GAP / 2, paddingRight: GAP / 2 }}
        >
          {Array.from({ length: BOARD_SIZE }, (_, i) => (
            <div
              key={i}
              style={{ width: CELL_SIZE + GAP }}
              className="text-center"
            >
              {String.fromCharCode(97 + i)}
            </div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}

/* --------- Pion premium avec respiration --------- */
function Pawn({
  color,
  isActive,
}: {
  color: "blue" | "red";
  isActive: boolean;
}) {
  const palette =
    color === "blue"
      ? {
          core: "from-blue-300 via-blue-500 to-blue-800",
          ring: "ring-blue-300/70",
          glow: "rgba(96,165,250,0.55)",
          center: "bg-blue-200/80",
        }
      : {
          core: "from-red-300 via-red-500 to-red-800",
          ring: "ring-red-300/70",
          glow: "rgba(248,113,113,0.55)",
          center: "bg-red-200/80",
        };

  return (
    <motion.div
      layoutId={`pawn-${color}`}
      className="relative"
      transition={{ type: "spring", stiffness: 380, damping: 30 }}
    >
      {/* Halo de respiration */}
      {isActive && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{ background: palette.glow, filter: "blur(8px)" }}
          animate={{
            scale: [1, 1.4, 1],
            opacity: [0.4, 0.75, 0.4],
          }}
          transition={{
            duration: 1.8,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      )}

      {/* Corps du pion */}
      <motion.div
        className={`relative w-9 h-9 rounded-full flex items-center justify-center shadow-lg ring-2 ${palette.ring} bg-gradient-to-br ${palette.core}`}
        animate={
          isActive
            ? {
                boxShadow: [
                  `0 0 0 0 ${palette.glow}`,
                  `0 0 14px 4px ${palette.glow}`,
                  `0 0 0 0 ${palette.glow}`,
                ],
                scale: [1, 1.04, 1],
              }
            : {}
        }
        transition={{
          duration: 1.8,
          repeat: isActive ? Infinity : 0,
          ease: "easeInOut",
        }}
      >
        <div
          className={`w-3 h-3 rounded-full ${palette.center} shadow-inner`}
        />
      </motion.div>
    </motion.div>
  );
}