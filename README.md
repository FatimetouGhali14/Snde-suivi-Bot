# SNDE Suivi POC

Plateforme automatisée de suivi journalier des directions SNDE via bot Telegram.

## Stack

- Python 3.12
- PostgreSQL 16 (via Docker)
- python-telegram-bot 21.x
- asyncpg, openpyxl, pydantic

## Démarrage rapide

### Prérequis

- Python 3.12
- Docker Desktop
- VS Code (recommandé)

### Installation

```bash
# 1. Cloner le projet
git clone <url> snde-suivi-poc
cd snde-suivi-poc

# 2. Environnement Python
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. Configuration
cp .env.example .env
# Éditer .env avec tes valeurs (BOT_TOKEN notamment)

# 4. Base de données
docker compose up -d
```

### Vérifier que tout marche

```bash
# Postgres tourne ?
docker compose ps

# Les tables sont créées ?
docker exec -it snde-postgres psql -U snde -d snde_suivi -c "\dt"

# Lancer les tests
pytest
```

## Structure du projet