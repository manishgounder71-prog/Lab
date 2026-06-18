import aiosqlite
import json
import logging
import os

logger = logging.getLogger("persistence_sqlite")

DB_PATH = os.getenv("SQLITE_PATH", os.path.join(os.path.dirname(__file__), "crisis_state.db"))


class SQLitePersistence:
    """Zero-dependency persistence using SQLite.
    Substitutes for RedisPersistence when Redis is not available."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.is_available = False

    async def initialize(self):
        try:
            self.conn = await aiosqlite.connect(self.db_path)
            self.conn.row_factory = aiosqlite.Row
            await self.conn.execute("PRAGMA journal_mode=WAL")
            await self.conn.execute("PRAGMA synchronous=NORMAL")
            await self._create_tables()
            self.is_available = True
            logger.info(f"SQLite persistence initialized at {self.db_path}")
            return True
        except Exception as e:
            logger.warning(f"SQLite persistence unavailable: {e}")
            self.is_available = False
            return False

    async def _create_tables(self):
        await self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                source TEXT NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS scenarios (
                scenario_id TEXT PRIMARY KEY,
                definition JSON NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS simulation_state (
                key TEXT PRIMARY KEY,
                value JSON NOT NULL,
                updated_at TEXT DEFAULT (datetime('now'))
            );
        """)
        await self.conn.commit()

    async def push_alert(self, alert: dict):
        if not self.is_available:
            return
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO alerts (id, timestamp, source, event_type, severity, title, description, status) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (alert["id"], alert["timestamp"], alert["source"], alert["event_type"],
                 alert["severity"], alert["title"], alert["description"], alert["status"])
            )
            await self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite push_alert failed: {e}")

    async def load_alerts(self) -> list:
        if not self.is_available:
            return []
        try:
            cursor = await self.conn.execute(
                "SELECT * FROM alerts ORDER BY timestamp DESC LIMIT 50"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.warning(f"SQLite load_alerts failed: {e}")
            return []

    async def save_scenario_definition(self, scenario_id: str, definition: dict):
        if not self.is_available:
            return
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO scenarios (scenario_id, definition) VALUES (?, ?)",
                (scenario_id, json.dumps(definition, default=str))
            )
            await self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite save_scenario failed: {e}")

    async def restore_dynamic_scenarios(self) -> dict:
        if not self.is_available:
            return {}
        try:
            cursor = await self.conn.execute(
                "SELECT scenario_id, definition FROM scenarios"
            )
            rows = await cursor.fetchall()
            result = {}
            for row in rows:
                try:
                    result[row["scenario_id"]] = json.loads(row["definition"])
                except json.JSONDecodeError:
                    continue
            return result
        except Exception as e:
            logger.warning(f"SQLite restore_scenarios failed: {e}")
            return {}

    async def save_full_state(self, scenario_id: str, state_payload: dict, sim_data: dict):
        if not self.is_available:
            return
        try:
            await self.conn.execute(
                "INSERT OR REPLACE INTO simulation_state (key, value) VALUES (?, ?)",
                ("active_scenario_id", json.dumps(scenario_id))
            )
            await self.conn.execute(
                "INSERT OR REPLACE INTO simulation_state (key, value) VALUES (?, ?)",
                ("state_payload", json.dumps(state_payload, default=str))
            )
            await self.conn.execute(
                "INSERT OR REPLACE INTO simulation_state (key, value) VALUES (?, ?)",
                ("sim_data", json.dumps(sim_data, default=str))
            )
            await self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite save_full_state failed: {e}")

    async def restore_state(self) -> tuple:
        if not self.is_available:
            return None, None, None
        try:
            cursor = await self.conn.execute(
                "SELECT key, value FROM simulation_state WHERE key IN ('active_scenario_id', 'state_payload', 'sim_data')"
            )
            rows = await cursor.fetchall()
            result = {row["key"]: row["value"] for row in rows}
            scenario_id = json.loads(result.get("active_scenario_id", "null"))
            state_payload = json.loads(result.get("state_payload", "null")) if result.get("state_payload") else None
            sim_data = json.loads(result.get("sim_data", "null")) if result.get("sim_data") else None
            return scenario_id, state_payload, sim_data
        except Exception as e:
            logger.warning(f"SQLite restore_state failed: {e}")
            return None, None, None

    async def clear_simulation(self, scenario_id: str):
        if not self.is_available:
            return
        try:
            await self.conn.execute("DELETE FROM simulation_state WHERE key LIKE 'sim_%' OR key IN ('active_scenario_id', 'state_payload', 'sim_data')")
            await self.conn.commit()
        except Exception as e:
            logger.warning(f"SQLite clear_simulation failed: {e}")

    async def close(self):
        if self.is_available:
            try:
                await self.conn.close()
            except Exception:
                pass
