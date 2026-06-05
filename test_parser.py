# test_parser.py
from src.parsers.excel_parser import lire_fichier_excel

lignes = lire_fichier_excel("test_instructions.xlsx")

print(f"\n{len(lignes)} instructions trouvees :\n")
for ligne in lignes:
    print(f"Ligne {ligne.ligne_numero}")
    print(f"  Direction : {ligne.direction_code}")
    print(f"  Action    : {ligne.action}")
    print(f"  Delai     : {ligne.delai}")
    print(f"  Priorite  : {ligne.priorite}")
    print()