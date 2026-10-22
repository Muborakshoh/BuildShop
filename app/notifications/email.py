"""Email notifications via SMTP (Gmail free: 500/day)."""

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def _send_email(to: str, subject: str, html_body: str) -> bool:
    """Send email via SMTP. Returns True on success."""
    if not settings.smtp_host or not settings.smtp_username:
        logger.debug("SMTP not configured, skipping email")
        return False
    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"СохтМатериал <{settings.smtp_from_email}>"
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        if settings.smtp_use_tls:
            server = smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=10)

        server.login(settings.smtp_username, settings.smtp_password)
        server.sendmail(settings.smtp_from_email, to, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        logger.warning("Email send failed: %s", e)
        return False


def send_order_confirmation(to: str, order_id: int, total: str, items_html: str):
    subject = f"Фармоиш #{order_id} қабул шуд — СохтМатериал"
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:0 auto">
      <h2 style="color:#2563eb">🛒 Фармоиши шумо қабул шуд!</h2>
      <p>Рақами фармоиш: <b>#{order_id}</b></p>
      <table style="width:100%;border-collapse:collapse;margin:16px 0">
        {items_html}
      </table>
      <p style="font-size:18px"><b>Ҳамагӣ: {total} сомонӣ</b></p>
      <p style="color:#666;font-size:13px">Мо бо шумо тамос мегирем барои тасдиқ.</p>
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
      <p style="color:#999;font-size:11px">СохтМатериал — Мағозаи масолеҳи сохтмонӣ</p>
    </div>
    """
    _send_email(to, subject, html)


def send_order_status_update(to: str, order_id: int, new_status: str, comment: str | None = None):
    status_labels = {
        "created": "🆕 Қабул шуд",
        "confirmed": "✅ Тасдиқ шуд",
        "assembling": "📦 Ҷамъ карда мешавад",
        "delivering": "🚚 Дар роҳ",
        "delivered": "📬 Расонида шуд",
        "completed": "🎉 Иҷро шуд",
        "cancelled": "❌ Бекор шуд",
    }
    label = status_labels.get(new_status, new_status)
    subject = f"Фармоиш #{order_id} — {label}"
    comment_html = f"<p>💬 {comment}</p>" if comment else ""
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:0 auto">
      <h2 style="color:#2563eb">📋 Ҳолати фармоиш #{order_id}</h2>
      <p style="font-size:18px">{label}</p>
      {comment_html}
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
      <p style="color:#999;font-size:11px">СохтМатериал — Мағозаи масолеҳи сохтмонӣ</p>
    </div>
    """
    _send_email(to, subject, html)


def send_welcome_email(to: str, name: str):
    subject = "Хуш омадед ба СохтМатериал!"
    html = f"""
    <div style="font-family:sans-serif;max-width:500px;margin:0 auto">
      <h2 style="color:#2563eb">👋 Хуш омадед, {name}!</h2>
      <p>Шумо бомуваффақият ба СохтМатериал сабтином шудед.</p>
      <p>Акнун шумо метавонед:</p>
      <ul>
        <li>Маҳсулотро харед ва фармоиш диҳед</li>
        <li>Тақризҳо гузоред</li>
        <li>Ҳолати фармоишро пайгирӣ кунед</li>
      </ul>
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
      <p style="color:#999;font-size:11px">СохтМатериал — Мағозаи масолеҳи сохтмонӣ</p>
    </div>
    """
    _send_email(to, subject, html)
