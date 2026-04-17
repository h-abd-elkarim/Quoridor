import React from "react";
import { motion } from "framer-motion";

interface Props {
  row: number;
  col: number;
  hasP1: boolean;
  hasP2: boolean;
  isValidMove: boolean;
  currentPlayer: number;
}

/**
 * NB : ce composant n'est pas directement utilisé par Board.tsx refondu
 * (la grille est rendue inline), mais est conservé pour compatibilité
 * si tu veux l'utiliser ailleurs.
 */
export default function Cell({
  hasP1,
  hasP2,
  isValidMove,
  currentPlayer,
}: Props) {
  return (
    <div
      className={`
        w-12 h-12 rounded-md flex items-center justify-center cursor-pointer
        transition-all duration-150
        ${
          isValidMove
            ? "bg-emerald-400/15 ring-1 ring-emerald-400/60"
            : "bg-white/[0.02] ring-1 ring-white/5"
        }
      `}
    >
      {hasP1 && (
        <motion.div
          layoutId="pawn-1"
          className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-blue-700 ring-2 ring-blue-300/60 shadow-lg"
          animate={{
            scale: currentPlayer === 1 ? [1, 1.08, 1] : 1,
          }}
          transition={{
            repeat: currentPlayer === 1 ? Infinity : 0,
            duration: 1.4,
            ease: "easeInOut",
          }}
        />
      )}
      {hasP2 && (
        <motion.div
          layoutId="pawn-2"
          className="w-8 h-8 rounded-full bg-gradient-to-br from-red-400 to-red-700 ring-2 ring-red-300/60 shadow-lg"
          animate={{
            scale: currentPlayer === 2 ? [1, 1.08, 1] : 1,
          }}
          transition={{
            repeat: currentPlayer === 2 ? Infinity : 0,
            duration: 1.4,
            ease: "easeInOut",
          }}
        />
      )}
    </div>
  );
}