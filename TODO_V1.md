# TODO V1 — Améliorations avant mise en production

Ce document liste les améliorations à apporter au POC SNDE Suivi Bot
avant la mise en production réelle sur le serveur SNDE.

À faire **après validation complète du POC** et **en binôme avec Fatimetou**.

---

## 1. Migration pg8000 → asyncpg (priorité haute)

### Pourquoi
- pg8000 est synchrone : bloque le bot pendant chaque requête SQL
- asyncpg est asynchrone natif et 3-5x plus rapide
- Critique en production avec 12 directions + DG envoyant simultanément

### Effort estimé
2-3 heures de travail bien fait

### Fichiers à modifier

| Fichier | Changement |
|---|---|
| `pyproject.toml` | Retirer `pg8000`, ajouter `asyncpg` |
| `src/db/pool.py` | Réécrire avec `asyncpg.create_pool()` |
| `src/db/repository_directeurs.py` | Toutes les fonctions deviennent `async` |
| `src/db/repository_rapports.py` | Idem |
| `src/services/synthese.py` | Idem |
| `src/services/fusion_excel.py` | Idem |
| `src/bot/handlers/excel.py` | Adapter les appels avec `await` |
| `src/bot/handlers/modele.py` | Idem |
| `src/bot/handlers/synthese_cmd.py` | Idem |
| `src/bot/handlers/whoami.py` | Idem |
| `scripts/enroler_directeur.py` | Asyncifier |

### Note importante
Le fix Windows ProactorEventLoop est déjà en place dans `main.py` :
```python
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
```
Donc asyncpg devrait fonctionner sur Windows.

---

## 2. Nettoyage code (priorité moyenne)

### 2.1 Encodage UTF-8
- Fichiers source contiennent caractères mal encodés (`ðŸ"‹`, `âœ…`)
- Cosmétique mais à corriger pour la lisibilité
- **Effort** : 30 min

### 2.2 Renommage cohérence "Colonnes"
Le côté utilisateur a été renommé "KPIs" → "Colonnes remplies", mais le code interne garde encore l'ancien naming :
- `class KPI` → `class Colonne`
- `verifier_kpis_remplis()` → `verifier_colonnes_remplies()`
- `rapport.kpis` → `rapport.colonnes`
- Commentaires et docstrings

**Effort** : 30 min

### 2.3 Suppression des doublons de tables
La table `rapports` (créée par `001_init_poc.sql`) fait doublon avec `rapports_quotidiens`. Choisir une seule table et migrer.

**Décision à prendre avec Fatimetou.**

**Effort** : 30 min

### 2.4 Suppression du `handler_excel` inutilisé
Le handler du workflow `DG → directeurs` n'est plus actif dans `main.py`. Le code est conservé "pour référence" mais peut être supprimé proprement ou déplacé dans un dossier `legacy/`.

**Effort** : 10 min

### 2.5 Réorganisation des imports
Plusieurs fonctions ont des imports au milieu (au lieu d'être en haut du fichier). À nettoyer pour PEP 8 strict.

**Effort** : 15 min

---

## 3. Tests automatisés (priorité moyenne)

### À ajouter
- Tests unitaires sur `excel_parser.py` (parsing)
- Tests unitaires sur `repository_rapports.py` (versionnage)
- Tests d'intégration sur les handlers (avec mock Telegram)
- Tests E2E reproductibles (Tâche 7 du POC)

**Outils** : pytest + pytest-asyncio + pytest-postgresql

**Effort** : 4-6 heures

---

## 4. Configuration et constants

### À créer
- Fichier `src/core/constants.py` centralisant :
  - Couleurs SNDE
  - Messages utilisateur (refus, confirmations, erreurs)
  - Horaires (8h, 21h, 22h)
  - Codes des 12 directions
- Permettrait de personnaliser facilement sans toucher au code

**Effort** : 30 min

---

## 5. Sécurité et robustesse

### À faire
- Validation stricte des inputs Telegram (anti-injection)
- Rate limiting par chat_id (anti-spam)
- Logs structurés (JSON) pour analyse en prod
- Mot de passe BD fort en production (pas `snde`/`motdepasse` !)
- Variables sensibles via secrets manager (pas `.env` en prod)

**Effort** : 2-3 heures

---

## 6. Observabilité

### À ajouter
- Métriques Prometheus (rapports/jour, latence, erreurs)
- Dashboard Grafana ou alternative
- Alerting si bot down (Telegram unreachable, BD unreachable)
- Endpoint /health pour health-check Render

**Effort** : 3-4 heures

---

## 7. Documentation

### À créer
- `README.md` principal (vue d'ensemble, installation, démarrage)
- `SETUP_LOCAL.md` (procédure développeur)
- `DEPLOY.md` (procédure de mise en production)
- `ARCHITECTURE.md` (schémas, choix techniques)
- `OPERATIONS.md` (procédures DG, ajout directeur, etc.)

**Effort** : 3-4 heures

---

## 8. Déploiement

### À configurer
- Compte Render.com
- Service PostgreSQL Render
- Service Worker pour le bot
- Variables d'environnement Render
- Domain personnalisé si besoin

**Effort** : 2-3 heures

---

## Récap effort total V1

| Catégorie | Effort |
|---|---|
| Migration asyncpg | 2-3h |
| Nettoyage code | 2h |
| Tests automatisés | 4-6h |
| Constants/config | 30 min |
| Sécurité | 2-3h |
| Observabilité | 3-4h |
| Documentation | 3-4h |
| Déploiement | 2-3h |
| **TOTAL** | **~3 jours** |

---

## Décisions à prendre avec Fatimetou

1. Garder pg8000 ou migrer asyncpg ?
2. Garder `rapports` ou `rapports_quotidiens` ? (suppression du doublon)
3. Quels horaires définitifs (8h/21h/22h ou autres) ?
4. Quel workflow définitif : directeur → DG (actuel) ou autre ?
5. Render vs autre cloud (Railway, Fly.io, AWS, serveur SNDE on-premise) ?

---

*Document créé le 09/06/2026.*
*À mettre à jour au fur et à mesure de l'avancement V1.*