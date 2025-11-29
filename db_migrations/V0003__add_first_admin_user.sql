INSERT INTO users (telegram_id, username, first_name, role) 
VALUES (5948140558, 'admin', 'Admin', 'client') 
ON CONFLICT (telegram_id) DO NOTHING;

INSERT INTO admin_users (telegram_id) 
VALUES (5948140558) 
ON CONFLICT (telegram_id) DO NOTHING;
