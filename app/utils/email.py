import smtplib
import ssl
import certifi
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def send_verification_email(email_to: str, code: str):
    message = MIMEMultipart("alternative")
    message["Subject"] = "Email Verification"
    message["From"] = settings.EMAIL_HOST_USER
    message["To"] = email_to

    html_content = f"""
    <html>
      <body>
        <p>Ваш код подтверждения: <strong>{code}</strong></p>
      </body>
    </html>
    """
    message.attach(MIMEText(html_content, "html"))

    context = ssl.create_default_context(cafile=certifi.where())

    with smtplib.SMTP_SSL(settings.EMAIL_HOST, settings.EMAIL_PORT, context=context) as server:
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        server.sendmail(settings.EMAIL_HOST_USER, email_to, message.as_string())