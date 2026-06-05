"""
Handler de la commande /ping.

Sert uniquement de smoke test : vérifier que toute la chaîne
Telegram -> bot -> réponse fonctionne avant d'écrire la logique métier.
"""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)


async def handler_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Répond 'pong' à toute commande /ping.

    Args:
        update: Message reçu de Telegram.
        context: Contexte d'exécution (inutilisé ici).
    """
    user = update.effective_user
    chat_id = update.effective_chat.id

    logger.info(
        "Ping reçu de chat_id=%s user=@%s",
        chat_id,
        user.username if user else "inconnu",
    )

    await update.message.reply_text("pong 🏓")