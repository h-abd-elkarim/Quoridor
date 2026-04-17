import { motion } from "framer-motion";

interface Props {
  row: number;
  col: number;
  hasP1: boolean;
  hasP2: boolean;
  isValidMove: boolean;
  currentPlayer: number;
}

export default function Cell({ hasP1, hasP2, isValidMove, currentPlayer }: Props) {
  return (
    <div
      className={`
        w-12 h-12 rounded-sm flex items-center justify-center cursor-pointer
        transition-all duration-150
        ${isValidMove ? "bg-emerald-400/40 ring-2 ring-emerald-400" : "bg-amber-50/10"}
      `}
    >
      {hasP1 && (
        <motion.div
          layoutId="pawn-1"
          className="w-8 h-8 rounded-full bg-blue-500 shadow-lg ring-2 ring-blue-300"
          animate={{ scale: currentPlayer === 1 ? [1, 1.1, 1] : 1 }}
          transition={{ repeat: currentPlayer === 1 ? Infinity : 0, duration: 1.2 }}
        />
      )}
      {hasP2 && (
        <motion.div
          layoutId="pawn-2"
          className="w-8 h-8 rounded-full bg-red-500 shadow-lg ring-2 ring-red-300"
          animate={{ scale: currentPlayer === 2 ? [1, 1.1, 1] : 1 }}
          transition={{ repeat: currentPlayer === 2 ? Infinity : 0, duration: 1.2 }}
        />
      )}
    </div>
  );
}
