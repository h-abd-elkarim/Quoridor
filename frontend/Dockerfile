# ── Frontend Quoridor — React + Vite ─────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# Dépendances npm en premier (layer cacheable)
COPY package.json package-lock.json* ./
RUN npm install

# Copie le code source
COPY . .

# Expose le port Vite
EXPOSE 5173

# Lance le dev server en exposant sur toutes les interfaces réseau
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"]