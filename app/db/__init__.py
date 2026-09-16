import aiosqlite
import os
import json

DB_PATH = os.getenv("DATABASE_PATH", "/app/app/db/homelab.db")

def ensure_db_dir():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

async def get_db():
    ensure_db_dir()
    return aiosqlite.connect(DB_PATH)

async def init_db():
    ensure_db_dir()
    async with get_db() as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA foreign_keys=ON")

        await db.executescript("""
            CREATE TABLE IF NOT EXISTS data_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                config TEXT,
                secret_json TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS docker_url_overrides (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_source_id INTEGER NOT NULL,
                container_id TEXT NOT NULL,
                custom_url TEXT NOT NULL,
                display_name TEXT,
                FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE CASCADE,
                UNIQUE(data_source_id, container_id)
            );

            CREATE TABLE IF NOT EXISTS storage_mounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_source_id INTEGER,
                host_label TEXT NOT NULL,
                mount_path TEXT NOT NULL,
                filesystem_type TEXT DEFAULT 'auto',
                display_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY (data_source_id) REFERENCES data_sources(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS link_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                tab TEXT NOT NULL DEFAULT 'internal',
                display_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                icon_type TEXT DEFAULT 'emoji',
                icon_value TEXT NOT NULL,
                display_order INTEGER DEFAULT 0,
                is_visible INTEGER DEFAULT 1,
                FOREIGN KEY (group_id) REFERENCES link_groups(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        await db.commit()

        default_groups = [
            ("Monitoring", "internal", 0),
            ("Media", "internal", 1),
            ("Development", "internal", 2),
            ("Network", "internal", 3),
            ("Cloud / Services", "external", 0),
            ("Reference", "external", 1),
        ]

        for name, tab, order in default_groups:
            await db.execute(
                "INSERT OR IGNORE INTO link_groups (name, tab, display_order) VALUES (?, ?, ?)",
                (name, tab, order)
            )
        await db.commit()

async def is_setup_complete() -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "SELECT value FROM settings WHERE key = 'setup_complete'"
        )
        row = await cursor.fetchone()
        return row is not None and row[0] == "true"

async def mark_setup_complete():
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES ('setup_complete', 'true')"
        )
        await db.commit()
