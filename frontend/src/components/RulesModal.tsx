/**
 * RulesModal.tsx
 * ──────────────
 * Modal pédagogique présentant les règles complètes du jeu Quoridor.
 * Accessible depuis le bouton "Règles" du HUD.
 *
 * Consigne universitaire : "L'utilisateur devra avoir la possibilité
 * de connaître les règles."
 */

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

// ── Types ──────────────────────────────────────────────────────────────────
interface RulesModalProps {
  /** Callback de fermeture du modal */
  onClose: () => void;
}

// ── Données textuelles des règles ──────────────────────────────────────────
const RULES_SECTIONS = [
  {
    title: "🎯 Objectif",
    content:
      "Chaque joueur doit amener son pion jusqu'à la rangée opposée du plateau. " +
      "Le Joueur 1 (violet) part du bas et vise la rangée 9. " +
      "Le Joueur 2 (ambre) part du haut et vise la rangée 1.",
  },
  {
    title: "♟ Déplacement du pion",
    content:
      "À chaque tour, un joueur peut déplacer son pion d'une case dans l'une " +
      "des quatre directions cardinales (Nord, Sud, Est, Ouest), à condition " +
      "qu'aucune barrière ne bloque le passage et que la case soit libre.\n\n" +
      "Si les deux pions sont adjacents :\n" +
      "• Saut direct → si la case derrière l'adversaire est libre.\n" +
      "• Bifurcation → si elle est bloquée (barrière ou bord), on peut " +
      "aller latéralement.",
  },
  {
    title: "🧱 Pose d'une barrière",
    content:
      "Chaque joueur possède 10 barrières. Une barrière couvre 2 segments " +
      "d'arêtes consécutifs et peut être horizontale ou verticale.\n\n" +
      "⚠ Règle fondamentale : il est INTERDIT de poser une barrière qui " +
      "bloquerait totalement l'un des joueurs — chaque joueur doit toujours " +
      "avoir au moins un chemin vers sa ligne d'arrivée (vérifié par BFS).",
  },
  {
    title: "🏆 Victoire",
    content:
      "La partie se termine dès qu'un joueur atteint n'importe quelle case " +
      "de sa rangée d'arrivée. Ce joueur est déclaré vainqueur.",
  },
  {
    title: "💡 Conseils stratégiques",
    content:
      "• Avancez vite en début de partie pour forcer l'adversaire à poser des barrières.\n" +
      "• Utilisez vos barrières pour allonger le chemin adverse, pas pour bloquer complètement.\n" +
      "• Gardez quelques barrières en réserve pour la phase finale.\n" +
      "• Lorsque vous n'avez plus de barrières, foncez : votre seul atout est la vitesse.",
  },
];

// ── Composant principal ────────────────────────────────────────────────────
export default function RulesModal({ onClose }: RulesModalProps) {
  // Index de la section actuellement affichée
  const [activeSection, setActiveSection] = useState(0);

  return (
    // Overlay sombre
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        style={{ background: "rgba(10,6,20,0.85)" }}
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose} // Ferme en cliquant à l'extérieur
      >
        {/* Fenêtre du modal */}
        <motion.div
          className="relative w-full max-w-2xl glass rounded-2xl border border-violet-500/30 overflow-hidden"
          initial={{ scale: 0.92, y: 24 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.92, y: 24 }}
          onClick={(e) => e.stopPropagation()} // Empêche la fermeture au clic interne
        >
          {/* En-tête */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-white/10">
            <h2 className="font-mono text-sm font-bold uppercase tracking-widest text-violet-300">
              📖 Règles du Quoridor
            </h2>
            <button
              onClick={onClose}
              className="text-zinc-500 hover:text-white transition-colors text-lg leading-none"
              aria-label="Fermer les règles"
            >
              ✕
            </button>
          </div>

          {/* Navigation par onglets */}
          <div className="flex overflow-x-auto border-b border-white/10 px-4 pt-3 gap-2">
            {RULES_SECTIONS.map((section, i) => (
              <button
                key={i}
                onClick={() => setActiveSection(i)}
                className={`
                  whitespace-nowrap px-3 py-1.5 rounded-t text-[10px] font-mono
                  uppercase tracking-wider transition-all
                  ${activeSection === i
                    ? "bg-violet-600/30 text-violet-300 border-b-2 border-violet-400"
                    : "text-zinc-500 hover:text-zinc-300"}
                `}
              >
                {section.title}
              </button>
            ))}
          </div>

          {/* Contenu de la section active */}
          <div className="px-6 py-5 min-h-[200px]">
            <motion.div
              key={activeSection}
              initial={{ opacity: 0, x: 8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className="font-mono text-sm text-violet-200 font-bold mb-3">
                {RULES_SECTIONS[activeSection].title}
              </h3>
              {/* Rendu multi-lignes (supporte les \n dans le contenu) */}
              {RULES_SECTIONS[activeSection].content
                .split("\n")
                .map((line, j) => (
                  <p key={j} className="text-zinc-300 text-xs leading-5 mb-1">
                    {line || "\u00A0"}
                  </p>
                ))}
            </motion.div>
          </div>

          {/* Diagramme ASCII du plateau */}
          <div className="mx-6 mb-5 p-3 rounded-lg bg-black/30 border border-white/10">
            <p className="font-mono text-[9px] text-violet-400 uppercase tracking-widest mb-2">
              Schéma du plateau (9×9)
            </p>
            <pre className="font-mono text-[8px] text-zinc-400 leading-3">
{`  a b c d e f g h i     Joueur 2 part ici ↑
9 . . . . 2 . . . .
8 . . . . . . . . .
7 . . . . . . . . .
6 . . . . . . . . .
5 . . . . . . . . .
4 . . . . . . . . .
3 . . . . . . . . .
2 . . . . . . . . .
1 . . . . 1 . . . .   Joueur 1 part ici ↓`}
            </pre>
          </div>

          {/* Navigation précédent/suivant */}
          <div className="flex justify-between items-center px-6 py-3 border-t border-white/10">
            <button
              onClick={() => setActiveSection((s) => Math.max(0, s - 1))}
              disabled={activeSection === 0}
              className="text-[10px] font-mono text-zinc-400 hover:text-white disabled:opacity-30 transition"
            >
              ← Précédent
            </button>
            <span className="text-[9px] font-mono text-zinc-600">
              {activeSection + 1} / {RULES_SECTIONS.length}
            </span>
            <button
              onClick={() =>
                setActiveSection((s) =>
                  Math.min(RULES_SECTIONS.length - 1, s + 1)
                )
              }
              disabled={activeSection === RULES_SECTIONS.length - 1}
              className="text-[10px] font-mono text-zinc-400 hover:text-white disabled:opacity-30 transition"
            >
              Suivant →
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
