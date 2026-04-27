from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from typing import Any

from shared.schemas import AccountProfile, AppSettings, ExtendedProfile, FocusPlan, UserProfile
from simulator.behavior_simulator import BehaviorSimulationConfig, BehaviorSimulator

try:
    import mysql.connector
    from mysql.connector import Error
except ModuleNotFoundError as exc:  # pragma: no cover
    mysql = None
    Error = Exception
    MYSQL_IMPORT_ERROR = exc
else:
    MYSQL_IMPORT_ERROR = None


@dataclass(slots=True)
class MySQLConfig:
    host: str = os.getenv("BBOO_DB_HOST", "127.0.0.1")
    port: int = int(os.getenv("BBOO_DB_PORT", "3306"))
    user: str = os.getenv("BBOO_DB_USER", "root")
    password: str = os.getenv("BBOO_DB_PASSWORD", "")
    database: str = os.getenv("BBOO_DB_NAME", "bboo")
    session_ttl_hours: int = int(os.getenv("BBOO_SESSION_TTL_HOURS", "24"))
    remember_me_days: int = int(os.getenv("BBOO_REMEMBER_ME_DAYS", "30"))
    reset_code_minutes: int = int(os.getenv("BBOO_RESET_CODE_MINUTES", "15"))


class MySQLRepository:
    def __init__(self, config: MySQLConfig) -> None:
        if MYSQL_IMPORT_ERROR is not None:
            raise RuntimeError(
                "mysql-connector-python is required. Install dependencies with "
                "'pip install -r requirements.txt'."
            ) from MYSQL_IMPORT_ERROR
        self.config = config
        self.simulator = BehaviorSimulator(BehaviorSimulationConfig())

    def initialize(self) -> None:
        self._ensure_database()
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            statements = [
                """
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
                )
                """,
                """
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
                )
                """,
                """
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
                    CONSTRAINT fk_settings_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
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
                    CONSTRAINT fk_extended_profile_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
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
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS focus_plan_history (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    title VARCHAR(255) NOT NULL,
                    recommended_session_minutes INT NOT NULL,
                    focus_theme VARCHAR(255) NOT NULL,
                    steps_json JSON NOT NULL,
                    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_plan_history_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    session_token VARCHAR(128) NOT NULL UNIQUE,
                    remember_me BOOLEAN NOT NULL DEFAULT FALSE,
                    expires_at DATETIME NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_session_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS password_reset_tokens (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    reset_code VARCHAR(16) NOT NULL,
                    expires_at DATETIME NOT NULL,
                    used_at DATETIME NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_reset_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS daily_checkins (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    mood VARCHAR(40) NOT NULL,
                    energy VARCHAR(40) NOT NULL,
                    focus_feeling INT NOT NULL,
                    notes TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_checkin_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
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
                    CONSTRAINT fk_timer_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS dashboard_snapshots (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    focus_score INT NOT NULL,
                    chart_data_json JSON NOT NULL,
                    mode VARCHAR(32) NOT NULL,
                    language VARCHAR(8) NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_snapshot_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS guardian_links (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    guardian_user_id BIGINT NOT NULL,
                    child_user_id BIGINT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uq_guardian_child (guardian_user_id, child_user_id),
                    CONSTRAINT fk_guardian_user
                        FOREIGN KEY (guardian_user_id) REFERENCES users(id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_child_user
                        FOREIGN KEY (child_user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """,
            ]
            for statement in statements:
                cursor.execute(statement)
            migrations = [
                "ALTER TABLE user_sessions ADD COLUMN IF NOT EXISTS remember_me BOOLEAN NOT NULL DEFAULT FALSE",
            ]
            for statement in migrations:
                try:
                    cursor.execute(statement)
                except Error:
                    pass
            connection.commit()
        finally:
            connection.close()

    def create_user(self, payload: dict[str, Any], profile: UserProfile) -> dict[str, Any]:
        password_hash, password_salt = self._hash_password(payload["password"])
        remember_me = bool(payload.get("remember_me"))
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (payload["email"],))
            if cursor.fetchone():
                raise ValueError("An account with this email already exists.")
            cursor.execute(
                """
                INSERT INTO users (
                    first_name, last_name, email, password_hash, password_salt, country,
                    preferred_language, audience, role, permissions_granted
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    profile.account.first_name,
                    profile.account.last_name,
                    profile.account.email,
                    password_hash,
                    password_salt,
                    profile.account.country,
                    profile.account.preferred_language,
                    payload["audience"],
                    profile.account.role,
                    profile.permissions_granted,
                ),
            )
            user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO behavior_profiles (
                    user_id, daily_notifications, social_media_hours, sleep_hours,
                    planning_consistency, completed_focus_sessions_last_week
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    profile.daily_notifications,
                    profile.social_media_hours,
                    profile.sleep_hours,
                    profile.planning_consistency,
                    profile.completed_focus_sessions_last_week,
                ),
            )
            self._insert_default_settings(cursor, user_id=user_id, audience=payload["audience"])
            self._insert_default_extended_profile(cursor, user_id=user_id)
            connection.commit()
            session = self._create_session_payload(
                cursor=cursor,
                user_id=user_id,
                user_row=self._session_user_row_from_profile(profile=profile, audience=payload["audience"]),
                remember_me=remember_me,
            )
            connection.commit()
            return session
        finally:
            connection.close()

    def authenticate_user(self, email: str, password: str, language: str | None = None, remember_me: bool = False) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    id, first_name, last_name, email, password_hash, password_salt, country,
                    preferred_language, audience, role, permissions_granted
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user = cursor.fetchone()
            if not user or not self._verify_password(password, user["password_hash"], user["password_salt"]):
                raise ValueError("Invalid email or password.")
            if language and language != user["preferred_language"]:
                cursor.execute("UPDATE users SET preferred_language = %s WHERE id = %s", (language, user["id"]))
                user["preferred_language"] = language
            session = self._create_session_payload(cursor=cursor, user_id=user["id"], user_row=user, remember_me=remember_me)
            connection.commit()
            return session
        finally:
            connection.close()

    def load_session(self, token: str) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    s.user_id, s.session_token, s.remember_me, s.expires_at,
                    u.first_name, u.last_name, u.email, u.country, u.preferred_language,
                    u.audience, u.role, u.permissions_granted
                FROM user_sessions AS s
                JOIN users AS u ON u.id = s.user_id
                WHERE s.session_token = %s
                """,
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                raise ValueError("Your session was not found. Please log in again.")
            expires_at = row["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                cursor.execute("DELETE FROM user_sessions WHERE session_token = %s", (token,))
                connection.commit()
                raise ValueError("Your session has expired. Please log in again.")
            settings = self.load_settings(int(row["user_id"]))
            return {
                "user_id": int(row["user_id"]),
                "token": row["session_token"],
                "first_name": row["first_name"],
                "last_name": row["last_name"],
                "email": row["email"],
                "country": row["country"],
                "lang": row["preferred_language"],
                "audience": row["audience"],
                "mode": row["role"],
                "permissions": str(bool(row["permissions_granted"])).lower(),
                "remember_me": bool(row["remember_me"]),
                "app_name": settings.app_name,
            }
        finally:
            connection.close()

    def delete_session(self, token: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE session_token = %s", (token,))
            connection.commit()
        finally:
            connection.close()

    def delete_all_sessions(self, user_id: int, keep_token: str | None = None) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            if keep_token:
                cursor.execute("DELETE FROM user_sessions WHERE user_id = %s AND session_token <> %s", (user_id, keep_token))
            else:
                cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
            connection.commit()
        finally:
            connection.close()

    def request_password_reset(self, email: str) -> dict[str, str]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("We could not find an account for that email.")
            code = f"{secrets.randbelow(1000000):06d}"
            expires = datetime.now(timezone.utc) + timedelta(minutes=self.config.reset_code_minutes)
            cursor.execute("UPDATE password_reset_tokens SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL", (user["id"],))
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (user_id, reset_code, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user["id"], code, expires.replace(tzinfo=None)),
            )
            connection.commit()
            return {
                "message": f"Reset code generated for {user['first_name']}.",
                "reset_code": code,
            }
        finally:
            connection.close()

    def reset_password(self, email: str, reset_code: str, new_password: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
            if not user:
                raise ValueError("We could not find an account for that email.")
            cursor.execute(
                """
                SELECT id, expires_at, used_at
                FROM password_reset_tokens
                WHERE user_id = %s AND reset_code = %s
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (user["id"], reset_code),
            )
            token = cursor.fetchone()
            if not token or token["used_at"] is not None:
                raise ValueError("That reset code is invalid.")
            expires_at = token["expires_at"]
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if expires_at <= datetime.now(timezone.utc):
                raise ValueError("That reset code has expired.")
            password_hash, password_salt = self._hash_password(new_password)
            cursor.execute(
                "UPDATE users SET password_hash = %s, password_salt = %s WHERE id = %s",
                (password_hash, password_salt, user["id"]),
            )
            cursor.execute("UPDATE password_reset_tokens SET used_at = NOW() WHERE id = %s", (token["id"],))
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user["id"],))
            connection.commit()
        finally:
            connection.close()

    def load_profile(self, email: str) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            row = self._fetch_profile_row(cursor, "u.email = %s", (email,))
            return self._profile_from_row(row) if row else None
        finally:
            connection.close()

    def load_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            row = self._fetch_profile_row(cursor, "u.id = %s", (user_id,))
            return self._profile_from_row(row) if row else None
        finally:
            connection.close()

    def load_settings(self, user_id: int) -> AppSettings:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT app_name, study_start_time, study_end_time, sleep_target_hours,
                       focus_session_minutes, short_break_minutes, long_break_minutes
                FROM app_settings
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return AppSettings("Bboo", "16:00", "20:00", 8.0, 30, 5, 15)
            return AppSettings(
                app_name=row["app_name"],
                study_start_time=row["study_start_time"],
                study_end_time=row["study_end_time"],
                sleep_target_hours=float(row["sleep_target_hours"]),
                focus_session_minutes=int(row["focus_session_minutes"]),
                short_break_minutes=int(row["short_break_minutes"]),
                long_break_minutes=int(row["long_break_minutes"]),
            )
        finally:
            connection.close()

    def update_settings(self, user_id: int, payload: dict[str, Any]) -> AppSettings:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO app_settings (
                    user_id, app_name, study_start_time, study_end_time, sleep_target_hours,
                    focus_session_minutes, short_break_minutes, long_break_minutes
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    app_name = VALUES(app_name),
                    study_start_time = VALUES(study_start_time),
                    study_end_time = VALUES(study_end_time),
                    sleep_target_hours = VALUES(sleep_target_hours),
                    focus_session_minutes = VALUES(focus_session_minutes),
                    short_break_minutes = VALUES(short_break_minutes),
                    long_break_minutes = VALUES(long_break_minutes)
                """,
                (
                    user_id,
                    payload["app_name"],
                    payload["study_start_time"],
                    payload["study_end_time"],
                    payload["sleep_target_hours"],
                    payload["focus_session_minutes"],
                    payload["short_break_minutes"],
                    payload["long_break_minutes"],
                ),
            )
            connection.commit()
            return self.load_settings(user_id)
        finally:
            connection.close()

    def load_extended_profile(self, user_id: int) -> ExtendedProfile:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT age, schedule_type, goals_json, distraction_triggers_json,
                       sleep_target_hours, mood_baseline, energy_baseline
                FROM extended_profiles
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return ExtendedProfile(None, "student afternoons", [], [], 8.0, "steady", "medium")
            return ExtendedProfile(
                age=row["age"],
                schedule_type=row["schedule_type"],
                goals=self._json_load(row["goals_json"]),
                distraction_triggers=self._json_load(row["distraction_triggers_json"]),
                sleep_target_hours=float(row["sleep_target_hours"]),
                mood_baseline=row["mood_baseline"],
                energy_baseline=row["energy_baseline"],
            )
        finally:
            connection.close()

    def update_profile(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                UPDATE users
                SET first_name = %s, last_name = %s, country = %s, preferred_language = %s,
                    audience = %s, role = %s, permissions_granted = %s
                WHERE id = %s
                """,
                (
                    payload["first_name"],
                    payload["last_name"],
                    payload["country"],
                    payload["lang"],
                    payload["audience"],
                    payload["mode"],
                    str(payload["permissions"]).lower() == "true",
                    user_id,
                ),
            )
            cursor.execute(
                """
                INSERT INTO extended_profiles (
                    user_id, age, schedule_type, goals_json, distraction_triggers_json,
                    sleep_target_hours, mood_baseline, energy_baseline
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    age = VALUES(age),
                    schedule_type = VALUES(schedule_type),
                    goals_json = VALUES(goals_json),
                    distraction_triggers_json = VALUES(distraction_triggers_json),
                    sleep_target_hours = VALUES(sleep_target_hours),
                    mood_baseline = VALUES(mood_baseline),
                    energy_baseline = VALUES(energy_baseline)
                """,
                (
                    user_id,
                    payload.get("age"),
                    payload["schedule_type"],
                    dumps(payload["goals"]),
                    dumps(payload["distraction_triggers"]),
                    payload["sleep_target_hours"],
                    payload["mood_baseline"],
                    payload["energy_baseline"],
                ),
            )
            cursor.execute(
                """
                SELECT id, first_name, last_name, email, country, preferred_language,
                       audience, role, permissions_granted
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            connection.commit()
            settings = self.load_settings(user_id)
            session = self._session_payload(user_id=user_id, user_row=user, token=payload.get("token"))
            session["app_name"] = settings.app_name
            return session
        finally:
            connection.close()

    def load_focus_plan(self, user_id: int) -> FocusPlan | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT title, recommended_session_minutes, focus_theme, steps_json, attention_game, updated_at
                FROM focus_plans
                WHERE user_id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return FocusPlan(
                generated_at=self._iso_from_db(row["updated_at"]),
                title=row["title"],
                recommended_session_minutes=int(row["recommended_session_minutes"]),
                focus_theme=row["focus_theme"],
                steps=self._json_load(row["steps_json"]),
                attention_game=row["attention_game"],
            )
        finally:
            connection.close()

    def save_focus_plan(self, user_id: int, plan: FocusPlan) -> FocusPlan:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            self._upsert_focus_plan(cursor, user_id, plan)
            cursor.execute(
                """
                INSERT INTO focus_plan_history (user_id, title, recommended_session_minutes, focus_theme, steps_json)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, plan.title, plan.recommended_session_minutes, plan.focus_theme, dumps(plan.steps)),
            )
            connection.commit()
            return self.load_focus_plan(user_id) or plan
        finally:
            connection.close()

    def load_plan_history(self, user_id: int, limit: int = 6) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT saved_at, recommended_session_minutes, focus_theme, steps_json
                FROM focus_plan_history
                WHERE user_id = %s
                ORDER BY saved_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return [
                {
                    "saved_at": self._iso_from_db(row["saved_at"]),
                    "recommended_session_minutes": int(row["recommended_session_minutes"]),
                    "focus_theme": row["focus_theme"],
                    "steps": self._json_load(row["steps_json"]),
                }
                for row in cursor.fetchall()
            ]
        finally:
            connection.close()

    def record_checkin(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO daily_checkins (user_id, mood, energy, focus_feeling, notes)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, payload["mood"], payload["energy"], payload["focus_feeling"], payload["notes"]),
            )
            connection.commit()
            return {"message": "Daily check-in saved."}
        finally:
            connection.close()

    def recent_checkins(self, user_id: int, limit: int = 7) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT mood, energy, focus_feeling, notes, created_at
                FROM daily_checkins
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            return [
                {
                    "mood": row["mood"],
                    "energy": row["energy"],
                    "focus_feeling": int(row["focus_feeling"]),
                    "notes": row["notes"],
                    "created_at": self._iso_from_db(row["created_at"]),
                }
                for row in cursor.fetchall()
            ]
        finally:
            connection.close()

    def start_focus_timer(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO focus_timer_sessions (user_id, label, planned_minutes, started_at)
                VALUES (%s, %s, %s, %s)
                """,
                (user_id, payload["label"], payload["planned_minutes"], datetime.now(timezone.utc).replace(tzinfo=None)),
            )
            connection.commit()
            return {"timer_id": cursor.lastrowid, "message": "Focus timer started."}
        finally:
            connection.close()

    def complete_focus_timer(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE focus_timer_sessions
                SET completed = %s, actual_minutes = %s, ended_at = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    bool(payload["completed"]),
                    int(payload["actual_minutes"]),
                    datetime.now(timezone.utc).replace(tzinfo=None),
                    payload["timer_id"],
                    user_id,
                ),
            )
            connection.commit()
            return {"message": "Focus timer updated."}
        finally:
            connection.close()

    def recent_timers(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, label, planned_minutes, actual_minutes, completed, started_at, ended_at
                FROM focus_timer_sessions
                WHERE user_id = %s
                ORDER BY started_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = []
            for row in cursor.fetchall():
                rows.append(
                    {
                        "id": int(row["id"]),
                        "label": row["label"],
                        "planned_minutes": int(row["planned_minutes"]),
                        "actual_minutes": int(row["actual_minutes"]),
                        "completed": bool(row["completed"]),
                        "started_at": self._iso_from_db(row["started_at"]),
                        "ended_at": self._iso_from_db(row["ended_at"]) if row["ended_at"] else None,
                    }
                )
            return rows
        finally:
            connection.close()

    def record_dashboard_snapshot(self, user_id: int, focus_score: int, chart_payload: list[dict[str, Any]], mode: str, language: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO dashboard_snapshots (user_id, focus_score, chart_data_json, mode, language)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (user_id, focus_score, dumps(chart_payload), mode, language),
            )
            connection.commit()
        finally:
            connection.close()

    def snapshot_history(self, user_id: int, limit: int = 7) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT focus_score, chart_data_json, created_at
                FROM dashboard_snapshots
                WHERE user_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            items = []
            for row in reversed(cursor.fetchall()):
                items.append(
                    {
                        "focus_score": int(row["focus_score"]),
                        "chart_data": self._json_load(row["chart_data_json"]),
                        "created_at": self._iso_from_db(row["created_at"]),
                    }
                )
            return items
        finally:
            connection.close()

    def weekly_summary(self, user_id: int) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT COALESCE(SUM(actual_minutes), 0) AS total_minutes,
                       COALESCE(SUM(completed = TRUE), 0) AS completed_sessions
                FROM focus_timer_sessions
                WHERE user_id = %s AND started_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 7 DAY)
                """,
                (user_id,),
            )
            this_week = cursor.fetchone()
            cursor.execute(
                """
                SELECT COALESCE(SUM(actual_minutes), 0) AS total_minutes
                FROM focus_timer_sessions
                WHERE user_id = %s
                  AND started_at >= DATE_SUB(UTC_TIMESTAMP(), INTERVAL 14 DAY)
                  AND started_at < DATE_SUB(UTC_TIMESTAMP(), INTERVAL 7 DAY)
                """,
                (user_id,),
            )
            last_week = cursor.fetchone()
            cursor.execute(
                """
                SELECT COALESCE(COUNT(*), 0) AS streak_days
                FROM (
                    SELECT DATE(started_at) AS active_day
                    FROM focus_timer_sessions
                    WHERE user_id = %s AND completed = TRUE
                    GROUP BY DATE(started_at)
                ) AS daily
                WHERE active_day >= DATE_SUB(UTC_DATE(), INTERVAL 14 DAY)
                """,
                (user_id,),
            )
            streak_row = cursor.fetchone()
            total_minutes = int(this_week["total_minutes"] or 0)
            previous_minutes = int(last_week["total_minutes"] or 0)
            improvement = 100 if previous_minutes == 0 and total_minutes > 0 else 0
            if previous_minutes > 0:
                improvement = int(round(((total_minutes - previous_minutes) / previous_minutes) * 100))
            completed_sessions = int(this_week["completed_sessions"] or 0)
            avg_minutes = int(round(total_minutes / completed_sessions)) if completed_sessions else 0
            recommendation = "Keep the same evening focus block." if improvement >= 0 else "Reduce friction before your usual risk window."
            return {
                "headline": f"You improved {max(improvement, 0)}% this week." if improvement >= 0 else f"You dipped {abs(improvement)}% this week.",
                "improvement_percent": improvement,
                "streak_days": int(streak_row["streak_days"] or 0),
                "completed_sessions": completed_sessions,
                "average_focus_minutes": avg_minutes,
                "recommendation": recommendation,
            }
        finally:
            connection.close()

    def best_time_suggestions(self, user_id: int) -> dict[str, str]:
        settings = self.load_settings(user_id)
        extended = self.load_extended_profile(user_id)
        timers = self.recent_timers(user_id, limit=20)
        checkins = self.recent_checkins(user_id, limit=10)
        best_study = settings.study_start_time
        if timers:
            completed_hours = []
            for timer in timers:
                if timer["completed"]:
                    hour = datetime.fromisoformat(timer["started_at"]).hour
                    completed_hours.append(hour)
            if completed_hours:
                avg_hour = round(sum(completed_hours) / len(completed_hours))
                best_study = f"{avg_hour:02d}:00"
        mood_factor = "21:30"
        low_energy_nights = sum(1 for item in checkins if item["energy"] in {"low", "drained"})
        if low_energy_nights >= 3 or extended.sleep_target_hours >= 8.0:
            mood_factor = "21:00"
        return {
            "best_study_time": best_study,
            "best_sleep_protection_time": mood_factor,
            "risk_window": self.detect_risk_window(user_id),
        }

    def detect_risk_window(self, user_id: int) -> str:
        checkins = self.recent_checkins(user_id, limit=10)
        timers = self.recent_timers(user_id, limit=20)
        late_failures = 0
        for timer in timers:
            hour = datetime.fromisoformat(timer["started_at"]).hour
            if hour >= 20 and not timer["completed"]:
                late_failures += 1
        if late_failures >= 2 or any(item["focus_feeling"] <= 4 for item in checkins):
            return "8 PM - 10 PM"
        return "4 PM - 6 PM"

    def link_child_account(self, guardian_user_id: int, child_email: str) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id, first_name, last_name, audience FROM users WHERE email = %s", (child_email,))
            child = cursor.fetchone()
            if not child:
                raise ValueError("We could not find a child account with that email.")
            cursor.execute(
                """
                INSERT INTO guardian_links (guardian_user_id, child_user_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE child_user_id = VALUES(child_user_id)
                """,
                (guardian_user_id, child["id"]),
            )
            connection.commit()
            return {
                "message": f"Linked to {child['first_name']} {child['last_name']}.",
                "child_user_id": int(child["id"]),
            }
        finally:
            connection.close()

    def linked_children(self, guardian_user_id: int) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.id, u.first_name, u.last_name, u.email, u.audience
                FROM guardian_links AS g
                JOIN users AS u ON u.id = g.child_user_id
                WHERE g.guardian_user_id = %s
                ORDER BY g.created_at DESC
                """,
                (guardian_user_id,),
            )
            children = []
            for row in cursor.fetchall():
                summary = self.weekly_summary(int(row["id"]))
                children.append(
                    {
                        "user_id": int(row["id"]),
                        "name": f"{row['first_name']} {row['last_name']}",
                        "email": row["email"],
                        "audience": row["audience"],
                        "weekly_summary": summary,
                    }
                )
            return children
        finally:
            connection.close()

    def _ensure_database(self) -> None:
        connection = self._connection()
        try:
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{self.config.database}`")
            connection.commit()
        finally:
            connection.close()

    def _connection(self, database: str | None = None):
        params = {
            "host": self.config.host,
            "port": self.config.port,
            "user": self.config.user,
            "password": self.config.password,
        }
        if database:
            params["database"] = database
        try:
            return mysql.connector.connect(**params)
        except Error as exc:
            target = database or self.config.database
            raise RuntimeError(
                "Could not connect to MySQL. Make sure XAMPP MySQL is running and that "
                f"BBOO_DB_HOST/BBOO_DB_PORT/BBOO_DB_USER/BBOO_DB_PASSWORD can access the '{target}' database."
            ) from exc

    def _hash_password(self, password: str, salt: str | None = None) -> tuple[str, str]:
        salt = salt or secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120000)
        return digest.hex(), salt

    def _verify_password(self, password: str, expected_hash: str, salt: str) -> bool:
        candidate_hash, _ = self._hash_password(password, salt)
        return hmac.compare_digest(candidate_hash, expected_hash)

    def _session_payload(self, user_id: int, user_row: dict[str, Any], token: str | None = None, remember_me: bool = False) -> dict[str, Any]:
        return {
            "user_id": user_id,
            "token": token,
            "first_name": user_row["first_name"],
            "last_name": user_row["last_name"],
            "email": user_row["email"],
            "country": user_row["country"],
            "lang": user_row["preferred_language"],
            "audience": user_row["audience"],
            "mode": user_row["role"],
            "permissions": str(bool(user_row["permissions_granted"])).lower(),
            "remember_me": remember_me,
        }

    def _create_session_payload(self, cursor, user_id: int, user_row: dict[str, Any], remember_me: bool) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        ttl = timedelta(days=self.config.remember_me_days) if remember_me else timedelta(hours=self.config.session_ttl_hours)
        expires_at = datetime.now(timezone.utc) + ttl
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        cursor.execute(
            """
            INSERT INTO user_sessions (user_id, session_token, remember_me, expires_at)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, token, remember_me, expires_at.replace(tzinfo=None)),
        )
        session = self._session_payload(user_id=user_id, user_row=user_row, token=token, remember_me=remember_me)
        settings = self.load_settings(user_id)
        session["app_name"] = settings.app_name
        return session

    def _upsert_focus_plan(self, cursor, user_id: int, plan: FocusPlan) -> None:
        cursor.execute(
            """
            INSERT INTO focus_plans (user_id, title, recommended_session_minutes, focus_theme, steps_json, attention_game)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                title = VALUES(title),
                recommended_session_minutes = VALUES(recommended_session_minutes),
                focus_theme = VALUES(focus_theme),
                steps_json = VALUES(steps_json),
                attention_game = VALUES(attention_game)
            """,
            (user_id, plan.title, plan.recommended_session_minutes, plan.focus_theme, dumps(plan.steps), plan.attention_game),
        )

    def _fetch_profile_row(self, cursor, condition: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
        cursor.execute(
            f"""
            SELECT
                u.id, u.first_name, u.last_name, u.email, u.country, u.preferred_language,
                u.role, u.permissions_granted, u.audience,
                b.daily_notifications, b.social_media_hours, b.sleep_hours,
                b.planning_consistency, b.completed_focus_sessions_last_week
            FROM users AS u
            JOIN behavior_profiles AS b ON b.user_id = u.id
            WHERE {condition}
            """,
            params,
        )
        return cursor.fetchone()

    def _profile_from_row(self, row: dict[str, Any]) -> UserProfile:
        return UserProfile(
            account=AccountProfile(
                first_name=row["first_name"],
                last_name=row["last_name"],
                email=row["email"],
                country=row["country"],
                preferred_language=row["preferred_language"],
                role=row["role"],
                age_group=self._age_group_for_audience(row["audience"]),
            ),
            permissions_granted=bool(row["permissions_granted"]),
            daily_notifications=int(row["daily_notifications"]),
            social_media_hours=float(row["social_media_hours"]),
            sleep_hours=float(row["sleep_hours"]),
            planning_consistency=int(row["planning_consistency"]),
            completed_focus_sessions_last_week=int(row["completed_focus_sessions_last_week"]),
        )

    def _age_group_for_audience(self, audience: str) -> str:
        mapping = {
            "student": "teen",
            "young-adult": "young_adult",
            "child": "child",
        }
        return mapping.get(audience, "teen")

    def _insert_default_settings(self, cursor, user_id: int, audience: str) -> None:
        app_name = "Bboo Parent" if audience == "child" else "Bboo"
        cursor.execute(
            """
            INSERT INTO app_settings (
                user_id, app_name, study_start_time, study_end_time, sleep_target_hours,
                focus_session_minutes, short_break_minutes, long_break_minutes
            ) VALUES (%s, %s, '16:00', '20:00', 8.0, 30, 5, 15)
            """,
            (user_id, app_name),
        )

    def _insert_default_extended_profile(self, cursor, user_id: int) -> None:
        cursor.execute(
            """
            INSERT INTO extended_profiles (
                user_id, age, schedule_type, goals_json, distraction_triggers_json,
                sleep_target_hours, mood_baseline, energy_baseline
            ) VALUES (%s, NULL, %s, %s, %s, 8.0, 'steady', 'medium')
            """,
            (user_id, "student afternoons", dumps(["Improve focus consistency"]), dumps(["Notifications", "Short video feeds"])),
        )

    def _session_user_row_from_profile(self, profile: UserProfile, audience: str) -> dict[str, Any]:
        return {
            "first_name": profile.account.first_name,
            "last_name": profile.account.last_name,
            "email": profile.account.email,
            "country": profile.account.country,
            "preferred_language": profile.account.preferred_language,
            "audience": audience,
            "role": profile.account.role,
            "permissions_granted": profile.permissions_granted,
        }

    def _json_load(self, value: Any) -> list[Any]:
        if isinstance(value, list):
            return value
        if not value:
            return []
        return loads(value)

    def _iso_from_db(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc).isoformat()
