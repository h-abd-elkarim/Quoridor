import React from "react";
import { motion } from "framer-motion";

interface Props {
  validMoves: { row: number; col: number }[];
  playerRow: number;
  playerCol: number;
  cellSize: number;
  gap: number;
}

export default function PathOverlay({
  validMoves,
  playerRow,
  playerCol,
  cellSize,
  gap,
}: Props) {
  const unit = cellSize + gap;

  return (
    <>
      {validMoves.map((m, i) => {
        const dist =
          Math.abs(m.row - playerRow) + Math.abs(m.col - playerCol);
        return (
          <motion.div
            key={`${m.row}-${m.col}`}
            className="absolute pointer-events-none rounded-md"
            style={{
              left: m.col * unit + gap / 2,
              top: m.row * unit + gap / 2,
              width: cellSize,
              height: cellSize,
            }}
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{
              opacity: [0.35, 0.85, 0.35],
              scale: [0.9, 1, 0.9],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              delay: i * 0.09 + dist * 0.04,
              ease: "easeInOut",
            }}
          >
            <div className="w-full h-full rounded-md bg-emerald-400/20 ring-1 ring-emerald-400/60 shadow-[inset_0_0_12px_rgba(52,211,153,0.35)]" />
            {/* Crosshair central */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-1.5 h-1.5 rounded-full bg-emerald-300 shadow-[0_0_8px_rgba(52,211,153,0.9)]" />
            </div>
          </motion.div>
        );
      })}
    </>
  );
}