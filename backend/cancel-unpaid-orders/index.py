import json
import os
import psycopg2
from typing import Dict, Any
from datetime import datetime, timedelta

SCHEMA = 't_p39739760_garbage_bot_service'

def send_telegram_message(chat_id: int, text: str):
    '''Отправка сообщения через Telegram Bot API'''
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
    
    try:
        requests.post(url, json=data, timeout=5)
    except Exception:
        pass

def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    '''
    Автоматическая отмена неоплаченных заказов старше 30 минут
    Вызывается по расписанию или вручную
    '''
    method: str = event.get('httpMethod', 'POST')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Max-Age': '86400'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
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
        
        cutoff_time = datetime.now() - timedelta(minutes=30)
        
        cursor.execute(
            f"SELECT id, client_id, address, bag_count, price FROM {SCHEMA}.orders "
            "WHERE payment_status = %s AND detailed_status = %s "
            "AND created_at < %s AND status = %s",
            ('pending', 'waiting_payment', cutoff_time, 'pending')
        )
        expired_orders = cursor.fetchall()
        
        cancelled_count = 0
        for order in expired_orders:
            order_id, client_id, address, bag_count, price = order
            
            cursor.execute(
                f"UPDATE {SCHEMA}.orders SET status = %s, detailed_status = %s "
                "WHERE id = %s",
                ('cancelled', 'cancelled', order_id)
            )
            
            message = (
                f"❌ <b>Заказ #{order_id} отменён</b>\n\n"
                f"📍 Адрес: {address}\n"
                f"📦 Мешков: {bag_count}\n"
                f"💰 Сумма: {price} ₽\n\n"
                "Причина: не поступила оплата в течение 30 минут.\n\n"
                "Вы можете создать новый заказ в любое время."
            )
            
            send_telegram_message(client_id, message)
            cancelled_count += 1
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'status': 'success',
                'cancelled_orders': cancelled_count,
                'timestamp': datetime.now().isoformat()
            }),
            'isBase64Encoded': False
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': str(e)}),
            'isBase64Encoded': False
        }
