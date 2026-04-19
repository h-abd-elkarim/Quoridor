import { create } from "zustand";
import { gameApi, GameStateResponse, ValidActionsResponse } from "../api/client";

type GameMode = "PvP" | "PvE";

interface GameStore {
  gameId: string | null;
  gameState: GameStateResponse | null;
  validActions: ValidActionsResponse | null;
  difficulty: string;
  gameMode: GameMode;
  isAIThinking: boolean;
  lastAIInfo: { algorithm: string; nodes: number; depth: number } | null;
  error: string | null;

  // Actions
  createGame: () => Promise<void>;
  fetchValidActions: () => Promise<void>;
  playMove: (row: number, col: number) => Promise<void>;
  playWall: (row: number, col: number, orientation: "H" | "V") => Promise<void>;
  triggerAI: () => Promise<void>;
  setDifficulty: (d: string) => void;
  setGameMode: (mode: GameMode) => void;
}

export const useGameStore = create<GameStore>((set, get) => ({
  gameId: null,
  gameState: null,
  validActions: null,
  difficulty: "HARD",
  gameMode: "PvE",
  isAIThinking: false,
  lastAIInfo: null,
  error: null,

  createGame: async () => {
    try {
      const res = await gameApi.create();
      const id = res.data.game_id;
      const stateRes = await gameApi.get(id);
      set({ gameId: id, gameState: stateRes.data, error: null });
      await get().fetchValidActions();
    } catch (e) {
      set({ error: "Impossible de créer la partie." });
    }
  },

  fetchValidActions: async () => {
    const id = get().gameId;
    if (!id) return;
    const res = await gameApi.validActions(id);
    set({ validActions: res.data });
  },

  playMove: async (row, col) => {
    const id = get().gameId;
    if (!id) return;
    try {
      const res = await gameApi.playMove(id, row, col);
      const newState = res.data;
      set({ gameState: newState, error: null });
      await get().fetchValidActions();

      // Mode PvE : si c'est maintenant au tour du joueur 2 et que la partie continue,
      // l'IA joue automatiquement.
      if (
        get().gameMode === "PvE" &&
        newState.current_player === 2 &&
        newState.status === "ongoing"
      ) {
        await get().triggerAI();
      }
    } catch (e: any) {
      set({ error: e.response?.data?.detail ?? "Coup invalide." });
    }
  },

  playWall: async (row, col, orientation) => {
    const id = get().gameId;
    if (!id) return;
    try {
      const res = await gameApi.playWall(id, row, col, orientation);
      const newState = res.data;
      set({ gameState: newState, error: null });
      await get().fetchValidActions();

      // Mode PvE : même logique qu'après un déplacement.
      if (
        get().gameMode === "PvE" &&
        newState.current_player === 2 &&
        newState.status === "ongoing"
      ) {
        await get().triggerAI();
      }
    } catch (e: any) {
      set({ error: e.response?.data?.detail ?? "Barrière invalide." });
    }
  },

  triggerAI: async () => {
    const id = get().gameId;
    if (!id) return;
    set({ isAIThinking: true, error: null });
    try {
      const res = await gameApi.aiPlay(id, get().difficulty);
      set({
        gameState: res.data.game_state,
        isAIThinking: false,
        lastAIInfo: {
          algorithm: res.data.algorithm,
          nodes: res.data.nodes_explored,
          depth: res.data.depth,
        },
      });
      await get().fetchValidActions();
    } catch (e: any) {
      set({ isAIThinking: false, error: "L'IA a échoué." });
    }
  },

  setDifficulty: (d) => set({ difficulty: d }),
  setGameMode: (mode) => set({ gameMode: mode }),
}));