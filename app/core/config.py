from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str
    env: str

    secret_token: str

    openai_apikey: str

    class Config:
        env_file = ".env"

settings = Settings()
