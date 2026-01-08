import pandas as pd
from app import app
from models import db, Match, Team

CSV_PATH = "games.csv"

with app.app_context():
    df = pd.read_csv(CSV_PATH)
    df["game_date"] = pd.to_datetime(
        df["game_date"],
        format="mixed",
        errors="coerce"
    )
    df = df.dropna(subset=["game_date"])
    df = df.sort_values("game_date", ascending=False)
    df = df.head(2000)

    for _, row in df.iterrows():
        if not Team.query.get(row["team_id_home"]):
            continue
        if not Team.query.get(row["team_id_away"]):
            continue

        match = Match(
            home_team_id=int(row["team_id_home"]),
            away_team_id=int(row["team_id_away"]),
            date=row["game_date"],
            home_score=int(row["pts_home"]),
            away_score=int(row["pts_away"])
        )
        db.session.add(match)

    db.session.commit()

print("NBA matches imported successfully")