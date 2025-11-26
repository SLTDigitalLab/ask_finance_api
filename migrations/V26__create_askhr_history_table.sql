CREATE TABLE IF NOT EXISTS ask_hr_history (
   id SERIAL PRIMARY KEY,
   chat_id UUID NOT NULL,
   domain TEXT NOT NULL,
   role TEXT NOT NULL,       
   message TEXT NOT NULL,
   timestamp TIMESTAMP DEFAULT NOW()
);
