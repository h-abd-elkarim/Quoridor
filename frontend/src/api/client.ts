import axios from "axios";

const api = axios.create({
  baseURL: "http://localhost:8000",
  headers: { "Content-Type": "application/json" },
});

export type Orientation = "H" | "V";

export interface PlayerState {
  position: { row: number; col: number };
  walls_remaining: number;
}

export interface WallPlaced {
  row: number;
  col: number;
  orientation: Orientation;
}

export interface GameStateResponse {
  game_id: string;
  turn: number;
  status: string;
  current_player: number;
  players: Record<string, PlayerState>;
  walls_placed: WallPlaced[];
  zobrist_hash: number | null;
}

export interface ValidActionsResponse {
  game_id: string;
  current_player: number;
  moves: { row: number; col: number }[];
  walls: WallPlaced[];
  total_count: number;
}

export interface AIPlayResponse {
  game_state: GameStateResponse;
  algorithm: string;
  nodes_explored: number;
  depth: number;
  action_played: Record<string, unknown>;
}

export const gameApi = {
  create: () => api.post<{ game_id: string }>("/games"),

  get: (id: string) => api.get<GameStateResponse>(`/games/${id}`),

  validActions: (id: string) =>
    api.get<ValidActionsResponse>(`/games/${id}/valid-actions`),

  playMove: (id: string, row: number, col: number) =>
    api.post<GameStateResponse>(`/games/${id}/play`, {
      action: { type: "move", row, col },
    }),

  playWall: (id: string, row: number, col: number, orientation: Orientation) =>
    api.post<GameStateResponse>(`/games/${id}/play`, {
      action: { type: "wall", row, col, orientation },
    }),

  aiPlay: (id: string, difficulty: string) =>
    api.post<AIPlayResponse>(`/games/${id}/ai-play?difficulty=${difficulty}`),
};
