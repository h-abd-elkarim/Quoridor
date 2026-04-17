import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WallPlaced } from "../api/client";

interface Props {
  ghost: WallPlaced | null;
  cellSize: number;
  gap: number;
  isValid: boolean;
}

export default function WallGhost({ ghost, cellSize, gap, isValid }: Props) {
  const unit = cellSize + gap;
  const thickness = 6;
  const span = cellSize * 2 + gap;

  if (!ghost) return null;

  const isH = ghost.orientation === "H";
  const style = isH
    ? {
        left: ghost.col * unit + gap / 2,
        top: (ghost.row + 1) * unit + gap / 2 - thickness / 2,
        width: span,
        height: thickness,
      }
    : {
        left: (ghost.col + 1) * unit + gap / 2 - thickness / 2,
        top: ghost.row * unit + gap / 2,
        width: thickness,
        height: span,
      };

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={`${ghost.row}-${ghost.col}-${ghost.orientation}-${isValid}`}
        className="absolute rounded-full pointer-events-none"
        style={{
          ...style,
          background: isValid
            ? "rgba(251, 191, 36, 0.55)"
            : "rgba(239, 68, 68, 0.55)",
          boxShadow: isValid
            ? "0 0 14px 2px rgba(251, 191, 36, 0.45)"
            : "0 0 16px 3px rgba(239, 68, 68, 0.6)",
        }}
        initial={{ opacity: 0 }}
        animate={{
          opacity: isValid ? 1 : [0.4, 0.9, 0.4],
        }}
        exit={{ opacity: 0 }}
        transition={
          isValid
            ? { duration: 0.12 }
            : { duration: 0.8, repeat: Infinity, ease: "easeInOut" }
        }
      />
    </AnimatePresence>
  );
}