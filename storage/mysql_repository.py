from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from typing import Any

from shared.schemas import AccountProfile, DashboardSnapshot, FocusPlan, UserProfile

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


class MySQLRepository:
    def __init__(self, config: MySQLConfig) -> None:
        if MYSQL_IMPORT_ERROR is not None:
            raise RuntimeError(
                "mysql-connector-python is required. Install dependencies with 'pip install -r requirements.txt'."
            ) from MYSQL_IMPORT_ERROR
        self.config = config

    def initialize(self) -> None:
        self._ensure_database()
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            tables = [
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
                    CONSTRAINT fk_behavior_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
                    CONSTRAINT fk_focus_plan_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
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
                    attention_game VARCHAR(255) NOT NULL,
                    saved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_plan_history_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    session_token VARCHAR(128) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_session_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    user_id BIGINT PRIMARY KEY,
                    app_name VARCHAR(120) NOT NULL DEFAULT 'Bboo',
                    study_start TIME NOT NULL DEFAULT '16:00:00',
                    bedtime_target TIME NOT NULL DEFAULT '22:30:00',
                    sleep_target_hours INT NOT NULL DEFAULT 8,
                    default_session_minutes INT NOT NULL DEFAULT 30,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_settings_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS daily_checkins (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    mood INT NOT NULL,
                    energy INT NOT NULL,
                    notes TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_checkin_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS focus_timer_sessions (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    session_label VARCHAR(255) NOT NULL,
                    planned_minutes INT NOT NULL,
                    started_at DATETIME NOT NULL,
                    completed_at DATETIME NULL,
                    completed_successfully BOOLEAN NOT NULL DEFAULT FALSE,
                    CONSTRAINT fk_timer_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS dashboard_snapshots (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    focus_score INT NOT NULL,
                    current_state VARCHAR(120) NOT NULL,
                    headline VARCHAR(255) NOT NULL,
                    metrics_json JSON NOT NULL,
                    captured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_snapshot_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS app_usage_logs (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    app_name VARCHAR(120) NOT NULL,
                    usage_date DATE NOT NULL,
                    usage_hours DECIMAL(4, 1) NOT NULL DEFAULT 0,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_usage_day (user_id, app_name, usage_date),
                    CONSTRAINT fk_usage_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS guardian_links (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    parent_user_id BIGINT NOT NULL,
                    child_user_id BIGINT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE KEY uniq_parent_child (parent_user_id, child_user_id),
                    CONSTRAINT fk_guardian_parent FOREIGN KEY (parent_user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_guardian_child FOREIGN KEY (child_user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_conversations (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    title VARCHAR(255) NOT NULL DEFAULT 'Bboo assistant',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_agent_conversation_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_messages (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    conversation_id BIGINT NOT NULL,
                    role VARCHAR(24) NOT NULL,
                    message_text TEXT NOT NULL,
                    intent VARCHAR(80) NULL,
                    tool_name VARCHAR(120) NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_agent_message_conversation FOREIGN KEY (conversation_id) REFERENCES agent_conversations(id) ON DELETE CASCADE
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS agent_action_logs (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    conversation_id BIGINT NOT NULL,
                    tool_name VARCHAR(120) NOT NULL,
                    status VARCHAR(40) NOT NULL,
                    input_json JSON NOT NULL,
                    output_json JSON NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_agent_action_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    CONSTRAINT fk_agent_action_conversation FOREIGN KEY (conversation_id) REFERENCES agent_conversations(id) ON DELETE CASCADE
                )
                """,
            ]
            for statement in tables:
                cursor.execute(statement)
            connection.commit()
        finally:
            connection.close()

    def create_user(self, payload: dict[str, Any], profile: UserProfile) -> dict[str, Any]:
        password_hash, password_salt = self._hash_password(payload["password"])
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
            user_id = int(cursor.lastrowid)
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
            self._ensure_settings_row(cursor, user_id)
            connection.commit()
            session = self._create_session_payload(
                cursor,
                user_id,
                {
                    "first_name": profile.account.first_name,
                    "last_name": profile.account.last_name,
                    "email": profile.account.email,
                    "country": profile.account.country,
                    "preferred_language": profile.account.preferred_language,
                    "audience": payload["audience"],
                    "role": profile.account.role,
                    "permissions_granted": profile.permissions_granted,
                },
            )
            connection.commit()
            return session
        finally:
            connection.close()

    def authenticate_user(self, email: str, password: str, language: str | None = None) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, first_name, last_name, email, password_hash, password_salt, country,
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
            self._ensure_settings_row(cursor, int(user["id"]))
            session = self._create_session_payload(cursor, int(user["id"]), user)
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
                SELECT s.user_id, s.session_token, s.expires_at, u.first_name, u.last_name, u.email,
                       u.country, u.preferred_language, u.audience, u.role, u.permissions_granted
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

    def delete_other_sessions(self, user_id: int, keep_token: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE user_id = %s AND session_token <> %s", (user_id, keep_token))
            connection.commit()
        finally:
            connection.close()

    def load_profile(self, email: str) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(self._profile_query() + " WHERE u.email = %s", (email,))
            row = cursor.fetchone()
            return self._user_profile_from_row(row) if row else None
        finally:
            connection.close()

    def load_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(self._profile_query() + " WHERE u.id = %s", (user_id,))
            row = cursor.fetchone()
            return self._user_profile_from_row(row) if row else None
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
                SELECT id, first_name, last_name, email, country, preferred_language, audience, role, permissions_granted
                FROM users WHERE id = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            connection.commit()
            return self._session_payload(user_id, user, payload.get("token"))
        finally:
            connection.close()

    def load_settings(self, user_id: int) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            self._ensure_settings_row(cursor, user_id)
            cursor.execute(
                "SELECT app_name, study_start, bedtime_target, sleep_target_hours, default_session_minutes FROM app_settings WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            connection.commit()
            if not row:
                return self._default_settings()
            return {
                "app_name": row["app_name"],
                "study_start": self._format_time(row["study_start"]),
                "bedtime_target": self._format_time(row["bedtime_target"]),
                "sleep_target_hours": int(row["sleep_target_hours"]),
                "default_session_minutes": int(row["default_session_minutes"]),
            }
        finally:
            connection.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#Update Session Time----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#it used in **agent/assistant_engine.py** to change the profile Date Website:Application settings part
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def update_settings(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            self._ensure_settings_row(cursor, user_id)
            cursor.execute(
                """
                UPDATE app_settings
                SET app_name = %s, study_start = %s, bedtime_target = %s,
                    sleep_target_hours = %s, default_session_minutes = %s
                WHERE user_id = %s
                """,
                (
                    payload["app_name"],
                    payload["study_start"],
                    payload["bedtime_target"],
                    payload["sleep_target_hours"],
                    payload["default_session_minutes"],
                    user_id,
                ),
            )
            connection.commit()
            return self.load_settings(user_id)
        finally:
            connection.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def load_focus_plan(self, user_id: int) -> FocusPlan | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT title, recommended_session_minutes, focus_theme, steps_json, attention_game, updated_at FROM focus_plans WHERE user_id = %s",
                (user_id,),
            )
            row = cursor.fetchone()
            return self._plan_from_row(row, "updated_at") if row else None
        finally:
            connection.close()

    def save_focus_plan(self, user_id: int, plan: FocusPlan) -> FocusPlan:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT title, recommended_session_minutes, focus_theme, steps_json, attention_game FROM focus_plans WHERE user_id = %s",
                (user_id,),
            )
            current = cursor.fetchone()
            if current:
                self._insert_plan_history(
                    cursor,
                    user_id,
                    current["title"],
                    int(current["recommended_session_minutes"]),
                    current["focus_theme"],
                    self._json_loads(current["steps_json"]),
                    current["attention_game"],
                )
            self._upsert_focus_plan(cursor, user_id, plan)
            self._insert_plan_history(cursor, user_id, plan.title, plan.recommended_session_minutes, plan.focus_theme, plan.steps, plan.attention_game)
            connection.commit()
            return self.load_focus_plan(user_id) or plan
        finally:
            connection.close()

    def load_plan_history(self, user_id: int, limit: int = 8) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT title, recommended_session_minutes, focus_theme, steps_json, attention_game, saved_at
                FROM focus_plan_history
                WHERE user_id = %s
                ORDER BY saved_at DESC, id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall() or []
            return [
                {
                    "title": row["title"],
                    "recommended_session_minutes": int(row["recommended_session_minutes"]),
                    "focus_theme": row["focus_theme"],
                    "steps": self._json_loads(row["steps_json"]),
                    "attention_game": row["attention_game"],
                    "saved_at": self._to_iso(row["saved_at"]),
                }
                for row in rows
            ]
        finally:
            connection.close()

    def record_checkin(self, user_id: int, mood: int, energy: int, notes: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO daily_checkins (user_id, mood, energy, notes) VALUES (%s, %s, %s, %s)",
                (user_id, mood, energy, notes or None),
            )
            connection.commit()
        finally:
            connection.close()

    def recent_checkins(self, user_id: int, limit: int = 7) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, mood, energy, notes, created_at
                FROM daily_checkins
                WHERE user_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall() or []
            return [
                {
                    "id": int(row["id"]),
                    "mood": int(row["mood"]),
                    "energy": int(row["energy"]),
                    "notes": row["notes"] or "",
                    "created_at": self._to_iso(row["created_at"]),
                }
                for row in rows
            ]
        finally:
            connection.close()

    def start_focus_timer(self, user_id: int, minutes: int, label: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                "INSERT INTO focus_timer_sessions (user_id, session_label, planned_minutes, started_at) VALUES (%s, %s, %s, %s)",
                (user_id, label, minutes, datetime.now(timezone.utc).replace(tzinfo=None)),
            )
            connection.commit()
        finally:
            connection.close()

    def complete_focus_timer(self, user_id: int, timer_id: int, completed: bool) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                UPDATE focus_timer_sessions
                SET completed_at = %s, completed_successfully = %s
                WHERE id = %s AND user_id = %s
                """,
                (datetime.now(timezone.utc).replace(tzinfo=None), completed, timer_id, user_id),
            )
            connection.commit()
        finally:
            connection.close()

    def active_timer(self, user_id: int) -> dict[str, Any] | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, session_label, planned_minutes, started_at
                FROM focus_timer_sessions
                WHERE user_id = %s AND completed_at IS NULL
                ORDER BY started_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": int(row["id"]),
                "label": row["session_label"],
                "planned_minutes": int(row["planned_minutes"]),
                "started_at": self._to_iso(row["started_at"]),
            }
        finally:
            connection.close()

    def recent_timers(self, user_id: int, limit: int = 10) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, session_label, planned_minutes, started_at, completed_at, completed_successfully
                FROM focus_timer_sessions
                WHERE user_id = %s
                ORDER BY started_at DESC, id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = cursor.fetchall() or []
            return [
                {
                    "id": int(row["id"]),
                    "label": row["session_label"],
                    "planned_minutes": int(row["planned_minutes"]),
                    "started_at": self._to_iso(row["started_at"]),
                    "completed_at": self._to_iso(row["completed_at"]) if row["completed_at"] else None,
                    "completed_successfully": bool(row["completed_successfully"]),
                    "status": "active" if row["completed_at"] is None else ("completed" if row["completed_successfully"] else "stopped"),
                }
                for row in rows
            ]
        finally:
            connection.close()

    def save_app_usage(self, user_id: int, app_name: str, usage_date: str, usage_hours: float) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO app_usage_logs (user_id, app_name, usage_date, usage_hours)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    usage_hours = VALUES(usage_hours),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, app_name, usage_date, usage_hours),
            )
            connection.commit()
        finally:
            connection.close()

    def app_usage_summary(self, user_id: int) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            start_date = (datetime.now(timezone.utc).date() - timedelta(days=6)).isoformat()
            cursor.execute(
                """
                SELECT app_name, ROUND(SUM(usage_hours), 1) AS total_hours
                FROM app_usage_logs
                WHERE user_id = %s AND usage_date >= %s
                GROUP BY app_name
                ORDER BY total_hours DESC, app_name ASC
                """,
                (user_id, start_date),
            )
            apps = [
                {"app_name": row["app_name"], "total_hours": float(row["total_hours"] or 0)}
                for row in (cursor.fetchall() or [])
            ]
            cursor.execute(
                """
                SELECT app_name, usage_date, usage_hours
                FROM app_usage_logs
                WHERE user_id = %s AND usage_date >= %s
                ORDER BY usage_date DESC, usage_hours DESC, app_name ASC
                """,
                (user_id, start_date),
            )
            recent_entries = [
                {
                    "app_name": row["app_name"],
                    "usage_date": row["usage_date"].isoformat() if hasattr(row["usage_date"], "isoformat") else str(row["usage_date"]),
                    "usage_hours": float(row["usage_hours"] or 0),
                }
                for row in (cursor.fetchall() or [])
            ]
            selected_app = apps[0]["app_name"] if apps else None
            return {
                "apps": apps,
                "recent_entries": recent_entries[:14],
                "selected_app": selected_app,
            }
        finally:
            connection.close()

    def app_usage_detail(self, user_id: int, app_name: str) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            today = datetime.now(timezone.utc).date()
            date_list = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
            cursor.execute(
                """
                SELECT usage_date, usage_hours
                FROM app_usage_logs
                WHERE user_id = %s AND app_name = %s AND usage_date >= %s
                ORDER BY usage_date ASC
                """,
                (user_id, app_name, date_list[0].isoformat()),
            )
            rows = cursor.fetchall() or []
            usage_by_date = {
                (row["usage_date"].isoformat() if hasattr(row["usage_date"], "isoformat") else str(row["usage_date"])): float(row["usage_hours"] or 0)
                for row in rows
            }
            days = []
            for day in date_list:
                iso_day = day.isoformat()
                days.append(
                    {
                        "date": iso_day,
                        "label": day.strftime("%a"),
                        "hours": usage_by_date.get(iso_day, 0.0),
                    }
                )
            return {
                "app_name": app_name,
                "days": days,
                "total_hours": round(sum(item["hours"] for item in days), 1),
            }
        finally:
            connection.close()
    def live_behavior_signals(self, user_id: int) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            today = datetime.now(timezone.utc).date()
            start_date = today - timedelta(days=6)
            cursor.execute(
                """
                SELECT ROUND(COALESCE(SUM(usage_hours), 0), 1) AS total_hours
                FROM app_usage_logs
                WHERE user_id = %s AND usage_date = %s
                """,
                (user_id, today.isoformat()),
            )
            today_usage_hours = float((cursor.fetchone() or {}).get("total_hours") or 0)
            cursor.execute(
                """
                SELECT ROUND(COALESCE(SUM(usage_hours), 0), 1) AS total_hours
                FROM app_usage_logs
                WHERE user_id = %s AND usage_date >= %s
                """,
                (user_id, start_date.isoformat()),
            )
            last_week_usage_total = float((cursor.fetchone() or {}).get("total_hours") or 0)
            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM focus_timer_sessions
                WHERE user_id = %s AND completed_successfully = TRUE AND completed_at >= %s
                """,
                (user_id, datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)),
            )
            completed_focus_sessions = int((cursor.fetchone() or {}).get("count", 0))
            return {
                "today_usage_hours": today_usage_hours,
                "average_daily_usage_hours": round(last_week_usage_total / 7, 1),
                "completed_focus_sessions_last_week": completed_focus_sessions,
            }
        finally:
            connection.close()

    def record_dashboard_snapshot(self, user_id: int, dashboard: DashboardSnapshot) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO dashboard_snapshots (user_id, focus_score, current_state, headline, metrics_json)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    user_id,
                    int(dashboard.focus_score),
                    dashboard.current_state,
                    dashboard.headline,
                    dumps([metric.to_dict() for metric in dashboard.metrics]),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def linked_children(self, parent_user_id: int) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT u.id, u.first_name, u.last_name, u.email,
                       COALESCE(s.focus_score, 0) AS focus_score,
                       COALESCE(s.current_state, 'Awaiting data') AS current_state,
                       s.captured_at
                FROM guardian_links AS g
                JOIN users AS u ON u.id = g.child_user_id
                LEFT JOIN (
                    SELECT ds1.*
                    FROM dashboard_snapshots AS ds1
                    JOIN (
                        SELECT user_id, MAX(id) AS max_id
                        FROM dashboard_snapshots
                        GROUP BY user_id
                    ) AS latest ON latest.max_id = ds1.id
                ) AS s ON s.user_id = u.id
                WHERE g.parent_user_id = %s
                ORDER BY u.first_name, u.last_name
                """,
                (parent_user_id,),
            )
            rows = cursor.fetchall() or []
            items = []
            for row in rows:
                summary = self.weekly_summary(int(row["id"]))
                items.append(
                    {
                        "id": int(row["id"]),
                        "name": f"{row['first_name']} {row['last_name']}".strip(),
                        "email": row["email"],
                        "focus_score": int(row["focus_score"]),
                        "current_state": row["current_state"],
                        "snapshot_at": self._to_iso(row["captured_at"]) if row["captured_at"] else None,
                        "summary": summary["headline"],
                        "weekly_goal_completion": summary["weekly_goal_completion"],
                    }
                )
            return items
        finally:
            connection.close()

    def link_child_account(self, parent_user_id: int, child_email: str) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT id FROM users WHERE email = %s", (child_email,))
            child = cursor.fetchone()
            if not child:
                raise ValueError("We could not find a child account with that email.")
            if int(child["id"]) == parent_user_id:
                raise ValueError("You cannot link your own account as a child.")
            cursor.execute(
                """
                INSERT INTO guardian_links (parent_user_id, child_user_id)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE child_user_id = VALUES(child_user_id)
                """,
                (parent_user_id, int(child["id"])),
            )
            connection.commit()
        finally:
            connection.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#weekly summary retrieval----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#it used in **agent/assistant_engine.py** to get the weekly summary of the user and use it in the assistant response to provide more personalized insights and suggestions based on the user's recent focus and behavior patterns. This allows the assistant to tailor its advice and support to the user's current needs and progress.
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    def weekly_summary(self, user_id: int) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            now = datetime.now(timezone.utc).replace(tzinfo=None)
            week_ago = now - timedelta(days=7)
            two_weeks_ago = now - timedelta(days=14)
            cursor.execute("SELECT COUNT(*) AS count FROM focus_timer_sessions WHERE user_id = %s AND completed_successfully = TRUE AND completed_at >= %s", (user_id, week_ago))
            completed_this_week = int((cursor.fetchone() or {}).get("count", 0))
            cursor.execute("SELECT COUNT(*) AS count FROM focus_timer_sessions WHERE user_id = %s AND completed_successfully = TRUE AND completed_at >= %s AND completed_at < %s", (user_id, two_weeks_ago, week_ago))
            completed_last_week = int((cursor.fetchone() or {}).get("count", 0))
            cursor.execute("SELECT AVG(focus_score) AS average_score FROM dashboard_snapshots WHERE user_id = %s AND captured_at >= %s", (user_id, week_ago))
            avg_this_week = round(float((cursor.fetchone() or {}).get("average_score") or 0))
            cursor.execute("SELECT AVG(focus_score) AS average_score FROM dashboard_snapshots WHERE user_id = %s AND captured_at >= %s AND captured_at < %s", (user_id, two_weeks_ago, week_ago))
            avg_last_week = round(float((cursor.fetchone() or {}).get("average_score") or 0))
            cursor.execute("SELECT COUNT(*) AS count FROM focus_plan_history WHERE user_id = %s AND saved_at >= %s", (user_id, week_ago))
            plan_updates = int((cursor.fetchone() or {}).get("count", 0))
            cursor.execute(
                """
                SELECT DATE(created_at) AS checkin_date
                FROM daily_checkins
                WHERE user_id = %s
                GROUP BY DATE(created_at)
                ORDER BY checkin_date DESC
                LIMIT 21
                """,
                (user_id,),
            )
            streak = self._calculate_streak([row["checkin_date"] for row in (cursor.fetchall() or [])])
            weekly_goal_completion = min(100, int(round((completed_this_week / 5) * 100))) if completed_this_week else 0
            score_delta = avg_this_week - avg_last_week
            improvement_percent = 0 if avg_last_week <= 0 else int(round((score_delta / avg_last_week) * 100))
            milestone = "Recovery spark"
            if completed_this_week >= 7:
                milestone = "Deep focus champion"
            elif completed_this_week >= 5:
                milestone = "Momentum builder"
            elif streak >= 3:
                milestone = "Consistency rising"
            return {
                "headline": f"You improved {max(improvement_percent, 0)}% this week." if score_delta >= 0 else "This week dipped a little, but your data shows where to recover.",
                "completed_sessions_this_week": completed_this_week,
                "completed_sessions_last_week": completed_last_week,
                "average_focus_score_this_week": avg_this_week,
                "average_focus_score_last_week": avg_last_week,
                "score_delta": score_delta,
                "improvement_percent": improvement_percent,
                "plan_updates_this_week": plan_updates,
                "checkin_streak": streak,
                "weekly_goal_completion": weekly_goal_completion,
                "milestone": milestone,
                "recovery_trend": "up" if score_delta >= 0 else "down",
            }
        finally:
            connection.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#suggestion engine----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#it used in **agent/assistant_engine.py** to generate personalized suggestions for the user based
    def suggestion_engine(self, user_id: int, settings: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT HOUR(started_at) AS session_hour, COUNT(*) AS total
                FROM focus_timer_sessions
                WHERE user_id = %s AND completed_successfully = TRUE
                GROUP BY HOUR(started_at)
                ORDER BY total DESC, session_hour ASC
                LIMIT 1
                """,
                (user_id,),
            )
            best_hour_row = cursor.fetchone()
            best_study_time = settings["study_start"]
            if best_hour_row and best_hour_row["session_hour"] is not None:
                best_study_time = f"{int(best_hour_row['session_hour']):02d}:00"
            cursor.execute(
                """
                SELECT HOUR(captured_at) AS risk_hour, AVG(focus_score) AS avg_score
                FROM dashboard_snapshots
                WHERE user_id = %s
                GROUP BY HOUR(captured_at)
                ORDER BY avg_score ASC, risk_hour ASC
                LIMIT 1
                """,
                (user_id,),
            )
            risk_row = cursor.fetchone()
            risk_window = "20:00-22:00"
            if risk_row and risk_row["risk_hour"] is not None:
                start = int(risk_row["risk_hour"])
                risk_window = f"{start:02d}:00-{(start + 2) % 24:02d}:00"
            cursor.execute("SELECT AVG(energy) AS avg_energy FROM daily_checkins WHERE user_id = %s AND created_at >= %s", (user_id, datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=7)))
            avg_energy = float((cursor.fetchone() or {}).get("avg_energy") or 0)
            return {
                "best_study_time": best_study_time,
                "sleep_protection_time": settings["bedtime_target"],
                "risk_window": risk_window,
                "sleep_target_hours": int(settings["sleep_target_hours"]),
                "summary": f"Your strongest study window is around {best_study_time}, and your riskiest distraction window is {risk_window}.",
                "energy_note": "Your energy is holding up well." if avg_energy >= 3.5 else "Your recent energy is dipping, so protect sleep and shorten evening scrolling.",
            }
        finally:
            connection.close()
#----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

    def ensure_agent_conversation(self, user_id: int) -> int:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id
                FROM agent_conversations
                WHERE user_id = %s
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if row:
                return int(row["id"])
            cursor.execute(
                "INSERT INTO agent_conversations (user_id, title) VALUES (%s, %s)",
                (user_id, "Bboo assistant"),
            )
            connection.commit()
            return int(cursor.lastrowid)
        finally:
            connection.close()

    def record_agent_message(self, conversation_id: int, role: str, message_text: str, intent: str | None = None, tool_name: str | None = None) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO agent_messages (conversation_id, role, message_text, intent, tool_name)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (conversation_id, role, message_text, intent, tool_name),
            )
            cursor.execute("UPDATE agent_conversations SET updated_at = CURRENT_TIMESTAMP WHERE id = %s", (conversation_id,))
            connection.commit()
        finally:
            connection.close()

    def record_agent_action(
        self,
        *,
        user_id: int,
        conversation_id: int,
        tool_name: str,
        status: str,
        input_payload: dict[str, Any],
        output_payload: dict[str, Any],
    ) -> None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
                """
                INSERT INTO agent_action_logs (user_id, conversation_id, tool_name, status, input_json, output_json)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (user_id, conversation_id, tool_name, status, dumps(input_payload), dumps(output_payload)),
            )
            connection.commit()
        finally:
            connection.close()

    def agent_history(self, user_id: int, limit: int = 18) -> list[dict[str, Any]]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT m.role, m.message_text, m.intent, m.tool_name, m.created_at
                FROM agent_messages AS m
                JOIN agent_conversations AS c ON c.id = m.conversation_id
                WHERE c.user_id = %s
                ORDER BY m.id DESC
                LIMIT %s
                """,
                (user_id, limit),
            )
            rows = list(reversed(cursor.fetchall() or []))
            return [
                {
                    "role": row["role"],
                    "message": row["message_text"],
                    "intent": row["intent"],
                    "tool_name": row["tool_name"],
                    "created_at": self._to_iso(row["created_at"]),
                }
                for row in rows
            ]
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
        params = {"host": self.config.host, "port": self.config.port, "user": self.config.user, "password": self.config.password}
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

    def _session_payload(self, user_id: int, user_row: dict[str, Any], token: str | None = None) -> dict[str, Any]:
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
        }

    def _age_group_for_audience(self, audience: str) -> str:
        return {"student": "teen", "young-adult": "young_adult", "child": "child"}.get(audience, "teen")

    def _create_session_payload(self, cursor, user_id: int, user_row: dict[str, Any]) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.session_ttl_hours)
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        cursor.execute("INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)", (user_id, token, expires_at.replace(tzinfo=None)))
        return self._session_payload(user_id, user_row, token)

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

    def _insert_plan_history(self, cursor, user_id: int, title: str, minutes: int, theme: str, steps: list[str], game: str) -> None:
        cursor.execute(
            """
            INSERT INTO focus_plan_history (user_id, title, recommended_session_minutes, focus_theme, steps_json, attention_game)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (user_id, title, minutes, theme, dumps(steps), game),
        )

    def _default_settings(self) -> dict[str, Any]:
        return {"app_name": "Bboo", "study_start": "16:00", "bedtime_target": "22:30", "sleep_target_hours": 8, "default_session_minutes": 30}

    def _ensure_settings_row(self, cursor, user_id: int) -> None:
        defaults = self._default_settings()
        cursor.execute(
            """
            INSERT INTO app_settings (user_id, app_name, study_start, bedtime_target, sleep_target_hours, default_session_minutes)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE user_id = user_id
            """,
            (user_id, defaults["app_name"], defaults["study_start"], defaults["bedtime_target"], defaults["sleep_target_hours"], defaults["default_session_minutes"]),
        )

    def _profile_query(self) -> str:
        return """
            SELECT u.id, u.first_name, u.last_name, u.email, u.country, u.preferred_language, u.role,
                   u.permissions_granted, u.audience, b.daily_notifications, b.social_media_hours,
                   b.sleep_hours, b.planning_consistency, b.completed_focus_sessions_last_week
            FROM users AS u
            JOIN behavior_profiles AS b ON b.user_id = u.id
        """

    def _user_profile_from_row(self, row: dict[str, Any]) -> UserProfile:
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

    def _json_loads(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return value
        if isinstance(value, (bytes, bytearray)):
            value = value.decode("utf-8")
        if isinstance(value, str):
            parsed = loads(value)
            return parsed if isinstance(parsed, list) else [str(parsed)]
        return [str(value)]

    def _plan_from_row(self, row: dict[str, Any], timestamp_key: str) -> FocusPlan:
        return FocusPlan(
            generated_at=self._to_iso(row[timestamp_key]),
            title=row["title"],
            recommended_session_minutes=int(row["recommended_session_minutes"]),
            focus_theme=row["focus_theme"],
            steps=self._json_loads(row["steps_json"]),
            attention_game=row["attention_game"],
        )

    def _to_iso(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        else:
            value = value.astimezone(timezone.utc)
        return value.isoformat()

    def _format_time(self, value: Any) -> str:
        return value.strftime("%H:%M") if hasattr(value, "strftime") else str(value)[:5]

    def _calculate_streak(self, dates: list[Any]) -> int:
        normalized = [value.date() if isinstance(value, datetime) else value for value in dates]
        if not normalized:
            return 0
        today = datetime.now(timezone.utc).date()
        streak = 0
        current = today
        values = set(normalized)
        while current in values:
            streak += 1
            current = current - timedelta(days=1)
        if streak == 0 and (today - timedelta(days=1)) in values:
            current = today - timedelta(days=1)
            while current in values:
                streak += 1
                current = current - timedelta(days=1)
        return streak
