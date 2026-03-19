import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)


class EmailClient:
    """SMTP email client for notifications and digests."""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        if not self.username or not self.password:
            logger.warning("Email not configured. Skipping send.")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = to

            if body_text:
                msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, to, msg.as_string())

            logger.info(f"Email sent to {to}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False

    def send_digest(self, to: str, stats: dict) -> bool:
        """Send daily job search digest email."""
        subject = f"Your Daily Job Search Update - {stats.get('new_jobs', 0)} new jobs found"
        html = f"""
<html><body>
<h2>Daily Job Search Digest</h2>
<hr>
<h3>Today's Summary</h3>
<ul>
  <li>New jobs discovered: <strong>{stats.get('new_jobs', 0)}</strong></li>
  <li>High match jobs: <strong>{stats.get('high_match', 0)}</strong></li>
  <li>Active applications: <strong>{stats.get('active_apps', 0)}</strong></li>
  <li>Pending tasks: <strong>{stats.get('pending_tasks', 0)}</strong></li>
</ul>
<p><a href="http://localhost:5173">Open Dashboard &rarr;</a></p>
</body></html>"""
        return self.send(to, subject, html)
