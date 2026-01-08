import sys
import os
import pandas as pd
from collections import defaultdict, deque

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(BASE_DIR)

from app import app
from models import Match

ROLLING_N = 5
ELO_START = 1500
K_FACTOR = 20


def build_dataset():
    with app.app_context():
        matches = Match.query.order_by(Match.date).all()
        history = defaultdict(lambda: deque(maxlen=ROLLING_N))
        elo = defaultdict(lambda: ELO_START)
        home_history = defaultdict(lambda: deque(maxlen=ROLLING_N))
        away_history = defaultdict(lambda: deque(maxlen=ROLLING_N))

        data = []

        for m in matches:
            home_id = m.home_team_id
            away_id = m.away_team_id

            home_elo = elo[home_id]
            away_elo = elo[away_id]
            elo_diff = home_elo - away_elo

            if len(history[home_id]) == ROLLING_N and len(history[away_id]) == ROLLING_N:
                def stats(hist):
                    games = len(hist)
                    wins = sum(1 for g in hist if g["win"])
                    points = sum(g["points"] for g in hist)
                    return games, wins, points

                hg, hw, hp = stats(history[home_id])
                ag, aw, ap = stats(history[away_id])

                hhg, hhw, _ = stats(home_history[home_id])
                aag, aaw, _ = stats(away_history[away_id])

                data.append({
                    "home_avg_pts_last_5": hp / hg,
                    "home_winrate_last_5": hw / hg,
                    "home_home_winrate_last_5": (hhw / hhg) if hhg else 0,
                    "home_home_games_last_5": hhg,

                    "away_avg_pts_last_5": ap / ag,
                    "away_winrate_last_5": aw / ag,
                    "away_away_winrate_last_5": (aaw / aag) if aag else 0,
                    "away_away_games_last_5": aag,

                    "home_elo": home_elo,
                    "away_elo": away_elo,
                    "elo_diff": elo_diff,


                    "label": 1 if m.home_score > m.away_score else 0
                })

            expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
            result_home = 1 if m.home_score > m.away_score else 0

            elo[home_id] += K_FACTOR * (result_home - expected_home)
            elo[away_id] += K_FACTOR * ((1 - result_home) - (1 - expected_home))

            history[home_id].append({
                "points": m.home_score,
                "win": m.home_score > m.away_score
            })

            history[away_id].append({
                "points": m.away_score,
                "win": m.away_score < m.home_score
            })

            home_history[home_id].append({
                "points": m.home_score,
                "win": m.home_score > m.away_score
            })

            away_history[away_id].append({
                "points": m.away_score,
                "win": m.away_score < m.home_score
            })

        return pd.DataFrame(data)

if __name__ == "__main__":
    df = build_dataset()
    df.to_csv("ml/dataset.csv", index=False)
    print("Dataset created:", df.shape)