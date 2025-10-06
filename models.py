from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class CaseSearch(db.Model):
    __tablename__ = 'case_searches'
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(100), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    court_type = db.Column(db.String(20), nullable=False)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    raw_response_path = db.Column(db.String(500))
    details = db.relationship('CaseDetail', backref='search', uselist=False, cascade='all, delete-orphan')

class CaseDetail(db.Model):
    __tablename__ = 'case_details'
    id = db.Column(db.Integer, primary_key=True)
    search_id = db.Column(db.Integer, db.ForeignKey('case_searches.id'), nullable=False)
    cnr_number = db.Column(db.String(50))
    filing_number = db.Column(db.String(100))
    registration_number = db.Column(db.String(100))
    filing_date = db.Column(db.Date)
    registration_date = db.Column(db.Date)
    case_status = db.Column(db.String(100))
    is_disposed = db.Column(db.Boolean, default=False)
    next_hearing_date = db.Column(db.Date)
    court_name = db.Column(db.String(200))
    judge_name = db.Column(db.String(200))
    parties = db.relationship('Party', backref='case', lazy=True, cascade='all, delete-orphan')
    orders = db.relationship('CourtOrder', backref='case', lazy=True, cascade='all, delete-orphan')

class Party(db.Model):
    __tablename__ = 'parties'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case_details.id'), nullable=False)
    party_type = db.Column(db.String(50))
    name = db.Column(db.String(200), nullable=False)
    advocate_name = db.Column(db.String(200))

class CourtOrder(db.Model):
    __tablename__ = 'court_orders'
    id = db.Column(db.Integer, primary_key=True)
    case_id = db.Column(db.Integer, db.ForeignKey('case_details.id'), nullable=False)
    order_date = db.Column(db.Date)
    order_type = db.Column(db.String(100))
    order_text = db.Column(db.Text)
    pdf_url = db.Column(db.String(500))
    local_pdf_path = db.Column(db.String(500))
    downloaded = db.Column(db.Boolean, default=False)
