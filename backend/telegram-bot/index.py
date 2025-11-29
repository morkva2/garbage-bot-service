"""
Business: Telegram bot for garbage collection courier service with roles
Args: event - webhook from Telegram with updates
      context - cloud function context with request_id
Returns: HTTP response with statusCode 200
"""

import json
import os
import psycopg2
from typing import Dict, Any, Optional, List
from datetime import datetime

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

ORDER_STATUSES = {
    'searching_courier': '🔍 В поиске курьера',
    'courier_on_way': '🚗 Курьер едет',
    'courier_working': '🛠 Курьер выполняет заказ',
    'completed': '✅ Завершён',
    'cancelled': '❌ Отменён'
}

def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    return psycopg2.connect(database_url)

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> None:
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    url = TELEGRAM_API.format(token=token, method='sendMessage')
    
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)
    
    import urllib.request
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    urllib.request.urlopen(req)

def check_user_role(telegram_id: int, conn) -> str:
    cursor = conn.cursor()
    
    cursor.execute("SELECT 1 FROM admin_users WHERE telegram_id = %s", (telegram_id,))
    if cursor.fetchone():
        cursor.close()
        return 'admin'
    
    cursor.execute("SELECT 1 FROM operator_users WHERE telegram_id = %s", (telegram_id,))
    if cursor.fetchone():
        cursor.close()
        return 'operator'
    
    cursor.execute("SELECT role FROM users WHERE telegram_id = %s", (telegram_id,))
    user = cursor.fetchone()
    cursor.close()
    
    return user[0] if user else 'client'

def get_main_menu_keyboard(role: str) -> Dict:
    if role == 'admin':
        return {
            'inline_keyboard': [
                [{'text': '👑 Админ-панель', 'callback_data': 'admin_panel'}],
                [{'text': '📊 Статистика сервиса', 'callback_data': 'admin_stats'}],
                [{'text': '👔 Управление курьерами', 'callback_data': 'admin_couriers'}],
                [{'text': '👥 Управление операторами', 'callback_data': 'admin_operators'}],
                [{'text': '📦 Все заказы', 'callback_data': 'admin_all_orders'}]
            ]
        }
    elif role == 'operator':
        return {
            'inline_keyboard': [
                [{'text': '📞 Активные заказы', 'callback_data': 'operator_active_orders'}],
                [{'text': '💬 Чаты заказов', 'callback_data': 'operator_chats'}],
                [{'text': '📊 Статистика', 'callback_data': 'operator_stats'}]
            ]
        }
    elif role == 'courier':
        return get_courier_menu_keyboard()
    else:
        return {
            'inline_keyboard': [
                [{'text': '👔 Стать курьером', 'callback_data': 'apply_courier'}],
                [{'text': '👤 Для клиентов', 'callback_data': 'client_menu'}],
                [{'text': '⭐ Отзывы', 'callback_data': 'reviews'}],
                [{'text': '💬 Поддержка', 'url': 'https://t.me/support'}]
            ]
        }

def get_courier_menu_keyboard() -> Dict:
    return {
        'inline_keyboard': [
            [{'text': '📦 Доступные заказы', 'callback_data': 'courier_available'}],
            [{'text': '🚚 Текущие заказы', 'callback_data': 'courier_current'}],
            [{'text': '📊 История заказов', 'callback_data': 'courier_history'}],
            [{'text': '💰 Статистика и финансы', 'callback_data': 'courier_stats'}],
            [{'text': '💬 Связаться с поддержкой', 'url': 'https://t.me/support'}],
            [{'text': '💵 Вывод денежных средств', 'callback_data': 'courier_withdraw'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }

def get_client_menu_keyboard() -> Dict:
    return {
        'inline_keyboard': [
            [{'text': '➕ Сделать заказ', 'callback_data': 'client_new_order'}],
            [{'text': '📦 Активные заказы', 'callback_data': 'client_active'}],
            [{'text': '📊 История заказов', 'callback_data': 'client_history'}],
            [{'text': '💳 Способ оплаты', 'callback_data': 'client_payment'}],
            [{'text': '💬 Связаться с поддержкой', 'url': 'https://t.me/support'}],
            [{'text': '⭐ Подписка', 'callback_data': 'client_subscription'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }

def get_or_create_user(telegram_id: int, username: str, first_name: str, conn) -> Dict:
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT telegram_id, username, first_name, role FROM users WHERE telegram_id = %s",
        (telegram_id,)
    )
    user = cursor.fetchone()
    
    if user:
        cursor.close()
        return {
            'telegram_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'role': user[3]
        }
    
    cursor.execute(
        "INSERT INTO users (telegram_id, username, first_name, role) VALUES (%s, %s, %s, %s) RETURNING telegram_id, username, first_name, role",
        (telegram_id, username, first_name, 'client')
    )
    new_user = cursor.fetchone()
    conn.commit()
    cursor.close()
    
    return {
        'telegram_id': new_user[0],
        'username': new_user[1],
        'first_name': new_user[2],
        'role': new_user[3]
    }

def handle_start(chat_id: int, telegram_id: int, username: str, first_name: str, conn) -> None:
    get_or_create_user(telegram_id, username, first_name, conn)
    role = check_user_role(telegram_id, conn)
    
    if role == 'admin':
        welcome_text = "👑 <b>Админ-панель</b>\n\nДобро пожаловать в панель администратора."
    elif role == 'operator':
        welcome_text = "📞 <b>Панель оператора</b>\n\nДобро пожаловать в панель оператора."
    elif role == 'courier':
        welcome_text = "👔 <b>Меню курьера</b>\n\nВыберите действие:"
    else:
        welcome_text = (
            "🚚 <b>Курьерская служба «Экономь время»</b>\n\n"
            "Добро пожаловать! Мы предоставляем услуги вывоза мусора.\n\n"
            "Выберите действие:"
        )
    
    send_message(chat_id, welcome_text, get_main_menu_keyboard(role))

def handle_apply_courier(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT status FROM courier_applications WHERE telegram_id = %s ORDER BY created_at DESC LIMIT 1",
        (telegram_id,)
    )
    existing = cursor.fetchone()
    
    if existing and existing[0] == 'pending':
        text = "⏳ Ваша заявка на рассмотрении. Ожидайте одобрения администратора."
        cursor.close()
        keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
        send_message(chat_id, text, keyboard)
        return
    
    cursor.execute(
        "INSERT INTO courier_applications (telegram_id, status) VALUES (%s, %s)",
        (telegram_id, 'pending')
    )
    conn.commit()
    cursor.close()
    
    text = (
        "✅ Заявка на роль курьера отправлена!\n\n"
        "Администратор рассмотрит её в ближайшее время."
    )
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
    send_message(chat_id, text, keyboard)

def handle_client_menu(chat_id: int) -> None:
    text = "👤 <b>Меню клиента</b>\n\nВыберите действие:"
    send_message(chat_id, text, get_client_menu_keyboard())

def handle_courier_available_orders(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, address, description, price, detailed_status FROM orders WHERE status = %s ORDER BY created_at DESC LIMIT 10",
        ('pending',)
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "📦 <b>Доступные заказы</b>\n\nНет доступных заказов"
        keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
        send_message(chat_id, text, keyboard)
        return
    
    text = "📦 <b>Доступные заказы</b>\n\n"
    keyboard_buttons = []
    
    for order in orders:
        order_id, address, description, price, detailed_status = order
        status_text = ORDER_STATUSES.get(detailed_status, detailed_status)
        text += f"🆔 Заказ #{order_id}\n"
        text += f"📍 {address}\n"
        text += f"📝 {description}\n"
        text += f"💰 {price} ₽\n"
        text += f"Статус: {status_text}\n\n"
        keyboard_buttons.append([{'text': f'✅ Принять #{order_id}', 'callback_data': f'accept_order_{order_id}'}])
    
    keyboard_buttons.append([{'text': '⬅️ Назад', 'callback_data': 'start'}])
    send_message(chat_id, text, {'inline_keyboard': keyboard_buttons})

def handle_accept_order(chat_id: int, telegram_id: int, order_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute("SELECT status FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    
    if not order or order[0] != 'pending':
        send_message(chat_id, "❌ Заказ недоступен или уже принят")
        cursor.close()
        return
    
    cursor.execute(
        "UPDATE orders SET status = %s, courier_id = %s, accepted_at = %s, detailed_status = %s WHERE id = %s",
        ('accepted', telegram_id, datetime.now(), 'courier_on_way', order_id)
    )
    conn.commit()
    cursor.close()
    
    text = f"✅ Заказ #{order_id} принят!\n\nСтатус: 🚗 Курьер едет"
    keyboard = {
        'inline_keyboard': [
            [{'text': '🚚 Текущие заказы', 'callback_data': 'courier_current'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    send_message(chat_id, text, keyboard)

def handle_courier_current_orders(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, address, description, price, detailed_status FROM orders WHERE courier_id = %s AND status = %s ORDER BY accepted_at DESC",
        (telegram_id, 'accepted')
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "🚚 <b>Текущие заказы</b>\n\nНет текущих заказов"
        keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
        send_message(chat_id, text, keyboard)
        return
    
    text = "🚚 <b>Текущие заказы</b>\n\n"
    keyboard_buttons = []
    
    for order in orders:
        order_id, address, description, price, detailed_status = order
        status_text = ORDER_STATUSES.get(detailed_status, detailed_status)
        text += f"🆔 Заказ #{order_id}\n"
        text += f"📍 {address}\n"
        text += f"📝 {description}\n"
        text += f"💰 {price} ₽\n"
        text += f"Статус: {status_text}\n\n"
        
        if detailed_status == 'courier_on_way':
            keyboard_buttons.append([{'text': f'🛠 Начать работу #{order_id}', 'callback_data': f'start_work_{order_id}'}])
        elif detailed_status == 'courier_working':
            keyboard_buttons.append([{'text': f'✅ Завершить #{order_id}', 'callback_data': f'complete_order_{order_id}'}])
    
    keyboard_buttons.append([{'text': '⬅️ Назад', 'callback_data': 'start'}])
    send_message(chat_id, text, {'inline_keyboard': keyboard_buttons})

def handle_start_work(chat_id: int, telegram_id: int, order_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE orders SET detailed_status = %s WHERE id = %s AND courier_id = %s",
        ('courier_working', order_id, telegram_id)
    )
    conn.commit()
    cursor.close()
    
    text = f"🛠 Работа над заказом #{order_id} начата!"
    keyboard = {
        'inline_keyboard': [
            [{'text': '✅ Завершить заказ', 'callback_data': f'complete_order_{order_id}'}],
            [{'text': '⬅️ Назад', 'callback_data': 'courier_current'}]
        ]
    }
    send_message(chat_id, text, keyboard)

def handle_complete_order(chat_id: int, telegram_id: int, order_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute("SELECT courier_id, price FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    
    if not order or order[0] != telegram_id:
        send_message(chat_id, "❌ Заказ не найден")
        cursor.close()
        return
    
    price = order[1]
    
    cursor.execute(
        "UPDATE orders SET status = %s, completed_at = %s, detailed_status = %s WHERE id = %s",
        ('completed', datetime.now(), 'completed', order_id)
    )
    
    cursor.execute(
        "INSERT INTO courier_stats (courier_id, total_orders, total_earnings) "
        "VALUES (%s, 1, %s) "
        "ON CONFLICT (courier_id) DO UPDATE SET "
        "total_orders = courier_stats.total_orders + 1, "
        "total_earnings = courier_stats.total_earnings + %s, "
        "updated_at = %s",
        (telegram_id, price, price, datetime.now())
    )
    
    conn.commit()
    cursor.close()
    
    text = f"✅ Заказ #{order_id} завершён!\n\n💰 Заработано: {price} ₽"
    keyboard = {
        'inline_keyboard': [
            [{'text': '💰 Статистика', 'callback_data': 'courier_stats'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    send_message(chat_id, text, keyboard)

def handle_courier_stats(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT total_orders, total_earnings FROM courier_stats WHERE courier_id = %s",
        (telegram_id,)
    )
    stats = cursor.fetchone()
    
    cursor.execute("SELECT AVG(rating) FROM ratings WHERE courier_id = %s", (telegram_id,))
    avg_rating = cursor.fetchone()
    cursor.close()
    
    if not stats:
        total_orders = 0
        total_earnings = 0
    else:
        total_orders = stats[0]
        total_earnings = stats[1]
    
    rating = round(avg_rating[0], 1) if avg_rating[0] else 0.0
    avg_check = round(total_earnings / total_orders) if total_orders > 0 else 0
    
    text = (
        "💰 <b>Финансовая статистика</b>\n\n"
        f"📦 Всего заказов: {total_orders}\n"
        f"💵 Заработано: {total_earnings} ₽\n"
        f"💳 Средний чек: {avg_check} ₽\n"
        f"⭐ Средний рейтинг: {rating}\n"
    )
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '💵 Вывод средств', 'callback_data': 'courier_withdraw'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    send_message(chat_id, text, keyboard)

def handle_reviews(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT r.rating, r.review, u.first_name FROM ratings r "
        "JOIN users u ON r.courier_id = u.telegram_id "
        "ORDER BY r.created_at DESC LIMIT 10"
    )
    reviews = cursor.fetchall()
    cursor.close()
    
    if not reviews:
        text = "⭐ <b>Отзывы клиентов</b>\n\nОтзывов пока нет"
    else:
        text = "⭐ <b>Отзывы клиентов</b>\n\n"
        for review in reviews:
            rating, review_text, courier_name = review
            stars = '⭐' * rating
            text += f"{stars} - {courier_name}\n"
            if review_text:
                text += f"💬 {review_text}\n"
            text += "\n"
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
    send_message(chat_id, text, keyboard)

def handle_client_new_order(chat_id: int) -> None:
    text = (
        "➕ <b>Создание нового заказа</b>\n\n"
        "Отправьте информацию о заказе в формате:\n\n"
        "<code>Адрес\n"
        "Описание\n"
        "Цена</code>\n\n"
        "<b>Пример:</b>\n"
        "ул. Ленина, д. 45, кв. 12\n"
        "Вывоз строительного мусора (3 мешка)\n"
        "1500"
    )
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Отмена', 'callback_data': 'client_menu'}]]}
    send_message(chat_id, text, keyboard)

def handle_client_active_orders(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT o.id, o.address, o.description, o.price, o.detailed_status, u.first_name "
        "FROM orders o "
        "LEFT JOIN users u ON o.courier_id = u.telegram_id "
        "WHERE o.client_id = %s AND o.status IN (%s, %s) "
        "ORDER BY o.created_at DESC",
        (telegram_id, 'pending', 'accepted')
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "📦 <b>Активные заказы</b>\n\nНет активных заказов"
    else:
        text = "📦 <b>Активные заказы</b>\n\n"
        for order in orders:
            order_id, address, description, price, detailed_status, courier_name = order
            status_text = ORDER_STATUSES.get(detailed_status, detailed_status)
            text += f"🆔 Заказ #{order_id}\n"
            text += f"📍 {address}\n"
            text += f"📝 {description}\n"
            text += f"💰 {price} ₽\n"
            text += f"Статус: {status_text}\n"
            if courier_name:
                text += f"Курьер: {courier_name}\n"
            text += "\n"
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'client_menu'}]]}
    send_message(chat_id, text, keyboard)

def handle_operator_active_orders(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT o.id, o.address, o.description, o.price, o.detailed_status, "
        "u1.first_name as client_name, u2.first_name as courier_name "
        "FROM orders o "
        "JOIN users u1 ON o.client_id = u1.telegram_id "
        "LEFT JOIN users u2 ON o.courier_id = u2.telegram_id "
        "WHERE o.status IN (%s, %s) "
        "ORDER BY o.created_at DESC LIMIT 20",
        ('pending', 'accepted')
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "📞 <b>Активные заказы</b>\n\nНет активных заказов"
        keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
    else:
        text = "📞 <b>Активные заказы</b>\n\n"
        keyboard_buttons = []
        
        for order in orders:
            order_id, address, description, price, detailed_status, client_name, courier_name = order
            status_text = ORDER_STATUSES.get(detailed_status, detailed_status)
            text += f"🆔 #{order_id} | {status_text}\n"
            text += f"Клиент: {client_name}\n"
            if courier_name:
                text += f"Курьер: {courier_name}\n"
            text += f"💰 {price} ₽\n\n"
            
            keyboard_buttons.append([
                {'text': f'💬 Чат #{order_id}', 'callback_data': f'operator_chat_{order_id}'},
                {'text': f'📝 Статус #{order_id}', 'callback_data': f'operator_status_{order_id}'}
            ])
        
        keyboard_buttons.append([{'text': '⬅️ Назад', 'callback_data': 'start'}])
        keyboard = {'inline_keyboard': keyboard_buttons}
    
    send_message(chat_id, text, keyboard)

def handle_operator_change_status(chat_id: int, order_id: int, conn) -> None:
    text = f"📝 Изменить статус заказа #{order_id}"
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '🔍 В поиске курьера', 'callback_data': f'set_status_{order_id}_searching_courier'}],
            [{'text': '🚗 Курьер едет', 'callback_data': f'set_status_{order_id}_courier_on_way'}],
            [{'text': '🛠 Курьер выполняет заказ', 'callback_data': f'set_status_{order_id}_courier_working'}],
            [{'text': '✅ Завершён', 'callback_data': f'set_status_{order_id}_completed'}],
            [{'text': '❌ Отменён', 'callback_data': f'set_status_{order_id}_cancelled'}],
            [{'text': '⬅️ Назад', 'callback_data': 'operator_active_orders'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)

def handle_set_order_status(chat_id: int, order_id: int, new_status: str, conn) -> None:
    cursor = conn.cursor()
    
    status_mapping = {
        'completed': 'completed',
        'cancelled': 'cancelled',
        'searching_courier': 'pending',
        'courier_on_way': 'accepted',
        'courier_working': 'accepted'
    }
    
    main_status = status_mapping.get(new_status, 'pending')
    
    cursor.execute(
        "UPDATE orders SET detailed_status = %s, status = %s WHERE id = %s",
        (new_status, main_status, order_id)
    )
    conn.commit()
    cursor.close()
    
    status_text = ORDER_STATUSES.get(new_status, new_status)
    text = f"✅ Статус заказа #{order_id} изменён на: {status_text}"
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '📞 Активные заказы', 'callback_data': 'operator_active_orders'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)

def handle_admin_panel(chat_id: int, conn) -> None:
    text = "👑 <b>Админ-панель</b>\n\nВыберите действие:"
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '👔 Заявки курьеров', 'callback_data': 'admin_courier_applications'}],
            [{'text': '👥 Добавить оператора', 'callback_data': 'admin_add_operator'}],
            [{'text': '📊 Статистика сервиса', 'callback_data': 'admin_stats'}],
            [{'text': '📦 Все заказы', 'callback_data': 'admin_all_orders'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)

def handle_admin_add_operator(chat_id: int) -> None:
    text = (
        "👥 <b>Добавить оператора</b>\n\n"
        "Отправьте Telegram ID пользователя, которого хотите назначить оператором.\n\n"
        "Формат: <code>operator_add ID</code>\n\n"
        "<b>Пример:</b>\n"
        "<code>operator_add 123456789</code>"
    )
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'admin_panel'}]]}
    send_message(chat_id, text, keyboard)

def handle_admin_stats(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = %s", ('client',))
    total_clients = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = %s", ('courier',))
    total_couriers = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM operator_users")
    total_operators = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = %s", ('completed',))
    completed_orders = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(price) FROM orders WHERE status = %s", ('completed',))
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.execute(
        "SELECT AVG(price) FROM orders WHERE status = %s",
        ('completed',)
    )
    avg_order = cursor.fetchone()[0] or 0
    
    cursor.close()
    
    text = (
        "📊 <b>Статистика сервиса</b>\n\n"
        f"👥 Пользователей:\n"
        f"  • Клиентов: {total_clients}\n"
        f"  • Курьеров: {total_couriers}\n"
        f"  • Операторов: {total_operators}\n\n"
        f"📦 Заказов:\n"
        f"  • Всего: {total_orders}\n"
        f"  • Завершено: {completed_orders}\n\n"
        f"💰 Финансы:\n"
        f"  • Общая выручка: {int(total_revenue)} ₽\n"
        f"  • Средний чек: {int(avg_order)} ₽"
    )
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'admin_panel'}]]}
    send_message(chat_id, text, keyboard)

def handle_add_operator(chat_id: int, admin_id: int, operator_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute("SELECT telegram_id FROM users WHERE telegram_id = %s", (operator_id,))
    user_exists = cursor.fetchone()
    
    if not user_exists:
        cursor.close()
        send_message(chat_id, "❌ Пользователь не найден. Попросите его сначала запустить бота через /start")
        return
    
    cursor.execute(
        "INSERT INTO operator_users (telegram_id, added_by) VALUES (%s, %s) ON CONFLICT (telegram_id) DO NOTHING",
        (operator_id, admin_id)
    )
    conn.commit()
    cursor.close()
    
    send_message(operator_id, "✅ Вы назначены оператором! Используйте /start для доступа к панели оператора.")
    send_message(chat_id, f"✅ Пользователь {operator_id} назначен оператором")

def handle_client_history(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT o.id, o.address, o.description, o.price, o.detailed_status, u.first_name "
        "FROM orders o "
        "LEFT JOIN users u ON o.courier_id = u.telegram_id "
        "WHERE o.client_id = %s AND o.status = %s "
        "ORDER BY o.completed_at DESC LIMIT 10",
        (telegram_id, 'completed')
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "📊 <b>История заказов</b>\n\nНет завершённых заказов"
    else:
        text = "📊 <b>История заказов</b>\n\n"
        for order in orders:
            order_id, address, description, price, detailed_status, courier_name = order
            text += f"🆔 Заказ #{order_id}\n"
            text += f"📍 {address}\n"
            text += f"📝 {description}\n"
            text += f"💰 {price} ₽\n"
            if courier_name:
                text += f"Курьер: {courier_name}\n"
            text += "\n"
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'client_menu'}]]}
    send_message(chat_id, text, keyboard)

def handle_courier_history(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, address, description, price FROM orders "
        "WHERE courier_id = %s AND status = %s "
        "ORDER BY completed_at DESC LIMIT 10",
        (telegram_id, 'completed')
    )
    orders = cursor.fetchall()
    cursor.close()
    
    if not orders:
        text = "📊 <b>История заказов</b>\n\nНет завершённых заказов"
    else:
        text = "📊 <b>История заказов</b>\n\n"
        for order in orders:
            order_id, address, description, price = order
            text += f"🆔 Заказ #{order_id}\n"
            text += f"📍 {address}\n"
            text += f"📝 {description}\n"
            text += f"💰 {price} ₽\n\n"
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
    send_message(chat_id, text, keyboard)

def handle_client_payment(chat_id: int) -> None:
    text = (
        "💳 <b>Способ оплаты</b>\n\n"
        "Доступные способы оплаты:\n"
        "• 💳 Банковская карта\n"
        "• 💵 Наличные курьеру\n"
        "• 📱 СБП\n\n"
        "Способ оплаты выбирается при согласовании заказа с курьером."
    )
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'client_menu'}]]}
    send_message(chat_id, text, keyboard)

def handle_client_subscription(chat_id: int) -> None:
    text = (
        "⭐ <b>Подписка</b>\n\n"
        "Текущий план: <b>Базовый</b>\n\n"
        "Преимущества:\n"
        "• ✅ Без комиссии за первые 3 заказа\n"
        "• ✅ Приоритетная поддержка\n"
        "• ✅ Скидки на услуги\n\n"
        "Для перехода на премиум-план свяжитесь с поддержкой."
    )
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'client_menu'}]]}
    send_message(chat_id, text, keyboard)

def handle_courier_withdraw(chat_id: int, telegram_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT total_earnings FROM courier_stats WHERE courier_id = %s",
        (telegram_id,)
    )
    stats = cursor.fetchone()
    cursor.close()
    
    balance = stats[0] if stats else 0
    
    text = (
        "💵 <b>Вывод средств</b>\n\n"
        f"Доступно для вывода: <b>{balance} ₽</b>\n\n"
        "Для вывода средств свяжитесь с администратором через кнопку ниже."
    )
    keyboard = {
        'inline_keyboard': [
            [{'text': '💬 Связаться с администратором', 'url': 'https://t.me/support'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
    send_message(chat_id, text, keyboard)

def handle_operator_stats(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = %s", ('pending',))
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = %s", ('accepted',))
    active = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status = %s AND DATE(completed_at) = CURRENT_DATE",
        ('completed',)
    )
    today_completed = cursor.fetchone()[0]
    
    cursor.close()
    
    text = (
        "📊 <b>Статистика оператора</b>\n\n"
        f"🔍 Ожидают курьера: {pending}\n"
        f"🚚 В работе: {active}\n"
        f"✅ Завершено сегодня: {today_completed}"
    )
    
    keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'start'}]]}
    send_message(chat_id, text, keyboard)

def handle_admin_courier_applications(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT ca.id, ca.telegram_id, u.first_name, u.username "
        "FROM courier_applications ca "
        "JOIN users u ON ca.telegram_id = u.telegram_id "
        "WHERE ca.status = %s "
        "ORDER BY ca.created_at DESC LIMIT 10",
        ('pending',)
    )
    applications = cursor.fetchall()
    cursor.close()
    
    if not applications:
        text = "👔 <b>Заявки курьеров</b>\n\nНет новых заявок"
        keyboard = {'inline_keyboard': [[{'text': '⬅️ Назад', 'callback_data': 'admin_panel'}]]}
    else:
        text = "👔 <b>Заявки курьеров</b>\n\n"
        keyboard_buttons = []
        
        for app in applications:
            app_id, telegram_id, first_name, username = app
            text += f"👤 {first_name} (@{username or 'нет username'})\n"
            text += f"ID: {telegram_id}\n\n"
            
            keyboard_buttons.append([
                {'text': f'✅ Одобрить {first_name}', 'callback_data': f'approve_courier_{telegram_id}'},
                {'text': f'❌ Отклонить', 'callback_data': f'reject_courier_{telegram_id}'}
            ])
        
        keyboard_buttons.append([{'text': '⬅️ Назад', 'callback_data': 'admin_panel'}])
        keyboard = {'inline_keyboard': keyboard_buttons}
    
    send_message(chat_id, text, keyboard)

def handle_approve_courier(chat_id: int, admin_id: int, courier_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE users SET role = %s WHERE telegram_id = %s",
        ('courier', courier_id)
    )
    
    cursor.execute(
        "UPDATE courier_applications SET status = %s, reviewed_by = %s, reviewed_at = %s WHERE telegram_id = %s AND status = %s",
        ('approved', admin_id, datetime.now(), courier_id, 'pending')
    )
    
    conn.commit()
    cursor.close()
    
    send_message(courier_id, "✅ Поздравляем! Ваша заявка на роль курьера одобрена.\n\nИспользуйте /start для доступа к меню курьера.")
    send_message(chat_id, "✅ Курьер одобрен")

def handle_reject_courier(chat_id: int, admin_id: int, courier_id: int, conn) -> None:
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE courier_applications SET status = %s, reviewed_by = %s, reviewed_at = %s WHERE telegram_id = %s AND status = %s",
        ('rejected', admin_id, datetime.now(), courier_id, 'pending')
    )
    
    conn.commit()
    cursor.close()
    
    send_message(courier_id, "❌ К сожалению, ваша заявка на роль курьера отклонена.")
    send_message(chat_id, "❌ Заявка отклонена")

def handle_admin_all_orders(chat_id: int, conn) -> None:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status = %s",
        ('pending',)
    )
    pending = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status = %s",
        ('accepted',)
    )
    active = cursor.fetchone()[0]
    
    cursor.execute(
        "SELECT COUNT(*) FROM orders WHERE status = %s",
        ('completed',)
    )
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT SUM(price) FROM orders WHERE status = %s", ('completed',))
    total_revenue = cursor.fetchone()[0] or 0
    
    cursor.close()
    
    text = (
        "📦 <b>Все заказы</b>\n\n"
        f"🔍 В ожидании: {pending}\n"
        f"🚚 В работе: {active}\n"
        f"✅ Завершено: {completed}\n\n"
        f"💰 Общая выручка: {total_revenue} ₽"
    )
    
    keyboard = {
        'inline_keyboard': [
            [{'text': '⬅️ Назад', 'callback_data': 'admin_panel'}]
        ]
    }
    
    send_message(chat_id, text, keyboard)

def handle_callback_query(callback_query: Dict, conn) -> None:
    chat_id = callback_query['message']['chat']['id']
    telegram_id = callback_query['from']['id']
    username = callback_query['from'].get('username', '')
    first_name = callback_query['from'].get('first_name', '')
    data = callback_query['data']
    
    role = check_user_role(telegram_id, conn)
    
    if data == 'start':
        handle_start(chat_id, telegram_id, username, first_name, conn)
    elif data == 'apply_courier':
        handle_apply_courier(chat_id, telegram_id, conn)
    elif data == 'client_menu':
        handle_client_menu(chat_id)
    elif data == 'courier_available':
        handle_courier_available_orders(chat_id, telegram_id, conn)
    elif data == 'courier_current':
        handle_courier_current_orders(chat_id, telegram_id, conn)
    elif data == 'courier_stats':
        handle_courier_stats(chat_id, telegram_id, conn)
    elif data == 'reviews':
        handle_reviews(chat_id, conn)
    elif data == 'client_new_order':
        handle_client_new_order(chat_id)
    elif data == 'client_active':
        handle_client_active_orders(chat_id, telegram_id, conn)
    elif data == 'operator_active_orders':
        if role in ['operator', 'admin']:
            handle_operator_active_orders(chat_id, conn)
    elif data == 'admin_panel':
        if role == 'admin':
            handle_admin_panel(chat_id, conn)
    elif data == 'admin_courier_applications':
        if role == 'admin':
            handle_admin_courier_applications(chat_id, conn)
    elif data == 'admin_all_orders':
        if role == 'admin':
            handle_admin_all_orders(chat_id, conn)
    elif data == 'admin_add_operator':
        if role == 'admin':
            handle_admin_add_operator(chat_id)
    elif data == 'admin_stats':
        if role == 'admin':
            handle_admin_stats(chat_id, conn)
    elif data == 'client_history':
        handle_client_history(chat_id, telegram_id, conn)
    elif data == 'courier_history':
        handle_courier_history(chat_id, telegram_id, conn)
    elif data == 'client_payment':
        handle_client_payment(chat_id)
    elif data == 'client_subscription':
        handle_client_subscription(chat_id)
    elif data == 'courier_withdraw':
        handle_courier_withdraw(chat_id, telegram_id, conn)
    elif data == 'operator_stats':
        if role in ['operator', 'admin']:
            handle_operator_stats(chat_id, conn)
    elif data == 'operator_chats':
        if role in ['operator', 'admin']:
            send_message(chat_id, "💬 Функция чата в разработке")
    elif data.startswith('accept_order_'):
        order_id = int(data.split('_')[2])
        handle_accept_order(chat_id, telegram_id, order_id, conn)
    elif data.startswith('start_work_'):
        order_id = int(data.split('_')[2])
        handle_start_work(chat_id, telegram_id, order_id, conn)
    elif data.startswith('complete_order_'):
        order_id = int(data.split('_')[2])
        handle_complete_order(chat_id, telegram_id, order_id, conn)
    elif data.startswith('operator_status_'):
        if role in ['operator', 'admin']:
            order_id = int(data.split('_')[2])
            handle_operator_change_status(chat_id, order_id, conn)
    elif data.startswith('set_status_'):
        if role in ['operator', 'admin']:
            parts = data.split('_')
            order_id = int(parts[2])
            new_status = '_'.join(parts[3:])
            handle_set_order_status(chat_id, order_id, new_status, conn)
    elif data.startswith('approve_courier_'):
        if role == 'admin':
            courier_id = int(data.split('_')[2])
            handle_approve_courier(chat_id, telegram_id, courier_id, conn)
    elif data.startswith('reject_courier_'):
        if role == 'admin':
            courier_id = int(data.split('_')[2])
            handle_reject_courier(chat_id, telegram_id, courier_id, conn)

def handle_message(message: Dict, conn) -> None:
    chat_id = message['chat']['id']
    telegram_id = message['from']['id']
    username = message['from'].get('username', '')
    first_name = message['from'].get('first_name', '')
    text = message.get('text', '')
    
    if text == '/start':
        handle_start(chat_id, telegram_id, username, first_name, conn)
        return
    
    if text.startswith('operator_add '):
        role = check_user_role(telegram_id, conn)
        if role == 'admin':
            try:
                operator_id = int(text.split(' ')[1])
                handle_add_operator(chat_id, telegram_id, operator_id, conn)
            except (ValueError, IndexError):
                send_message(chat_id, "❌ Неверный формат. Используйте: operator_add ID")
        return
    
    lines = text.strip().split('\n')
    if len(lines) == 3:
        address = lines[0].strip()
        description = lines[1].strip()
        try:
            price = int(lines[2].strip())
            
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO orders (client_id, address, description, price, status, detailed_status) "
                "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (telegram_id, address, description, price, 'pending', 'searching_courier')
            )
            order_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            
            text = (
                f"✅ Заказ #{order_id} создан!\n\n"
                f"📍 {address}\n"
                f"📝 {description}\n"
                f"💰 {price} ₽\n\n"
                "🔍 Статус: В поиске курьера"
            )
            keyboard = {
                'inline_keyboard': [
                    [{'text': '📦 Мои заказы', 'callback_data': 'client_active'}],
                    [{'text': '⬅️ Назад', 'callback_data': 'client_menu'}]
                ]
            }
            send_message(chat_id, text, keyboard)
            return
        except ValueError:
            pass
    
    send_message(chat_id, "Используйте /start для начала работы")

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method == 'POST':
        body = json.loads(event.get('body', '{}'))
        
        conn = get_db_connection()
        
        if 'message' in body:
            handle_message(body['message'], conn)
        elif 'callback_query' in body:
            handle_callback_query(body['callback_query'], conn)
        
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
    
    return {
        'statusCode': 405,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'error': 'Method not allowed'}),
        'isBase64Encoded': False
    }