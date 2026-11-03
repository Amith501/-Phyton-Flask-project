"""SQLite data layer for the Spendly application.

Provides:
    get_db()       — a connection with dict-like rows and FK enforcement
    init_db()      — creates the users and expenses tables (idempotent)
    seed_db()      — inserts one demo user + 8 sample expenses, once only
"""

import os
import sqlite3

from werkzeug.security import generate_password_hash

# Fixed expense categories used throughout the app.
CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]

# Path to the database file, in the project root (parent of the database/ package).
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "spendly.db")


def get_db():
    """Open a connection to spendly.db with row_factory and foreign keys on."""
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def init_db():
    """Create the users and expenses tables if they do not already exist.

    Safe to call repeatedly — uses CREATE TABLE IF NOT EXISTS.
    """
    db = get_db()
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at    TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            amount      REAL NOT NULL,
            category    TEXT NOT NULL,
            date        TEXT NOT NULL,
            description TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        )
        """
    )
    db.commit()
    db.close()


def seed_db():
    """Insert one demo user and 8 sample expenses.

    Returns early if the users table already contains data, so repeated
    calls never duplicate records.
    """
    db = get_db()
    existing = db.execute("SELECT id FROM users LIMIT 1").fetchone()
    if existing:
        db.close()
        return

    demo_password = generate_password_hash("demo123")
    cursor = db.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", demo_password),
    )
    user_id = cursor.lastrowid

    today = "2026-11-03"
    expenses = [
        (user_id, 12.50, "Food", today, "Lunch with team"),
        (user_id, 45.00, "Transport", "2026-11-02", "Monthly bus pass"),
        (user_id, 89.99, "Bills", "2026-11-01", "Electricity bill"),
        (user_id, 30.00, "Health", "2026-11-03", "Pharmacy"),
        (user_id, 55.00, "Entertainment", "2026-11-02", "Movie night"),
        (user_id, 120.00, "Shopping", "2026-11-01", "New shoes"),
        (user_id, 25.00, "Other", "2026-11-03", "Donation"),
        (user_id, 8.75, "Food", "2026-11-03", "Coffee"),
    ]
    db.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        expenses,
    )

    db.commit()
    db.close()