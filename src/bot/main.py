"""
Point d'entrée du bot Telegram SNDE Suivi.

Lance le bot en mode polling : il interroge Telegram en boucle pour
récupérer les nouveaux messages. Idéal en développement local.

Usage :
    python -m src.bot.main
"""
from __future__ import annotations

import asyncio
import logging
import sys

# Fix Windows — doit être avant tout autre import async
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.bot.handlers.ping import handler_ping
from src.bot.handlers.whoami import handler_whoami
from src.bot.handlers.excel import handler_rapport_excel
from src.bot.handlers.rapport import handler_rapport
from src.core.config import settings
from src.db.pool import get_pool, fermer_pool


def configurer_logging() -> None:
    """Configure le logger global avec un format lisible en dev."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def construire_application() -> Application:
    """Construit l'application python-telegram-bot avec ses handlers."""
    application = (
        Application.builder()
        .token(settings.bot_token)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .build()
    )

    # Commandes existantes
    application.add_handler(CommandHandler("ping", handler_ping))
    application.add_handler(CommandHandler("whoami", handler_whoami))
    application.add_handler(CommandHandler("rapport", handler_rapport))

    # Réception fichier Excel rempli par un directeur
    application.add_handler(
        MessageHandler(filters.Document.ALL, handler_rapport_excel)
    )

    return application


async def post_init(application: Application) -> None:
    """Initialise le pool PostgreSQL au démarrage du bot."""
    logger = logging.getLogger(__name__)
    await get_pool()
    logger.info("Pool PostgreSQL connecte")


async def post_shutdown(application: Application) -> None:
    """Ferme le pool PostgreSQL à l'arrêt du bot."""
    logger = logging.getLogger(__name__)
    await fermer_pool()
    logger.info("Pool PostgreSQL ferme")


def main() -> None:
    """Point d'entrée principal : configure et lance le bot en polling."""
    configurer_logging()
    logger = logging.getLogger(__name__)

    logger.info("Demarrage du bot SNDE Suivi...")
    application = construire_application()

    logger.info("Bot pret. En attente de messages Telegram...")
    application.run_polling(
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()