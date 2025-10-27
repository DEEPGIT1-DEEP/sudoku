from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3

app = FastAPI(title="Sudoku Score API")

# -------- Enable CORS --------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update to your frontend domain later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Database Setup --------
def init_db():
    conn = sqlite3.connect("scores.db")
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


init_db()


# -------- Models --------
class ScoreData(BaseModel):
    player_name: str
    score: int


# -------- Endpoints --------
@app.post("/submit_score")
def submit_score(data: ScoreData):
    """Store a new Sudoku score"""
    conn = sqlite3.connect("scores.db")
    cur = conn.cursor()
    cur.execute("INSERT INTO scores (player_name, score) VALUES (?, ?)", (data.player_name, data.score))
    conn.commit()
    conn.close()
    return {"message": f"✅ Score of {data.score} saved for {data.player_name}"}


@app.get("/highscore")
def get_highscore():
    """Fetch top 10 unique players with their highest scores"""
    conn = sqlite3.connect("scores.db")
    cur = conn.cursor()

    # ✅ Get highest score per player (unique)
    cur.execute("""
        SELECT player_name, MAX(score) as max_score, MAX(timestamp)
        FROM scores
        GROUP BY player_name
        ORDER BY max_score DESC
        LIMIT 10
    """)
    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail="No scores found.")

    results = [
        {"rank": i + 1, "player_name": row[0], "score": row[1], "timestamp": row[2]}
        for i, row in enumerate(rows)
    ]

    return {"top_10_scores": results}


@app.delete("/delete_player/{player_name}")
def delete_player(player_name: str):
    """Delete a player and all their scores"""
    conn = sqlite3.connect("scores.db")
    cur = conn.cursor()

    # Check if player exists
    cur.execute("SELECT COUNT(*) FROM scores WHERE player_name = ?", (player_name,))
    count = cur.fetchone()[0]

    if count == 0:
        conn.close()
        raise HTTPException(status_code=404, detail=f"❌ Player '{player_name}' not found in database.")

    # Delete player
    cur.execute("DELETE FROM scores WHERE player_name = ?", (player_name,))
    conn.commit()
    conn.close()

    return {"message": f"🗑️ Player '{player_name}' and all their scores have been deleted successfully."}


@app.get("/")
def home():
    return {
        "message": "🎮 Sudoku Score API is running!",
        "usage": {
            "POST /submit_score": {"player_name": "Deepak", "score": 450},
            "GET /highscore": "Returns top 10 unique players with their highest scores",
            "DELETE /delete_player/{player_name}": "Deletes a specific player and their scores"
        }
    }
