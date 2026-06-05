# src/db/repository_directeurs.py
# Requetes SQL pour la table directeurs — version pg8000 (Windows)
import logging
from src.db.pool import get_connexion

logger = logging.getLogger(__name__)


def trouver_par_chat_id(chat_id: int):
    """
    Cherche un directeur par son identifiant Telegram.
    Retourne None si non trouve.
    """
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT matricule, nom_complet, direction_code, telegram_chat_id
        FROM directeurs
        WHERE telegram_chat_id = %s
        """,
        (chat_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "matricule"        : row[0],
        "nom_complet"      : row[1],
        "direction_code"   : row[2],
        "telegram_chat_id" : row[3],
    }


def lister_tous():
    """Retourne la liste de tous les directeurs."""
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT matricule, nom_complet, direction_code, telegram_chat_id
        FROM directeurs
        ORDER BY direction_code
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "matricule"        : r[0],
            "nom_complet"      : r[1],
            "direction_code"   : r[2],
            "telegram_chat_id" : r[3],
        }
        for r in rows
    ]