import json
import os
import urllib.request
from typing import Dict, Optional

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"

def _make_request(method: str, payload: Dict) -> None:
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    url = TELEGRAM_API.format(token=token, method=method)
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        if method == 'sendMessage':
            print(f"Error in {method}: {e}")

def send_message(chat_id: int, text: str, reply_markup: Optional[Dict] = None) -> None:
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    _make_request('sendMessage', payload)

def edit_message(chat_id: int, message_id: int, text: str, reply_markup: Optional[Dict] = None) -> None:
    payload = {
        'chat_id': chat_id,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    
    if reply_markup:
        payload['reply_markup'] = reply_markup
    
    _make_request('editMessageText', payload)

def delete_message(chat_id: int, message_id: int) -> None:
    payload = {
        'chat_id': chat_id,
        'message_id': message_id
    }
    
    _make_request('deleteMessage', payload)
