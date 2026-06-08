"""
Service de synthèse DG en temps réel.

Maintient un message Telegram unique côté DG qui est édité à chaque
nouveau rapport reçu. Permet au DG de voir d'un coup d'œil l'état
des 12 directions du jour.
"""
from __future__ import annotations

import logging
from datetime import date as Date, datetime

from telegram import Bot
from telegram.error import BadRequest

from src.db.pool import get_connexion
from src.parsers.excel_parser import ONGLETS_DIRECTIONS

logger = logging.getLogger(__name__)


def recuperer_rapports_du_jour() -> dict[str, dict]:
    """
    Retourne tous les rapports envoyés aujourd'hui, indexés par direction.
    
    Returns:
        dict {direction_code: {nom_directeur, heure_envoi, statut, ...}}
    """
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 
            d.direction_code,
            d.nom_complet,
            r.heure_envoi,
            r.statut,
            r.envoye_avant_21h
        FROM rapports_quotidiens r
        JOIN directeurs d ON r.directeur_uuid = d.id
        WHERE r.date_rapport = CURRENT_DATE
        ORDER BY r.heure_envoi DESC
        """
    )
    rows = cursor.fetchall()
    
    # Si une direction a envoyé plusieurs fois, on garde le plus récent
    rapports = {}
    for row in rows:
        code = row[0]
        if code not in rapports:
            rapports[code] = {
                "nom_directeur": row[1],
                "heure_envoi": row[2],
                "statut": row[3],
                "avant_21h": row[4],
            }
    return rapports


def construire_message_synthese() -> str:
    """
    Construit le texte du message de synthèse à envoyer/éditer.
    """
    rapports = recuperer_rapports_du_jour()
    aujourd_hui = Date.today().strftime("%d/%m/%Y")
    nb_recus = len(rapports)
    total = len(ONGLETS_DIRECTIONS)
    
    lignes = [
        f"📊 TABLEAU DE BORD — {aujourd_hui}",
        "━━━━━━━━━━━━━━━━━━━━━━━",
        f"Rapports reçus : {nb_recus}/{total}",
        "",
    ]
    
    # Une ligne par direction
    for code in ONGLETS_DIRECTIONS.keys():
        if code in rapports:
            r = rapports[code]
            heure = r["heure_envoi"].strftime("%H:%M") if r["heure_envoi"] else "—"
            statut_emoji = "✅" if r["avant_21h"] else "🟠"
            statut_txt = "à l'heure" if r["avant_21h"] else "en retard"
            lignes.append(f"{statut_emoji} {code:<7} {heure}  ({statut_txt})")
        else:
            lignes.append(f"⬜ {code:<7} —")
    
    lignes.append("")
    lignes.append(f"Dernière mise à jour : {datetime.now().strftime('%H:%M')}")
    
    return "\n".join(lignes)


def recuperer_synthese_du_jour() -> dict | None:
    """
    Retourne la synthèse du jour en BD, ou None si pas encore créée.
    """
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, chat_id_dg, message_id, derniere_maj
        FROM synthese_dg
        WHERE date_synthese = CURRENT_DATE
        LIMIT 1
        """
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return {
        "id": row[0],
        "chat_id_dg": row[1],
        "message_id": row[2],
        "derniere_maj": row[3],
    }


def enregistrer_synthese(chat_id_dg: int, message_id: int) -> None:
    """Crée la ligne de synthèse pour aujourd'hui."""
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO synthese_dg (date_synthese, chat_id_dg, message_id)
        VALUES (CURRENT_DATE, %s, %s)
        ON CONFLICT (date_synthese) DO UPDATE 
        SET message_id = EXCLUDED.message_id,
            derniere_maj = NOW()
        """,
        (chat_id_dg, message_id)
    )
    conn.commit()


def mettre_a_jour_timestamp() -> None:
    """Met à jour le timestamp de dernière modification."""
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE synthese_dg 
        SET derniere_maj = NOW()
        WHERE date_synthese = CURRENT_DATE
        """
    )
    conn.commit()


async def mettre_a_jour_synthese_dg(bot: Bot, chat_id_dg: int) -> None:
    """
    Met à jour le tableau de bord DG.
    
    - Si un message existe déjà pour aujourd'hui : on l'édite
    - Si pas de message : on en crée un nouveau et on stocke son ID
    
    Args:
        bot: Instance Telegram Bot (depuis context.bot)
        chat_id_dg: chat_id Telegram du DG
    """
    texte = construire_message_synthese()
    synthese = recuperer_synthese_du_jour()
    
    if synthese and synthese["message_id"]:
        # Tentative d'édition du message existant
        try:
            await bot.edit_message_text(
                chat_id=chat_id_dg,
                message_id=synthese["message_id"],
                text=texte,
            )
            mettre_a_jour_timestamp()
            logger.info("Synthese DG mise a jour (edit message %s)", synthese["message_id"])
            return
        except BadRequest as e:
            # Si le message est introuvable ou identique, on en crée un nouveau
            logger.warning("Edition impossible (%s), creation nouveau message", e)
    
    # Création d'un nouveau message
    message = await bot.send_message(
        chat_id=chat_id_dg,
        text=texte,
    )
    enregistrer_synthese(chat_id_dg, message.message_id)
    logger.info("Nouvelle synthese DG creee (message %s)", message.message_id)