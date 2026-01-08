import requests
from datetime import datetime, timedelta
from app import app, db
from models import Team, FutureMatch
from predict import predict_future_match

API_KEY = "4a1ec037-551c-43eb-b6f7-0457cbc834a4"
API_URL = "https://api.balldontlie.io/v1/games"

DAYS_AHEAD = 60
LIMIT = 10


def fetch_future_games():
    today = datetime.utcnow().date()
    end_date = today + timedelta(days=DAYS_AHEAD)

    headers = {"Authorization": API_KEY}
    params = {
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d"),
        "per_page": 100
    }

    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()

    return response.json()["data"]


def save_future_matches():
    games = fetch_future_games()
    saved = 0

    for game in games:
        if game["status"] == "Final":
            continue

        home_name = game["home_team"]["full_name"]
        away_name = game["visitor_team"]["full_name"]
        game_date = datetime.fromisoformat(game["date"])

        home_team = Team.query.filter_by(full_name=home_name).first()
        away_team = Team.query.filter_by(full_name=away_name).first()

        if not home_team or not away_team:
            continue

        exists = FutureMatch.query.filter_by(
            home_team_id=home_team.team_id,
            away_team_id=away_team.team_id,
            date=game_date
        ).first()

        if exists:
            continue

        prediction = predict_future_match(
            home_team.team_id,
            away_team.team_id
        )

        if not prediction:
            continue

        fm = FutureMatch(
            home_team_id=home_team.team_id,
            away_team_id=away_team.team_id,
            date=game_date,
            home_win_probability=prediction["home_win_probability"],
            away_win_probability=prediction["away_win_probability"],
            home_odds=prediction["home_odds"],
            away_odds=prediction["away_odds"]
        )

        db.session.add(fm)
        saved += 1

        if saved >= LIMIT:
            break

    db.session.commit()
    print(f"✅ Saved {saved} future matches to database")


if __name__ == "__main__":
    with app.app_context():
        print("Fetching & saving future NBA matches...")
        save_future_matches()