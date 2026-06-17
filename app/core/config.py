from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    PORT: int = 8000

    # O formato atualizado do Pydantic v2
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()