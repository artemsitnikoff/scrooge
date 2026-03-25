import logging
import smtplib
import ssl
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_otp_email(to_email: str, code: str) -> bool:
    if not is_smtp_configured():
        logger.warning("SMTP не настроен, OTP не отправлен")
        return False

    sender = settings.smtp_from or settings.smtp_user
    subject = f"SCROOGE — код для входа: {code}"
    body = (
        f"Ваш код для входа в личный кабинет SCROOGE:\n\n"
        f"    {code}\n\n"
        f"Код действителен 10 минут.\n"
        f"Если вы не запрашивали вход — проигнорируйте это письмо."
    )

    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to_email

    try:
        ctx = ssl.create_default_context()
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ctx) as server:
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                server.starttls(context=ctx)
                server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)
        logger.info("OTP отправлен на %s", to_email)
        return True
    except Exception as e:
        logger.error("Ошибка отправки OTP на %s: %s", to_email, e)
        return False
