ALTER TABLE orders ADD COLUMN IF NOT EXISTS detailed_status VARCHAR(100) DEFAULT 'searching_courier';

CREATE TABLE IF NOT EXISTS order_chat (
    id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id),
    sender_id BIGINT NOT NULL REFERENCES users(telegram_id),
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_order_chat_order_id ON order_chat(order_id);
CREATE INDEX idx_order_chat_sender_id ON order_chat(sender_id);

CREATE TABLE IF NOT EXISTS admin_users (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id),
    added_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS operator_users (
    telegram_id BIGINT PRIMARY KEY REFERENCES users(telegram_id),
    added_by BIGINT REFERENCES users(telegram_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS courier_applications (
    id BIGSERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL REFERENCES users(telegram_id),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by BIGINT REFERENCES users(telegram_id),
    reviewed_at TIMESTAMP
);

CREATE INDEX idx_courier_applications_telegram_id ON courier_applications(telegram_id);
CREATE INDEX idx_courier_applications_status ON courier_applications(status);
