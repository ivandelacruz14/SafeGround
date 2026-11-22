import logging
import smtplib
from email.message import EmailMessage

from flask import current_app

log = logging.getLogger(__name__)
OUTBOX = []  # used by the "memory" backend in tests


def send_mail(to, subject, body):
    cfg = current_app.config
    backend = cfg["MAIL_BACKEND"]
    if backend == "memory":
        OUTBOX.append({"to": to, "subject": subject, "body": body})
        return
    if backend == "console":
        log.warning("EMAIL (console backend) to=%s subject=%s\n%s", to, subject, body)
        return
    msg = EmailMessage()
    msg["From"], msg["To"], msg["Subject"] = cfg["MAIL_FROM"], to, subject
    msg.set_content(body)
    with smtplib.SMTP(cfg["MAIL_HOST"], cfg["MAIL_PORT"], timeout=10) as s:
        if cfg["MAIL_USE_TLS"]:
            s.starttls()
        if cfg["MAIL_USERNAME"]:
            s.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
        s.send_message(msg)
