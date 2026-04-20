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
