from flask_sqlalchemy import SQLAlchemy
from enum import Enum
class AssetStatus(Enum):
    FINE = "Fine"
    DAMAGED = "Damaged"
    LOST = "Lost"

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), nullable=False)

    transactions = db.relationship('Transaction', backref='user', lazy=True)

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.String(4), default='2025')
    total_fund = db.Column(db.Float, default=0.0)
    remaining_fund = db.Column(db.Float, default=0.0)

    transactions = db.relationship('Transaction', backref='budget', lazy=True)

class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), default='Storage')
    status = db.Column(db.Enum(AssetStatus), default=AssetStatus.FINE, nullable=False)
    count = db.Column(db.Integer, nullable=False)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cost = db.Column(db.Float, nullable=False) # amount
    note = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    author = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    budget_id = db.Column(db.Integer, db.ForeignKey('budget.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True) # receipt
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    parent_id = db.Column(db.String(100), nullable=True)  # e.g., could be linked to Transaction or Event

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(300), nullable=True)
    date = db.Column(db.DateTime, nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)

class ActionLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=True)
    action = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

