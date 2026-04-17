# ── Backend Quoridor — FastAPI + Uvicorn ──────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Dépendances système légères (curl pour le healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Installe les dépendances Python en premier (layer cacheable)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code source
COPY . .

# Expose le port FastAPI
EXPOSE 8000

# Lance Uvicorn avec rechargement auto désactivé en prod
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]