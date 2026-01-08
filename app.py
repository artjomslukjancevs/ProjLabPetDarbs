import os
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from models import db, Team, Match, FutureMatch
from ml.predict import predict_future_match
from flask import render_template
from models import UserPrediction

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

from sqlalchemy.orm import aliased
from models import UserPrediction

@app.route("/", methods=["GET"])
def index():
    matches = Match.query.order_by(Match.date.desc()).limit(20).all()
    matches_data = [{
        "date": m.date.strftime("%Y-%m-%d"),
        "home": Team.query.get(m.home_team_id).abbreviation,
        "away": Team.query.get(m.away_team_id).abbreviation
    } for m in matches]

    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)

    future_matches = (
        db.session.query(FutureMatch, HomeTeam, AwayTeam)
        .join(HomeTeam, FutureMatch.home_team_id == HomeTeam.team_id)
        .join(AwayTeam, FutureMatch.away_team_id == AwayTeam.team_id)
        .order_by(FutureMatch.date.asc())
        .limit(10)
        .all()
    )

    user_history = UserPrediction.query.order_by(UserPrediction.created_at.desc()).limit(5).all()


    return render_template(
    "index.html",
    matches=matches_data,
    future_matches=future_matches,
    prediction=None,
    home_team_name=None,
    away_team_name=None,
    user_history=user_history
)


@app.route("/api/matches")
def api_matches():
    matches = Match.query.order_by(Match.date.desc()).limit(20).all()
    return [{
        "id": m.match_id,
        "date": m.date.strftime("%Y-%m-%d"),
        "home": Team.query.get(m.home_team_id).abbreviation,
        "away": Team.query.get(m.away_team_id).abbreviation
    } for m in matches]

@app.route("/debug/db")
def debug_db():
    return {
        "teams": Team.query.count(),
        "matches": Match.query.count()
    }

@app.route("/api/predict/<int:match_id>")
def api_predict(match_id):
    match = Match.query.get(match_id)
    if not match:
        return {"error": "Match not found"}, 404

    result = predict_future_match(match.home_team_id, match.away_team_id)
    if result is None:
        return {"error": "Not enough historical data"}, 400

    home_team = Team.query.get(match.home_team_id)
    away_team = Team.query.get(match.away_team_id)

    return {
        "home_team": home_team.full_name,
        "away_team": away_team.full_name,
        **result
    }


from sqlalchemy.orm import aliased

@app.route("/api/predict/custom", methods=["POST"])
def api_predict_custom():
    home_team_name = request.form.get("home_team")
    away_team_name = request.form.get("away_team")

    home_team = Team.query.filter_by(full_name=home_team_name).first()
    away_team = Team.query.filter_by(full_name=away_team_name).first()

    if not home_team or not away_team:
        return {"error": "Invalid team names"}, 400

    prediction = predict_future_match(home_team.team_id, away_team.team_id)

    HomeTeam = aliased(Team)
    AwayTeam = aliased(Team)

    future_matches = (
        db.session.query(FutureMatch, HomeTeam, AwayTeam)
        .join(HomeTeam, FutureMatch.home_team_id == HomeTeam.team_id)
        .join(AwayTeam, FutureMatch.away_team_id == AwayTeam.team_id)
        .order_by(FutureMatch.date.asc())
        .limit(10)
        .all()
    )

    history_entry = UserPrediction(
    home_team=home_team.full_name,
    away_team=away_team.full_name,
    home_win_probability=prediction["home_win_probability"],
    away_win_probability=prediction["away_win_probability"],
    home_odds=prediction["home_odds"],
    away_odds=prediction["away_odds"]
)

    db.session.add(history_entry)
    db.session.commit()


    history = UserPrediction.query.order_by(UserPrediction.created_at.desc()).limit(5).all()

    return render_template(
    "index.html",
    prediction=prediction,
    home_team_name=home_team.full_name,
    away_team_name=away_team.full_name,
    future_matches=future_matches,
    user_history=history
    )


if __name__ == "__main__":
    app.run(debug=True)
