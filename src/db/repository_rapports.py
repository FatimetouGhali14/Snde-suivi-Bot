# src/db/repository_rapports.py
import logging
from datetime import date, datetime
from src.db.pool import get_connexion

logger = logging.getLogger(__name__)


def generer_reference() -> str:
    """Génère une référence unique."""
    now = datetime.now()
    return f"INST-{now.strftime('%Y%m%d-%H%M%S')}"


# ── INSTRUCTIONS ───────────────────────────────────

def creer_instruction(
    direction_code : str,
    action         : str,
    delai          : date | None,
    priorite       : str,
) -> dict:
    """Crée une instruction en base."""
    conn      = get_connexion()
    cursor    = conn.cursor()
    reference = generer_reference()

    cursor.execute(
        """
        INSERT INTO instructions
            (reference, direction_code, action, delai, priorite)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, reference, direction_code, action, delai, priorite, statut_reponse
        """,
        (reference, direction_code, action, delai, priorite)
    )
    conn.commit()
    row = cursor.fetchone()

    logger.info(f"Instruction créée : {reference} → {direction_code}")
    return {
        "id"             : row[0],
        "reference"      : row[1],
        "direction_code" : row[2],
        "action"         : row[3],
        "delai"          : row[4],
        "priorite"       : row[5],
        "statut_reponse" : row[6],
    }


def lister_instructions_en_attente() -> list[dict]:
    """Retourne toutes les instructions en attente."""
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id, reference, direction_code, action,
               delai, priorite, statut_reponse
        FROM instructions
        WHERE statut_reponse IN ('en_attente', 'en_cours')
        ORDER BY date_envoi_dg DESC
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id"             : r[0],
            "reference"      : r[1],
            "direction_code" : r[2],
            "action"         : r[3],
            "delai"          : r[4],
            "priorite"       : r[5],
            "statut_reponse" : r[6],
        }
        for r in rows
    ]


def mettre_a_jour_statut(instruction_id: int, statut: str) -> None:
    """Met à jour le statut d'une instruction."""
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE instructions
        SET statut_reponse = %s, date_reponse = NOW()
        WHERE id = %s
        """,
        (statut, instruction_id)
    )
    conn.commit()
    logger.info(f"Instruction #{instruction_id} → {statut}")


# ── RAPPORTS QUOTIDIENS ────────────────────────────

def enregistrer_rapport(
    directeur_uuid: str,
    contenu: str,
    instruction_id: int | None = None,
) -> dict:
    """
    Enregistre le rapport d'un directeur.
    Détermine automatiquement avant ou après 21h.
    
    Args:
        directeur_uuid: UUID du directeur (depuis directeurs.id)
        contenu: Description du rapport (ex: "5/8 colonnes remplies")
        instruction_id: Optionnel — liaison à une instruction du DG
    
    Returns:
        dict avec id, statut, avant_21h
    """
    conn = get_connexion()
    cursor = conn.cursor()
    maintenant = datetime.now()
    avant_21h = maintenant.hour < 21
    statut = "a_l_heure" if avant_21h else "en_retard"

    cursor.execute(
        """
        INSERT INTO rapports_quotidiens
            (instruction_id, directeur_uuid, contenu,
             date_rapport, heure_envoi, statut, envoye_avant_21h)
        VALUES (%s, %s, %s, CURRENT_DATE, NOW(), %s, %s)
        RETURNING id, statut, envoye_avant_21h
        """,
        (instruction_id, directeur_uuid, contenu, statut, avant_21h),
    )
    conn.commit()
    row = cursor.fetchone()

    logger.info(
        "Rapport enregistre - directeur %s, instruction %s, statut %s",
        directeur_uuid,
        instruction_id if instruction_id else "(aucune)",
        statut,
    )
    return {
        "id": row[0],
        "statut": row[1],
        "avant_21h": row[2],
    }
    """
    Enregistre le rapport d'un directeur.
    Détermine automatiquement avant ou après 21h.
    """
    conn       = get_connexion()
    cursor     = conn.cursor()
    maintenant = datetime.now()
    avant_21h  = maintenant.hour < 21
    statut     = "a_l_heure" if avant_21h else "en_retard"

    cursor.execute(
        """
        INSERT INTO rapports_quotidiens
            (instruction_id, directeur_uuid, contenu,
             date_rapport, heure_envoi, statut, envoye_avant_21h)
        VALUES (%s, %s, %s, CURRENT_DATE, NOW(), %s, %s)
        RETURNING id, statut, envoye_avant_21h
        """,
        (instruction_id, directeur_uuid, contenu, statut, avant_21h)
    )
    conn.commit()
    row = cursor.fetchone()

    logger.info(
        f"Rapport enregistré — directeur {directeur_uuid} "
        f"instruction #{instruction_id} — {statut}"
    )
    return {
        "id"       : row[0],
        "statut"   : row[1],
        "avant_21h": row[2],
    }


def rapports_du_jour() -> list[dict]:
    """Retourne tous les rapports envoyés aujourd'hui."""
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            r.id, r.contenu, r.heure_envoi, r.statut,
            r.envoye_avant_21h,
            d.nom_complet, d.direction_code,
            i.reference, i.action
        FROM rapports_quotidiens r
        JOIN directeurs   d ON r.directeur_uuid   = d.id
        JOIN instructions i ON r.instruction_id = i.id
        WHERE r.date_rapport = CURRENT_DATE
        ORDER BY r.heure_envoi
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "id"             : r[0],
            "contenu"        : r[1],
            "heure_envoi"    : r[2],
            "statut"         : r[3],
            "avant_21h"      : r[4],
            "nom_directeur"  : r[5],
            "direction_code" : r[6],
            "reference"      : r[7],
            "action"         : r[8],
        }
        for r in rows
    ]


def directions_sans_rapport_ce_soir() -> list[dict]:
    """
    Retourne les directions sans rapport aujourd'hui.
    Utilisé à 21h pour les alertes.
    """
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT DISTINCT
            d.id, d.nom_complet, d.direction_code,
            d.telegram_chat_id,
            i.id as instruction_id, i.reference, i.action
        FROM instructions i
        JOIN directeurs d ON i.direction_code = d.direction_code
        WHERE
            i.statut_reponse IN ('en_attente', 'en_cours')
            AND NOT EXISTS (
                SELECT 1 FROM rapports_quotidiens r
                WHERE r.instruction_id = i.id
                AND r.date_rapport = CURRENT_DATE
            )
        """
    )
    rows = cursor.fetchall()
    return [
        {
            "directeur_uuid"   : str(r[0]),
            "nom_complet"      : r[1],
            "direction_code"   : r[2],
            "telegram_chat_id" : r[3],
            "instruction_id"   : r[4],
            "reference"        : r[5],
            "action"           : r[6],
        }
        for r in rows
    ]


# ── ALERTES ────────────────────────────────────────

def enregistrer_alerte(
    instruction_id   : int,
    type_alerte      : str,
    envoye_dg        : bool = False,
    envoye_directeur : bool = False,
) -> None:
    """Enregistre une alerte en base."""
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO alertes
            (instruction_id, type_alerte, envoye_dg, envoye_directeur)
        VALUES (%s, %s, %s, %s)
        """,
        (instruction_id, type_alerte, envoye_dg, envoye_directeur)
    )
    conn.commit()
    logger.info(f"Alerte : {type_alerte} instruction #{instruction_id}")


def alerte_deja_envoyee(instruction_id: int, type_alerte: str) -> bool:
    """Vérifie si une alerte a déjà été envoyée aujourd'hui."""
    conn   = get_connexion()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT COUNT(*) FROM alertes
        WHERE instruction_id = %s
        AND type_alerte = %s
        AND date_envoi::date = CURRENT_DATE
        """,
        (instruction_id, type_alerte)
    )
    count = cursor.fetchone()[0]
    return count > 0