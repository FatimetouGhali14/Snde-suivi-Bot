"""
Point d'entrée du bot Telegram SNDE Suivi.

Lance le bot en mode polling : il interroge Telegram en boucle pour
récupérer les nouveaux messages. Idéal en développement local.

Usage :
    python -m src.bot.main
"""
from __future__ import annotations

import logging

from telegram.ext import Application, CommandHandler

from src.bot.handlers.ping import handler_ping
from src.core.config import settings


def configurer_logging() -> None:
    """Configure le logger global avec un format lisible en dev."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=getattr(logging, settings.log_level.upper(), logging.INFO),
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)


def construire_application() -> Application:
    """Construit l'application python-telegram-bot avec ses handlers."""
    application = Application.builder().token(settings.bot_token).build()
    application.add_handler(CommandHandler("ping", handler_ping))
    return application


def main() -> None:
    """Point d'entrée principal : configure et lance le bot en polling."""
    configurer_logging()
    logger = logging.getLogger(__name__)

    logger.info("Démarrage du bot SNDE Suivi...")
    application = construire_application()

    logger.info("Bot prêt. En attente de messages Telegram...")
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()