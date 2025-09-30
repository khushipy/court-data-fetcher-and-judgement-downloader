from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///court_cases.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'downloads'

# Initialize the database
db = SQLAlchemy(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database Models
class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    case_type = db.Column(db.String(50), nullable=False)
    case_number = db.Column(db.String(50), nullable=False)
    case_year = db.Column(db.Integer, nullable=False)
    court_type = db.Column(db.String(20), nullable=False)
    party_names = db.Column(db.Text)
    filing_date = db.Column(db.Date)
    next_hearing_date = db.Column(db.Date)
    case_status = db.Column(db.String(100))
    raw_response = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Routes
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This creates the database tables
    app.run(debug=True)  # This starts the Flask development server