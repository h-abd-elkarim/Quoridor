import React from "react";
import { motion } from "framer-motion";
import { WallPlaced } from "../api/client";

interface Props {
  wall: WallPlaced;
  cellSize: number;
  gap: number;
}

export default function Wall({ wall, cellSize, gap }: Props) {
  const unit = cellSize + gap;
  const thickness = 6;
  const span = cellSize * 2 + gap;

  const isH = wall.orientation === "H";

  const style = isH
    ? {
        left: wall.col * unit + gap / 2,
        top: (wall.row + 1) * unit + gap / 2 - thickness / 2,
        width: span,
        height: thickness,
        transformOrigin: "left center",
      }
    : {
        left: (wall.col + 1) * unit + gap / 2 - thickness / 2,
        top: wall.row * unit + gap / 2,
        width: thickness,
        height: span,
        transformOrigin: "center top",
      };

  return (
    <motion.div
      className="absolute rounded-full pointer-events-none"
      style={{
        ...style,
        background:
          "linear-gradient(90deg, rgba(251,191,36,0.95), rgba(245,158,11,1), rgba(251,191,36,0.95))",
        boxShadow:
          "0 0 14px 2px rgba(251,191,36,0.55), inset 0 0 6px rgba(255,255,255,0.35)",
      }}
      initial={{
        scaleX: isH ? 0 : 1,
        scaleY: isH ? 1 : 0,
        opacity: 0,
      }}
      animate={{ scaleX: 1, scaleY: 1, opacity: 1 }}
      transition={{
        type: "spring",
        stiffness: 260,
        damping: 14,
        mass: 0.7,
      }}
    >
      {/* Halo de déploiement */}
      <motion.div
        className="absolute inset-0 rounded-full bg-amber-300/40"
        initial={{ opacity: 0.9, scale: 1 }}
        animate={{ opacity: 0, scale: 1.8 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </motion.div>
  );
}