# test_regles.py
from datetime import date, timedelta
from src.core.regles_metier import (
    calculer_statut,
    calculer_taux_execution,
    generer_message_synthese,
    StatutReponse
)

aujourd_hui = date.today()

# Test 1 — instruction en retard
print("Test 1 — En retard :")
r = calculer_statut(
    delai          = aujourd_hui - timedelta(days=2),
    statut_reponse = StatutReponse.EN_ATTENTE
)
print(f"  {r.emoji} {r.statut} — {r.message}\n")

# Test 2 — instruction urgente (demain)
print("Test 2 — Echeance demain :")
r = calculer_statut(
    delai          = aujourd_hui + timedelta(days=1),
    statut_reponse = StatutReponse.EN_COURS
)
print(f"  {r.emoji} {r.statut} — {r.message}\n")

# Test 3 — instruction dans les délais
print("Test 3 — Dans les delais :")
r = calculer_statut(
    delai          = aujourd_hui + timedelta(days=5),
    statut_reponse = StatutReponse.EN_ATTENTE
)
print(f"  {r.emoji} {r.statut} — {r.message}\n")

# Test 4 — instruction terminée
print("Test 4 — Terminee :")
r = calculer_statut(
    delai          = aujourd_hui - timedelta(days=1),
    statut_reponse = StatutReponse.FAIT
)
print(f"  {r.emoji} {r.statut} — {r.message}\n")

# Test 5 — taux d'exécution
print("Test 5 — Taux execution :")
instructions = [
    {"statut_reponse": StatutReponse.FAIT},
    {"statut_reponse": StatutReponse.FAIT},
    {"statut_reponse": StatutReponse.EN_COURS},
    {"statut_reponse": StatutReponse.EN_ATTENTE},
    {"statut_reponse": StatutReponse.BLOQUE},
]
stats = calculer_taux_execution(instructions)
print(generer_message_synthese(stats))