from settings import db, bcrypt
from flask_login import UserMixin


class Battle(db.Model):
    __tablename__ = 'battles'
    __fields__ = ['id', 'user_id', 'select_poke', 'opponent_poke', 'select_is_win', 'quanity_rounds', 'created_at']

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", back_populates="battles")

    select_poke = db.Column(db.String(100), nullable=False)
    opponent_poke = db.Column(db.String(100), nullable=False)
    select_is_win = db.Column(db.Boolean, nullable=False)
    quanity_rounds = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now())

    def __init__(self, select_poke, opponent_poke, select_is_win, quanity_rounds, user_id=None, created_at=None):
        super().__init__()
        self.select_poke = select_poke,
        self.opponent_poke = opponent_poke
        self.select_is_win = select_is_win
        self.quanity_rounds = quanity_rounds
        if user_id:
            self.user_id = user_id
        if created_at:
            self.created_at = created_at

    def __repr__(self):
        return '<Battle: id=%s, user_id=%s, select_poke=%s, opponent_poke=%s, select_is_win=%s, quanity_rounds=%s, created_at=%s>' \
               % (self.id, self.user_id, self.select_poke, self.opponent_poke, self.select_is_win,
                  self.quanity_rounds, self.created_at)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    __fields__ = ['id', 'name', 'email', 'password', 'created_on', 'updated_on']

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now())
    updated_on = db.Column(db.DateTime(timezone=True), nullable=False, default=db.func.now(), onupdate=db.func.now())

    battles = db.relationship('Battle', back_populates='user', lazy=True)

    def __init__(self, name, email, password):
        super().__init__()
        self.name = name
        self.email = email
        self.password = self.get_password_hash(password)

    def __repr__(self):
        return '<User: id=%s, name=%s, email=%s, created_on==%s, updated_on==%s>' \
            % (self.id, self.name, self.email, self.created_on, self.updated_on)
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password, password)

    def get_password_hash(self, password):
        return bcrypt.generate_password_hash(password).decode('utf-8')
