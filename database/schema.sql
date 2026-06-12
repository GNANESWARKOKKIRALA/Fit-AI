-- ============================================================================
-- FitAI Database Schema
-- All tables use IF NOT EXISTS for idempotent initialization.
-- ============================================================================

-- Users table: core authentication data
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Profiles table: one-to-one with users
CREATE TABLE IF NOT EXISTS profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE,
    age INTEGER,
    gender TEXT,
    height REAL,
    weight REAL,
    goal_weight REAL,
    activity_level TEXT,
    fitness_goal TEXT,
    workout_preference TEXT,
    diet_preference TEXT,
    medical_notes TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Fitness goals: multiple goals per user
CREATE TABLE IF NOT EXISTS fitness_goals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    goal_type TEXT NOT NULL,
    target_value REAL,
    current_value REAL DEFAULT 0,
    start_date TEXT,
    target_date TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Workout logs
CREATE TABLE IF NOT EXISTS workout_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_type TEXT NOT NULL,
    duration_minutes INTEGER,
    calories_burned REAL,
    exercises TEXT,
    notes TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Weight logs
CREATE TABLE IF NOT EXISTS weight_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    weight REAL NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Calorie logs
CREATE TABLE IF NOT EXISTS calorie_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    calories_consumed REAL,
    calories_burned REAL,
    meal_details TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Water intake logs
CREATE TABLE IF NOT EXISTS water_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount_ml REAL NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Sleep logs
CREATE TABLE IF NOT EXISTS sleep_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    sleep_hours REAL,
    sleep_quality TEXT,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- AI-generated reports
CREATE TABLE IF NOT EXISTS ai_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    report_type TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Chat history with AI assistant
CREATE TABLE IF NOT EXISTS chat_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Step logs
CREATE TABLE IF NOT EXISTS step_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    steps INTEGER NOT NULL,
    logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- ============================================================================
-- Indexes for fast lookups on user_id across all log / child tables
-- ============================================================================
CREATE INDEX IF NOT EXISTS idx_profiles_user_id        ON profiles (user_id);
CREATE INDEX IF NOT EXISTS idx_fitness_goals_user_id   ON fitness_goals (user_id);
CREATE INDEX IF NOT EXISTS idx_workout_logs_user_id    ON workout_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_weight_logs_user_id     ON weight_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_calorie_logs_user_id    ON calorie_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_water_logs_user_id      ON water_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_sleep_logs_user_id      ON sleep_logs (user_id);
CREATE INDEX IF NOT EXISTS idx_ai_reports_user_id      ON ai_reports (user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id    ON chat_history (user_id);
CREATE INDEX IF NOT EXISTS idx_step_logs_user_id       ON step_logs (user_id);
