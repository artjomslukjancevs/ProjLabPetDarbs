import pandas as pd
from app import app
from models import db, Team

CSV_PATH = "data/teams.csv"

with app.app_context():
    df = pd.read_csv(CSV_PATH)

    for _, row in df.iterrows():
        team = Team(
            team_id=int(row["id"]),
            full_name=row["full_name"],
            abbreviation=row["abbreviation"],
            nickname=row["nickname"],
            city=row["city"],
            state=row["state"],
            year_founded=int(row["year_founded"]),
            league="NBA"
        )
        db.session.merge(team)

    db.session.commit()

print("NBA teams imported successfully")
