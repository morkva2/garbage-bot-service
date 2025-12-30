from typing import Dict

def get_main_menu_keyboard(role: str) -> Dict:
    if role == 'admin':
        return {
            'inline_keyboard': [
                [{'text': '👑 Админ-панель', 'callback_data': 'admin_panel'}],
                [{'text': '📞 Режим оператора', 'callback_data': 'switch_to_operator'}],
                [{'text': '👔 Режим курьера', 'callback_data': 'switch_to_courier'}],
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
            [{'text': '💬 Связаться с поддержкой', 'url': 'https://t.me/support'}],
            [{'text': '⭐ Подписка', 'callback_data': 'client_subscription'}],
            [{'text': '⬅️ Назад', 'callback_data': 'start'}]
        ]
    }
