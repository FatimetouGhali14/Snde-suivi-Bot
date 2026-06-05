# test_persistance.py
from datetime import date, timedelta
from src.db.repository_rapports import (
    creer_instruction,
    enregistrer_rapport,
    rapports_du_jour,
    lister_instructions_en_attente,
)
from src.db.repository_directeurs import lister_tous

# Créer une instruction test
print("1. Creation instruction...")
inst = creer_instruction(
    direction_code = "DAF",
    action         = "Preparer le bilan financier",
    delai          = date.today() + timedelta(days=3),
    priorite       = "urgent"
)
print(f"   Instruction creee : {inst['reference']}")

# Lister les instructions en attente
print("\n2. Instructions en attente...")
instructions = lister_instructions_en_attente()
print(f"   {len(instructions)} instruction(s) en attente")

# Enregistrer un rapport
print("\n3. Enregistrement rapport...")
directeurs = lister_tous()
if directeurs:
    # Récupérer l'UUID du premier directeur
    directeur_uuid = directeurs[0]["id"] if "id" in directeurs[0] else None
    
    # Chercher l'UUID depuis la BD directement
    from src.db.pool import get_connexion
    conn = get_connexion()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM directeurs LIMIT 1")
    row = cursor.fetchone()
    if row:
        directeur_uuid = str(row[0])
        rapport = enregistrer_rapport(
            instruction_id = inst["id"],
            directeur_uuid = directeur_uuid,
            contenu        = "Bilan financier prepare et soumis"
        )
        print(f"   Rapport enregistre — statut : {rapport['statut']}")

# Rapports du jour
print("\n4. Rapports du jour...")
rapports = rapports_du_jour()
print(f"   {len(rapports)} rapport(s) aujourd'hui")
for r in rapports:
    emoji = "✅" if r["avant_21h"] else "🟠"
    print(f"   {emoji} {r['direction_code']} — {r['statut']}")

print("\nTest persistance termine !")