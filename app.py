from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
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

    def to_dict(self):
        return {
            'id': self.id,
            'case_type': self.case_type,
            'case_number': self.case_number,
            'case_year': self.case_year,
            'court_type': self.court_type,
            'party_names': self.party_names,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'next_hearing_date': self.next_hearing_date.isoformat() if self.next_hearing_date else None,
            'case_status': self.case_status,
            'created_at': self.created_at.isoformat()
        }

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_case():
    data = request.get_json()
    
    # Basic validation
    if not all(k in data for k in ['court_type', 'case_type', 'case_number', 'case_year']):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # For now, return a mock response
    # In the next step, we'll implement actual database search
    mock_case = {
        'case_type': data['case_type'],
        'case_number': data['case_number'],
        'case_year': data['case_year'],
        'court_type': data['court_type'],
        'party_names': 'Sample Petitioner vs. Sample Respondent',
        'filing_date': '2023-01-15',
        'next_hearing_date': '2023-11-10',
        'case_status': 'Pending',
        'is_mock': True
    }
    
    return jsonify(mock_case)

# Add a route to view all cases (for testing)
@app.route('/cases')
def view_cases():
    cases = Case.query.all()
    return jsonify([case.to_dict() for case in cases])

if __name__ == '__main__':
    app.run(debug=True)