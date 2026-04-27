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
    CONSTRAINT fk_behavior_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS app_settings (
    user_id BIGINT PRIMARY KEY,
    app_name VARCHAR(120) NOT NULL DEFAULT 'Bboo',
    study_start_time VARCHAR(8) NOT NULL DEFAULT '16:00',
    study_end_time VARCHAR(8) NOT NULL DEFAULT '20:00',
    sleep_target_hours DECIMAL(3,1) NOT NULL DEFAULT 8.0,
    focus_session_minutes INT NOT NULL DEFAULT 30,
    short_break_minutes INT NOT NULL DEFAULT 5,
    long_break_minutes INT NOT NULL DEFAULT 15,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS extended_profiles (
    user_id BIGINT PRIMARY KEY,
    age INT NULL,
    schedule_type VARCHAR(80) NOT NULL DEFAULT 'student afternoons',
    goals_json JSON NOT NULL,
    distraction_triggers_json JSON NOT NULL,
    sleep_target_hours DECIMAL(3,1) NOT NULL DEFAULT 8.0,
    mood_baseline VARCHAR(40) NOT NULL DEFAULT 'steady',
    energy_baseline VARCHAR(40) NOT NULL DEFAULT 'medium',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_extended_profile_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
    CONSTRAINT fk_focus_plan_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS focus_plan_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    recommended_session_minutes INT NOT NULL,
    focus_theme VARCHAR(255) NOT NULL,
    steps_json JSON NOT NULL,
    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_plan_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    session_token VARCHAR(128) NOT NULL UNIQUE,
    remember_me BOOLEAN NOT NULL DEFAULT FALSE,
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    reset_code VARCHAR(16) NOT NULL,
    expires_at DATETIME NOT NULL,
    used_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reset_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS daily_checkins (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    mood VARCHAR(40) NOT NULL,
    energy VARCHAR(40) NOT NULL,
    focus_feeling INT NOT NULL,
    notes TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_checkin_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS focus_timer_sessions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    label VARCHAR(120) NOT NULL,
    planned_minutes INT NOT NULL,
    actual_minutes INT NOT NULL DEFAULT 0,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    started_at DATETIME NOT NULL,
    ended_at DATETIME NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_timer_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS dashboard_snapshots (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    focus_score INT NOT NULL,
    chart_data_json JSON NOT NULL,
    mode VARCHAR(32) NOT NULL,
    language VARCHAR(8) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_snapshot_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS guardian_links (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    guardian_user_id BIGINT NOT NULL,
    child_user_id BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_guardian_child (guardian_user_id, child_user_id),
    CONSTRAINT fk_guardian_user FOREIGN KEY (guardian_user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_child_user FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE CASCADE
);
