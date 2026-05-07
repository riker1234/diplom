from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/peripheral_dss"
    DNS_UPDATE_INTERVAL_HOURS: int = 12
    WB_UPDATE_INTERVAL_HOURS: int = 12
    ADMIN_KEY: str = "diplom2026"

settings = Settings()
