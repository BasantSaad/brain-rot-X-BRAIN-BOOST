from __future__ import annotations

import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass
from typing import Any

from shared.schemas import AccountProfile, UserProfile

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
            return self._session_payload(user_id=user_id, user_row={
                "first_name": profile.account.first_name,
                "last_name": profile.account.last_name,
                "email": profile.account.email,
                "country": profile.account.country,
                "preferred_language": profile.account.preferred_language,
                "audience": payload["audience"],
                "role": profile.account.role,
                "permissions_granted": profile.permissions_granted,
            })
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
                connection.commit()
                user["preferred_language"] = language

            return self._session_payload(user_id=user["id"], user_row=user)
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

    def _session_payload(self, user_id: int, user_row: dict[str, Any]) -> dict[str, Any]:
        return {
            "user_id": user_id,
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
