from fastapi import FastAPI
from pydantic import BaseModel
import random
import sqlite3

app = FastAPI(title="Yahtzee Mini API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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


c.execute("SELECT COUNT(*) FROM transactions")
if c.fetchone()[0] == 0:
    c.execute("INSERT INTO transactions (value, type) VALUES (?, ?)", (100, "Init"))
    conn.commit()


class RollRequest(BaseModel):
    bet: int


def get_balance():
    c.execute("SELECT SUM(value) FROM transactions")
    result = c.fetchone()[0]
    return result if result else 0


from collections import Counter

def check_combination(dice):
    counts = Counter(dice)
    values = sorted(counts.values(), reverse=True)

    if values == [6]:  
        return "Yahtzee", 8
    if values == [4, 2]:
        return "4+2", 3
    if values.count(2) == 3:
        return "Three Pairs", 2
    if any(v >= 2 for v in values):
        return "Pair", 0.9
    return None, 0

def simulate_roll(bet):
    dice = [random.randint(1, 6) for _ in range(6)]
    combo, coef = check_combination(dice)
    win = int(bet * coef) if coef > 0 else 0
    return win


def test_rtp(iterations=100000, bet=10):
    total_bet = 0
    total_win = 0

    for _ in range(iterations):
        total_bet += bet
        total_win += simulate_roll(bet)

    rtp = (total_win / total_bet) * 100
    print(f"Simulated {iterations} rolls")
    print(f"Total Bet: {total_bet}, Total Win: {total_win}")
    print(f"RTP: {rtp:.2f}%")


@app.get("/balance")
def balance():
    return {"balance": get_balance()}

@app.post("/reset")
def reset_balance():
    c.execute("DELETE FROM transactions")
    c.execute("INSERT INTO transactions (value, type) VALUES (?, ?)", (100, "Init"))
    conn.commit()
    return {"balance": get_balance()}

@app.post("/roll")
def roll(data: RollRequest):
    bet = data.bet
    current_balance = get_balance()
    if bet > current_balance:
        raise HTTPException(status_code=400, detail="Not enough balance")
    if bet <= 0:
        raise HTTPException(status_code=400, detail="Bet must be > 0")

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

@app.get("/test_rtp")
def rtp_endpoint(iterations: int = 100000, bet: int = 10):
    total_bet = 0
    total_win = 0

    for _ in range(iterations):
        total_bet += bet
        total_win += simulate_roll(bet)

    rtp = (total_win / total_bet) * 100
    return {
        "simulated_rolls": iterations,
        "total_bet": total_bet,
        "total_win": total_win,
        "RTP": f"{rtp:.2f}%"
    }
