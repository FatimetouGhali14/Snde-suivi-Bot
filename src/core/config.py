"""
Configuration applicative chargée depuis le fichier .env.

Utilisation :
    from src.core.config import settings
    print(settings.bot_token)
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Toutes les variables d'environnement validées au démarrage."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str
    directeur_test_chat_id: int = 0
    dg_chat_id: int = 0

    # Base de données
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "snde_suivi"
    db_user: str = "snde"
    db_password: str

    # Application
    log_level: str = "INFO"
    timezone: str = "Africa/Nouakchott"

    @property
    def database_url(self) -> str:
        """URL de connexion PostgreSQL au format asyncpg."""
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )


# Instance unique utilisée dans tout le projet
settings = Settings()  # type: ignore[call-arg]