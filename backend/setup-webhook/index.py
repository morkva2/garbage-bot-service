import json
import os
import urllib.request
import urllib.parse

def handler(event: dict, context) -> dict:
    """
    Настройка webhook для Telegram бота.
    Устанавливает URL для получения обновлений от Telegram.
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
        webhook_url = 'https://functions.poehali.dev/63e313ed-c4e7-40e4-baa0-e78c7b2a8391'
        
        api_url = f"https://api.telegram.org/bot{token}/setWebhook"
        data = urllib.parse.urlencode({'url': webhook_url}).encode('utf-8')
        
        req = urllib.request.Request(api_url, data=data)
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        
        if result.get('ok'):
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': True,
                    'message': 'Webhook установлен успешно',
                    'webhook_url': webhook_url
                }),
                'isBase64Encoded': False
            }
        else:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({
                    'success': False,
                    'error': result.get('description', 'Unknown error')
                }),
                'isBase64Encoded': False
            }
            
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': str(e)
            }),
            'isBase64Encoded': False
        }
