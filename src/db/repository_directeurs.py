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
        SELECT id, matricule, nom_complet, direction_code, telegram_chat_id
        FROM directeurs
        WHERE telegram_chat_id = %s
        """,
        (chat_id,)
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id"               : row[0],
        "matricule"        : row[1],
        "nom_complet"      : row[2],
        "direction_code"   : row[3],
        "telegram_chat_id" : row[4],
    }


def lister_tous():
    """Retourne la liste de tous les directeurs."""
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, matricule, nom_complet, direction_code, telegram_chat_id
        FROM directeurs
        ORDER BY direction_code
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id"               : r[0],
            "matricule"        : r[1],
            "nom_complet"      : r[2],
            "direction_code"   : r[3],
            "telegram_chat_id" : r[4],
        }
        for r in rows
    ]