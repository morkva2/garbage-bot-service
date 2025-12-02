-- Создаём временную таблицу для хранения состояния создания заказа
CREATE TABLE IF NOT EXISTS t_p39739760_garbage_bot_service.order_draft (
    telegram_id BIGINT PRIMARY KEY REFERENCES t_p39739760_garbage_bot_service.users(telegram_id),
    state VARCHAR(50) NOT NULL,
    order_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);