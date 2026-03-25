import logging
import smtplib
import ssl
import traceback
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    return bool(settings.smtp_host and settings.smtp_user and settings.smtp_password)


def send_otp_email(to_email: str, code: str) -> bool:
    if not is_smtp_configured():
        logger.warning("SMTP не настроен: host=%s, user=%s, password_set=%s",
                       settings.smtp_host, settings.smtp_user, bool(settings.smtp_password))
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

    logger.info("Отправка OTP: to=%s, host=%s:%d, user=%s, from=%s",
                to_email, settings.smtp_host, settings.smtp_port, settings.smtp_user, sender)

    try:
        ctx = ssl.create_default_context()
        if settings.smtp_port == 465:
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=ctx, timeout=15) as server:
                logger.info("SMTP_SSL подключение установлено")
                server.login(settings.smtp_user, settings.smtp_password)
                logger.info("SMTP login ок")
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
                server.starttls(context=ctx)
                logger.info("SMTP STARTTLS подключение установлено")
                server.login(settings.smtp_user, settings.smtp_password)
                logger.info("SMTP login ок")
                server.send_message(msg)
        logger.info("OTP успешно отправлен на %s", to_email)
        return True
    except smtplib.SMTPAuthenticationError as e:
        logger.error("SMTP auth ошибка: %s (проверьте пароль приложения)", e)
        return False
    except smtplib.SMTPException as e:
        logger.error("SMTP ошибка: %s", e)
        return False
    except Exception as e:
        logger.error("Ошибка отправки OTP на %s: %s\n%s", to_email, e, traceback.format_exc())
        return False
