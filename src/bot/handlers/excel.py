"""
src/bot/handlers/excel.py
Handlers de réception de fichiers Excel.

- handler_excel : le DG envoie un fichier multi-onglets, le bot dispatch
  aux directeurs (workflow actuellement non utilisé mais conservé).
- handler_rapport_excel : un directeur envoie son rapport rempli, le bot
  parse, sauvegarde en BD avec versionnage (renvoi correctif possible),
  et notifie le DG (forward + tableau de bord).
"""
from __future__ import annotations

import logging
import os
import tempfile
from datetime import date, datetime

from telegram import Update
from telegram.ext import ContextTypes

from src.core.config import settings
from src.db.pool import get_connexion
from src.db.repository_directeurs import lister_tous, trouver_par_chat_id
from src.db.repository_rapports import enregistrer_rapport, mettre_a_jour_statut
from src.parsers.excel_parser import (
    ONGLETS_DIRECTIONS,
    extraire_onglet_vers_bytes,
    lire_onglet_pour_direction,
    verifier_kpis_remplis,
)
from src.services.synthese import mettre_a_jour_synthese_dg

logger = logging.getLogger(__name__)


async def handler_excel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Le DG envoie le fichier Excel.
    Le bot distribue l'onglet de chaque directeur.
    
    Note : ce handler n'est plus actif dans main.py (workflow abandonné).
    Conservé pour référence ou usage futur.
    """
    chat_id = update.effective_chat.id

    if chat_id != settings.dg_chat_id:
        await update.message.reply_text(
            "Acces refuse.\n"
            "Seul le Directeur General peut envoyer ce fichier."
        )
        return

    document = update.message.document
    if not document:
        return

    nom_fichier = document.file_name or ""
    if not nom_fichier.endswith((".xlsx", ".xls")):
        await update.message.reply_text("Envoyez un fichier Excel (.xlsx)")
        return

    await update.message.reply_text(
        f"Fichier recu : {nom_fichier}\n"
        "Distribution en cours aux 12 directions..."
    )

    try:
        fichier = await context.bot.get_file(document.file_id)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            chemin_tmp = tmp.name
        await fichier.download_to_drive(chemin_tmp)

        directeurs = lister_tous()
        directeurs_par_code = {d["direction_code"]: d for d in directeurs}

        envoyes = []
        manquants = []

        for code_onglet, nom_direction in ONGLETS_DIRECTIONS.items():
            directeur = directeurs_par_code.get(code_onglet)

            if not directeur:
                manquants.append(f"{code_onglet} - directeur non enregistre")
                continue

            if not directeur.get("telegram_chat_id"):
                manquants.append(f"{code_onglet} - pas de Telegram ID")
                continue

            try:
                onglet_bytes = extraire_onglet_vers_bytes(chemin_tmp, code_onglet)
                date_str = date.today().strftime("%Y%m%d")
                nom_envoi = f"Rapport_{code_onglet}_{date_str}.xlsx"

                await context.bot.send_document(
                    chat_id=directeur["telegram_chat_id"],
                    document=onglet_bytes,
                    filename=nom_envoi,
                    caption=(
                        f"RAPPORT JOURNALIER - {nom_direction}\n"
                        f"--------------------------------\n"
                        f"Date : {date.today().strftime('%d/%m/%Y')}\n\n"
                        f"Remplissez vos 8 colonnes et renvoyez\n"
                        f"ce fichier avant 21h00.\n\n"
                        f"Deadline : 21h00 ce soir"
                    ),
                )
                envoyes.append(f"{code_onglet} - {nom_direction}")
                logger.info(
                    "Onglet %s envoye a %s",
                    code_onglet,
                    directeur["telegram_chat_id"],
                )

            except Exception as e:
                logger.error("Erreur envoi %s : %s", code_onglet, e)
                manquants.append(f"{code_onglet} - erreur : {e}")

        os.unlink(chemin_tmp)

        recap = (
            f"DISTRIBUTION TERMINEE\n"
            f"--------------------------------\n"
            f"Envoyes  : {len(envoyes)}/12\n"
            f"Problemes: {len(manquants)}\n"
            f"--------------------------------\n"
        )

        if envoyes:
            recap += "Directions notifiees :\n"
            for e in envoyes:
                recap += f"  - {e}\n"

        if manquants:
            recap += "\nProblemes :\n"
            for m in manquants:
                recap += f"  - {m}\n"

        recap += "\nLes directeurs ont jusqu'a 21h pour renvoyer leur rapport."
        await update.message.reply_text(recap)

    except Exception as e:
        logger.error("Erreur traitement Excel : %s", e, exc_info=True)
        await update.message.reply_text(f"Erreur lors du traitement : {e}")


async def handler_rapport_excel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Un directeur renvoie son onglet Excel rempli.
    
    - Parse le fichier
    - Enregistre en BD avec versionnage (renvoi correctif possible)
    - Notifie le DG (forward + tableau de bord)
    """
    chat_id = update.effective_chat.id
    document = update.message.document
    maintenant = datetime.now()
    avant_21h = maintenant.hour < 21

    if not document or not (document.file_name or "").endswith(".xlsx"):
        return

    # Identifier le directeur
    directeur = trouver_par_chat_id(chat_id)
    if not directeur:
        await update.message.reply_text(
            "Vous n'etes pas enregistre dans le systeme."
        )
        return

    await update.message.reply_text("Rapport recu - traitement en cours...")

    try:
        # Télécharger le fichier rempli
        fichier = await context.bot.get_file(document.file_id)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            chemin_tmp = tmp.name
        await fichier.download_to_drive(chemin_tmp)

        # Lire le rapport (auto-détection mono ou multi-onglets)
        code = directeur["direction_code"]
        rapport = lire_onglet_pour_direction(chemin_tmp, code)
        os.unlink(chemin_tmp)

        if not rapport:
            await update.message.reply_text(
                f"Onglet {code} introuvable dans votre fichier.\n"
                f"Verifiez que vous envoyez bien le bon modele."
            )
            return

        # Vérifier les colonnes remplies
        verification = verifier_kpis_remplis(rapport)
        statut_heure = "A L'HEURE" if avant_21h else "EN RETARD"

        # Rechercher une instruction "en_attente" pour cette direction
        conn = get_connexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM public.instructions WHERE direction_code = %s "
            "AND statut_reponse = 'en_attente' LIMIT 1",
            (code,),
        )
        row = cursor.fetchone()
        instruction_id = row[0] if row else None

        # Enregistrer le rapport (avec versionnage automatique)
        resultat = enregistrer_rapport(
            directeur_uuid=str(directeur["id"]),
            contenu=(
                f"{verification['remplis']}/{verification['total']} "
                f"colonnes remplies"
            ),
            instruction_id=instruction_id,
            telegram_file_id=document.file_id,
            nom_fichier=document.file_name,
        )
        version = resultat["version"]
        est_correction = resultat["est_correction"]

        # Si une instruction etait en attente, la marquer comme faite
        if instruction_id:
            mettre_a_jour_statut(instruction_id, "fait")

        # Confirmation au directeur (avec mention si correction)
        if est_correction:
            entete = f"Rapport CORRIGE (version {version})"
        else:
            entete = "Rapport enregistre"

        await update.message.reply_text(
            f"{entete}\n"
            f"--------------------------------\n"
            f"Direction : {directeur['direction_code']}\n"
            f"Colonnes remplies : "
            f"{verification['remplis']}/{verification['total']}\n"
            f"Heure : {maintenant.strftime('%H:%M')}\n"
            f"Statut : {statut_heure}"
        )

        # Notification spéciale au DG si retard
        if not avant_21h:
            retard = (maintenant.hour - 21) * 60 + maintenant.minute
            await context.bot.send_message(
                chat_id=settings.dg_chat_id,
                text=(
                    f"Rapport tardif recu\n"
                    f"Direction : {directeur['direction_code']}\n"
                    f"Nom : {directeur['nom_complet']}\n"
                    f"Retard : {retard} minutes\n"
                    f"Colonnes : {verification['remplis']}/{verification['total']}"
                ),
            )

        # Phase test : forward systematique au DG
        type_envoi = f"Rapport CORRIGE v{version}" if est_correction else "Rapport recu"
        await context.bot.send_message(
            chat_id=settings.dg_chat_id,
            text=(
                f"{type_envoi} de :\n"
                f"Direction : {directeur['direction_code']}\n"
                f"Nom : {directeur['nom_complet']}\n"
                f"Heure : {maintenant.strftime('%H:%M')}\n"
                f"Statut : {statut_heure}\n"
                f"Colonnes remplies : "
                f"{verification['remplis']}/{verification['total']}"
            ),
        )

        # Transferer aussi le fichier Excel au DG
        await context.bot.send_document(
            chat_id=settings.dg_chat_id,
            document=document.file_id,
            caption=(
                f"Rapport {directeur['direction_code']} "
                f"du {maintenant.strftime('%d/%m/%Y')}"
                f"{' (v' + str(version) + ')' if est_correction else ''}"
            ),
        )

        # Mettre a jour le tableau de bord DG
        await mettre_a_jour_synthese_dg(
            bot=context.bot,
            chat_id_dg=settings.dg_chat_id,
        )

    except Exception as e:
        logger.error("Erreur rapport directeur : %s", e, exc_info=True)
        await update.message.reply_text(f"Erreur : {e}")