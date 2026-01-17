from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(80), unique = True, nullable = False)
    password_hash = db.Column(db.String(255), nullable = False)

    tasks = db.relationship('MovieTask', backref = 'owner', lazy = True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class MovieTask(db.Model):
    __tablename__ = "movie_tasks"

    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(255), nullable = False)
    year = db.Column(db.String(10))
    plot = db.Column(db.Text)
    category = db.Column(db.String(255), default = "General")
    status = db.Column(db.String(20), default = 'pending')
    imdb_rating = db.Column(db.String(20))
    poster_url = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    deleted_at = db.Column(db.DateTime, nullable = True)
    trailer_link = db.Column(db.Text)
    

    def to_dict(self):
        return {
            'id' : self.id,
            'title' : self.title,
            'year' : self.year,
            'plot' : self.plot,
            'category' : self.category,
            'status': self.status,
            'imdb_rating' : self.imdb_rating,
            'poster_url' : self.poster_url,
            'trailer_link' : self.trailer_link
        }
