from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from json import dumps, loads
from typing import Any

from shared.schemas import AccountProfile, FocusPlan, UserProfile

try:
    import mysql.connector
    from mysql.connector import Error
except ModuleNotFoundError as exc:  # pragma: no cover - dependency is environment-specific
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
                "mysql-connector-python is required. Install dependencies with "
                "'pip install -r requirements.txt'."
            ) from MYSQL_IMPORT_ERROR
        self.config = config

    def initialize(self) -> None:
        self._ensure_database()
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            cursor.execute(
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
                """
            )
            cursor.execute(
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
                """
            )
            cursor.execute(
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
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id BIGINT PRIMARY KEY AUTO_INCREMENT,
                    user_id BIGINT NOT NULL,
                    session_token VARCHAR(128) NOT NULL UNIQUE,
                    expires_at DATETIME NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_session_user
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE
                )
                """
            )
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
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    password_salt,
                    country,
                    preferred_language,
                    audience,
                    role,
                    permissions_granted
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
                    user_id,
                    daily_notifications,
                    social_media_hours,
                    sleep_hours,
                    planning_consistency,
                    completed_focus_sessions_last_week
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
            connection.commit()
            session = self._create_session_payload(cursor=cursor, user_id=user_id, user_row={
                "first_name": profile.account.first_name,
                "last_name": profile.account.last_name,
                "email": profile.account.email,
                "country": profile.account.country,
                "preferred_language": profile.account.preferred_language,
                "audience": payload["audience"],
                "role": profile.account.role,
                "permissions_granted": profile.permissions_granted,
            })
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
                SELECT
                    id,
                    first_name,
                    last_name,
                    email,
                    password_hash,
                    password_salt,
                    country,
                    preferred_language,
                    audience,
                    role,
                    permissions_granted
                FROM users
                WHERE email = %s
                """,
                (email,),
            )
            user = cursor.fetchone()
            if not user or not self._verify_password(password, user["password_hash"], user["password_salt"]):
                raise ValueError("Invalid email or password.")

            if language and language != user["preferred_language"]:
                cursor.execute(
                    "UPDATE users SET preferred_language = %s WHERE id = %s",
                    (language, user["id"]),
                )
                user["preferred_language"] = language

            session = self._create_session_payload(cursor=cursor, user_id=user["id"], user_row=user)
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
                    s.user_id,
                    s.session_token,
                    s.expires_at,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.country,
                    u.preferred_language,
                    u.audience,
                    u.role,
                    u.permissions_granted
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

    def load_profile(self, email: str) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.country,
                    u.preferred_language,
                    u.role,
                    u.permissions_granted,
                    u.audience,
                    b.daily_notifications,
                    b.social_media_hours,
                    b.sleep_hours,
                    b.planning_consistency,
                    b.completed_focus_sessions_last_week
                FROM users AS u
                JOIN behavior_profiles AS b ON b.user_id = u.id
                WHERE u.email = %s
                """,
                (email,),
            )
            row = cursor.fetchone()
            if not row:
                return None

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
        finally:
            connection.close()

    def load_profile_by_user_id(self, user_id: int) -> UserProfile | None:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT
                    u.id,
                    u.first_name,
                    u.last_name,
                    u.email,
                    u.country,
                    u.preferred_language,
                    u.role,
                    u.permissions_granted,
                    u.audience,
                    b.daily_notifications,
                    b.social_media_hours,
                    b.sleep_hours,
                    b.planning_consistency,
                    b.completed_focus_sessions_last_week
                FROM users AS u
                JOIN behavior_profiles AS b ON b.user_id = u.id
                WHERE u.id = %s
                """,
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return self._user_profile_from_row(row)
        finally:
            connection.close()

    def update_profile(self, user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                UPDATE users
                SET
                    first_name = %s,
                    last_name = %s,
                    country = %s,
                    preferred_language = %s,
                    audience = %s,
                    role = %s,
                    permissions_granted = %s
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
                SELECT
                    id,
                    first_name,
                    last_name,
                    email,
                    country,
                    preferred_language,
                    audience,
                    role,
                    permissions_granted
                FROM users
                WHERE id = %s
                """,
                (user_id,),
            )
            user = cursor.fetchone()
            connection.commit()
            return self._session_payload(user_id=user_id, user_row=user, token=payload.get("token"))
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
            steps = row["steps_json"] if isinstance(row["steps_json"], list) else loads(row["steps_json"])
            return FocusPlan(
                generated_at=row["updated_at"].replace(tzinfo=timezone.utc).isoformat()
                if row["updated_at"].tzinfo is None
                else row["updated_at"].astimezone(timezone.utc).isoformat(),
                title=row["title"],
                recommended_session_minutes=int(row["recommended_session_minutes"]),
                focus_theme=row["focus_theme"],
                steps=steps,
                attention_game=row["attention_game"],
            )
        finally:
            connection.close()

    def save_focus_plan(self, user_id: int, plan: FocusPlan) -> FocusPlan:
        connection = self._connection(database=self.config.database)
        try:
            cursor = connection.cursor()
            self._upsert_focus_plan(cursor=cursor, user_id=user_id, plan=plan)
            connection.commit()
            return self.load_focus_plan(user_id) or plan
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
        mapping = {
            "student": "teen",
            "young-adult": "young_adult",
            "child": "child",
        }
        return mapping.get(audience, "teen")

    def _create_session_payload(self, cursor, user_id: int, user_row: dict[str, Any]) -> dict[str, Any]:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=self.config.session_ttl_hours)
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        cursor.execute(
            """
            INSERT INTO user_sessions (user_id, session_token, expires_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, token, expires_at.replace(tzinfo=None)),
        )
        return self._session_payload(user_id=user_id, user_row=user_row, token=token)

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
            (
                user_id,
                plan.title,
                plan.recommended_session_minutes,
                plan.focus_theme,
                dumps(plan.steps),
                plan.attention_game,
            ),
        )

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
