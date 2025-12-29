import json
import os
import urllib.request
import urllib.parse

def handler(event: dict, context) -> dict:
    """
    Диагностика Telegram бота - проверка webhook и отправка тестового сообщения.
    """
    method = event.get('httpMethod', 'GET')
    
    if method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': '',
            'isBase64Encoded': False
        }
    
    try:
        token = os.environ['TELEGRAM_BOT_TOKEN']
        
        query_params = event.get('queryStringParameters', {}) or {}
        action = query_params.get('action', 'webhook_info')
        
        if action == 'webhook_info':
            api_url = f"https://api.telegram.org/bot{token}/getWebhookInfo"
            req = urllib.request.Request(api_url)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result, ensure_ascii=False, indent=2),
                'isBase64Encoded': False
            }
        
        elif action == 'set_webhook':
            webhook_url = 'https://functions.poehali.dev/63e313ed-c4e7-40e4-baa0-e78c7b2a8391'
            api_url = f"https://api.telegram.org/bot{token}/setWebhook"
            
            data = urllib.parse.urlencode({'url': webhook_url}).encode('utf-8')
            req = urllib.request.Request(api_url, data=data)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result, ensure_ascii=False, indent=2),
                'isBase64Encoded': False
            }
        
        elif action == 'get_me':
            api_url = f"https://api.telegram.org/bot{token}/getMe"
            req = urllib.request.Request(api_url)
            response = urllib.request.urlopen(req)
            result = json.loads(response.read().decode('utf-8'))
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps(result, ensure_ascii=False, indent=2),
                'isBase64Encoded': False
            }
        
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'error': 'Invalid action',
                    'available_actions': ['webhook_info', 'set_webhook', 'get_me']
                }),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }),
            'isBase64Encoded': False
        }