# src/core/regles_metier.py
# Règles métier pour le calcul des statuts des instructions

from dataclasses import dataclass
from datetime import date
from enum import Enum


class Statut(str, Enum):
    """Statut d'une instruction selon les règles métier."""
    VERT   = "vert"    # Dans les délais
    ORANGE = "orange"  # Proche du délai
    ROUGE  = "rouge"   # En retard


class StatutReponse(str, Enum):
    """Statut de réponse d'un directeur."""
    EN_ATTENTE = "en_attente"
    EN_COURS   = "en_cours"
    FAIT       = "fait"
    BLOQUE     = "bloque"


@dataclass
class ResultatAnalyse:
    """Résultat de l'analyse d'une instruction."""
    statut          : Statut
    jours_restants  : int
    message         : str
    emoji           : str


def calculer_statut(
    delai          : date | None,
    statut_reponse : str,
    aujourd_hui    : date | None = None
) -> ResultatAnalyse:
    """
    Calcule le statut d'une instruction selon les règles :

    FAIT    → toujours VERT peu importe le délai
    BLOQUÉ  → toujours ROUGE
    Pas de délai → VERT par défaut

    Sinon selon les jours restants :
    ROUGE  → délai dépassé (jours < 0)
    ORANGE → délai dans moins de 2 jours
    VERT   → délai dans 2 jours ou plus
    """
    if aujourd_hui is None:
        aujourd_hui = date.today()

    # Instruction terminée → toujours vert
    if statut_reponse == StatutReponse.FAIT:
        return ResultatAnalyse(
            statut         = Statut.VERT,
            jours_restants = 0,
            message        = "Instruction executee avec succes",
            emoji          = "✅"
        )

    # Instruction bloquée → toujours rouge
    if statut_reponse == StatutReponse.BLOQUE:
        return ResultatAnalyse(
            statut         = Statut.ROUGE,
            jours_restants = 0,
            message        = "Instruction bloquee — intervention requise",
            emoji          = "🔴"
        )

    # Pas de délai → vert par défaut
    if delai is None:
        return ResultatAnalyse(
            statut         = Statut.VERT,
            jours_restants = 999,
            message        = "Aucun delai fixe",
            emoji          = "🟢"
        )

    # Calculer les jours restants
    jours_restants = (delai - aujourd_hui).days

    # Rouge → délai dépassé
    if jours_restants < 0:
        return ResultatAnalyse(
            statut         = Statut.ROUGE,
            jours_restants = jours_restants,
            message        = f"Retard de {abs(jours_restants)} jour(s)",
            emoji          = "🔴"
        )

    # Orange → moins de 2 jours
    if jours_restants < 2:
        return ResultatAnalyse(
            statut         = Statut.ORANGE,
            jours_restants = jours_restants,
            message        = f"Echeance dans {jours_restants} jour(s) — urgent",
            emoji          = "🟠"
        )

    # Vert → dans les délais
    return ResultatAnalyse(
        statut         = Statut.VERT,
        jours_restants = jours_restants,
        message        = f"Dans les delais — {jours_restants} jour(s) restants",
        emoji          = "🟢"
    )


def calculer_taux_execution(instructions: list[dict]) -> dict:
    """
    Calcule le taux d'exécution global.
    Retourne un dictionnaire avec les statistiques.
    """
    total      = len(instructions)
    faites     = sum(1 for i in instructions if i["statut_reponse"] == StatutReponse.FAIT)
    en_cours   = sum(1 for i in instructions if i["statut_reponse"] == StatutReponse.EN_COURS)
    en_attente = sum(1 for i in instructions if i["statut_reponse"] == StatutReponse.EN_ATTENTE)
    bloquees   = sum(1 for i in instructions if i["statut_reponse"] == StatutReponse.BLOQUE)

    taux = round((faites / total * 100), 1) if total > 0 else 0

    return {
        "total"      : total,
        "faites"     : faites,
        "en_cours"   : en_cours,
        "en_attente" : en_attente,
        "bloquees"   : bloquees,
        "taux"       : taux,
    }


def generer_message_synthese(stats: dict) -> str:
    """
    Génère le message de synthèse envoyé au DG chaque soir.
    """
    emoji_taux = "✅" if stats["taux"] >= 80 else "🟠" if stats["taux"] >= 50 else "🔴"

    return (
        f"📊 SYNTHESE DU JOUR\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"Total instructions : {stats['total']}\n"
        f"✅ Terminees       : {stats['faites']}\n"
        f"⏳ En cours        : {stats['en_cours']}\n"
        f"📋 En attente      : {stats['en_attente']}\n"
        f"🔴 Bloquees        : {stats['bloquees']}\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"{emoji_taux} Taux execution    : {stats['taux']}%"
    )