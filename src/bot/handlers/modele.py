"""
Handler /modele — envoi du formulaire Excel.

Déclencheur :
- Commande /modele
- Mot-clé "excel" (insensible à la casse, mot entier)

Comportement selon l'acteur :
- Directeur d'une direction : reçoit UNIQUEMENT son onglet
- Directeur General (DG)    : reçoit le fichier COMPLET multi-onglets
- Non enrôlé                : reçoit un message d'erreur
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path

from telegram import Update
from telegram.ext import ContextTypes

from src.db.repository_directeurs import trouver_par_chat_id
from src.parsers.excel_parser import (
    ONGLETS_DIRECTIONS,
    extraire_onglet_vers_bytes,
)

logger = logging.getLogger(__name__)

CHEMIN_MODELE = Path("data/SNDE_Rapport_Journalier_Toutes_Directions.xlsx")


async def handler_modele(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Envoie le formulaire Excel adapté à l'acteur."""
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

    code = directeur["direction_code"]
    date_str = date.today().strftime("%Y%m%d")

    # Cas 1 : le DG reçoit le fichier complet multi-onglets
    if code == "DG":
        logger.info(
            "Envoi modele complet au DG (%s)",
            directeur["matricule"],
        )
        try:
            with CHEMIN_MODELE.open("rb") as f:
                await context.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    filename=f"SNDE_Rapport_Complet_{date_str}.xlsx",
                    caption=(
                        f"Fichier modele complet\n"
                        f"--------------------------------\n"
                        f"Date : {date.today().strftime('%d/%m/%Y')}\n"
                        f"12 onglets : un par direction\n\n"
                        f"Reservation : consultation ou archivage."
                    ),
                )
        except Exception as e:
            logger.error("Erreur envoi modele DG : %s", e, exc_info=True)
            await update.message.reply_text(
                f"Erreur lors de l'envoi du fichier : {e}"
            )
        return

    # Cas 2 : directeur d'une direction — son onglet uniquement
    if code not in ONGLETS_DIRECTIONS:
        await update.message.reply_text(
            f"Aucun formulaire disponible pour la direction {code}."
        )
        return

    logger.info(
        "Envoi modele personnalise a %s (%s)",
        directeur["matricule"],
        code,
    )

    try:
        # Extraire uniquement l'onglet du directeur
        onglet_bytes = extraire_onglet_vers_bytes(CHEMIN_MODELE, code)
        nom_fichier = f"Rapport_{code}_{date_str}.xlsx"
        nom_direction = ONGLETS_DIRECTIONS[code]

        await context.bot.send_document(
            chat_id=chat_id,
            document=onglet_bytes,
            filename=nom_fichier,
            caption=(
                f"Formulaire de rapport journalier\n"
                f"--------------------------------\n"
                f"Direction : {nom_direction}\n"
                f"Code : {code}\n"
                f"Date : {date.today().strftime('%d/%m/%Y')}\n\n"
                f"Remplissez vos 8 colonnes et renvoyez ce fichier "
                f"avant 21h00."
            ),
        )

    except Exception as e:
        logger.error("Erreur envoi modele : %s", e, exc_info=True)
        await update.message.reply_text(
            f"Erreur lors de la generation du formulaire : {e}"
        )