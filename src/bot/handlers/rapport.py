# src/bot/handlers/rapport.py
# Handler pour la réception du rapport quotidien d'un directeur

from __future__ import annotations
import logging
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from src.db.repository_directeurs import trouver_par_chat_id
from src.db.repository_rapports import (
    enregistrer_rapport,
    lister_instructions_en_attente,
    mettre_a_jour_statut,
)
from src.core.config import settings

logger = logging.getLogger(__name__)


async def handler_rapport(
    update : Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Reçoit le rapport quotidien d'un directeur.
    Vérifie l'heure — avant ou après 21h.
    """
    chat_id    = update.effective_chat.id
    maintenant = datetime.now()
    avant_21h  = maintenant.hour < 21

    # Identifier le directeur
    directeur = trouver_par_chat_id(chat_id)

    if directeur is None:
        await update.message.reply_text(
            "Vous n'etes pas enregistré dans le système.\n"
            f"Votre identifiant : {chat_id}\n"
            "Contactez l'administrateur."
        )
        return

    # Chercher l'instruction en attente pour ce directeur
    instructions = lister_instructions_en_attente()
    instruction = next(
        (i for i in instructions
         if i["direction_code"] == directeur["direction_code"]),
        None
    )

    if instruction is None:
        await update.message.reply_text(
            "Aucune instruction en attente pour votre direction.\n"
            "Contactez le Directeur Général."
        )
        return

    # Récupérer le contenu du rapport
    contenu = update.message.text or ""
    if contenu.startswith("/rapport"):
        contenu = contenu.replace("/rapport", "").strip()

    if not contenu:
        await update.message.reply_text(
            "Envoyez votre rapport avec la commande :\n"
            "/rapport [votre texte ici]\n\n"
            "Exemple :\n"
            "/rapport Bilan financier préparé et soumis."
        )
        return

    enregistrer_rapport(
            directeur_uuid=str(directeur["id"]),
            contenu=(
                f"{verification['remplis']}/{verification['total']} "
                f"colonnes remplies"
            ),
            instruction_id=instruction_id,
            telegram_file_id=document.file_id,
            nom_fichier=document.file_name,
        )

    # Mettre à jour le statut de l'instruction
    mettre_a_jour_statut(instruction["id"], "fait")

    # Message de confirmation selon l'heure
    if avant_21h:
        confirmation = (
            f"✅ Rapport reçu à l'heure\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Direction  : {directeur['direction_code']}\n"
            f"Heure      : {maintenant.strftime('%H:%M')}\n"
            f"Statut     : A L'HEURE\n"
            f"Merci pour votre ponctualité !"
        )
    else:
        confirmation = (
            f"🟠 Rapport reçu en retard\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Direction  : {directeur['direction_code']}\n"
            f"Heure      : {maintenant.strftime('%H:%M')}\n"
            f"Statut     : EN RETARD\n"
            f"Rapport enregistré malgré le retard."
        )

    await update.message.reply_text(confirmation)

    # Notifier le DG si rapport en retard
    if not avant_21h:
        retard_minutes = (maintenant.hour - 21) * 60 + maintenant.minute
        await context.bot.send_message(
            chat_id = settings.dg_chat_id,
            text    = (
                f"📬 Rapport tardif reçu\n"
                f"Direction : {directeur['direction_code']}\n"
                f"Nom       : {directeur['nom_complet']}\n"
                f"Retard    : {retard_minutes} minutes\n"
                f"Contenu   : {contenu[:100]}..."
                if len(contenu) > 100 else contenu
            )
        )
        logger.info(
            f"DG notifié — rapport tardif {directeur['direction_code']}"
        )