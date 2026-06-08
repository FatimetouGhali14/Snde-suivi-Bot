"""
Handler /modele — envoi du formulaire Excel vierge au directeur.

Déclencheur :
- Commande /modele
- Mot-clé "excel" (insensible à la casse, mot entier)
"""
from __future__ import annotations

import logging
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from src.db.repository_directeurs import trouver_par_chat_id

logger = logging.getLogger(__name__)

CHEMIN_MODELE = Path("data/SNDE_Rapport_Journalier_Toutes_Directions.xlsx")


async def handler_modele(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Envoie le formulaire Excel vierge au directeur."""
    chat_id = update.effective_chat.id
    
    directeur = trouver_par_chat_id(chat_id)
    if not directeur:
        await update.message.reply_text(
            "Vous n'etes pas enregistre dans le systeme SNDE.\n"
            "Contactez l'administrateur."
        )
        return
    
    if not CHEMIN_MODELE.exists():
        logger.error("Fichier modele introuvable : %s", CHEMIN_MODELE)
        await update.message.reply_text(
            "Le fichier modele est temporairement indisponible.\n"
            "Contactez l'administrateur."
        )
        return
    
    logger.info(
        "Envoi modele a %s (%s)",
        directeur["matricule"],
        directeur["direction_code"],
    )
    
    with CHEMIN_MODELE.open("rb") as f:
        await context.bot.send_document(
            chat_id=chat_id,
            document=f,
            filename="SNDE_Rapport_Journalier.xlsx",
            caption=(
                f"Voici le formulaire de rapport journalier.\n\n"
                f"Direction : {directeur['direction_code']}\n"
                f"Remplissez votre onglet et renvoyez-le moi.\n\n"
                f"Deadline : 21h00 chaque jour"
            ),
        )