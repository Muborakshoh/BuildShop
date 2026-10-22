"""Telegram Bot integration — notifications + admin alerts. Fully free via Bot API."""

import hashlib
import hmac
import logging
from urllib.parse import urlencode

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BOT_API = "https://api.telegram.org/bot{token}/{method}"


async def _call(method: str, **params) -> dict | None:
    """Call Telegram Bot API. Returns None on failure (non-critical)."""
    token = settings.telegram_bot_token
    if not token:
        logger.debug("Telegram bot token not configured, skipping")
        return None
    url = BOT_API.format(token=token, method=method)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json={k: v for k, v in params.items() if v is not None})
            data = resp.json()
            if not data.get("ok"):
                logger.warning("Telegram API error: %s", data)
            return data
    except Exception as e:
        logger.warning("Telegram API call failed: %s", e)
        return None


# ── Notifications ──

async def send_message(chat_id: int | str, text: str, parse_mode: str = "HTML") -> dict | None:
    return await _call("sendMessage", chat_id=chat_id, text=text, parse_mode=parse_mode)


async def notify_admin_new_order(order_id: int, total: str, items_count: int, customer: str, phone: str | None = None):
    """Send new order notification to admin channel."""
    chat_id = settings.telegram_admin_chat_id
    if not chat_id:
        return
    phone_line = f"\n📞 {phone}" if phone else ""
    text = (
        f"🛒 <b>Фармоиши нав #{order_id}</b>\n"
        f"👤 {customer}{phone_line}\n"
        f"📦 {items_count} маҳсулот\n"
        f"💰 <b>{total} сомонӣ</b>"
    )
    await send_message(chat_id, text)


async def notify_admin_low_stock(product_name: str, quantity: int):
    chat_id = settings.telegram_admin_chat_id
    if not chat_id:
        return
    text = f"⚠️ <b>Захира кам:</b> {product_name} — {quantity} монд"
    await send_message(chat_id, text)


async def notify_admin_contact_form(name: str, email: str, message: str):
    chat_id = settings.telegram_admin_chat_id
    if not chat_id:
        return
    text = (
        f"✉️ <b>Пайғом аз сайт</b>\n"
        f"👤 {name}\n"
        f"📧 {email}\n"
        f"💬 {message[:500]}"
    )
    await send_message(chat_id, text)


async def notify_customer_order_status(chat_id: int, order_id: int, new_status: str, comment: str | None = None):
    """Notify customer about order status change via Telegram."""
    status_labels = {
        "created": "🆕 Қабул шуд",
        "confirmed": "✅ Тасдиқ шуд",
        "assembling": "📦 Ҷамъ карда шудааст",
        "delivering": "🚚 Интиқол дода шудааст",
        "delivered": "📬 Расонида шуд",
        "completed": "🎉 Иҷро шуд",
        "cancelled": "❌ Бекор шуд",
    }
    label = status_labels.get(new_status, new_status)
    text = f"📋 <b>Фармоиш #{order_id}</b>\nҲолат: {label}"
    if comment:
        text += f"\n💬 {comment}"
    await send_message(chat_id, text)


# ── Telegram Login verification ──

def verify_telegram_login(data: dict) -> bool:
    """Verify Telegram Login Widget data using bot token.
    
    See: https://core.telegram.org/widgets/login#checking-authorization
    """
    token = settings.telegram_bot_token
    if not token:
        return False

    check_hash = data.pop("hash", None)
    if not check_hash:
        return False

    # Build data-check-string
    items = sorted(data.items())
    data_check_string = "\n".join(f"{k}={v}" for k, v in items)

    # Secret key = SHA256 of bot token
    secret = hashlib.sha256(token.encode()).digest()
    computed = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()

    return computed == check_hash
