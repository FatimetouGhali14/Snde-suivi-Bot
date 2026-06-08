"""
Handler /synthese — envoi de la synthèse à la demande pour le DG.

Déclencheur :
- Commande /synthese
- Mot-clé "rapport" (insensible à la casse, mot entier)
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.db.repository_directeurs import trouver_par_chat_id
from src.services.synthese import construire_message_synthese

logger = logging.getLogger(__name__)


async def handler_synthese(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Envoie la synthèse du jour au DG à la demande."""
    chat_id = update.effective_chat.id
    
    directeur = trouver_par_chat_id(chat_id)
    if not directeur:
        await update.message.reply_text(
            "Vous n'etes pas enregistre dans le systeme."
        )
        return
    
    if directeur["direction_code"] != "DG":
        await update.message.reply_text(
            "Cette commande est reservee au Directeur General."
        )
        return
    
    logger.info("Synthese demandee par le DG (%s)", chat_id)
    
    texte = construire_message_synthese()
    await update.message.reply_text(texte)