from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str
    env: str

    secret_token: str

    groq_apikey: str
    google_cse_id: str
    google_api_key: str
    openai_api: str
    google_search_count: str

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

settings = Settings()
