# src/bot/handlers/excel.py
# Handler réception fichier Excel du DG + distribution aux directeurs

from __future__ import annotations
import logging
import os
import tempfile
from telegram import Update
from telegram.ext import ContextTypes
from src.core.config import settings
from src.parsers.excel_parser import (
    lire_fichier_complet,
    extraire_onglet_vers_bytes,
    ONGLETS_DIRECTIONS,
)
from src.db.repository_directeurs import lister_tous

logger = logging.getLogger(__name__)


async def handler_excel(
    update  : Update,
    context : ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Le DG envoie le fichier Excel.
    Le bot distribue l'onglet de chaque directeur.
    """
    chat_id = update.effective_chat.id

    # Vérifier que c'est le DG
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
        await update.message.reply_text(
            "Envoyez un fichier Excel (.xlsx)"
        )
        return

    # Confirmer réception
    msg = await update.message.reply_text(
        f"Fichier recu : {nom_fichier}\n"
        "Distribution en cours aux 12 directions..."
    )

    try:
        # Télécharger le fichier
        fichier = await context.bot.get_file(document.file_id)
        with tempfile.NamedTemporaryFile(
            suffix=".xlsx", delete=False
        ) as tmp:
            chemin_tmp = tmp.name
        await fichier.download_to_drive(chemin_tmp)

        # Récupérer les directeurs en BD
        directeurs = lister_tous()
        directeurs_par_code = {
            d["direction_code"]: d for d in directeurs
        }

        # Distribuer chaque onglet
        envoyes  = []
        manquants = []

        for code_onglet, nom_direction in ONGLETS_DIRECTIONS.items():
            directeur = directeurs_par_code.get(code_onglet)

            if not directeur:
                manquants.append(f"{code_onglet} — directeur non enregistré")
                continue

            if not directeur.get("telegram_chat_id"):
                manquants.append(f"{code_onglet} — pas de Telegram ID")
                continue

            try:
                # Extraire l'onglet en bytes
                onglet_bytes = extraire_onglet_vers_bytes(
                    chemin_tmp, code_onglet
                )

                # Nom du fichier à envoyer
                from datetime import date
                date_str   = date.today().strftime("%Y%m%d")
                nom_envoi  = f"Rapport_{code_onglet}_{date_str}.xlsx"

                # Envoyer au directeur
                await context.bot.send_document(
                    chat_id  = directeur["telegram_chat_id"],
                    document = onglet_bytes,
                    filename = nom_envoi,
                    caption  = (
                        f"📋 RAPPORT JOURNALIER — {nom_direction}\n"
                        f"━━━━━━━━━━━━━━━━\n"
                        f"Date : {date.today().strftime('%d/%m/%Y')}\n\n"
                        f"Remplissez vos 8 KPIs et renvoyez\n"
                        f"ce fichier avant 22h00.\n\n"
                        f"⚠️ Deadline : 22h00 ce soir"
                    )
                )
                envoyes.append(f"{code_onglet} — {nom_direction}")
                logger.info(f"Onglet {code_onglet} envoyé à {directeur['telegram_chat_id']}")

            except Exception as e:
                logger.error(f"Erreur envoi {code_onglet} : {e}")
                manquants.append(f"{code_onglet} — erreur : {e}")

        # Supprimer fichier temporaire
        os.unlink(chemin_tmp)

        # Récapitulatif au DG
        recap = (
            f"✅ DISTRIBUTION TERMINEE\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Envoyés  : {len(envoyes)}/12\n"
            f"Problemes: {len(manquants)}\n"
            f"━━━━━━━━━━━━━━━━\n"
        )

        if envoyes:
            recap += "Directions notifiées :\n"
            for e in envoyes:
                recap += f"  ✓ {e}\n"

        if manquants:
            recap += "\nProblèmes :\n"
            for m in manquants:
                recap += f"  ✗ {m}\n"

        recap += "\nLes directeurs ont jusqu'à 22h pour renvoyer leur rapport."
        await update.message.reply_text(recap)

    except Exception as e:
        logger.error(f"Erreur traitement Excel : {e}")
        await update.message.reply_text(
            f"Erreur lors du traitement : {e}"
        )


async def handler_rapport_excel(
    update  : Update,
    context : ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Un directeur renvoie son onglet Excel rempli.
    Le bot extrait les KPIs et sauvegarde en BD.
    """
    from src.db.repository_directeurs import trouver_par_chat_id
    from src.db.repository_rapports import enregistrer_rapport
    from src.parsers.excel_parser import lire_fichier_complet, verifier_kpis_remplis
    from datetime import datetime

    chat_id   = update.effective_chat.id
    document  = update.message.document
    maintenant = datetime.now()
    avant_21h  = maintenant.hour < 21

    if not document or not (document.file_name or "").endswith(".xlsx"):
        return

    # Identifier le directeur
    directeur = trouver_par_chat_id(chat_id)
    if not directeur:
        await update.message.reply_text(
            "Vous n'etes pas enregistré dans le système."
        )
        return

    await update.message.reply_text("Rapport reçu — traitement en cours...")

    try:
        # Télécharger le fichier rempli
        fichier = await context.bot.get_file(document.file_id)
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            chemin_tmp = tmp.name
        await fichier.download_to_drive(chemin_tmp)

        # Lire le rapport
        rapports = lire_fichier_complet(chemin_tmp)
        os.unlink(chemin_tmp)

        code = directeur["direction_code"]
        rapport = rapports.get(code)

        if not rapport:
            await update.message.reply_text(
                f"Onglet {code} introuvable dans votre fichier."
            )
            return

        # Vérifier les KPIs remplis
        verification = verifier_kpis_remplis(rapport)

        # Enregistrer en BD
        from src.db.pool import get_connexion
        conn   = get_connexion()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id FROM public.instructions WHERE direction_code = %s "
            "AND statut_reponse = 'en_attente' LIMIT 1",
            (code,)
        )
        row = cursor.fetchone()

        if row:
            instruction_id = row[0]
            rapport_bd = enregistrer_rapport(
                instruction_id = instruction_id,
                directeur_uuid = str(directeur["id"]),
                contenu        = f"{verification['remplis']}/{verification['total']} KPIs remplis",
            )

            # Mettre à jour statut instruction
            from src.db.repository_rapports import mettre_a_jour_statut
            mettre_a_jour_statut(instruction_id, "fait")

        # Confirmation au directeur
        statut_heure = "A L'HEURE" if avant_21h else "EN RETARD"
        await update.message.reply_text(
            f"Rapport enregistré\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Direction : {directeur['direction_code']}\n"
            f"KPIs remplis : {verification['remplis']}/{verification['total']}\n"
            f"Heure : {maintenant.strftime('%H:%M')}\n"
            f"Statut : {statut_heure}"
        )

        # Notifier DG si retard
        if not avant_21h:
            retard = (maintenant.hour - 21) * 60 + maintenant.minute
            await context.bot.send_message(
                chat_id = settings.dg_chat_id,
                text    = (
                    f"📬 Rapport tardif reçu\n"
                    f"Direction : {directeur['direction_code']}\n"
                    f"Nom : {directeur['nom_complet']}\n"
                    f"Retard : {retard} minutes\n"
                    f"KPIs : {verification['remplis']}/{verification['total']}"
                )
            )
    # Phase test : forwarder le rapport au DG à chaque envoi
        await context.bot.send_message(
            chat_id=settings.dg_chat_id,
            text=(
                f"Rapport recu de :\n"
                f"Direction : {directeur['direction_code']}\n"
                f"Nom : {directeur['nom_complet']}\n"
                f"Heure : {maintenant.strftime('%H:%M')}\n"
                f"Statut : {statut_heure}\n"
                f"KPIs remplis : {verification['remplis']}/{verification['total']}"
            )
        )
        
        # Transferer aussi le fichier Excel au DG
        await context.bot.send_document(
            chat_id=settings.dg_chat_id,
            document=document.file_id,
            caption=f"Rapport {directeur['direction_code']} du {maintenant.strftime('%d/%m/%Y')}"
        )
    except Exception as e:
        logger.error(f"Erreur rapport directeur : {e}")
        await update.message.reply_text(f"Erreur : {e}")