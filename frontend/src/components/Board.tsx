import { useGameStore } from "../store/useGameStore";
import Cell from "./Cell";
import Wall from "./Wall";
import PathOverlay from "./PathOverlay";
import { motion } from "framer-motion";

const BOARD_SIZE = 9;

export default function Board() {
  const { gameState, validActions, playMove } = useGameStore();
  if (!gameState) return null;

  const p1 = gameState.players["1"].position;
  const p2 = gameState.players["2"].position;
  const validMoves = validActions?.moves ?? [];

  const isValidMove = (r: number, c: number) =>
    validMoves.some((m) => m.row === r && m.col === c);

  return (
    <div className="relative inline-block">
      {/* Grille 9×9 */}
      <div
        className="grid gap-0.5 bg-amber-900/20 p-1 rounded-lg"
        style={{ gridTemplateColumns: `repeat(${BOARD_SIZE}, 1fr)` }}
      >
        {Array.from({ length: BOARD_SIZE }, (_, row) =>
          Array.from({ length: BOARD_SIZE }, (_, col) => (
            <motion.div
              key={`${row}-${col}`}
              whileHover={isValidMove(row, col) ? { scale: 1.08 } : {}}
              onClick={() => isValidMove(row, col) && playMove(row, col)}
            >
              <Cell
                row={row}
                col={col}
                hasP1={p1.row === row && p1.col === col}
                hasP2={p2.row === row && p2.col === col}
                isValidMove={isValidMove(row, col)}
                currentPlayer={gameState.current_player}
              />
            </motion.div>
          ))
        )}
      </div>

      {/* Barrières */}
      {gameState.walls_placed.map((w, i) => (
        <Wall key={i} wall={w} />
      ))}

      {/* Overlay BFS pédagogique */}
      <PathOverlay validMoves={validMoves} />
    </div>
  );
}
