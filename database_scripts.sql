-- Создание таблицы PsychologicalStates
CREATE TABLE IF NOT EXISTS PsychologicalStates (
    p_id SERIAL PRIMARY KEY,
    p_name VARCHAR(1024),
    typeOfState VARCHAR(1024),
    description TEXT
);

-- Создание таблицы ChatConditionalBranches
CREATE TABLE IF NOT EXISTS ChatConditionalBranches(
    c_id SERIAL PRIMARY KEY,
    psychological_state INTEGER REFERENCES PsychologicalStates(p_id),
    c_name VARCHAR(1024),
    condition TEXT,
    branch TEXT
);

-- Создание таблицы ChatHistory
CREATE TABLE IF NOT EXISTS ChatHistory(
    h_id SERIAL PRIMARY KEY,
    chat_conditional_branch INTEGER REFERENCES ChatConditionalBranches(c_id),
    user_hash_tg_id VARCHAR(256),
    h_date date not null default CURRENT_DATE,
    msg_bot TEXT,
    msg_user TEXT,
    state INT
);