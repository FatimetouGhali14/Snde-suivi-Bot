"""
Handler /synthese — envoi de la synthèse à la demande pour le DG.

Déclencheur : commande /synthese ou mot-clé "rapport".

Le DG reçoit :
1. Le tableau de bord textuel
2. Un fichier Excel consolidé (concaténation de tous les rapports du jour)
"""
from __future__ import annotations

import logging
from datetime import date as Date

from telegram import Update
from telegram.ext import ContextTypes

from src.db.repository_directeurs import trouver_par_chat_id
from src.services.synthese import construire_message_synthese
from src.services.fusion_excel import construire_fichier_consolide

logger = logging.getLogger(__name__)


async def handler_synthese(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Envoie la synthèse du jour au DG : texte + fichier consolidé."""
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
    
    # 1. Envoyer le tableau de bord textuel
    texte = construire_message_synthese()
    await update.message.reply_text(texte)
    
    # 2. Construire et envoyer le fichier Excel consolide
    await update.message.reply_text("Construction du fichier consolide...")
    
    try:
        fichier_bytes = await construire_fichier_consolide(context.bot)
        
        if fichier_bytes is None:
            await update.message.reply_text(
                "Aucun rapport recu aujourd'hui - pas de fichier consolide."
            )
            return
        
        date_str = Date.today().strftime("%Y%m%d")
        await context.bot.send_document(
            chat_id=chat_id,
            document=fichier_bytes,
            filename=f"Rapport_consolide_{date_str}.xlsx",
            caption=(
                f"Rapport consolide du "
                f"{Date.today().strftime('%d/%m/%Y')}\n"
                f"Contient un onglet par direction ayant envoye son rapport."
            ),
        )
        logger.info("Fichier consolide envoye au DG")
    
    except Exception as e:
        logger.error("Erreur construction fichier consolide : %s", e, exc_info=True)
        await update.message.reply_text(
            f"Erreur lors de la construction du fichier : {e}"
        )