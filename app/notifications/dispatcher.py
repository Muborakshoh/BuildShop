"""Unified notification dispatcher — sends via all configured channels."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.notifications.email import send_order_confirmation, send_order_status_update
from app.telegram.bot import (
    notify_admin_new_order,
    notify_customer_order_status,
    notify_admin_contact_form,
    notify_admin_low_stock,
)

logger = logging.getLogger(__name__)
_executor = ThreadPoolExecutor(max_workers=2)


def _run_async(coro):
    """Run async function from sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(coro)
        else:
            loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        loop.run_until_complete(coro)


def notify_new_order(db: Session, order) -> None:
    """Notify about new order via all channels."""
    from app.users.models import User
    user = db.query(User).get(order.user_id)
    if not user:
        return

    customer_name = user.full_name or user.email
    total_str = f"{order.total_amount:,.2f}"
    items_count = len(order.items)
    phone = order.phone or user.phone

    # Email to customer
    items_html = ""
    for item in order.items:
        name = item.product_name or f"#{item.product_id}"
        items_html += (
            f'<tr style="border-bottom:1px solid #eee">'
            f'<td style="padding:8px">{name}</td>'
            f'<td style="padding:8px;text-align:center">×{item.quantity}</td>'
            f'<td style="padding:8px;text-align:right">{item.unit_price * item.quantity:,.2f}</td>'
            f'</tr>'
        )
    if not user.email.endswith("@telegram.local"):
        _executor.submit(send_order_confirmation, user.email, order.id, total_str, items_html)

    # Telegram to admin
    _run_async(notify_admin_new_order(order.id, total_str, items_count, customer_name, phone))

    # Telegram to customer (if linked)
    if user.telegram_id:
        _run_async(notify_customer_order_status(user.telegram_id, order.id, "created"))


def notify_order_status_change(db: Session, order, new_status: str, comment: str | None = None) -> None:
    """Notify customer about order status change."""
    from app.users.models import User
    user = db.query(User).get(order.user_id)
    if not user:
        return

    # Email
    if not user.email.endswith("@telegram.local"):
        _executor.submit(send_order_status_update, user.email, order.id, new_status, comment)

    # Telegram
    if user.telegram_id:
        _run_async(notify_customer_order_status(user.telegram_id, order.id, new_status, comment))


def notify_contact_form(name: str, email: str, message: str) -> None:
    """Forward contact form submission to admin."""
    _run_async(notify_admin_contact_form(name, email, message))


def notify_low_stock(product_name: str, quantity: int) -> None:
    _run_async(notify_admin_low_stock(product_name, quantity))
