# PROJET-TDLOG - Backend

Ce README décrit le code du backend, le rôle des fichiers et comment démarrer le serveur en développement.

Résumé rapide
- Stack : FastAPI + SQLAlchemy + SQLite
- Point d'entrée : `app.main:app` (FastAPI)
- Base de données : fichier SQLite `app.db` à la racine du dépôt
- Lancement recommandé : `./scripts/start.sh` (crée/rafraîchit un `.venv`, installe les dépendances et démarre uvicorn)

---

Arborescence et description des fichiers importants

`app/`
- `main.py` : point d'assemblage de l'application FastAPI.
  - Crée les tables (`Base.metadata.create_all(bind=engine)`) au démarrage (pratique pour le dev).
  - Inclut le middleware CORS (actuellement `allow_origins=["*"]` pour le développement).
  - Montre les routes principales : `/` (root) et `/health` (santé).
  - Enregistre les routeurs : `auth`, `events`, `tickets`, `scan`, `admin`, `students`, `participants`.

- `db.py` : configuration SQLAlchemy
  - `DATABASE_URL = 'sqlite:///./app.db'` (fichier SQLite local)
  - `engine`, `SessionLocal` (factory) et `Base` (déclarative base)
  - `get_db()` : dépendance FastAPI qui yield/ferme la session DB

- `models.py` : modèles SQLAlchemy
  - `User`, `Event`, `EventAdmin`, `Ticket`, `Student`, `Participant`.
  - Les relations les plus importantes : `Event.created_by` et `Participant.event`.

- `schemas.py` : schémas Pydantic (contracts API)
  - Schémas pour les utilisateurs, événements, tickets, scan, students, participants
  - Utilisés pour la validation d'entrée et la sérialisation des réponses

- `security.py` : utilitaires de sécurité
  - Hashing des mots de passe (`passlib`/bcrypt)
  - Gestion des JWT (`jose`) : `create_access_token`, `SECRET_KEY`, `ALGORITHM`
  - NOTE: la `SECRET_KEY` actuelle est en clair et doit être changée en production

- `deps.py` : dépendances partagées
  - `get_current_user` : décode le JWT et retourne l'utilisateur courant depuis la DB

- `initial_superadmin.py` : helper qui garantit la présence d'un superadmin
  - Utilise les variables d'environnement `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME`
  - Lors du démarrage, `ensure_initial_superadmin()` crée le compte si nécessaire

`app/routers/` — routes (liste et rôle)
- `auth.py` : routes d'authentification
  - `POST /auth/signup` : créer un utilisateur
  - `POST /auth/login` : obtention d'un token (OAuth2PasswordRequestForm)
  - `GET /auth/me` : renvoie l'utilisateur courant (dépend de `get_current_user`)

- `events.py` : gestion des événements
  - `POST /events/` : création d'un event (nécessite authentification)
  - `GET /events/` : lister tous les évènements
  - `GET /events/{event_id}` : récupérer un event
  - `DELETE /events/{event_id}` : supprimer (seul owner ou superadmin)

- `tickets.py` : gestion des tickets par event
  - `POST /events/{event_id}/tickets/` : créer un ticket unique
  - `POST /events/{event_id}/tickets/bulk` : créer des tickets en masse
  - `GET /events/{event_id}/tickets/` : lister les tickets d'un event

- `participants.py` : participants attachés à un event
  - `GET /events/{event_id}/participants/` : liste (avec status ticket associé)
  - `POST /events/{event_id}/participants/` : création (génère un `qr_code` et crée aussi le `Ticket` associé)
  - `PUT /events/{event_id}/participants/{participant_id}` : mise à jour
  - `DELETE /events/{event_id}/participants/{participant_id}` : suppression (supprime aussi le ticket lié)

- `scan.py` : endpoint de scan (QR -> validation)
  - `POST /scan/` : body = `{ "token": "..." }` -> renvoie `ScanResult` (valid, reason, status...)
  - Comportement : trouve le ticket, vérifie `UNUSED` puis le marque `SCANNED` et enregistre `scanned_at`
  - `GET /scan/debug_raw` : renvoie les tickets en brut pour debug

- `students.py` : gestion des étudiants
  - `GET /students/`, `POST /students/` et import CSV via `POST /students/import-csv`
  - `GET /students/search?q=...` pour autocomplétion

- `admin.py` : gestion des admins d'un event
  - `POST /events/{event_id}/admins/` : ajouter un admin (vérifie que l'appelant est owner ou superadmin)
  - `GET /events/{event_id}/admins/` : lister les admins

Fichiers de config et utilitaires
- `requirements.txt` : dépendances Python (FastAPI, uvicorn, SQLAlchemy, jose, passlib, etc.)
- `app.db` : fichier SQLite (généré automatiquement au premier démarrage)
- `scripts/start.sh` : script idempotent qui recrée `.venv` si nécessaire, installe les dépendances et démarre uvicorn
  - Usage : `./scripts/start.sh` (depuis la racine du projet)

Comment démarrer en développement (recommandé)
1. Depuis la racine du dépôt backend :
```bash
chmod +x scripts/start.sh    # une seule fois
./scripts/start.sh
```
Le script fait : création/rafraîchissement du `.venv`, `pip install -r requirements.txt` et `uvicorn app.main:app --reload --port 8000`.

2. Alternative manuelle (si tu gères le venv toi-même) :
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

Variables d'environnement utiles
- `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD`, `SUPERADMIN_NAME` : pour `initial_superadmin.py`.
- `SECRET_KEY` (dans `app/security.py`) : actuellement en dur pour le dev — changez-le en prod et mettez-le dans une variable d'environnement ou gestionnaire de secrets.

Notes de sécurité / production
- Le projet utilise actuellement :
  - une `SECRET_KEY` en clair (changer absolument pour la prod)
  - `allow_origins=["*"]` en CORS (à restreindre en prod)
  - `Base.metadata.create_all(...)` : pratique en dev, mais en production préférez les migrations (Alembic)
- Pour la mise en production, envisagez : containerisation (Docker), gestion des secrets, base de données persistante (Postgres) et migration avec Alembic.

Développement & debug
- `app/main.py` active `ensure_initial_superadmin()` au démarrage : utile pour avoir un compte admin dès le début.
- Logs / debug : uvicorn `--reload` active le rechargement automatique (dev). Pour voir plus d'info, lance `python -m uvicorn app.main:app --reload --port 8000 --log-level debug`.

Points de contact rapides
- Endpoint racine : `GET /` → {"message": "Backend TDLOG running"}
- Health : `GET /health` → {"status": "ok"}
- Documentation API automatique (Swagger) : `http://localhost:8000/docs` après démarrage

Si tu veux
- Je peux ajouter un `Makefile` avec les commandes `make setup`, `make install`, `make start`.
- Je peux aussi ajouter un `.env.example` et expliquer la configuration pour la prod.

---

Si tu veux que je génère le `Makefile` et/ou `.vscode/launch.json`, dis-le et je les ajoute.

