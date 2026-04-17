from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import game_router

app = FastAPI(
    title="Quoridor API",
    version="0.3.0",
    description="Moteur de jeu Quoridor — Backend académique IA & Théorie des Jeux",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",   # CRA fallback
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "version": app.version}
