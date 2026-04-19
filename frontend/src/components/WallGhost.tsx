import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { WallPlaced } from "../api/client";

interface Props {
  ghost: WallPlaced | null;
  cellSize: number;
  gap: number;
  isValid: boolean;
}

/**
 * WallGhost — aperçu visuel du mur avant pose.
 *
 * CORRECTIONS anti-scintillement :
 *
 * 1. AnimatePresence sans mode="wait" (supprimé).
 *    L'ancien mode="wait" attendait la fin de l'exit (120ms) avant d'afficher
 *    la nouvelle position. Sur un survol rapide case→case, cela créait un
 *    flash invisible à chaque déplacement. Sans mode="wait", enter et exit
 *    se chevauchent : le ghost glisse directement sans disparaître.
 *
 * 2. La clé ne contient plus `isValid` dans sa partie principale.
 *    Avant : key=`${row}-${col}-${orientation}-${isValid}` forçait un
 *    remount complet (exit + enter) à chaque changement de validité, même
 *    si la position n'avait pas bougé → flash rouge→orange visible.
 *    Maintenant la clé change uniquement quand la POSITION change. La
 *    couleur (valid/invalid) est animée via une transition de style CSS
 *    sur le composant existant, sans remount.
 *
 * 3. Transition immédiate sur le déplacement (duration: 0) mais douce
 *    sur l'apparition/disparition (opacity 80ms). L'œil perçoit le
 *    glissement comme instantané sans latence visible.
 */
export default function WallGhost({ ghost, cellSize, gap, isValid }: Props) {
  const unit      = cellSize + gap;
  const thickness = 6;
  const span      = cellSize * 2 + gap;

  const getStyle = (g: WallPlaced) => {
    const isH = g.orientation === "H";
    return isH
      ? {
          left:   g.col * unit + gap / 2,
          top:    (g.row + 1) * unit + gap / 2 - thickness / 2,
          width:  span,
          height: thickness,
        }
      : {
          left:   (g.col + 1) * unit + gap / 2 - thickness / 2,
          top:    g.row * unit + gap / 2,
          width:  thickness,
          height: span,
        };
  };

  return (
    <AnimatePresence>
      {ghost && (
        <motion.div
          // La clé change uniquement si la position ou l'orientation change.
          // Le changement valid→invalid ne provoque plus de remount.
          key={`ghost-${ghost.row}-${ghost.col}-${ghost.orientation}`}
          className="absolute rounded-full pointer-events-none"
          style={{
            ...getStyle(ghost),
            // La couleur transite doucement via CSS (pas de remount Framer)
            background: isValid
              ? "rgba(251, 191, 36, 0.6)"
              : "rgba(239, 68, 68, 0.6)",
            boxShadow: isValid
              ? "0 0 14px 3px rgba(251, 191, 36, 0.5)"
              : "0 0 16px 4px rgba(239, 68, 68, 0.65)",
            transition: "background 0.15s ease, box-shadow 0.15s ease",
          }}
          // Apparition rapide, disparition rapide — pas de mode="wait"
          initial={{ opacity: 0 }}
          animate={{
            opacity: isValid
              ? 1
              : [0.45, 1, 0.45],   // clignotement rouge si invalide
          }}
          exit={{ opacity: 0, transition: { duration: 0.08 } }}
          transition={
            isValid
              ? { duration: 0.08 }
              : { duration: 0.75, repeat: Infinity, ease: "easeInOut" }
          }
        />
      )}
    </AnimatePresence>
  );
}