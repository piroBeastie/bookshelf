from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "BookShelf API"
    database_url: str = "postgresql+psycopg://bookshelf:bookshelf@localhost:5432/bookshelf"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
