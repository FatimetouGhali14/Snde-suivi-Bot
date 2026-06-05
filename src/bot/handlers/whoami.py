# src/bot/handlers/whoami.py
from __future__ import annotations
import logging
from telegram import Update
from telegram.ext import ContextTypes
from src.db.repository_directeurs import trouver_par_chat_id

logger = logging.getLogger(__name__)


async def handler_whoami(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    chat_id = update.effective_chat.id
    logger.info("Commande /whoami recue de chat_id=%s", chat_id)

    try:
        directeur = trouver_par_chat_id(chat_id)

        if directeur is None:
            await update.message.reply_text(
                f"Vous n'etes pas enregistre dans le systeme SNDE.\n"
                f"Votre identifiant : {chat_id}\n"
                f"Contactez l'administrateur."
            )
            return

        await update.message.reply_text(
            f"Identifie avec succes\n"
            f"Matricule : {directeur['matricule']}\n"
            f"Nom : {directeur['nom_complet']}\n"
            f"Direction : {directeur['direction_code']}\n"
            f"Chat ID : {directeur['telegram_chat_id']}"
        )

    except Exception as e:
        logger.error(f"Erreur whoami : {e}")
        await update.message.reply_text(
            "Erreur de connexion a la base de donnees."
        )