import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import game_router
from api import ai_router

# Activation des logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)

app = FastAPI(
    title="Quoridor API",
    version="0.4.0",
    description="Moteur de jeu Quoridor — Backend academique IA & Theorie des Jeux",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(ai_router.router)


@app.get("/health", tags=["infra"])
def health() -> dict:
    return {"status": "ok", "version": app.version}