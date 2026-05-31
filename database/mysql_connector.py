# database/mysql_connector.py
#
# MySQL connection pool for the Jarvis persistent memory system.
# Creates the database and tables automatically on first run.

import os
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling, Error as MySQLError
from dotenv import load_dotenv

load_dotenv()

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "jarvis_memory"),
}

_pool = None
_available = False


def _ensure_database():
    """Create the jarvis_memory database and required tables if they don't exist."""

    # Step 1 — connect WITHOUT a database to create it
    server_config = {k: v for k, v in MYSQL_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**server_config)
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{MYSQL_CONFIG['database']}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    conn.commit()
    conn.close()

    # Step 2 — connect TO the database and create tables
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            memory_key    VARCHAR(255)  NOT NULL,
            memory_value  TEXT          NOT NULL,
            category      VARCHAR(100)  DEFAULT 'personal',
            user_id       VARCHAR(100)  DEFAULT 'default',
            created_at    DATETIME      DEFAULT CURRENT_TIMESTAMP,
            updated_at    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_user_key (user_id, memory_key)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_logs (
            id            INT AUTO_INCREMENT PRIMARY KEY,
            action        VARCHAR(50)   NOT NULL,
            memory_key    VARCHAR(255)  NOT NULL,
            old_value     TEXT,
            new_value     TEXT,
            user_id       VARCHAR(100)  DEFAULT 'default',
            timestamp     DATETIME      DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    conn.commit()
    conn.close()


def initialize_mysql():
    """Create the connection pool.  Returns True on success."""
    global _pool, _available

    try:
        _ensure_database()

        _pool = pooling.MySQLConnectionPool(
            pool_name="jarvis_memory_pool",
            pool_size=5,
            pool_reset_session=True,
            **MYSQL_CONFIG,
        )

        _available = True
        print("MEMORY: MySQL connection pool initialized successfully.")
        return True

    except MySQLError as e:
        print(f"MEMORY ERROR: Could not connect to MySQL — {e}")
        print("MEMORY: The memory system will be unavailable this session.")
        _available = False
        return False


def is_available():
    """Check whether the MySQL pool is ready."""
    return _available


@contextmanager
def get_mysql_connection():
    """Context manager that yields a pooled MySQL connection.

    Usage::

        with get_mysql_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(...)
    """
    if not _available or _pool is None:
        raise RuntimeError("MySQL is not available.")

    conn = _pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
