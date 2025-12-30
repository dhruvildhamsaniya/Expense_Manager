import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.enabled = settings.EMAIL_ENABLED
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.SMTP_FROM_EMAIL or settings.SMTP_USERNAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None
    ):
        """Send email via SMTP."""
        if not self.enabled:
            logger.info(f"Email disabled. Would have sent: {subject} to {to_email}")
            return

        if not all([self.username, self.password, self.from_email]):
            logger.error("Email credentials not configured")
            return

        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.from_email
            message["To"] = to_email

            if body_text:
                message.attach(MIMEText(body_text, "plain"))

            message.attach(MIMEText(body_html, "html"))

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.username,
                password=self.password,
                start_tls=True,
            )

            logger.info(f"Email sent successfully to {to_email}: {subject}")

        except Exception:
            logger.exception("Failed to send email")


    async def send_budget_warning(
        self,
        user_email: str,
        category_name: str,
        percentage: float,
        budget: float,
        spent: float,
    ):
        """Send budget warning email."""
        subject = f"⚠️ Budget Warning: {category_name}"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #f39c12;">Budget Warning!</h2>
            <p>Your spending in <strong>{category_name}</strong> has reached
            <strong>{percentage:.1f}%</strong> of your budget.</p>
            <ul>
                <li>Budget: {budget:.2f}</li>
                <li>Spent: {spent:.2f}</li>
                <li>Remaining: {(budget - spent):.2f}</li>
            </ul>
            <p>
              <a href="http://localhost:8000/dashboard"
                 style="background:#3498db;color:white;padding:10px 20px;
                        text-decoration:none;border-radius:5px;">
                 View Dashboard
              </a>
            </p>
        </body>
        </html>
        """

        body_text = (
            f"Budget Warning! Your spending in {category_name} "
            f"has reached {percentage:.1f}% of your budget."
        )

        await self.send_email(user_email, subject, body_html, body_text)

    async def send_budget_exceeded(
        self,
        user_email: str,
        category_name: str,
        percentage: float,
        budget: float,
        spent: float,
    ):
        """Send budget exceeded email."""
        subject = f"🚨 Budget Exceeded: {category_name}"

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #e74c3c;">Budget Exceeded!</h2>
            <p>Your spending in <strong>{category_name}</strong> has exceeded
            your budget at <strong>{percentage:.1f}%</strong>!</p>
            <ul>
                <li>Budget: {budget:.2f}</li>
                <li>Spent: {spent:.2f}</li>
                <li>Over budget by: {(spent - budget):.2f}</li>
            </ul>
        </body>
        </html>
        """

        body_text = (
            f"Budget Exceeded! Your spending in {category_name} "
            f"has exceeded your budget."
        )

        await self.send_email(user_email, subject, body_html, body_text)

    async def send_recurring_reminder(self, user_email: str, expenses: List[dict]):
        """Send reminder for upcoming recurring expenses."""
        subject = "📅 Upcoming Recurring Expenses"

        expense_list = "".join(
            f"<li>{e['description']}: {e['amount']:.2f} — {e['frequency']}</li>"
            for e in expenses
        )

        body_html = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2>Upcoming Recurring Expenses</h2>
            <ul>{expense_list}</ul>
        </body>
        </html>
        """

        await self.send_email(user_email, subject, body_html)


email_service = EmailService()
