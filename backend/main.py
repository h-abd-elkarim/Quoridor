from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import game_router
from api import ai_router

# 1. On crée l'application en PREMIER
app = FastAPI(
    title="Quoridor API",
    version="0.4.0",
    description="Moteur de jeu Quoridor — Backend académique IA & Théorie des Jeux",
)

# 2. Ensuite, on ajoute les middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev
        "http://localhost:3000",   # CRA fallback
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Maintenant que "app" existe, on peut lui attacher les routeurs
app.include_router(game_router)
app.include_router(ai_router.router)

# 4. Et enfin la route de santé
@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "version": app.version}