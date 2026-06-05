import pg8000
from src.core.config import settings

conn = pg8000.connect(
    host     = settings.db_host,
    port     = settings.db_port,
    database = settings.db_name,
    user     = settings.db_user,
    password = settings.db_password
)
conn.run("SET search_path TO public")

# Voir tous les directeurs
rows = conn.run("SELECT matricule, direction_code, telegram_chat_id FROM public.directeurs ORDER BY matricule")
print("Tous les directeurs :")
for r in rows:
    print(f"  {r}")

# Chercher PROD
rows2 = conn.run("SELECT * FROM public.directeurs WHERE direction_code = 'PROD'")
print(f"\nPROD : {rows2}")

conn.close()