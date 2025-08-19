from fastapi import FastAPI
from pydantic import BaseModel
import random
import sqlite3

app = FastAPI(title="Yahtzee Mini API")

# --- База SQLite ---
conn = sqlite3.connect("game.db", check_same_thread=False)
c = conn.cursor()
c.execute("""
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    value INTEGER,
    type TEXT
)
""")
conn.commit()

# Ініціалізація стартового балансу
c.execute("SELECT COUNT(*) FROM transactions")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO transactions (value, type) VALUES (?, ?)", (100, "Init"))
    conn.commit()

# --- Модель запиту ---
class RollRequest(BaseModel):
    bet: int

# --- Функція балансу ---
def get_balance():
    c.execute("SELECT SUM(value) FROM transactions")
    result = c.fetchone()[0]
    return result if result else 0

# --- Перевірка комбінацій ---
from collections import Counter

def check_combination(dice):
    counts = Counter(dice)
    values = sorted(counts.values(), reverse=True)

    if values == [6]:  # всі однакові
        return "Yahtzee", 10
    if values == [4, 2]:
        return "4+2", 2
    if values.count(2) == 3:
        return "Three Pairs", 3
    if 2 in values:
        return "Pair", 1.5
    return None, 0


# --- API endpoints ---
@app.get("/balance")
def balance():
    return {"balance": get_balance()}

@app.post("/roll")
def roll(data: RollRequest):
    bet = data.bet
    if bet <= 0:
        return {"error": "Bet must be > 0"}

    # Знімаємо ставку
    c.execute("INSERT INTO transactions (value, type) VALUES (?, ?)", (-bet, "Bet"))
    conn.commit()

    # Генеруємо кубики (6 штук)
    dice = [random.randint(1, 6) for _ in range(6)]

    # Перевіряємо комбінацію
    combo, coef = check_combination(dice)
    win = 0
    if coef > 0:
        win = int(bet * coef)
        c.execute("INSERT INTO transactions (value, type) VALUES (?, ?)", (win, "Win"))
        conn.commit()

    return {
        "dice": dice,
        "combination": combo,
        "win": win,
        "balance": get_balance()
    }
