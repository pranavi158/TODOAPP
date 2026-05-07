from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from enum import Enum

db = SQLAlchemy()

class PriorityLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key = True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(300), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    priority = db.Column(db.Enum(PriorityLevel), default=PriorityLevel.MEDIUM, nullable=False)
    deadline_date = db.Column(db.Date, nullable=True)
    premium = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))