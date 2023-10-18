from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()


class Battle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    select_poke = db.Column(db.String(100), nullable=False)
    opponent_poke = db.Column(db.String(100), nullable=False)
    select_is_win = db.Column(db.Boolean, nullable=False)
    quanity_rounds = db.Column(db.Integer, nullable=False)    
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now())
