import json
import os
import base64
import psycopg2
from typing import Dict, Any
from decimal import Decimal

SCHEMA = 't_p39739760_garbage_bot_service'

def send_telegram_message(chat_id: int, text: str, reply_markup: str = None):
    import requests
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return
    
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        data['reply_markup'] = reply_markup
    
    try:
        requests.post(url, json=data, timeout=5)
    except Exception:
        pass

def create_payment(body_data: Dict, context: Any) -> Dict[str, Any]:
    import requests
    
    amount = body_data.get('amount')
    description = body_data.get('description', 'Оплата заказа')
    order_id = body_data.get('order_id')
    
    if not amount or not order_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing required fields: amount, order_id'}),
            'isBase64Encoded': False
        }
    
    shop_id = os.environ.get('YOOMONEY_SHOP_ID')
    secret_key = os.environ.get('YOOMONEY_SECRET_KEY')
    
    if not shop_id or not secret_key:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Payment credentials not configured'}),
            'isBase64Encoded': False
        }
    
    auth_string = f"{shop_id}:{secret_key}"
    auth_b64 = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
    
    payment_data = {
        'amount': {
            'value': f"{Decimal(str(amount)):.2f}",
            'currency': 'RUB'
        },
        'capture': True,
        'confirmation': {
            'type': 'redirect',
            'return_url': 'https://t.me/garbagetakeoutbot'
        },
        'description': description,
        'metadata': {
            'order_id': str(order_id)
        }
    }
    
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json',
        'Idempotence-Key': f'order_{order_id}_{context.request_id}'
    }
    
    response = requests.post(
        'https://api.yookassa.ru/v3/payments',
        json=payment_data,
        headers=headers,
        timeout=10
    )
    
    if response.status_code != 200:
        return {
            'statusCode': response.status_code,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'error': 'Payment creation failed',
                'details': response.text
            }),
            'isBase64Encoded': False
        }
    
    payment_response = response.json()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({
            'payment_id': payment_response['id'],
            'payment_url': payment_response['confirmation']['confirmation_url'],
            'status': payment_response['status']
        }),
        'isBase64Encoded': False
    }

def process_webhook(body_data: Dict) -> Dict[str, Any]:
    import requests
    
    event_type = body_data.get('event')
    payment_object = body_data.get('object', {})
    
    if event_type != 'payment.succeeded':
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'status': 'ignored'}),
            'isBase64Encoded': False
        }
    
    payment_id = payment_object.get('id')
    payment_status = payment_object.get('status')
    metadata = payment_object.get('metadata', {})
    order_id = metadata.get('order_id')
    
    if not order_id or not payment_id:
        return {
            'statusCode': 400,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Missing order_id or payment_id'}),
            'isBase64Encoded': False
        }
    
    dsn = os.environ.get('DATABASE_URL')
    if not dsn:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Database not configured'}),
            'isBase64Encoded': False
        }
    
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    
    if order_id.startswith('sub_'):
        subscription_id = int(order_id.replace('sub_', ''))
        
        cursor.execute(
            f"UPDATE {SCHEMA}.subscriptions SET payment_status = %s, paid_at = NOW(), is_active = %s "
            f"WHERE id = %s RETURNING client_id, type, end_date",
            (payment_status, True, subscription_id)
        )
        sub_result = cursor.fetchone()
        
        if sub_result:
            client_id, sub_type, end_date = sub_result
            sub_name = "Ежедневно" if sub_type == 'daily' else "Через день"
            
            message = (
                f"✅ <b>Подписка активирована!</b>\n\n"
                f"⭐ Тип: {sub_name}\n"
                f"📅 Действует до: {end_date.strftime('%d.%m.%Y')}\n\n"
                "Теперь вы можете заказывать вывоз до 2 пакетов без доплаты!"
            )
            
            keyboard = json.dumps({
                'inline_keyboard': [
                    [{'text': '➕ Новый заказ', 'callback_data': 'client_new_order'}],
                    [{'text': '⬅️ Главное меню', 'callback_data': 'client_menu'}]
                ]
            })
            
            send_telegram_message(client_id, message, keyboard)
    else:
        cursor.execute(
            f"UPDATE {SCHEMA}.orders SET payment_status = %s, paid_at = NOW(), detailed_status = %s WHERE id = %s RETURNING client_id, address, bag_count, price",
            (payment_status, 'searching_courier', order_id)
        )
        result = cursor.fetchone()
        
        if result:
            client_id, address, bag_count, price = result
            
            message = f"✅ <b>Оплата прошла успешно!</b>\n\n"
            message += f"📦 Заказ #{order_id}\n"
            message += f"🗑 Мешков: {bag_count}\n"
            message += f"📍 Адрес: {address}\n\n"
            message += "Курьер скоро свяжется с вами для согласования времени вывоза."
            
            keyboard = json.dumps({
                'inline_keyboard': [
                    [{'text': '📦 Мои заказы', 'callback_data': 'client_active_orders'}],
                    [{'text': '⬅️ Главное меню', 'callback_data': 'client_menu'}]
                ]
            })
            
            send_telegram_message(client_id, message, keyboard)
            
            cursor.execute(
                f"SELECT telegram_id FROM {SCHEMA}.users WHERE role = %s",
                ('courier',)
            )
            couriers = cursor.fetchall()
            
            notification_keyboard_json = json.dumps({
                'inline_keyboard': [
                    [{'text': '✅ Принять', 'callback_data': f'accept_order_{order_id}'}]
                ]
            })
            
            for courier in couriers:
                courier_id = courier[0]
                
                bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
                if bot_token:
                    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
                    data = {
                        'chat_id': courier_id,
                        'text': f"🆕 Новый заказ #{order_id}\n📍 {address}\n📦 {bag_count} мешков\n💰 {price} ₽",
                        'reply_markup': notification_keyboard_json
                    }
                    try:
                        requests.post(url, json=data, timeout=5)
                    except Exception:
                        pass
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'status': 'processed'}),
        'isBase64Encoded': False
    }

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Единая функция для работы с ЮMoney
    POST /create - создание платежа (принимает: amount, description, order_id)
    POST /webhook - обработка уведомлений от ЮMoney
    '''
    method: str = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, X-User-Id',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    if method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Method not allowed'}),
            'isBase64Encoded': False
        }
    
    try:
        body_str = event.get('body', '{}')
        if not body_str or body_str.strip() == '':
            body_str = '{}'
        
        body_data = json.loads(body_str)
        
        path = event.get('pathParams', {}).get('proxy', '')
        
        if 'event' in body_data:
            return process_webhook(body_data)
        else:
            return create_payment(body_data, context)
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
