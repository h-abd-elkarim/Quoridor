/**
 * demo_games.ts
 * ─────────────
 * Cinq parties de démonstration commentées, couvrant les principales
 * stratégies du Quoridor. Chaque coup est accompagné d'une explication
 * tactique à destination de l'utilisateur.
 *
 * Consigne universitaire : "L'utilisateur devra avoir la possibilité
 * d'avoir des exemples de parties."
 *
 * Format d'une action :
 *   { type: "move" | "wall", ... } — voir les interfaces ci-dessous.
 */

// ── Interfaces ─────────────────────────────────────────────────────────────

/** Déplacement d'un pion */
export interface MoveAction {
  type: "move";
  row: number;
  col: number;
}

/** Pose d'une barrière */
export interface WallAction {
  type: "wall";
  row: number;
  col: number;
  orientation: "H" | "V";
}

/** Un coup dans une partie de démo, avec explication */
export interface DemoMove {
  player: 1 | 2;
  action: MoveAction | WallAction;
  /** Explication tactique affichée dans le DemoPlayer */
  comment: string;
}

/** Une partie complète de démonstration */
export interface DemoGame {
  id: number;
  title: string;
  description: string;
  moves: DemoMove[];
}

// ── Parties de démonstration ───────────────────────────────────────────────

export const DEMO_GAMES: DemoGame[] = [
  // ── Partie 1 : Ouverture centrale ───────────────────────────────────────
  {
    id: 1,
    title: "Ouverture centrale",
    description:
      "Les deux joueurs avancent directement au centre — la ligne la plus rapide " +
      "pour traverser. Idéale pour apprendre les bases du déplacement.",
    moves: [
      { player: 1, action: { type: "move", row: 1, col: 4 }, comment: "Joueur 1 avance d'une case. Priorité absolue : progresser vers la rangée 9." },
      { player: 2, action: { type: "move", row: 7, col: 4 }, comment: "Joueur 2 répond symétriquement. Aucun des deux ne dépense de barrière." },
      { player: 1, action: { type: "move", row: 2, col: 4 }, comment: "Avance encore. Sans barrières adverses, foncer est optimal." },
      { player: 2, action: { type: "move", row: 6, col: 4 }, comment: "Idem pour Joueur 2. La colonne centrale est la route la plus directe." },
      { player: 1, action: { type: "move", row: 3, col: 4 }, comment: "Joueur 1 atteint la moitié du plateau. Les décisions stratégiques commencent." },
      { player: 2, action: { type: "move", row: 5, col: 4 }, comment: "Les deux pions sont maintenant séparés d'une seule case !" },
      { player: 1, action: { type: "move", row: 4, col: 4 }, comment: "Saut possible désormais — mais attention, Joueur 2 peut bloquer." },
      { player: 2, action: { type: "wall", row: 4, col: 3, orientation: "H" }, comment: "Joueur 2 pose une barrière horizontale. Joueur 1 doit contourner !" },
      { player: 1, action: { type: "move", row: 4, col: 3 }, comment: "Joueur 1 bifurque à gauche. La barrière a coûté du temps à l'adversaire." },
      { player: 2, action: { type: "move", row: 4, col: 4 }, comment: "Joueur 2 avance pendant que Joueur 1 contourne. Avantage de tempo !" },
    ],
  },

  // ── Partie 2 : Stratégie des barrières ─────────────────────────────────
  {
    id: 2,
    title: "Stratégie des barrières",
    description:
      "Démonstration de l'utilisation défensive et offensive des barrières. " +
      "Forcer l'adversaire à faire un grand détour peut décider du résultat.",
    moves: [
      { player: 1, action: { type: "move", row: 1, col: 4 }, comment: "Avance classique vers le centre." },
      { player: 2, action: { type: "wall", row: 1, col: 3, orientation: "H" }, comment: "Joueur 2 place immédiatement une barrière pour bloquer la route directe de Joueur 1." },
      { player: 1, action: { type: "move", row: 1, col: 3 }, comment: "Joueur 1 contourne par la gauche." },
      { player: 2, action: { type: "move", row: 7, col: 4 }, comment: "Pendant que Joueur 1 contourne, Joueur 2 avance librement." },
      { player: 1, action: { type: "wall", row: 6, col: 3, orientation: "H" }, comment: "Joueur 1 rend la pareille — barrière symétrique pour ralentir Joueur 2." },
      { player: 2, action: { type: "move", row: 7, col: 3 }, comment: "Joueur 2 doit aussi contourner. Les deux ont dépensé une barrière." },
      { player: 1, action: { type: "move", row: 2, col: 3 }, comment: "Joueur 1 continue son avance malgré le détour." },
      { player: 2, action: { type: "wall", row: 2, col: 2, orientation: "V" }, comment: "Barrière verticale ! Joueur 2 crée un couloir forcé pour Joueur 1." },
      { player: 1, action: { type: "move", row: 2, col: 4 }, comment: "Joueur 1 revient vers le centre — la barrière l'a obligé à zigzaguer." },
      { player: 2, action: { type: "move", row: 6, col: 3 }, comment: "Joueur 2 avance tranquillement pendant que Joueur 1 se repositionne." },
    ],
  },

  // ── Partie 3 : Finale sans barrières ───────────────────────────────────
  {
    id: 3,
    title: "Course finale sans barrières",
    description:
      "Quand les deux joueurs n'ont plus de barrières, la partie se réduit " +
      "à une course pure. Analyser les distances est crucial.",
    moves: [
      { player: 1, action: { type: "move", row: 1, col: 4 }, comment: "Début de la phase finale — les deux joueurs ont épuisé leurs barrières." },
      { player: 2, action: { type: "move", row: 7, col: 4 }, comment: "Sans barrières, chaque coup doit rapprocher directement de la ligne." },
      { player: 1, action: { type: "move", row: 2, col: 4 }, comment: "Joueur 1 a 6 cases à parcourir. Joueur 2 en a aussi 6." },
      { player: 2, action: { type: "move", row: 6, col: 4 }, comment: "Parité parfaite — le premier joueur a l'avantage du premier coup." },
      { player: 1, action: { type: "move", row: 3, col: 4 }, comment: "Joueur 1 à 5 cases. L'avantage du premier joueur se confirme." },
      { player: 2, action: { type: "move", row: 5, col: 4 }, comment: "Joueur 2 à 5 cases. Ils sont à égalité de distance, mais Joueur 1 joue en premier." },
      { player: 1, action: { type: "move", row: 4, col: 4 }, comment: "Joueur 1 au centre ! Plus que 4 cases." },
      { player: 2, action: { type: "move", row: 4, col: 5 }, comment: "Joueur 2 bifurque pour éviter le blocage face-à-face." },
      { player: 1, action: { type: "move", row: 5, col: 4 }, comment: "Joueur 1 continue en ligne droite. 3 cases restantes !" },
      { player: 2, action: { type: "move", row: 3, col: 5 }, comment: "Joueur 2 suit sa propre route. C'est une course pure maintenant." },
    ],
  },

  // ── Partie 4 : Technique du saut ───────────────────────────────────────
  {
    id: 4,
    title: "Technique du saut",
    description:
      "Les règles de saut sont complexes mais puissantes. " +
      "Savoir exploiter ou contrecarrer un saut peut changer l'issue.",
    moves: [
      { player: 1, action: { type: "move", row: 1, col: 4 }, comment: "Avance centrale standard." },
      { player: 2, action: { type: "move", row: 7, col: 4 }, comment: "Réponse symétrique de Joueur 2." },
      { player: 1, action: { type: "move", row: 2, col: 4 }, comment: "Joueur 1 continue son chemin." },
      { player: 2, action: { type: "move", row: 6, col: 4 }, comment: "Rapprochement progressif." },
      { player: 1, action: { type: "move", row: 3, col: 4 }, comment: "Joueur 1 se place. Dans 2 coups, les pions seront adjacents." },
      { player: 2, action: { type: "move", row: 5, col: 4 }, comment: "Joueur 2 est à 2 cases de Joueur 1." },
      { player: 1, action: { type: "move", row: 4, col: 4 }, comment: "Pions adjacents ! La règle de saut s'applique désormais." },
      { player: 2, action: { type: "move", row: 4, col: 5 }, comment: "Joueur 2 aurait pu tenter un saut par-dessus Joueur 1. Il choisit de bifurquer." },
      { player: 1, action: { type: "move", row: 5, col: 4 }, comment: "Saut ! Joueur 1 saute par-dessus l'endroit où était Joueur 2." },
      { player: 2, action: { type: "wall", row: 5, col: 3, orientation: "H" }, comment: "Joueur 2 bloque la progression de Joueur 1 avec une barrière défensive." },
    ],
  },

  // ── Partie 5 : Stratégie experte ───────────────────────────────────────
  {
    id: 5,
    title: "Stratégie experte — Labyrinthisation",
    description:
      "Technique avancée : créer un labyrinthe qui oblige l'adversaire à faire " +
      "un très long détour tout en conservant sa propre route courte.",
    moves: [
      { player: 1, action: { type: "move", row: 1, col: 4 }, comment: "Ouverture standard." },
      { player: 2, action: { type: "move", row: 7, col: 4 }, comment: "Réponse de Joueur 2." },
      { player: 1, action: { type: "wall", row: 5, col: 4, orientation: "H" }, comment: "STRATÉGIE : Joueur 1 place une barrière au milieu du plateau, anticipant la route de Joueur 2." },
      { player: 2, action: { type: "move", row: 6, col: 4 }, comment: "Joueur 2 n'est pas encore bloqué — il peut contourner." },
      { player: 1, action: { type: "move", row: 2, col: 4 }, comment: "Joueur 1 avance librement sur son côté du plateau." },
      { player: 2, action: { type: "move", row: 6, col: 3 }, comment: "Joueur 2 cherche un chemin alternatif à gauche." },
      { player: 1, action: { type: "wall", row: 5, col: 2, orientation: "V" }, comment: "Joueur 1 ferme le couloir gauche ! Joueur 2 doit aller à droite." },
      { player: 2, action: { type: "move", row: 6, col: 4 }, comment: "Joueur 2 recule pour trouver un passage. Le détour s'allonge." },
      { player: 1, action: { type: "move", row: 3, col: 4 }, comment: "Joueur 1 continue d'avancer pendant que Joueur 2 tâtonne." },
      { player: 2, action: { type: "move", row: 6, col: 5 }, comment: "Joueur 2 tente le couloir droit. La technique de labyrinthisation a fonctionné." },
    ],
  },
];
