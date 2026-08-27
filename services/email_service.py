from __future__ import annotations

import os
import smtplib
import ssl
from dataclasses import dataclass, field
from email.message import EmailMessage


@dataclass(slots=True)
class EmailConfig:
    host: str = field(default_factory=lambda: os.getenv("BBOO_SMTP_HOST", ""))
    port: int = field(default_factory=lambda: int(os.getenv("BBOO_SMTP_PORT", "587")))
    username: str = field(default_factory=lambda: os.getenv("BBOO_SMTP_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("BBOO_SMTP_PASSWORD", ""))
    sender: str = field(default_factory=lambda: os.getenv("BBOO_EMAIL_FROM", "Bboo <no-reply@bboo.app>"))
    use_tls: bool = field(default_factory=lambda: os.getenv("BBOO_SMTP_TLS", "true").lower() != "false")


class EmailService:
    def __init__(self, config: EmailConfig | None = None) -> None:
        self.config = config or EmailConfig()

    def is_configured(self) -> bool:
        return bool(self.config.host)

    def send_screen_time_reminder(
        self,
        *,
        to_email: str,
        first_name: str,
        app_name: str,
        usage_date: str,
        threshold_minutes: int,
        total_minutes: int,
    ) -> bool:
        if not self.is_configured():
            return False

        message = EmailMessage()
        message["From"] = self.config.sender
        message["To"] = to_email
        message["Subject"] = f"Bboo screen time reminder: {self._format_minutes(threshold_minutes)} on {app_name}"
        message.set_content(
            "\n".join(
                [
                    f"Hi {first_name or 'there'},",
                    "",
                    f"You have reached {self._format_minutes(threshold_minutes)} of screen time on {app_name} for {usage_date}.",
                    f"Your saved total is now {self._format_minutes(total_minutes)}.",
                    "",
                    "Take a short pause, check your plan, and decide whether this app still deserves your attention right now.",
                    "",
                    "Bboo",
                ]
            )
        )

        with smtplib.SMTP(self.config.host, self.config.port, timeout=15) as smtp:
            if self.config.use_tls:
                smtp.starttls(context=ssl.create_default_context())
            if self.config.username:
                smtp.login(self.config.username, self.config.password)
            smtp.send_message(message)
        return True

    def _format_minutes(self, minutes: int) -> str:
        hours, remainder = divmod(minutes, 60)
        if hours and remainder:
            return f"{hours} hr {remainder} min"
        if hours:
            return f"{hours} hr" if hours == 1 else f"{hours} hrs"
        return f"{remainder} min"
