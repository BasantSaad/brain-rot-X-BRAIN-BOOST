CREATE DATABASE IF NOT EXISTS `bboo`;
USE `bboo`;

CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    password_salt VARCHAR(64) NOT NULL,
    country VARCHAR(100) NOT NULL,
    preferred_language VARCHAR(8) NOT NULL DEFAULT 'en',
    audience VARCHAR(32) NOT NULL DEFAULT 'student',
    role VARCHAR(32) NOT NULL DEFAULT 'user',
    permissions_granted BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS behavior_profiles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    daily_notifications INT NOT NULL,
    social_media_hours DECIMAL(4, 1) NOT NULL,
    sleep_hours DECIMAL(4, 1) NOT NULL,
    planning_consistency INT NOT NULL,
    completed_focus_sessions_last_week INT NOT NULL,
    generated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_behavior_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS focus_plans (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    recommended_session_minutes INT NOT NULL,
    focus_theme VARCHAR(255) NOT NULL,
    steps_json JSON NOT NULL,
    attention_game VARCHAR(255) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_focus_plan_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(128) NOT NULL UNIQUE,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    user_id BIGINT PRIMARY KEY,
    app_name VARCHAR(120) NOT NULL DEFAULT 'Bboo',
    study_start TIME NOT NULL DEFAULT '16:00:00',
    bedtime_target TIME NOT NULL DEFAULT '22:30:00',
    sleep_target_hours INT NOT NULL DEFAULT 8,
    default_session_minutes INT NOT NULL DEFAULT 30,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_checkins (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    mood INT NOT NULL,
    energy INT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_checkin_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS focus_timer_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_label VARCHAR(255) NOT NULL,
    planned_minutes INT NOT NULL,
    started_at DATETIME NOT NULL,
    completed_at DATETIME NULL,
    completed_successfully BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_timer_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_usage_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    app_name VARCHAR(120) NOT NULL,
    usage_date DATE NOT NULL,
    usage_hours DECIMAL(4, 1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_usage_day (user_id, app_name, usage_date),
    CONSTRAINT fk_usage_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dashboard_snapshots (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    focus_score INT NOT NULL,
    current_state VARCHAR(120) NOT NULL,
    headline VARCHAR(255) NOT NULL,
    metrics_json JSON NOT NULL,
    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_snapshot_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guardian_links (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    parent_user_id BIGINT NOT NULL,
    child_user_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uniq_parent_child (parent_user_id, child_user_id),
    CONSTRAINT fk_guardian_parent
        FOREIGN KEY (parent_user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_guardian_child
        FOREIGN KEY (child_user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_conversations (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL DEFAULT 'Bboo assistant',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_conversation_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_messages (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    conversation_id BIGINT NOT NULL,
    role VARCHAR(24) NOT NULL,
    message_text TEXT NOT NULL,
    intent VARCHAR(80) NULL,
    tool_name VARCHAR(120) NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_message_conversation
        FOREIGN KEY (conversation_id) REFERENCES agent_conversations(id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS agent_action_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    conversation_id BIGINT NOT NULL,
    tool_name VARCHAR(120) NOT NULL,
    status VARCHAR(40) NOT NULL,
    input_json JSON NOT NULL,
    output_json JSON NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_action_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_agent_action_conversation
        FOREIGN KEY (conversation_id) REFERENCES agent_conversations(id)
        ON DELETE CASCADE
);
