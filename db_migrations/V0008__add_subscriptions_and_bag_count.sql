-- Добавляем таблицу подписок
CREATE TABLE IF NOT EXISTS subscriptions (
    id BIGSERIAL PRIMARY KEY,
    client_id BIGINT NOT NULL REFERENCES users(telegram_id),
    type VARCHAR(50) NOT NULL CHECK (type IN ('daily', 'alternate_day')),
    price INTEGER NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    bags_used_today INTEGER DEFAULT 0,
    last_order_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_subscriptions_client_id ON subscriptions(client_id);
CREATE INDEX idx_subscriptions_is_active ON subscriptions(is_active);

-- Добавляем количество пакетов в заказы
ALTER TABLE orders ADD COLUMN IF NOT EXISTS bag_count INTEGER DEFAULT 1;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS is_subscription_order BOOLEAN DEFAULT false;