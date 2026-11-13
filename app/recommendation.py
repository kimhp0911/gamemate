import json
from pathlib import Path
from app.database import get_connection

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sample_recommendations.json"

def load_sample_recommendations():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    with get_connection() as connection:
        for game in data["games"]:
            connection.execute(
                "INSERT OR IGNORE INTO games(id, name) VALUES (?, ?)",
                (game["id"], game["name"])
            )
        for rec in data.get("recommendations", []):
            connection.execute(
                """INSERT INTO recommendations
                (game_id, character_id, category, item_name, notes, source, game_version)
                SELECT ?, ?, ?, ?, ?, ?, ?
                WHERE NOT EXISTS (
                    SELECT 1 FROM recommendations
                    WHERE game_id=? AND character_id=? AND category=? AND item_name=?
                )""",
                (
                    rec["game_id"], rec["character_id"], rec["category"],
                    rec["item_name"], rec.get("notes", ""),
                    rec.get("source", "sample"), rec.get("game_version", ""),
                    rec["game_id"], rec["character_id"], rec["category"], rec["item_name"]
                )
            )
