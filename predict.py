import joblib
from collections import defaultdict, deque
from models import Match

ROLLING_N = 5
ELO_START = 1500
K_FACTOR = 20

model = joblib.load("model.pkl")

def predict_future_match(home_team_id, away_team_id):
    matches = Match.query.order_by(Match.date).all()

    history = defaultdict(lambda: deque(maxlen=ROLLING_N))
    home_history = defaultdict(lambda: deque(maxlen=ROLLING_N))
    away_history = defaultdict(lambda: deque(maxlen=ROLLING_N))
    elo = defaultdict(lambda: ELO_START)

    for m in matches:
        hid, aid = m.home_team_id, m.away_team_id

        home_elo = elo[hid]
        away_elo = elo[aid]

        expected_home = 1 / (1 + 10 ** ((away_elo - home_elo) / 400))
        result_home = 1 if m.home_score > m.away_score else 0

        elo[hid] += K_FACTOR * (result_home - expected_home)
        elo[aid] += K_FACTOR * ((1 - result_home) - (1 - expected_home))

        history[hid].append({"points": m.home_score, "win": m.home_score > m.away_score})
        history[aid].append({"points": m.away_score, "win": m.away_score < m.home_score})

        home_history[hid].append({"points": m.home_score, "win": m.home_score > m.away_score})
        away_history[aid].append({"points": m.away_score, "win": m.away_score < m.home_score})

    if len(history[home_team_id]) < ROLLING_N or len(history[away_team_id]) < ROLLING_N:
        return None

    def stats(hist):
        games = len(hist)
        wins = sum(1 for g in hist if g["win"])
        points = sum(g["points"] for g in hist)
        return games, wins, points

    hg, hw, hp = stats(history[home_team_id])
    hhg, hhw, _ = stats(home_history[home_team_id])
    ag, aw, ap = stats(history[away_team_id])
    aag, aaw, _ = stats(away_history[away_team_id])

    home_elo = elo[home_team_id]
    away_elo = elo[away_team_id]
    elo_diff = home_elo - away_elo

    import pandas as pd

    X = pd.DataFrame([{
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
        "elo_diff": elo_diff
    }])

    prob_home = model.predict_proba(X)[0][1]
    prob_home = max(min(prob_home, 0.999), 0.001)

    return {
        "home_win_probability": round(prob_home, 3),
        "away_win_probability": round(1 - prob_home, 3),
        "home_odds": round(1 / prob_home, 2),
        "away_odds": round(1 / (1 - prob_home), 2)
    }
