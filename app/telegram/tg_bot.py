"""
Full-featured Telegram Bot for BuildShop (СохтМатериал).

Customer features:
  /start — Main menu
  Browse categories → products → add to cart
  Cart management → checkout → order
  Order history & tracking
  Building materials calculator
  News feed
  Language selection (TJ/RU/EN)

Admin features:
  /admin — Admin dashboard
  Order management with status buttons
  Daily/weekly sales reports
  Low stock alerts
  Broadcast to customers
  User search
  Quick stock update
"""
import asyncio
import logging
import math
import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# ── Setup paths ──
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import func as sa_func, desc
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.session import SessionLocal
from app.products.models import Category, Product
from app.inventory.models import Inventory
from app.orders.models import Order, OrderItem, OrderStatus, OrderStatusHistory, VALID_TRANSITIONS
from app.users.models import User, UserRole
from app.cms.models import News, PageStatus
# Register ALL SQLAlchemy models so mappers resolve correctly
import app.auth.models as _auth_models  # noqa: F401
import app.cashier.models as _cashier_models  # noqa: F401
import app.cms.models as _cms_models  # noqa: F401
import app.delivery.models as _delivery_models  # noqa: F401
import app.inventory.models as _inventory_models  # noqa: F401
import app.orders.models as _orders_models  # noqa: F401
import app.products.models as _products_models  # noqa: F401
import app.promos.models as _promos_models  # noqa: F401
import app.reviews.models as _reviews_models  # noqa: F401
import app.users.models as _users_models  # noqa: F401

logger = logging.getLogger(__name__)

# ── In-memory carts: {telegram_id: {product_id: qty}} ──
carts: dict[int, dict[int, int]] = {}

# ── User language preferences ──
user_langs: dict[int, str] = {}

# ── FSM States ──
class BotStates(StatesGroup):
    waiting_broadcast = State()
    waiting_phone = State()
    waiting_address = State()
    calc_paint_area = State()
    calc_tile_area = State()
    calc_concrete_volume = State()
    calc_wallpaper_dims = State()
    calc_bricks_area = State()
    waiting_stock_product_id = State()
    waiting_stock_qty = State()

# ── Translations ──
TR = {
    'tj': {
        'welcome': '🏗 <b>СохтМатериал</b>\n\nМағозаи масолеҳи сохтмонӣ\nЛутфан аз менюи поён интихоб кунед:',
        'categories': '📂 Категорияҳо', 'cart': '🛒 Сабад', 'my_orders': '📋 Фармоишҳои ман',
        'calculator': '🧮 Калькулятор', 'news': '📰 Хабарҳо', 'language': '🌐 Забон',
        'back': '◀️ Бозгашт', 'back_to_menu': '🏠 Менюи асосӣ',
        'empty_cart': '🛒 Сабади шумо холӣ аст', 'cart_title': '🛒 <b>Сабади шумо:</b>\n',
        'cart_total': '\n💰 <b>Ҷамъ: {} сомонӣ</b>', 'checkout': '✅ Фармоиш додан',
        'clear_cart': '🗑 Тоза кардан', 'added_to_cart': '✅ {} ба сабад илова шуд',
        'removed_from_cart': '❌ Аз сабад нест шуд', 'cart_cleared': '🗑 Сабад тоза шуд',
        'enter_phone': '📞 Рақами телефонатонро ворид кунед:', 'enter_address': '📍 Суроғаи расонидро ворид кунед:',
        'order_created': '✅ Фармоиши #{} қабул шуд!\n💰 Маблағ: {} сомонӣ\nМо бо шумо тамос мегирем.',
        'order_empty': 'Сабад холӣ аст, аввал маҳсулот интихоб кунед.',
        'no_orders': '📋 Шумо ҳанӯз фармоиш надодаед.', 'order_list_title': '📋 <b>Фармоишҳои шумо:</b>\n',
        'in_stock': '✅ Мавҷуд: {} {}', 'out_of_stock': '❌ Нест',
        'price': '💰 {} сомонӣ / {}', 'select_category': '📂 Категорияро интихоб кунед:',
        'products_in': '📦 Маҳсулот дар <b>{}</b>:', 'no_products': 'Маҳсулот ёфт нашуд.',
        'product_detail': '📦 <b>{name}</b>\n\n{desc}\n\n{price}\n{stock}',
        'add_to_cart': '🛒 Ба сабад', 'qty_plus': '➕', 'qty_minus': '➖',
        'calc_title': '🧮 <b>Калькулятори сохтмонӣ</b>\n\nНавъи ҳисобро интихоб кунед:',
        'calc_paint': '🎨 Ранг', 'calc_tile': '🏁 Кошӣ', 'calc_concrete': '🧱 Бетон',
        'calc_wallpaper': '🖼 Обой', 'calc_bricks': '🧱 Хишт',
        'calc_paint_prompt': '🎨 Масоҳати девор/шифтро ворид кунед (м²):',
        'calc_tile_prompt': '🏁 Масоҳатро ворид кунед (м²):',
        'calc_concrete_prompt': '🧱 Ҳаҷми бетонро ворид кунед (м³):',
        'calc_wallpaper_prompt': '🖼 Андозаи ҳуҷра: дарозӣ x бар x баландӣ (масалан: 5 4 2.7):',
        'calc_bricks_prompt': '🧱 Масоҳати деворро ворид кунед (м²):',
        'calc_paint_result': '🎨 <b>Ҳисоби ранг</b>\nМасоҳат: {} м²\nРанг: <b>{:.1f} литр</b>\n(1 қабат, ~10м²/литр)',
        'calc_tile_result': '🏁 <b>Ҳисоби кошӣ</b>\nМасоҳат: {} м²\n+10% захира\nЛозим: <b>{:.1f} м²</b> кошӣ',
        'calc_concrete_result': '🧱 <b>Ҳисоби бетон</b>\nҲаҷм: {} м³\nСемент (M400): <b>{:.0f} халта</b> (50кг)\nРег: <b>{:.1f} м³</b>\nШағал: <b>{:.1f} м³</b>',
        'calc_wallpaper_result': '🖼 <b>Ҳисоби обой</b>\nҲуҷра: {}x{}x{} м\nМасоҳат: {:.1f} м²\nЛозим: <b>{:.0f} рулон</b> (10м x 0.53м)',
        'calc_bricks_result': '🧱 <b>Ҳисоби хишт</b>\nМасоҳат: {} м²\nХишт: <b>{:.0f} дона</b>\n(250x120x65мм, бо дарз)',
        'news_title': '📰 <b>Хабарҳо:</b>\n', 'no_news': '📰 Хабарҳо нест.',
        'lang_select': '🌐 Забонро интихоб кунед:', 'lang_set': '✅ Забон иваз шуд',
        'page': 'Саҳ. {}/{}', 'next_page': '▶️', 'prev_page': '◀️',
        'status_created': '🆕 Сохта шуд', 'status_confirmed': '✅ Тасдиқ', 'status_assembling': '📦 Ҷамъ',
        'status_delivering': '🚚 Интиқол', 'status_delivered': '📬 Расонида', 'status_completed': '🎉 Иҷро',
        'status_cancelled': '❌ Бекор', 'pickup': '🏪 Худгирӣ', 'delivery': '🚚 Расонидан',
    },
    'ru': {
        'welcome': '🏗 <b>СохтМатериал</b>\n\nМагазин строительных материалов\nВыберите из меню ниже:',
        'categories': '📂 Категории', 'cart': '🛒 Корзина', 'my_orders': '📋 Мои заказы',
        'calculator': '🧮 Калькулятор', 'news': '📰 Новости', 'language': '🌐 Язык',
        'back': '◀️ Назад', 'back_to_menu': '🏠 Главное меню',
        'empty_cart': '🛒 Ваша корзина пуста', 'cart_title': '🛒 <b>Ваша корзина:</b>\n',
        'cart_total': '\n💰 <b>Итого: {} сом.</b>', 'checkout': '✅ Оформить заказ',
        'clear_cart': '🗑 Очистить', 'added_to_cart': '✅ {} добавлен в корзину',
        'removed_from_cart': '❌ Удалён из корзины', 'cart_cleared': '🗑 Корзина очищена',
        'enter_phone': '📞 Введите номер телефона:', 'enter_address': '📍 Введите адрес доставки:',
        'order_created': '✅ Заказ #{} принят!\n💰 Сумма: {} сом.\nМы свяжемся с вами.',
        'order_empty': 'Корзина пуста, сначала добавьте товары.',
        'no_orders': '📋 У вас пока нет заказов.', 'order_list_title': '📋 <b>Ваши заказы:</b>\n',
        'in_stock': '✅ В наличии: {} {}', 'out_of_stock': '❌ Нет в наличии',
        'price': '💰 {} сом. / {}', 'select_category': '📂 Выберите категорию:',
        'products_in': '📦 Товары в <b>{}</b>:', 'no_products': 'Товары не найдены.',
        'product_detail': '📦 <b>{name}</b>\n\n{desc}\n\n{price}\n{stock}',
        'add_to_cart': '🛒 В корзину', 'qty_plus': '➕', 'qty_minus': '➖',
        'calc_title': '🧮 <b>Строительный калькулятор</b>\n\nВыберите тип расчёта:',
        'calc_paint': '🎨 Краска', 'calc_tile': '🏁 Плитка', 'calc_concrete': '🧱 Бетон',
        'calc_wallpaper': '🖼 Обои', 'calc_bricks': '🧱 Кирпич',
        'calc_paint_prompt': '🎨 Введите площадь стен/потолка (м²):',
        'calc_tile_prompt': '🏁 Введите площадь (м²):',
        'calc_concrete_prompt': '🧱 Введите объём бетона (м³):',
        'calc_wallpaper_prompt': '🖼 Размер комнаты: длина x ширина x высота (напр: 5 4 2.7):',
        'calc_bricks_prompt': '🧱 Введите площадь стены (м²):',
        'calc_paint_result': '🎨 <b>Расчёт краски</b>\nПлощадь: {} м²\nКраска: <b>{:.1f} литров</b>\n(1 слой, ~10м²/литр)',
        'calc_tile_result': '🏁 <b>Расчёт плитки</b>\nПлощадь: {} м²\n+10% запас\nНужно: <b>{:.1f} м²</b> плитки',
        'calc_concrete_result': '🧱 <b>Расчёт бетона</b>\nОбъём: {} м³\nЦемент (M400): <b>{:.0f} мешков</b> (50кг)\nПесок: <b>{:.1f} м³</b>\nЩебень: <b>{:.1f} м³</b>',
        'calc_wallpaper_result': '🖼 <b>Расчёт обоев</b>\nКомната: {}x{}x{} м\nПлощадь: {:.1f} м²\nНужно: <b>{:.0f} рулонов</b> (10м x 0.53м)',
        'calc_bricks_result': '🧱 <b>Расчёт кирпича</b>\nПлощадь: {} м²\nКирпичей: <b>{:.0f} шт</b>\n(250x120x65мм, со швом)',
        'news_title': '📰 <b>Новости:</b>\n', 'no_news': '📰 Нет новостей.',
        'lang_select': '🌐 Выберите язык:', 'lang_set': '✅ Язык изменён',
        'page': 'Стр. {}/{}', 'next_page': '▶️', 'prev_page': '◀️',
        'status_created': '🆕 Создан', 'status_confirmed': '✅ Подтв.', 'status_assembling': '📦 Сборка',
        'status_delivering': '🚚 Доставка', 'status_delivered': '📬 Доставлен', 'status_completed': '🎉 Выполнен',
        'status_cancelled': '❌ Отменён', 'pickup': '🏪 Самовывоз', 'delivery': '🚚 Доставка',
    },
    'en': {
        'welcome': '🏗 <b>BuildShop</b>\n\nConstruction materials store\nSelect from menu below:',
        'categories': '📂 Categories', 'cart': '🛒 Cart', 'my_orders': '📋 My orders',
        'calculator': '🧮 Calculator', 'news': '📰 News', 'language': '🌐 Language',
        'back': '◀️ Back', 'back_to_menu': '🏠 Main menu',
        'empty_cart': '🛒 Your cart is empty', 'cart_title': '🛒 <b>Your cart:</b>\n',
        'cart_total': '\n💰 <b>Total: {} TJS</b>', 'checkout': '✅ Place order',
        'clear_cart': '🗑 Clear', 'added_to_cart': '✅ {} added to cart',
        'removed_from_cart': '❌ Removed from cart', 'cart_cleared': '🗑 Cart cleared',
        'enter_phone': '📞 Enter your phone number:', 'enter_address': '📍 Enter delivery address:',
        'order_created': '✅ Order #{} placed!\n💰 Total: {} TJS\nWe will contact you.',
        'order_empty': 'Cart is empty, add products first.',
        'no_orders': '📋 You have no orders yet.', 'order_list_title': '📋 <b>Your orders:</b>\n',
        'in_stock': '✅ In stock: {} {}', 'out_of_stock': '❌ Out of stock',
        'price': '💰 {} TJS / {}', 'select_category': '📂 Select a category:',
        'products_in': '📦 Products in <b>{}</b>:', 'no_products': 'No products found.',
        'product_detail': '📦 <b>{name}</b>\n\n{desc}\n\n{price}\n{stock}',
        'add_to_cart': '🛒 Add to cart', 'qty_plus': '➕', 'qty_minus': '➖',
        'calc_title': '🧮 <b>Building Calculator</b>\n\nSelect calculation type:',
        'calc_paint': '🎨 Paint', 'calc_tile': '🏁 Tiles', 'calc_concrete': '🧱 Concrete',
        'calc_wallpaper': '🖼 Wallpaper', 'calc_bricks': '🧱 Bricks',
        'calc_paint_prompt': '🎨 Enter wall/ceiling area (m²):',
        'calc_tile_prompt': '🏁 Enter area (m²):',
        'calc_concrete_prompt': '🧱 Enter concrete volume (m³):',
        'calc_wallpaper_prompt': '🖼 Room size: length x width x height (e.g.: 5 4 2.7):',
        'calc_bricks_prompt': '🧱 Enter wall area (m²):',
        'calc_paint_result': '🎨 <b>Paint calculation</b>\nArea: {} m²\nPaint: <b>{:.1f} liters</b>\n(1 coat, ~10m²/liter)',
        'calc_tile_result': '🏁 <b>Tile calculation</b>\nArea: {} m²\n+10% waste\nNeeded: <b>{:.1f} m²</b> of tiles',
        'calc_concrete_result': '🧱 <b>Concrete calculation</b>\nVolume: {} m³\nCement (M400): <b>{:.0f} bags</b> (50kg)\nSand: <b>{:.1f} m³</b>\nGravel: <b>{:.1f} m³</b>',
        'calc_wallpaper_result': '🖼 <b>Wallpaper calculation</b>\nRoom: {}x{}x{} m\nArea: {:.1f} m²\nNeeded: <b>{:.0f} rolls</b> (10m x 0.53m)',
        'calc_bricks_result': '🧱 <b>Brick calculation</b>\nArea: {} m²\nBricks: <b>{:.0f} pcs</b>\n(250x120x65mm, with mortar)',
        'news_title': '📰 <b>News:</b>\n', 'no_news': '📰 No news.',
        'lang_select': '🌐 Select language:', 'lang_set': '✅ Language changed',
        'page': 'Page {}/{}', 'next_page': '▶️', 'prev_page': '◀️',
        'status_created': '🆕 Created', 'status_confirmed': '✅ Confirmed', 'status_assembling': '📦 Assembling',
        'status_delivering': '🚚 Delivering', 'status_delivered': '📬 Delivered', 'status_completed': '🎉 Completed',
        'status_cancelled': '❌ Cancelled', 'pickup': '🏪 Pickup', 'delivery': '🚚 Delivery',
    },
}

def tr(tg_id: int, key: str) -> str:
    lang = user_langs.get(tg_id, 'tj')
    return TR.get(lang, TR['tj']).get(key, key)

from contextlib import contextmanager

@contextmanager
def get_db_ctx():
    """Context manager that ensures the DB session is always closed."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db() -> Session:
    """Legacy helper — prefer get_db_ctx() context manager."""
    return SessionLocal()

PER_PAGE = 6

# ══════════════════════════════════════════════════════════
# KEYBOARDS
# ══════════════════════════════════════════════════════════

def main_menu_kb(tg_id: int) -> InlineKeyboardMarkup:
    t = lambda k: tr(tg_id, k)
    cart_count = sum(carts.get(tg_id, {}).values())
    cart_label = f"{t('cart')} ({cart_count})" if cart_count else t('cart')
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t('categories'), callback_data='categories:0'),
         InlineKeyboardButton(text=cart_label, callback_data='cart')],
        [InlineKeyboardButton(text=t('my_orders'), callback_data='my_orders'),
         InlineKeyboardButton(text=t('calculator'), callback_data='calculator')],
        [InlineKeyboardButton(text=t('news'), callback_data='news:0'),
         InlineKeyboardButton(text=t('language'), callback_data='lang')],
    ])

def back_menu_kb(tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(tg_id, 'back_to_menu'), callback_data='main_menu')]
    ])

# ══════════════════════════════════════════════════════════
# ROUTER — customer
# ══════════════════════════════════════════════════════════
customer_router = Router()

@customer_router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    # Auto-register / link
    admin_ids = _get_admin_chat_ids()
    with get_db_ctx() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            role = UserRole.ADMIN if tg_id in admin_ids else UserRole.BUYER
            user = User(
                email=f"tg_{tg_id}@telegram.local",
                full_name=message.from_user.full_name or "Telegram User",
                hashed_password="!tg_no_login",
                role=role,
                telegram_id=tg_id,
                telegram_username=message.from_user.username,
                is_active=True,
            )
            db.add(user); db.commit()
        elif tg_id in admin_ids and user.role not in (UserRole.ADMIN, UserRole.MANAGER):
            # Ensure env-listed admin always has admin role in DB
            user.role = UserRole.ADMIN
            db.commit()
    await message.answer(tr(tg_id, 'welcome'), reply_markup=main_menu_kb(tg_id), parse_mode=ParseMode.HTML)

@customer_router.callback_query(F.data == 'main_menu')
async def cb_main_menu(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = cb.from_user.id
    await cb.message.edit_text(tr(tg_id, 'welcome'), reply_markup=main_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── Language ──
@customer_router.callback_query(F.data == 'lang')
async def cb_lang(cb: CallbackQuery):
    tg_id = cb.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🇹🇯 Тоҷикӣ', callback_data='set_lang:tj'),
         InlineKeyboardButton(text='🇷🇺 Русский', callback_data='set_lang:ru'),
         InlineKeyboardButton(text='🇬🇧 English', callback_data='set_lang:en')],
        [InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data='main_menu')],
    ])
    await cb.message.edit_text(tr(tg_id, 'lang_select'), reply_markup=kb, parse_mode=ParseMode.HTML)

@customer_router.callback_query(F.data.startswith('set_lang:'))
async def cb_set_lang(cb: CallbackQuery):
    lang = cb.data.split(':')[1]
    user_langs[cb.from_user.id] = lang
    tg_id = cb.from_user.id
    await cb.answer(tr(tg_id, 'lang_set'))
    await cb.message.edit_text(tr(tg_id, 'welcome'), reply_markup=main_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── Categories ──
@customer_router.callback_query(F.data.startswith('categories:'))
async def cb_categories(cb: CallbackQuery):
    tg_id = cb.from_user.id
    page = int(cb.data.split(':')[1])
    with get_db_ctx() as db:
        total_cats = db.query(sa_func.count(Category.id)).scalar() or 0
        page_cats = db.query(Category).order_by(Category.name).offset(page * PER_PAGE).limit(PER_PAGE).all()
    total_pages = max(1, math.ceil(total_cats / PER_PAGE))
    buttons = []
    for i in range(0, len(page_cats), 2):
        row = []
        for c in page_cats[i:i+2]:
            row.append(InlineKeyboardButton(text=f"📁 {c.name}", callback_data=f'cat:{c.id}:0'))
        buttons.append(row)
    # Pagination
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'prev_page'), callback_data=f'categories:{page-1}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'next_page'), callback_data=f'categories:{page+1}'))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'back_to_menu'), callback_data='main_menu')])
    text = tr(tg_id, 'select_category')
    if total_pages > 1:
        text += f"\n{tr(tg_id, 'page').format(page+1, total_pages)}"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

# ── Products in category ──
@customer_router.callback_query(F.data.startswith('cat:'))
async def cb_products(cb: CallbackQuery):
    tg_id = cb.from_user.id
    parts = cb.data.split(':')
    cat_id, page = int(parts[1]), int(parts[2])
    with get_db_ctx() as db:
        cat = db.query(Category).get(cat_id)
        if not cat:
            await cb.answer("Not found"); return
        cat_name = cat.name
        total_prods = db.query(sa_func.count(Product.id)).filter(Product.category_id == cat_id).scalar() or 0
        # Single query with LEFT JOIN to get stock in one go
        rows = (
            db.query(Product, Inventory.quantity)
            .outerjoin(Inventory, Product.id == Inventory.product_id)
            .filter(Product.category_id == cat_id)
            .order_by(Product.name)
            .offset(page * PER_PAGE).limit(PER_PAGE)
            .all()
        )
        page_prods = [(p, int(qty) if qty else 0) for p, qty in rows]
        prod_stocks = {p.id: stock for p, stock in page_prods}
    total_pages = max(1, math.ceil(total_prods / PER_PAGE))
    if not page_prods:
        await cb.message.edit_text(tr(tg_id, 'no_products'),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data='categories:0')]
            ]), parse_mode=ParseMode.HTML)
        return
    buttons = []
    for p, stock in page_prods:
        stock_icon = '✅' if stock > 0 else '❌'
        buttons.append([InlineKeyboardButton(
            text=f"{stock_icon} {p.name} — {p.price} сом.",
            callback_data=f'prod:{p.id}'
        )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'prev_page'), callback_data=f'cat:{cat_id}:{page-1}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'next_page'), callback_data=f'cat:{cat_id}:{page+1}'))
    if nav:
        buttons.append(nav)
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data='categories:0')])
    text = tr(tg_id, 'products_in').format(cat_name)
    if total_pages > 1:
        text += f"\n{tr(tg_id, 'page').format(page+1, total_pages)}"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

# ── Product detail ──
@customer_router.callback_query(F.data.startswith('prod:'))
async def cb_product_detail(cb: CallbackQuery):
    tg_id = cb.from_user.id
    prod_id = int(cb.data.split(':')[1])
    with get_db_ctx() as db:
        p = db.query(Product).filter(Product.id == prod_id).first()
        if not p:
            await cb.answer("Not found"); return
        inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
        stock = int(inv.quantity) if inv else 0
        cat_id = p.category_id
        price_str = tr(tg_id, 'price').format(p.price, p.unit)
        stock_str = tr(tg_id, 'in_stock').format(stock, p.unit) if stock > 0 else tr(tg_id, 'out_of_stock')
        desc = (p.description or '')[:300]
        text = tr(tg_id, 'product_detail').format(name=p.name, desc=desc, price=price_str, stock=stock_str)
    cart_qty = carts.get(tg_id, {}).get(prod_id, 0)
    buttons = []
    if stock > 0:
        if cart_qty > 0:
            buttons.append([
                InlineKeyboardButton(text='➖', callback_data=f'cart_minus:{prod_id}'),
                InlineKeyboardButton(text=f'🛒 {cart_qty}', callback_data='noop'),
                InlineKeyboardButton(text='➕', callback_data=f'cart_plus:{prod_id}'),
            ])
        else:
            buttons.append([InlineKeyboardButton(text=tr(tg_id, 'add_to_cart'), callback_data=f'add:{prod_id}')])
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data=f'cat:{cat_id}:0')])
    # Send with photo if available
    if p.image_url and p.image_url.startswith('http'):
        try:
            await cb.message.delete()
            await cb.message.answer_photo(p.image_url, caption=text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

# ── Cart operations ──
@customer_router.callback_query(F.data.startswith('add:'))
async def cb_add_to_cart(cb: CallbackQuery):
    tg_id = cb.from_user.id
    prod_id = int(cb.data.split(':')[1])
    if tg_id not in carts:
        carts[tg_id] = {}
    carts[tg_id][prod_id] = carts[tg_id].get(prod_id, 0) + 1
    with get_db_ctx() as db:
        p = db.query(Product).get(prod_id)
        name = p.name if p else '?'
    await cb.answer(tr(tg_id, 'added_to_cart').format(name))
    # Refresh product detail
    await cb_product_detail(cb)

@customer_router.callback_query(F.data.startswith('cart_plus:'))
async def cb_cart_plus(cb: CallbackQuery):
    tg_id = cb.from_user.id
    prod_id = int(cb.data.split(':')[1])
    if tg_id not in carts:
        carts[tg_id] = {}
    carts[tg_id][prod_id] = carts[tg_id].get(prod_id, 0) + 1
    await cb.answer('➕')
    cb.data = f'prod:{prod_id}'
    await cb_product_detail(cb)

@customer_router.callback_query(F.data.startswith('cart_minus:'))
async def cb_cart_minus(cb: CallbackQuery):
    tg_id = cb.from_user.id
    prod_id = int(cb.data.split(':')[1])
    if tg_id in carts and prod_id in carts[tg_id]:
        carts[tg_id][prod_id] -= 1
        if carts[tg_id][prod_id] <= 0:
            del carts[tg_id][prod_id]
    await cb.answer('➖')
    cb.data = f'prod:{prod_id}'
    await cb_product_detail(cb)

@customer_router.callback_query(F.data.startswith('cart_rm:'))
async def cb_cart_remove(cb: CallbackQuery):
    tg_id = cb.from_user.id
    prod_id = int(cb.data.split(':')[1])
    if tg_id in carts and prod_id in carts[tg_id]:
        del carts[tg_id][prod_id]
    await cb.answer(tr(tg_id, 'removed_from_cart'))
    await show_cart(cb)

# ── Cart view ──
@customer_router.callback_query(F.data == 'cart')
async def show_cart(cb: CallbackQuery):
    tg_id = cb.from_user.id
    items = carts.get(tg_id, {})
    if not items:
        await cb.message.edit_text(tr(tg_id, 'empty_cart'), reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)
        return
    with get_db_ctx() as db:
        text = tr(tg_id, 'cart_title')
        total = Decimal('0')
        buttons = []
        for pid, qty in list(items.items()):
            p = db.query(Product).get(pid)
            if not p:
                del items[pid]; continue
            line_total = p.price * qty
            total += line_total
            text += f"\n• {p.name} x{qty} = {line_total} сом."
            buttons.append([
                InlineKeyboardButton(text=f'➖', callback_data=f'cart_minus_v:{pid}'),
                InlineKeyboardButton(text=f'{p.name[:20]} x{qty}', callback_data='noop'),
                InlineKeyboardButton(text=f'➕', callback_data=f'cart_plus_v:{pid}'),
                InlineKeyboardButton(text='🗑', callback_data=f'cart_rm:{pid}'),
            ])
        text += tr(tg_id, 'cart_total').format(total)
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'checkout'), callback_data='checkout')])
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'clear_cart'), callback_data='clear_cart'),
                     InlineKeyboardButton(text=tr(tg_id, 'back_to_menu'), callback_data='main_menu')])
    try:
        await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)
    except Exception:
        await cb.message.delete()
        await cb.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

@customer_router.callback_query(F.data.startswith('cart_plus_v:'))
async def cb_cart_plus_view(cb: CallbackQuery):
    tg_id = cb.from_user.id
    pid = int(cb.data.split(':')[1])
    if tg_id not in carts: carts[tg_id] = {}
    carts[tg_id][pid] = carts[tg_id].get(pid, 0) + 1
    await show_cart(cb)

@customer_router.callback_query(F.data.startswith('cart_minus_v:'))
async def cb_cart_minus_view(cb: CallbackQuery):
    tg_id = cb.from_user.id
    pid = int(cb.data.split(':')[1])
    if tg_id in carts and pid in carts[tg_id]:
        carts[tg_id][pid] -= 1
        if carts[tg_id][pid] <= 0:
            del carts[tg_id][pid]
    await show_cart(cb)

@customer_router.callback_query(F.data == 'clear_cart')
async def cb_clear_cart(cb: CallbackQuery):
    tg_id = cb.from_user.id
    carts.pop(tg_id, None)
    await cb.answer(tr(tg_id, 'cart_cleared'))
    await cb.message.edit_text(tr(tg_id, 'empty_cart'), reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── Checkout flow ──
@customer_router.callback_query(F.data == 'checkout')
async def cb_checkout(cb: CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    if not carts.get(tg_id):
        await cb.answer(tr(tg_id, 'order_empty')); return
    await state.set_state(BotStates.waiting_phone)
    await cb.message.edit_text(tr(tg_id, 'enter_phone'), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data='cart')]
    ]), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    tg_id = message.from_user.id
    await state.set_state(BotStates.waiting_address)
    await message.answer(tr(tg_id, 'enter_address'), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.waiting_address)
async def process_address(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    data = await state.get_data()
    phone = data.get('phone', '')
    address = message.text
    items = carts.get(tg_id, {})
    if not items:
        await message.answer(tr(tg_id, 'order_empty'))
        await state.clear(); return

    with get_db_ctx() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await message.answer("Error: user not found"); await state.clear(); return

        # Calculate total & create order
        total = Decimal('0')
        order_items = []
        for pid, qty in items.items():
            p = db.query(Product).get(pid)
            if not p: continue
            total += p.price * qty
            order_items.append(OrderItem(product_id=p.id, product_name=p.name, quantity=qty, unit_price=p.price))
            # Decrease stock
            inv = db.query(Inventory).filter(Inventory.product_id == p.id).first()
            if inv:
                inv.quantity = max(0, inv.quantity - qty)

        order = Order(
            user_id=user.id, status=OrderStatus.CREATED, total_amount=total,
            delivery_address=address, delivery_method='delivery', phone=phone,
            payment_method='cash', delivery_price=Decimal('0'),
        )
        db.add(order); db.flush()
        for oi in order_items:
            oi.order_id = order.id
            db.add(oi)
        db.add(OrderStatusHistory(order_id=order.id, old_status=None, new_status='created', changed_by=user.id))
        db.commit()
        order_id = order.id

        # Notify admin
        admin_chat = settings.telegram_admin_chat_id
        if admin_chat:
            item_lines = '\n'.join(f"  • {oi.product_name} x{oi.quantity} = {oi.unit_price * oi.quantity}" for oi in order_items)
            admin_text = (
                f"🛒 <b>Фармоиши нав #{order_id}</b>\n"
                f"👤 {user.full_name}\n📞 {phone}\n📍 {address}\n\n"
                f"{item_lines}\n\n💰 <b>Ҷамъ: {total} сомонӣ</b>"
            )
            try:
                bot = cb_checkout.__self__ if hasattr(cb_checkout, '__self__') else None
                # We'll use the global bot instance
                await _bot_instance.send_message(int(admin_chat), admin_text, parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='✅ Тасдиқ', callback_data=f'adm_status:{order_id}:confirmed'),
                         InlineKeyboardButton(text='❌ Рад', callback_data=f'adm_status:{order_id}:cancelled')],
                    ]))
            except Exception as e:
                logger.warning(f"Failed to notify admin: {e}")

    carts.pop(tg_id, None)
    await state.clear()
    await message.answer(tr(tg_id, 'order_created').format(order_id, total),
        reply_markup=main_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── My orders ──
@customer_router.callback_query(F.data == 'my_orders')
async def cb_my_orders(cb: CallbackQuery):
    tg_id = cb.from_user.id
    with get_db_ctx() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        if not user:
            await cb.message.edit_text(tr(tg_id, 'no_orders'), reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)
            return
        orders = db.query(Order).filter(Order.user_id == user.id).order_by(desc(Order.created_at)).limit(10).all()
        if not orders:
            await cb.message.edit_text(tr(tg_id, 'no_orders'), reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)
            return
        text = tr(tg_id, 'order_list_title')
        status_keys = {
            'created': 'status_created', 'confirmed': 'status_confirmed', 'assembling': 'status_assembling',
            'delivering': 'status_delivering', 'delivered': 'status_delivered', 'completed': 'status_completed',
            'cancelled': 'status_cancelled',
        }
        for o in orders:
            sk = status_keys.get(o.status.value, o.status.value)
            text += f"\n#{o.id} | {tr(tg_id, sk)} | {o.total_amount} сом. | {o.created_at.strftime('%d.%m.%Y')}"
    await cb.message.edit_text(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── Calculator ──
@customer_router.callback_query(F.data == 'calculator')
async def cb_calculator(cb: CallbackQuery):
    tg_id = cb.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(tg_id, 'calc_paint'), callback_data='calc:paint'),
         InlineKeyboardButton(text=tr(tg_id, 'calc_tile'), callback_data='calc:tile')],
        [InlineKeyboardButton(text=tr(tg_id, 'calc_concrete'), callback_data='calc:concrete'),
         InlineKeyboardButton(text=tr(tg_id, 'calc_wallpaper'), callback_data='calc:wallpaper')],
        [InlineKeyboardButton(text=tr(tg_id, 'calc_bricks'), callback_data='calc:bricks')],
        [InlineKeyboardButton(text=tr(tg_id, 'back_to_menu'), callback_data='main_menu')],
    ])
    await cb.message.edit_text(tr(tg_id, 'calc_title'), reply_markup=kb, parse_mode=ParseMode.HTML)

@customer_router.callback_query(F.data.startswith('calc:'))
async def cb_calc_type(cb: CallbackQuery, state: FSMContext):
    tg_id = cb.from_user.id
    calc_type = cb.data.split(':')[1]
    prompts = {
        'paint': ('calc_paint_prompt', BotStates.calc_paint_area),
        'tile': ('calc_tile_prompt', BotStates.calc_tile_area),
        'concrete': ('calc_concrete_prompt', BotStates.calc_concrete_volume),
        'wallpaper': ('calc_wallpaper_prompt', BotStates.calc_wallpaper_dims),
        'bricks': ('calc_bricks_prompt', BotStates.calc_bricks_area),
    }
    prompt_key, fsm_state = prompts[calc_type]
    await state.set_state(fsm_state)
    await cb.message.edit_text(tr(tg_id, prompt_key), reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=tr(tg_id, 'back'), callback_data='calculator')]
    ]), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.calc_paint_area)
async def calc_paint(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        area = float(message.text.replace(',', '.'))
        liters = area / 10.0
        text = tr(tg_id, 'calc_paint_result').format(area, liters)
    except ValueError:
        text = "❌ Error"; 
    await state.clear()
    await message.answer(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.calc_tile_area)
async def calc_tile(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        area = float(message.text.replace(',', '.'))
        needed = area * 1.10
        text = tr(tg_id, 'calc_tile_result').format(area, needed)
    except ValueError:
        text = "❌ Error"
    await state.clear()
    await message.answer(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.calc_concrete_volume)
async def calc_concrete(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        vol = float(message.text.replace(',', '.'))
        cement_bags = vol * 6.4  # ~320kg/m3 / 50kg
        sand = vol * 0.5
        gravel = vol * 0.8
        text = tr(tg_id, 'calc_concrete_result').format(vol, cement_bags, sand, gravel)
    except ValueError:
        text = "❌ Error"
    await state.clear()
    await message.answer(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.calc_wallpaper_dims)
async def calc_wallpaper(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        parts = message.text.replace(',', '.').split()
        l, w, h = float(parts[0]), float(parts[1]), float(parts[2])
        perimeter = 2 * (l + w)
        area = perimeter * h
        roll_area = 10 * 0.53  # standard roll
        rolls = math.ceil(area / roll_area * 1.1)
        text = tr(tg_id, 'calc_wallpaper_result').format(l, w, h, area, rolls)
    except (ValueError, IndexError):
        text = "❌ Error (format: 5 4 2.7)"
    await state.clear()
    await message.answer(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

@customer_router.message(BotStates.calc_bricks_area)
async def calc_bricks(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    try:
        area = float(message.text.replace(',', '.'))
        bricks = area * 51  # ~51 bricks/m2 with mortar joints
        text = tr(tg_id, 'calc_bricks_result').format(area, bricks)
    except ValueError:
        text = "❌ Error"
    await state.clear()
    await message.answer(text, reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)

# ── News ──
@customer_router.callback_query(F.data.startswith('news:'))
async def cb_news(cb: CallbackQuery):
    tg_id = cb.from_user.id
    page = int(cb.data.split(':')[1])
    news_per_page = 5
    with get_db_ctx() as db:
        total_news = db.query(sa_func.count(News.id)).filter(News.status == PageStatus.PUBLISHED).scalar() or 0
        page_articles = (
            db.query(News).filter(News.status == PageStatus.PUBLISHED)
            .order_by(desc(News.created_at))
            .offset(page * news_per_page).limit(news_per_page).all()
        )
    if not page_articles and page == 0:
        await cb.message.edit_text(tr(tg_id, 'no_news'), reply_markup=back_menu_kb(tg_id), parse_mode=ParseMode.HTML)
        return
    total_pages = max(1, math.ceil(total_news / news_per_page))
    text = tr(tg_id, 'news_title')
    for a in page_articles:
        date = a.created_at.strftime('%d.%m.%Y') if a.created_at else ''
        text += f"\n📌 <b>{a.title}</b>\n{a.summary or ''}\n<i>{date}</i>\n"
    buttons = []
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'prev_page'), callback_data=f'news:{page-1}'))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text=tr(tg_id, 'next_page'), callback_data=f'news:{page+1}'))
    if nav: buttons.append(nav)
    buttons.append([InlineKeyboardButton(text=tr(tg_id, 'back_to_menu'), callback_data='main_menu')])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

@customer_router.callback_query(F.data == 'noop')
async def cb_noop(cb: CallbackQuery):
    await cb.answer()

# ══════════════════════════════════════════════════════════
# ROUTER — admin
# ══════════════════════════════════════════════════════════
admin_router = Router()

def _get_admin_chat_ids() -> set[int]:
    """Get admin Telegram IDs from env (comma-separated)."""
    raw = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '') or ''
    ids = set()
    for part in raw.split(','):
        part = part.strip()
        if part.isdigit():
            ids.add(int(part))
    return ids

def is_admin(tg_id: int) -> bool:
    # Check env-based admin list first (bot creator)
    if tg_id in _get_admin_chat_ids():
        return True
    # Then check DB role
    with get_db_ctx() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        return user is not None and user.role in (UserRole.ADMIN, UserRole.MANAGER)

@admin_router.message(Command('admin'))
async def cmd_admin(message: Message):
    tg_id = message.from_user.id
    if not is_admin(tg_id):
        await message.answer("⛔ Дастрасӣ нест / Access denied"); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Ҳисобот', callback_data='adm_report'),
         InlineKeyboardButton(text='📋 Фармоишҳо', callback_data='adm_orders:0')],
        [InlineKeyboardButton(text='⚠️ Захираи кам', callback_data='adm_lowstock'),
         InlineKeyboardButton(text='👥 Муштариён', callback_data='adm_users')],
        [InlineKeyboardButton(text='📦 Захира иваз', callback_data='adm_stock_update'),
         InlineKeyboardButton(text='📢 Broadcast', callback_data='adm_broadcast')],
        [InlineKeyboardButton(text='🏠 Менюи асосӣ', callback_data='main_menu')],
    ])
    await message.answer(
        '🔧 <b>Панели админ</b>\n\nИнтихоб кунед:', reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_router.callback_query(F.data == 'adm_panel')
async def cb_admin_panel(cb: CallbackQuery):
    tg_id = cb.from_user.id
    if not is_admin(tg_id):
        await cb.answer("⛔"); return
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Ҳисобот', callback_data='adm_report'),
         InlineKeyboardButton(text='📋 Фармоишҳо', callback_data='adm_orders:0')],
        [InlineKeyboardButton(text='⚠️ Захираи кам', callback_data='adm_lowstock'),
         InlineKeyboardButton(text='👥 Муштариён', callback_data='adm_users')],
        [InlineKeyboardButton(text='📦 Захира иваз', callback_data='adm_stock_update'),
         InlineKeyboardButton(text='📢 Broadcast', callback_data='adm_broadcast')],
    ])
    await cb.message.edit_text('🔧 <b>Панели админ</b>', reply_markup=kb, parse_mode=ParseMode.HTML)

# ── Sales report ──
@admin_router.callback_query(F.data == 'adm_report')
async def cb_admin_report(cb: CallbackQuery):
    if not is_admin(cb.from_user.id):
        await cb.answer("⛔"); return
    with get_db_ctx() as db:
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())

        # Today — use SQL aggregates instead of loading all orders
        today_stats = db.query(
            sa_func.count(Order.id), sa_func.coalesce(sa_func.sum(Order.total_amount), 0)
        ).filter(Order.created_at >= today_start).first()
        today_count, today_revenue = today_stats[0], today_stats[1]

        # This week
        week_stats = db.query(
            sa_func.count(Order.id), sa_func.coalesce(sa_func.sum(Order.total_amount), 0)
        ).filter(Order.created_at >= week_start).first()
        week_count, week_revenue = week_stats[0], week_stats[1]

        # Total
        total_orders = db.query(sa_func.count(Order.id)).scalar() or 0
        total_revenue = db.query(sa_func.sum(Order.total_amount)).scalar() or Decimal('0')

        # New users today
        new_users = db.query(sa_func.count(User.id)).filter(User.created_at >= today_start).scalar() or 0

        # Pending orders
        pending = db.query(sa_func.count(Order.id)).filter(Order.status.in_([OrderStatus.CREATED, OrderStatus.CONFIRMED])).scalar() or 0

        # Top 5 products
        from sqlalchemy import desc as sa_desc
        top_prods = db.query(
            OrderItem.product_name, sa_func.sum(OrderItem.quantity).label('total_qty')
        ).group_by(OrderItem.product_name).order_by(sa_desc('total_qty')).limit(5).all()

    top_text = '\n'.join(f"  {i+1}. {p[0]} — {p[1]} шт." for i, p in enumerate(top_prods)) or '  —'

    text = (
        f"📊 <b>Ҳисоботи фурӯш</b>\n\n"
        f"📅 <b>Имрӯз:</b>\n  Фармоишҳо: {today_count}\n  Даромад: {today_revenue} сом.\n\n"
        f"📅 <b>Ин ҳафта:</b>\n  Фармоишҳо: {week_count}\n  Даромад: {week_revenue} сом.\n\n"
        f"📈 <b>Умумӣ:</b>\n  Фармоишҳо: {total_orders}\n  Даромад: {total_revenue} сом.\n\n"
        f"👥 Муштариёни нав имрӯз: {new_users}\n"
        f"⏳ Фармоишҳои интизорӣ: {pending}\n\n"
        f"🏆 <b>Топ-5 маҳсулот:</b>\n{top_text}"
    )
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔄 Навсозӣ', callback_data='adm_report')],
        [InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')],
    ]), parse_mode=ParseMode.HTML)

# ── Recent orders ──
@admin_router.callback_query(F.data.startswith('adm_orders:'))
async def cb_admin_orders(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    page = int(cb.data.split(':')[1])
    with get_db_ctx() as db:
        orders = db.query(Order).options(selectinload(Order.items)).order_by(desc(Order.created_at)).offset(page*8).limit(8).all()
        users_map = {}
        for o in orders:
            if o.user_id not in users_map:
                u = db.query(User).get(o.user_id)
                users_map[o.user_id] = u.full_name if u else '?'
    if not orders:
        await cb.message.edit_text('📋 Фармоишҳо нест.', reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')]
        ]), parse_mode=ParseMode.HTML); return

    status_icons = {
        'created': '🆕', 'confirmed': '✅', 'assembling': '📦',
        'delivering': '🚚', 'delivered': '📬', 'completed': '🎉', 'cancelled': '❌',
    }
    text = '📋 <b>Фармоишҳо:</b>\n'
    buttons = []
    for o in orders:
        icon = status_icons.get(o.status.value, '❓')
        text += f"\n{icon} #{o.id} | {users_map.get(o.user_id,'?')} | {o.total_amount} сом."
        buttons.append([InlineKeyboardButton(text=f'{icon} #{o.id} — {o.total_amount} сом.', callback_data=f'adm_order:{o.id}')])

    nav = []
    if page > 0: nav.append(InlineKeyboardButton(text='◀️', callback_data=f'adm_orders:{page-1}'))
    nav.append(InlineKeyboardButton(text=f'Саҳ. {page+1}', callback_data='noop'))
    nav.append(InlineKeyboardButton(text='▶️', callback_data=f'adm_orders:{page+1}'))
    buttons.append(nav)
    buttons.append([InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

# ── Order detail + status change ──
@admin_router.callback_query(F.data.startswith('adm_order:'))
async def cb_admin_order_detail(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    order_id = int(cb.data.split(':')[1])
    with get_db_ctx() as db:
        order = db.query(Order).options(selectinload(Order.items)).filter(Order.id == order_id).first()
        if not order: await cb.answer("Not found"); return
        user = db.query(User).get(order.user_id)
        items_text = '\n'.join(f"  • {i.product_name} x{i.quantity} = {i.unit_price * i.quantity}" for i in order.items)
        status_val = order.status.value
        # Valid transitions
        from app.orders.models import VALID_TRANSITIONS
        valid_next = VALID_TRANSITIONS.get(order.status, [])

    status_icons = {
        'created': '🆕 Сохта шуд', 'confirmed': '✅ Тасдиқ', 'assembling': '📦 Ҷамъ',
        'delivering': '🚚 Интиқол', 'delivered': '📬 Расонида', 'completed': '🎉 Иҷро', 'cancelled': '❌ Бекор',
    }
    text = (
        f"📋 <b>Фармоиш #{order_id}</b>\n\n"
        f"👤 {user.full_name if user else '?'}\n"
        f"📞 {order.phone or '—'}\n"
        f"📍 {order.delivery_address}\n"
        f"💳 {order.payment_method}\n\n"
        f"📦 <b>Маҳсулотҳо:</b>\n{items_text}\n\n"
        f"💰 <b>Ҷамъ: {order.total_amount} сомонӣ</b>\n"
        f"📊 Ҳолат: {status_icons.get(status_val, status_val)}\n"
        f"📅 {order.created_at.strftime('%d.%m.%Y %H:%M')}"
    )
    buttons = []
    if valid_next:
        row = []
        for ns in valid_next:
            label = status_icons.get(ns.value, ns.value)[:15]
            row.append(InlineKeyboardButton(text=label, callback_data=f'adm_status:{order_id}:{ns.value}'))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text='◀️ Фармоишҳо', callback_data='adm_orders:0')])
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode=ParseMode.HTML)

# ── Change order status (admin) ──
@admin_router.callback_query(F.data.startswith('adm_status:'))
async def cb_admin_change_status(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    parts = cb.data.split(':')
    order_id, new_status_str = int(parts[1]), parts[2]
    # Validate status value
    try:
        new_status_enum = OrderStatus(new_status_str)
    except ValueError:
        await cb.answer(f"❌ Ҳолати нодуруст: {new_status_str}"); return
    with get_db_ctx() as db:
        order = db.query(Order).get(order_id)
        if not order: await cb.answer("Not found"); return
        # Validate transition
        valid_next = VALID_TRANSITIONS.get(order.status, [])
        if new_status_enum not in valid_next:
            await cb.answer(f"❌ Гузариш аз {order.status.value} ба {new_status_str} мумкин нест"); return
        admin_user = db.query(User).filter(User.telegram_id == cb.from_user.id).first()
        old_status = order.status.value
        order.status = new_status_enum
        db.add(OrderStatusHistory(
            order_id=order_id, old_status=old_status, new_status=new_status_str,
            changed_by=admin_user.id if admin_user else None,
        ))
        db.commit()

        # Notify customer via Telegram if they have telegram_id
        customer = db.query(User).get(order.user_id)
        if customer and customer.telegram_id:
            status_labels = {
                'created': '🆕 Қабул шуд', 'confirmed': '✅ Тасдиқ шуд', 'assembling': '📦 Ҷамъ карда мешавад',
                'delivering': '🚚 Интиқол дода мешавад', 'delivered': '📬 Расонида шуд',
                'completed': '🎉 Иҷро шуд', 'cancelled': '❌ Бекор шуд',
            }
            label = status_labels.get(new_status, new_status)
            notify_text = f"📋 <b>Фармоиш #{order_id}</b>\nҲолати нав: {label}"
            try:
                await _bot_instance.send_message(customer.telegram_id, notify_text, parse_mode=ParseMode.HTML)
            except Exception as e:
                logger.warning(f"Failed to notify customer: {e}")

    await cb.answer(f"✅ Ҳолат иваз шуд → {new_status}")
    # Refresh order detail
    cb.data = f'adm_order:{order_id}'
    await cb_admin_order_detail(cb)

# ── Low stock ──
@admin_router.callback_query(F.data == 'adm_lowstock')
async def cb_admin_lowstock(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    with get_db_ctx() as db:
        low = db.query(Product, Inventory).join(Inventory, Product.id == Inventory.product_id).filter(
            Inventory.quantity <= 10
        ).order_by(Inventory.quantity).limit(20).all()
    if not low:
        text = '✅ <b>Ҳама маҳсулотҳо дар захира ҳаст!</b>'
    else:
        text = '⚠️ <b>Маҳсулотҳо бо захираи кам:</b>\n'
        for p, inv in low:
            icon = '🔴' if inv.quantity <= 3 else '🟡'
            text += f"\n{icon} {p.name} — <b>{int(inv.quantity)} {p.unit}</b>"
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔄 Навсозӣ', callback_data='adm_lowstock')],
        [InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')],
    ]), parse_mode=ParseMode.HTML)

# ── Users stats ──
@admin_router.callback_query(F.data == 'adm_users')
async def cb_admin_users(cb: CallbackQuery):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    with get_db_ctx() as db:
        total = db.query(sa_func.count(User.id)).scalar() or 0
        tg_users = db.query(sa_func.count(User.id)).filter(User.telegram_id.isnot(None)).scalar() or 0
        buyers = db.query(sa_func.count(sa_func.distinct(Order.user_id))).scalar() or 0
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        new_today = db.query(sa_func.count(User.id)).filter(User.created_at >= today).scalar() or 0
        # Top customers
        top = db.query(User.full_name, sa_func.sum(Order.total_amount).label('total')).join(
            Order, Order.user_id == User.id
        ).group_by(User.id, User.full_name).order_by(desc('total')).limit(5).all()
    top_text = '\n'.join(f"  {i+1}. {t[0]} — {t[1]} сом." for i, t in enumerate(top)) or '  —'
    text = (
        f"👥 <b>Муштариён</b>\n\n"
        f"Ҳамагӣ: {total}\n"
        f"Telegram: {tg_users}\n"
        f"Харидорон: {buyers}\n"
        f"Нав имрӯз: {new_today}\n\n"
        f"🏆 <b>Топ-5 муштарӣ:</b>\n{top_text}"
    )
    await cb.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')],
    ]), parse_mode=ParseMode.HTML)

# ── Stock update ──
@admin_router.callback_query(F.data == 'adm_stock_update')
async def cb_stock_update(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    await state.set_state(BotStates.waiting_stock_product_id)
    await cb.message.edit_text(
        '📦 <b>Иваз кардани захира</b>\n\nID-и маҳсулотро ворид кунед:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='◀️ Админ', callback_data='adm_panel')]
        ]), parse_mode=ParseMode.HTML)

@admin_router.message(BotStates.waiting_stock_product_id)
async def process_stock_product(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        pid = int(message.text)
        with get_db_ctx() as db:
            p = db.query(Product).get(pid)
            if not p:
                await message.answer("❌ Маҳсулот ёфт нашуд"); return
            inv = db.query(Inventory).filter(Inventory.product_id == pid).first()
            current = int(inv.quantity) if inv else 0
        await state.update_data(stock_pid=pid)
        await state.set_state(BotStates.waiting_stock_qty)
        await message.answer(f"📦 {p.name}\nЗахираи ҳозира: {current} {p.unit}\n\nМиқдори навро ворид кунед:", parse_mode=ParseMode.HTML)
    except ValueError:
        await message.answer("❌ ID бояд рақам бошад")

@admin_router.message(BotStates.waiting_stock_qty)
async def process_stock_qty(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    try:
        qty = int(message.text)
        data = await state.get_data()
        pid = data['stock_pid']
        with get_db_ctx() as db:
            inv = db.query(Inventory).filter(Inventory.product_id == pid).first()
            if inv:
                inv.quantity = qty
            else:
                db.add(Inventory(product_id=pid, quantity=qty))
            db.commit()
            p = db.query(Product).get(pid)
        await state.clear()
        await message.answer(f"✅ Захираи {p.name} ба {qty} иваз шуд", parse_mode=ParseMode.HTML)
    except ValueError:
        await message.answer("❌ Рақам ворид кунед")

# ── Broadcast ──
@admin_router.callback_query(F.data == 'adm_broadcast')
async def cb_broadcast(cb: CallbackQuery, state: FSMContext):
    if not is_admin(cb.from_user.id): await cb.answer("⛔"); return
    await state.set_state(BotStates.waiting_broadcast)
    await cb.message.edit_text(
        '📢 <b>Broadcast</b>\n\nПайғомро ворид кунед, ки ба ҳамаи муштариён фиристода мешавад:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='◀️ Бекор', callback_data='adm_panel')]
        ]), parse_mode=ParseMode.HTML)

@admin_router.message(BotStates.waiting_broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id): return
    text = message.text
    await state.clear()
    with get_db_ctx() as db:
        users = db.query(User.telegram_id).filter(User.telegram_id.isnot(None)).all()
    sent, failed = 0, 0
    for (tg_id,) in users:
        if tg_id == message.from_user.id: continue
        try:
            await _bot_instance.send_message(tg_id, f"📢 <b>СохтМатериал</b>\n\n{text}", parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            failed += 1
        await asyncio.sleep(0.05)
    await message.answer(f"📢 Broadcast иҷро шуд!\n✅ Фиристода: {sent}\n❌ Хато: {failed}", parse_mode=ParseMode.HTML)


# ══════════════════════════════════════════════════════════
# NEWS BROADCAST — call from backend on news publish
# ══════════════════════════════════════════════════════════
async def broadcast_news(title: str, summary: str | None, slug: str):
    """Send news to all telegram users."""
    with get_db_ctx() as db:
        users = db.query(User.telegram_id).filter(User.telegram_id.isnot(None)).all()
    text = f"📰 <b>Хабари нав!</b>\n\n<b>{title}</b>\n{summary or ''}"
    for (tg_id,) in users:
        try:
            await _bot_instance.send_message(tg_id, text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await asyncio.sleep(0.05)


# ══════════════════════════════════════════════════════════
# BOT ENTRY POINT
# ══════════════════════════════════════════════════════════
_bot_instance: Bot = None

async def main():
    global _bot_instance
    token = settings.telegram_bot_token
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in .env!")
        sys.exit(1)

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    _bot_instance = bot
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(customer_router)
    dp.include_router(admin_router)

    # Set bot commands
    await bot.set_my_commands([
        types.BotCommand(command='start', description='🏠 Менюи асосӣ / Главное меню'),
        types.BotCommand(command='admin', description='🔧 Панели админ'),
    ])

    print(f"🤖 Bot started: @{settings.telegram_bot_username or 'unknown'}")
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
