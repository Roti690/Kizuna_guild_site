from pydantic_settings import BaseSettings, SettingsConfigDict
import os

class Settings(BaseSettings):
    app_name: str = "Kizuna"
    database_url: str = "sqlite:///./kizuna.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    session_secret: str = os.getenv("SESSION_SECRET", "dev-change-me")
    officer_password: str = os.getenv("OFFICER_PASSWORD", "dev-password-change-me")


settings = Settings()