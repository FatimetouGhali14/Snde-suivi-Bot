"""
Script utilitaire pour enroler un directeur (lier son chat_id Telegram).

Usage :
    python -m scripts.enroler_directeur PROD001 6676318397
    python -m scripts.enroler_directeur DG001 7288783007

Pour reset (mettre chat_id a NULL) :
    python -m scripts.enroler_directeur PROD001 --reset

Pour lister tous les directeurs :
    python -m scripts.enroler_directeur --list
"""
from __future__ import annotations

import sys

import pg8000

from src.core.config import settings


def get_conn():
    """Retourne une connexion PostgreSQL."""
    return pg8000.connect(
        host=settings.db_host,
        port=settings.db_port,
        database=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )


def lister_directeurs() -> None:
    """Affiche tous les directeurs et leur statut d'enrolement."""
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT matricule, direction_code, nom_complet, telegram_chat_id "
        "FROM directeurs ORDER BY matricule"
    )
    rows = cursor.fetchall()

    print()
    print(f"{'Matricule':<12} {'Direction':<8} {'Chat ID':<15} {'Nom'}")
    print("-" * 80)
    for row in rows:
        matricule = row[0]
        direction = row[1]
        nom = row[2]
        chat_id = str(row[3]) if row[3] else "(non enrole)"
        print(f"{matricule:<12} {direction:<8} {chat_id:<15} {nom}")
    print()

    conn.close()


def enroler(matricule: str, chat_id: int | None) -> None:
    """Lie un chat_id a un matricule (ou le retire si None)."""
    conn = get_conn()
    cursor = conn.cursor()

    # Verifier que le directeur existe
    cursor.execute(
        "SELECT id, nom_complet, direction_code, telegram_chat_id "
        "FROM directeurs WHERE matricule = %s",
        (matricule,),
    )
    row = cursor.fetchone()

    if row is None:
        print(f"ERREUR : Aucun directeur avec matricule {matricule}")
        print("Utilisez --list pour voir les matricules disponibles.")
        conn.close()
        sys.exit(1)

    ancien_chat_id = row[3]

    # Si on veut affecter un chat_id, verifier qu'il n'est pas deja pris
    if chat_id is not None:
        cursor.execute(
            "SELECT matricule FROM directeurs "
            "WHERE telegram_chat_id = %s AND matricule != %s",
            (chat_id, matricule),
        )
        existant = cursor.fetchone()
        if existant:
            print(
                f"ERREUR : Le chat_id {chat_id} est deja utilise "
                f"par {existant[0]}."
            )
            print("Liberez-le d'abord avec :")
            print(f"  python -m scripts.enroler_directeur {existant[0]} --reset")
            conn.close()
            sys.exit(1)

    # Mise a jour
    cursor.execute(
        "UPDATE directeurs SET telegram_chat_id = %s WHERE matricule = %s",
        (chat_id, matricule),
    )
    conn.commit()

    print()
    print(f"Matricule       : {matricule}")
    print(f"Nom             : {row[1]}")
    print(f"Direction       : {row[2]}")
    print(f"Ancien chat_id  : {ancien_chat_id}")
    print(f"Nouveau chat_id : {chat_id if chat_id is not None else '(reset)'}")
    print()
    print("OK - Mise a jour effectuee")
    print()

    conn.close()


def main() -> None:
    """Parse les arguments et lance l'action."""
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    arg1 = sys.argv[1]

    # Mode liste
    if arg1 == "--list":
        lister_directeurs()
        return

    # Mode enroler / reset
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    matricule = arg1.upper()
    arg2 = sys.argv[2]

    if arg2 == "--reset":
        enroler(matricule, None)
    else:
        try:
            chat_id = int(arg2)
        except ValueError:
            print(f"ERREUR : chat_id doit etre un nombre entier, recu '{arg2}'")
            sys.exit(1)
        enroler(matricule, chat_id)


if __name__ == "__main__":
    main()