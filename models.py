from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Team(db.Model):
    team_id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    abbreviation = db.Column(db.String(5))
    nickname = db.Column(db.String(50))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    year_founded = db.Column(db.Integer)
    league = db.Column(db.String(10), default="NBA")


class Match(db.Model):
    match_id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    away_team_id = db.Column(db.Integer, db.ForeignKey('team.team_id'))
    date = db.Column(db.DateTime)
    home_score = db.Column(db.Integer)
    away_score = db.Column(db.Integer)


class Prediction(db.Model):
    prediction_id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.match_id'))
    predicted_winner = db.Column(db.String(100))
    win_probability = db.Column(db.Float)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)

class FutureMatch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    home_team_id = db.Column(db.Integer, nullable=False)
    away_team_id = db.Column(db.Integer, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    home_win_probability = db.Column(db.Float)
    away_win_probability = db.Column(db.Float)
    home_odds = db.Column(db.Float)
    away_odds = db.Column(db.Float)

class UserPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    home_team = db.Column(db.String(100))
    away_team = db.Column(db.String(100))

    home_win_probability = db.Column(db.Float)
    away_win_probability = db.Column(db.Float)

    home_odds = db.Column(db.Float)
    away_odds = db.Column(db.Float)
