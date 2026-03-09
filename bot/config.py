from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    db_path: str = "data/scrooge.db"
    queue_interval_seconds: int = 60
    max_retries: int = 5
    utko_base_url: str = "https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1"

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8000

    # Webhook (если пусто — используется polling)
    webhook_url: str = ""
    webhook_path: str = "/webhook/telegram"

    model_config = {"env_file": ".env", "env_prefix": "SCROOGE_"}


settings = Settings()
