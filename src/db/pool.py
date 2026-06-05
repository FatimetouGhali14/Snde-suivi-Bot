# src/db/pool.py
import pg8000
import logging
from src.core.config import settings

logger = logging.getLogger(__name__)

_connexion = None


def get_connexion():
    """Retourne la connexion PostgreSQL."""
    global _connexion
    if _connexion is None:
        logger.info("Connexion PostgreSQL en cours...")
        _connexion = pg8000.connect(
            host=settings.db_host,
            port=settings.db_port,
            database=settings.db_name,
            user=settings.db_user,
            password=settings.db_password
        )
        # Forcer le schéma public
        cursor = _connexion.cursor()
        cursor.execute("SET search_path TO public;")
        _connexion.commit()
        logger.info("Connexion PostgreSQL etablie !")
    return _connexion


def fermer_connexion():
    """Ferme la connexion."""
    global _connexion
    if _connexion:
        _connexion.close()
        _connexion = None
        logger.info("Connexion fermee")


async def get_pool():
    return get_connexion()


async def fermer_pool():
    fermer_connexion()