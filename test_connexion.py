import asyncio
import sys

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import asyncpg

async def test():
    try:
        conn = await asyncpg.connect(
            host="localhost",
            port=5432,
            database="snde_suivi",
            user="snde",
            password="motdepasse"
        )
        print("asyncpg connecte !")
        await conn.close()
    except Exception as e:
        print(f"Erreur : {e}")

asyncio.run(test())