from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    bot_token: str
    db_path: str = "data/scrooge.db"
    queue_interval_seconds: int = 60
    max_retries: int = 5
    utko_base_url: str = "https://api.utko.mnr.gov.ru/reo-weight-control-api/api/v1"

    # FastAPI
    host: str = "0.0.0.0"
    port: int = 8111
    api_token: str = ""
    provider_token: str = ""

    # ЮKassa
    yukassa_shop_id: str = ""
    yukassa_secret_key: str = ""

    # Webhook (если пусто — используется polling)
    webhook_url: str = ""
    webhook_path: str = "/webhook/telegram"

    # Личный кабинет — JWT
    jwt_secret: str = ""

    # Личный кабинет — SMTP для OTP
    smtp_host: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""

    # Личный кабинет — base URL для ЮKassa return_url
    web_base_url: str = ""

    model_config = {"env_file": ".env", "env_prefix": "SCROOGE_"}


settings = Settings()
