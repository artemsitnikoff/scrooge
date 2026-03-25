import json
import os

import aiosqlite

from config import settings

_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), settings.db_path)


async def _connect() -> aiosqlite.Connection:
    db = aiosqlite.connect(_DB_PATH)
    conn = await db
    conn.row_factory = aiosqlite.Row
    await conn.execute("PRAGMA journal_mode=WAL")
    return conn


async def init_db() -> None:
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = await _connect()
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                access_key TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(telegram_id),
                name TEXT NOT NULL,
                object_id TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_db_id INTEGER NOT NULL REFERENCES objects(id),
                user_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                activated_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                payment_id TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                email TEXT UNIQUE,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS otp_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                code TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                used INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS web_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                yukassa_payment_id TEXT UNIQUE NOT NULL,
                user_id INTEGER NOT NULL,
                object_db_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                amount INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_db_id INTEGER NOT NULL REFERENCES objects(id),
                payload TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                attempts INTEGER DEFAULT 0,
                error TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await conn.commit()
    finally:
        await conn.close()


# --- users ---

async def ensure_user(telegram_id: int) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)", (telegram_id,)
        )
        await conn.commit()
    finally:
        await conn.close()


async def set_access_key(telegram_id: int, access_key: str) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "INSERT INTO users (telegram_id, access_key) VALUES (?, ?) "
            "ON CONFLICT(telegram_id) DO UPDATE SET access_key = ?",
            (telegram_id, access_key, access_key),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_access_key(telegram_id: int) -> str | None:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT access_key FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return row["access_key"] if row else None
    finally:
        await conn.close()


# --- objects ---

async def add_object(user_id: int, name: str, object_id: str) -> int:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "INSERT INTO objects (user_id, name, object_id) VALUES (?, ?, ?)",
            (user_id, name, object_id),
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def rename_object(pk: int, user_id: int, new_name: str) -> bool:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "UPDATE objects SET name = ? WHERE id = ? AND user_id = ?",
            (new_name, pk, user_id),
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()


async def get_objects(user_id: int) -> list[dict]:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT * FROM objects WHERE user_id = ? ORDER BY created_at", (user_id,)
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def get_object(pk: int) -> dict | None:
    conn = await _connect()
    try:
        cursor = await conn.execute("SELECT * FROM objects WHERE id = ?", (pk,))
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def delete_object(pk: int, user_id: int) -> bool:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "DELETE FROM objects WHERE id = ? AND user_id = ?", (pk, user_id)
        )
        await conn.commit()
        return cursor.rowcount > 0
    finally:
        await conn.close()


# --- subscriptions ---

async def activate_subscription(
    object_db_id: int, user_id: int, plan: str, payment_id: str | None = None
) -> dict:
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    # Если есть активная подписка — продлеваем от её конца
    current = await get_subscription(object_db_id)
    if current and current["expires_at"] > now.isoformat():
        base = datetime.fromisoformat(current["expires_at"])
    else:
        base = now

    days = 365 if plan == "year" else 30
    expires_at = base + timedelta(days=days)

    conn = await _connect()
    try:
        cursor = await conn.execute(
            """INSERT INTO subscriptions (object_db_id, user_id, plan, activated_at, expires_at, payment_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (object_db_id, user_id, plan, now.isoformat(), expires_at.isoformat(), payment_id),
        )
        await conn.commit()
        return {
            "id": cursor.lastrowid,
            "expires_at": expires_at.isoformat(),
        }
    finally:
        await conn.close()


async def get_subscription(object_db_id: int) -> dict | None:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT * FROM subscriptions
               WHERE object_db_id = ?
               ORDER BY expires_at DESC LIMIT 1""",
            (object_db_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def is_subscription_active(object_db_id: int) -> bool:
    from datetime import datetime

    sub = await get_subscription(object_db_id)
    if not sub:
        return False
    return sub["expires_at"] > datetime.utcnow().isoformat()


async def get_expiring_subscriptions(days: int = 3) -> list[dict]:
    """Подписки, истекающие в ближайшие N дней."""
    from datetime import datetime, timedelta

    now = datetime.utcnow().isoformat()
    deadline = (datetime.utcnow() + timedelta(days=days)).isoformat()

    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT s.*, o.name AS object_name, o.id AS obj_pk
               FROM subscriptions s
               JOIN objects o ON s.object_db_id = o.id
               WHERE s.expires_at > ? AND s.expires_at <= ?
               AND s.id = (
                   SELECT id FROM subscriptions s2
                   WHERE s2.object_db_id = s.object_db_id
                   ORDER BY s2.expires_at DESC LIMIT 1
               )""",
            (now, deadline),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def get_subscriptions_for_user(user_id: int) -> list[dict]:
    """Все объекты пользователя с информацией о подписке."""
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT o.id, o.name, o.object_id,
                      (SELECT expires_at FROM subscriptions s
                       WHERE s.object_db_id = o.id
                       ORDER BY s.expires_at DESC LIMIT 1) AS expires_at
               FROM objects o
               WHERE o.user_id = ?
               ORDER BY o.created_at""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


# --- queue ---

async def enqueue_records(object_db_id: int, records: list[dict]) -> int:
    conn = await _connect()
    try:
        await conn.executemany(
            "INSERT INTO queue (object_db_id, payload) VALUES (?, ?)",
            [(object_db_id, json.dumps(r, ensure_ascii=False)) for r in records],
        )
        await conn.commit()
        return len(records)
    finally:
        await conn.close()


async def get_pending_records(limit: int = 50) -> list[dict]:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT q.*, o.object_id, o.user_id, u.access_key
               FROM queue q
               JOIN objects o ON q.object_db_id = o.id
               JOIN users u ON o.user_id = u.telegram_id
               WHERE q.status IN ('pending', 'error')
                 AND q.attempts < ?
                 AND u.access_key IS NOT NULL
               ORDER BY q.created_at
               LIMIT ?""",
            (settings.max_retries, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def mark_record(record_id: int, status: str, error: str | None = None) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            """UPDATE queue
               SET status = ?, error = ?, attempts = attempts + 1,
                   updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (status, error, record_id),
        )
        await conn.commit()
    finally:
        await conn.close()


async def get_recent_errors(user_id: int, limit: int = 5) -> list[dict]:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT o.name, q.error, q.updated_at
               FROM queue q
               JOIN objects o ON q.object_db_id = o.id
               WHERE o.user_id = ? AND q.status = 'error' AND q.error IS NOT NULL
               ORDER BY q.updated_at DESC
               LIMIT ?""",
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


async def get_queue_stats(user_id: int) -> list[dict]:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT o.id, o.name, o.object_id,
                      COUNT(CASE WHEN q.status = 'pending' THEN 1 END) AS pending,
                      COUNT(CASE WHEN q.status = 'sending' THEN 1 END) AS sending,
                      COUNT(CASE WHEN q.status = 'sent' THEN 1 END) AS sent,
                      COUNT(CASE WHEN q.status = 'error' THEN 1 END) AS errors,
                      MAX(CASE WHEN q.status = 'sent' THEN q.updated_at END) AS last_sent
               FROM objects o
               LEFT JOIN queue q ON q.object_db_id = o.id
               WHERE o.user_id = ?
               GROUP BY o.id
               ORDER BY o.created_at""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        await conn.close()


# --- accounts (ЛК) ---

_SYNTHETIC_ID_BASE = 9_000_000_000


async def _next_synthetic_user_id() -> int:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT MAX(telegram_id) FROM users WHERE telegram_id >= ?",
            (_SYNTHETIC_ID_BASE,),
        )
        row = await cursor.fetchone()
        max_id = row[0]
        return (max_id + 1) if max_id else _SYNTHETIC_ID_BASE
    finally:
        await conn.close()


async def get_or_create_account_by_telegram(telegram_id: int) -> dict:
    await ensure_user(telegram_id)
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT * FROM accounts WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        await conn.execute(
            "INSERT INTO accounts (telegram_id) VALUES (?)", (telegram_id,)
        )
        await conn.commit()
        cursor = await conn.execute(
            "SELECT * FROM accounts WHERE telegram_id = ?", (telegram_id,)
        )
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await conn.close()


async def get_or_create_account_by_email(email: str) -> dict:
    email = email.lower().strip()
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT * FROM accounts WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        if row:
            return dict(row)
        # Создаём синтетического пользователя в users
        synthetic_id = await _next_synthetic_user_id()
        await conn.execute(
            "INSERT INTO users (telegram_id) VALUES (?)", (synthetic_id,)
        )
        await conn.execute(
            "INSERT INTO accounts (telegram_id, email) VALUES (?, ?)",
            (synthetic_id, email),
        )
        await conn.commit()
        cursor = await conn.execute(
            "SELECT * FROM accounts WHERE email = ?", (email,)
        )
        row = await cursor.fetchone()
        return dict(row)
    finally:
        await conn.close()


async def get_account(account_id: int) -> dict | None:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def get_user_id_for_account(account_id: int) -> int | None:
    account = await get_account(account_id)
    if not account:
        return None
    return account["telegram_id"]


# --- OTP ---

async def create_otp(email: str, code: str, expires_at: str) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "INSERT INTO otp_codes (email, code, expires_at) VALUES (?, ?, ?)",
            (email.lower().strip(), code, expires_at),
        )
        await conn.commit()
    finally:
        await conn.close()


async def verify_otp(email: str, code: str) -> bool:
    from datetime import datetime

    email = email.lower().strip()
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """SELECT id, expires_at FROM otp_codes
               WHERE email = ? AND code = ? AND used = 0
               ORDER BY created_at DESC LIMIT 1""",
            (email, code),
        )
        row = await cursor.fetchone()
        if not row:
            return False
        if row["expires_at"] < datetime.utcnow().isoformat():
            return False
        await conn.execute(
            "UPDATE otp_codes SET used = 1 WHERE id = ?", (row["id"],)
        )
        await conn.commit()
        return True
    finally:
        await conn.close()


# --- web_payments ---

async def create_web_payment(
    yukassa_payment_id: str, user_id: int, object_db_id: int, plan: str, amount: int
) -> int:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            """INSERT INTO web_payments (yukassa_payment_id, user_id, object_db_id, plan, amount)
               VALUES (?, ?, ?, ?, ?)""",
            (yukassa_payment_id, user_id, object_db_id, plan, amount),
        )
        await conn.commit()
        return cursor.lastrowid
    finally:
        await conn.close()


async def get_web_payment_by_yukassa_id(yukassa_payment_id: str) -> dict | None:
    conn = await _connect()
    try:
        cursor = await conn.execute(
            "SELECT * FROM web_payments WHERE yukassa_payment_id = ?",
            (yukassa_payment_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
    finally:
        await conn.close()


async def update_web_payment_status(yukassa_payment_id: str, status: str) -> None:
    conn = await _connect()
    try:
        await conn.execute(
            "UPDATE web_payments SET status = ? WHERE yukassa_payment_id = ?",
            (status, yukassa_payment_id),
        )
        await conn.commit()
    finally:
        await conn.close()
