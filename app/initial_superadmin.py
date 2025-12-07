import os
from contextlib import contextmanager

from sqlalchemy.orm import Session

from .db import SessionLocal
from . import models
from .security import hash_password


@contextmanager
def _session_scope():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_initial_superadmin() -> None:
    """
    Crée un compte superadmin s'il n'existe pas encore.
    Utilise les variables d'environnement suivantes (avec valeurs par défaut) :
        - SUPERADMIN_EMAIL
        - SUPERADMIN_PASSWORD
        - SUPERADMIN_NAME
    """
    email = os.getenv("SUPERADMIN_EMAIL", "admin@tdlog.local")
    password = os.getenv("SUPERADMIN_PASSWORD", "changeme")
    name = os.getenv("SUPERADMIN_NAME", "Super Admin")

    if not email or not password:
        # Si la configuration est vide, on ne tente rien.
        return

    with _session_scope() as db:
        existing = db.query(models.User).filter(models.User.email == email).first()
        if existing:
            return

        user = models.User(
            email=email,
            name=name or "Super Admin",
            hashed_password=hash_password(password),
            is_superadmin=True,
        )
        db.add(user)
        db.commit()
