import json
import os
import psycopg2
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

def handler(event: dict, context) -> dict:
    """
    Telegram бот для службы вывоза мусора.
    Управляет заказами между клиентами, курьерами, операторами и администраторами.
    """
    method = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body = json.loads(event.get('body', '{}'))
        
        if not body.get('message') and not body.get('callback_query'):
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'ok': True}),
                'isBase64Encoded': False
            }
        
        bot = TelegramBot()
        bot.process_update(body)
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error processing update: {e}")
        print(f"Full traceback: {error_details}")
        print(f"Update body: {json.dumps(body, ensure_ascii=False)}")
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'ok': True}),
            'isBase64Encoded': False
        }


class Database:
    def __init__(self):
        self.dsn = os.environ['DATABASE_URL']
        self.schema = 't_p39739760_garbage_bot_service'
    
    def get_connection(self):
        conn = psycopg2.connect(self.dsn)
        return conn
    
    def execute(self, query: str, params: tuple = None, fetch: bool = False):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {self.schema}")
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
        finally:
            conn.close()
    
    def fetchone(self, query: str, params: tuple = None):
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(f"SET search_path TO {self.schema}")
                cur.execute(query, params)
                return cur.fetchone()
        finally:
            conn.close()


class TelegramBot:
    def __init__(self):
        self.token = os.environ['TELEGRAM_BOT_TOKEN']
        self.db = Database()
        self.api_url = f"https://api.telegram.org/bot{self.token}"
    
    def process_update(self, update: dict):
        if 'message' in update:
            self.handle_message(update['message'])
        elif 'callback_query' in update:
            self.handle_callback(update['callback_query'])
    
    def handle_message(self, message: dict):
        chat_id = message['chat']['id']
        user = message.get('from', {})
        text = message.get('text', '')
        
        telegram_id = user.get('id')
        username = user.get('username', '')
        first_name = user.get('first_name', '')
        
        db_user = self.get_or_create_user(telegram_id, username, first_name)
        
        if db_user and db_user[6]:  # is_frozen
            self.send_message(chat_id, "❄️ Ваш аккаунт заморожен. Обратитесь к администратору.")
            return
        
        if text == '/start':
            self.show_main_menu(chat_id, db_user[4])  # role
        elif text == '/menu':
            self.show_main_menu(chat_id, db_user[4])
        else:
            self.handle_text_input(chat_id, telegram_id, text, db_user[4])
    
    def handle_callback(self, callback: dict):
        chat_id = callback['message']['chat']['id']
        message_id = callback['message']['message_id']
        data = callback['data']
        user_id = callback['from']['id']
        
        self.answer_callback_query(callback['id'])
        
        user = self.get_user(user_id)
        if not user:
            return
        
        role = user[4]
        
        if data == 'main_menu':
            self.delete_message(chat_id, message_id)
            self.show_main_menu(chat_id, role)
        elif data == 'create_order':
            self.start_order_creation(chat_id, user_id)
        elif data == 'my_orders':
            self.show_my_orders(chat_id, user_id, role)
        elif data == 'buy_subscription':
            self.show_subscription_options(chat_id, user_id)
        elif data.startswith('sub_'):
            self.process_subscription_purchase(chat_id, user_id, data)
        elif data.startswith('order_'):
            self.show_order_details(chat_id, user_id, data, role)
        elif data == 'available_orders' and role == 'courier':
            self.show_available_orders(chat_id, user_id)
        elif data.startswith('accept_order_') and role == 'courier':
            order_id = int(data.replace('accept_order_', ''))
            self.accept_order(chat_id, user_id, order_id)
        elif data == 'become_courier':
            self.start_courier_application(chat_id, user_id)
        elif data == 'courier_stats' and role == 'courier':
            self.show_courier_stats(chat_id, user_id)
        elif data == 'admin_panel' and role == 'admin':
            self.show_admin_panel(chat_id)
        elif data.startswith('admin_'):
            self.handle_admin_action(chat_id, user_id, data)
    
    def get_or_create_user(self, telegram_id: int, username: str, first_name: str):
        user = self.get_user(telegram_id)
        if not user:
            self.db.execute(
                "INSERT INTO users (telegram_id, username, first_name, role, is_frozen) VALUES (%s, %s, %s, %s, %s)",
                (telegram_id, username, first_name, 'client', False)
            )
            user = self.get_user(telegram_id)
        return user
    
    def get_user(self, telegram_id: int):
        return self.db.fetchone("SELECT * FROM users WHERE telegram_id = %s", (telegram_id,))
    
    def show_main_menu(self, chat_id: int, role: str):
        keyboard = []
        
        if role == 'client':
            keyboard = [
                [{'text': '📦 Создать заказ', 'callback_data': 'create_order'}],
                [{'text': '📋 Мои заказы', 'callback_data': 'my_orders'}],
                [{'text': '⭐ Купить подписку', 'callback_data': 'buy_subscription'}],
                [{'text': '🚚 Стать курьером', 'callback_data': 'become_courier'}]
            ]
        elif role == 'courier':
            keyboard = [
                [{'text': '📦 Доступные заказы', 'callback_data': 'available_orders'}],
                [{'text': '📋 Мои заказы', 'callback_data': 'my_orders'}],
                [{'text': '📊 Статистика', 'callback_data': 'courier_stats'}]
            ]
        elif role == 'admin':
            keyboard = [
                [{'text': '👨‍💼 Панель администратора', 'callback_data': 'admin_panel'}],
                [{'text': '📋 Все заказы', 'callback_data': 'my_orders'}]
            ]
        
        self.send_message(
            chat_id,
            f"🏠 Главное меню\nВаша роль: {self.get_role_name(role)}",
            {'inline_keyboard': keyboard}
        )
    
    def get_role_name(self, role: str) -> str:
        roles = {
            'client': '👤 Клиент',
            'courier': '🚚 Курьер',
            'operator': '👨‍💼 Оператор',
            'admin': '👑 Администратор'
        }
        return roles.get(role, role)
    
    def start_order_creation(self, chat_id: int, user_id: int):
        self.send_message(
            chat_id,
            "📦 Создание заказа\n\nУкажите количество пакетов мусора (35л каждый):",
            {'inline_keyboard': [
                [{'text': '1 пакет', 'callback_data': 'bags_1'}, {'text': '2 пакета', 'callback_data': 'bags_2'}],
                [{'text': '3 пакета', 'callback_data': 'bags_3'}, {'text': '4 пакета', 'callback_data': 'bags_4'}],
                [{'text': '❌ Отмена', 'callback_data': 'main_menu'}]
            ]}
        )
    
    def show_my_orders(self, chat_id: int, user_id: int, role: str):
        if role == 'courier':
            orders = self.db.execute(
                "SELECT id, client_id, address, bag_count, price, detailed_status FROM orders WHERE courier_id = %s ORDER BY created_at DESC LIMIT 10",
                (user_id,), fetch=True
            )
        else:
            orders = self.db.execute(
                "SELECT id, client_id, address, bag_count, price, detailed_status FROM orders WHERE client_id = %s ORDER BY created_at DESC LIMIT 10",
                (user_id,), fetch=True
            )
        
        if not orders:
            self.send_message(chat_id, "📋 У вас пока нет заказов", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
            return
        
        text = "📋 Ваши заказы:\n\n"
        keyboard = []
        
        for order in orders:
            status_emoji = self.get_status_emoji(order[5])
            text += f"{status_emoji} Заказ #{order[0]} - {order[3]} пак. - {order[4]}₽\n"
            keyboard.append([{'text': f"Заказ #{order[0]}", 'callback_data': f'order_{order[0]}'}])
        
        keyboard.append([{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}])
        self.send_message(chat_id, text, {'inline_keyboard': keyboard})
    
    def get_status_emoji(self, status: str) -> str:
        statuses = {
            'waiting_payment': '💳',
            'searching_courier': '🔍',
            'courier_on_way': '🚗',
            'courier_working': '🚚',
            'completed': '✅',
            'cancelled': '❌'
        }
        return statuses.get(status, '📦')
    
    def show_subscription_options(self, chat_id: int, user_id: int):
        daily_price = self.get_setting('subscription_daily_price', '2499')
        alternate_price = self.get_setting('subscription_alternate_price', '1399')
        
        self.send_message(
            chat_id,
            f"⭐ Подписки на вывоз мусора\n\n"
            f"📅 Каждый день - {daily_price}₽/месяц\n"
            f"Вывоз мусора каждый день (до 2 пакетов в день бесплатно)\n\n"
            f"📆 Через день - {alternate_price}₽/месяц\n"
            f"Вывоз мусора через день (до 2 пакетов в день бесплатно)",
            {'inline_keyboard': [
                [{'text': f'📅 Каждый день - {daily_price}₽', 'callback_data': 'sub_daily'}],
                [{'text': f'📆 Через день - {alternate_price}₽', 'callback_data': 'sub_alternate'}],
                [{'text': '❌ Отмена', 'callback_data': 'main_menu'}]
            ]}
        )
    
    def process_subscription_purchase(self, chat_id: int, user_id: int, sub_type: str):
        self.send_message(chat_id, "💳 Создаю платёж...", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
    
    def show_order_details(self, chat_id: int, user_id: int, data: str, role: str):
        order_id = int(data.replace('order_', ''))
        order = self.db.fetchone(
            "SELECT id, client_id, courier_id, address, bag_count, price, detailed_status, created_at FROM orders WHERE id = %s",
            (order_id,)
        )
        
        if not order:
            self.send_message(chat_id, "❌ Заказ не найден", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
            return
        
        status_emoji = self.get_status_emoji(order[6])
        text = f"{status_emoji} Заказ #{order[0]}\n\n"
        text += f"📍 Адрес: {order[3]}\n"
        text += f"📦 Пакетов: {order[4]}\n"
        text += f"💰 Цена: {order[5]}₽\n"
        text += f"📅 Создан: {order[7].strftime('%d.%m.%Y %H:%M')}\n"
        
        self.send_message(chat_id, text, {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
    
    def show_available_orders(self, chat_id: int, user_id: int):
        orders = self.db.execute(
            "SELECT id, address, bag_count, price FROM orders WHERE detailed_status = 'searching_courier' LIMIT 10",
            fetch=True
        )
        
        if not orders:
            self.send_message(chat_id, "📦 Нет доступных заказов", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
            return
        
        text = "📦 Доступные заказы:\n\n"
        keyboard = []
        
        for order in orders:
            text += f"Заказ #{order[0]}: {order[1]} - {order[2]} пак. - {order[3]}₽\n"
            keyboard.append([{'text': f"Принять #{order[0]}", 'callback_data': f'accept_order_{order[0]}'}])
        
        keyboard.append([{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}])
        self.send_message(chat_id, text, {'inline_keyboard': keyboard})
    
    def accept_order(self, chat_id: int, user_id: int, order_id: int):
        self.db.execute(
            "UPDATE orders SET courier_id = %s, detailed_status = 'courier_on_way', accepted_at = NOW() WHERE id = %s AND detailed_status = 'searching_courier'",
            (user_id, order_id)
        )
        self.send_message(chat_id, f"✅ Вы приняли заказ #{order_id}", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
    
    def start_courier_application(self, chat_id: int, user_id: int):
        self.send_message(
            chat_id,
            "🚚 Заявка на становление курьером\n\nОтправьте ваше ФИО для рассмотрения заявки",
            {'inline_keyboard': [[{'text': '❌ Отмена', 'callback_data': 'main_menu'}]]}
        )
    
    def show_courier_stats(self, chat_id: int, user_id: int):
        stats = self.db.fetchone(
            "SELECT total_orders, total_earnings, average_rating FROM courier_stats WHERE courier_id = %s",
            (user_id,)
        )
        
        if not stats:
            self.send_message(chat_id, "📊 Статистика пока пуста", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
            return
        
        text = f"📊 Ваша статистика\n\n"
        text += f"📦 Выполнено заказов: {stats[0]}\n"
        text += f"💰 Заработано: {stats[1]}₽\n"
        text += f"⭐ Средний рейтинг: {stats[2]:.1f}\n"
        
        self.send_message(chat_id, text, {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
    
    def show_admin_panel(self, chat_id: int):
        self.send_message(
            chat_id,
            "👨‍💼 Панель администратора",
            {'inline_keyboard': [
                [{'text': '📊 Статистика сервиса', 'callback_data': 'admin_stats'}],
                [{'text': '🚚 Заявки курьеров', 'callback_data': 'admin_courier_apps'}],
                [{'text': '⚙️ Настройки цен', 'callback_data': 'admin_settings'}],
                [{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]
            ]}
        )
    
    def handle_admin_action(self, chat_id: int, user_id: int, data: str):
        self.send_message(chat_id, "⚙️ Функция в разработке", {'inline_keyboard': [[{'text': '🏠 Главное меню', 'callback_data': 'main_menu'}]]})
    
    def handle_text_input(self, chat_id: int, user_id: int, text: str, role: str):
        pass
    
    def get_setting(self, key: str, default: str = '') -> str:
        result = self.db.fetchone("SELECT value FROM settings WHERE key = %s", (key,))
        return result[0] if result else default
    
    def send_message(self, chat_id: int, text: str, reply_markup: dict = None):
        import urllib.request
        import urllib.parse
        
        data = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }
        
        if reply_markup:
            data['reply_markup'] = json.dumps(reply_markup)
        
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(f"{self.api_url}/sendMessage", data=encoded_data)
        
        try:
            urllib.request.urlopen(req)
        except Exception as e:
            print(f"Error sending message: {e}")
    
    def answer_callback_query(self, callback_id: str):
        import urllib.request
        import urllib.parse
        
        data = {'callback_query_id': callback_id}
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(f"{self.api_url}/answerCallbackQuery", data=encoded_data)
        
        try:
            urllib.request.urlopen(req)
        except:
            pass
    
    def delete_message(self, chat_id: int, message_id: int):
        import urllib.request
        import urllib.parse
        
        data = {'chat_id': chat_id, 'message_id': message_id}
        encoded_data = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(f"{self.api_url}/deleteMessage", data=encoded_data)
        
        try:
            urllib.request.urlopen(req)
        except:
            pass