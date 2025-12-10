-- Add preferred_time column to orders table
ALTER TABLE t_p39739760_garbage_bot_service.orders 
ADD COLUMN IF NOT EXISTS preferred_time VARCHAR(100);