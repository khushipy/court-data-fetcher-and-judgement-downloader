from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///court_cases.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)

# Models
class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cnr_number = db.Column(db.String(50), unique=True)
    filing_number = db.Column(db.String(50))
    filing_date = db.Column(db.DateTime)
    registration_number = db.Column(db.String(50))
    registration_date = db.Column(db.DateTime)
    status = db.Column(db.String(100))
    court_type = db.Column(db.String(50))
    state = db.Column(db.String(50))
    case_type = db.Column(db.String(50))
    year = db.Column(db.Integer)
    parties = db.Column(db.Text)  # JSON string of parties
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'cnr_number': self.cnr_number,
            'filing_number': self.filing_number,
            'filing_date': self.filing_date.isoformat() if self.filing_date else None,
            'registration_number': self.registration_number,
            'registration_date': self.registration_date.isoformat() if self.registration_date else None,
            'status': self.status,
            'court_type': self.court_type,
            'state': self.state,
            'case_type': self.case_type,
            'year': self.year,
            'parties': json.loads(self.parties) if self.parties else [],
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Routes
@app.route('/api/search', methods=['POST'])
def search_cases():
    try:
        data = request.get_json()
        
        # Basic validation
        required_fields = ['state', 'case_type', 'case_number', 'year']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Build query
        query = Case.query.filter(
            Case.state == data['state'],
            Case.case_type == data['case_type'],
            Case.year == int(data['year'])
        )
        
        # Add case number filter if provided
        if data.get('case_number'):
            query = query.filter(Case.filing_number.like(f"%{data['case_number']}%"))
        
        # Execute query
        cases = query.order_by(Case.filing_date.desc()).limit(50).all()
        
        # Format results
        results = [case.to_dict() for case in cases]
        
        return jsonify({
            'success': True,
            'count': len(results),
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/cases/<int:case_id>', methods=['GET'])
def get_case_details(case_id):
    try:
        case = Case.query.get_or_404(case_id)
        
        # In a real app, you might fetch additional details here
        # For now, we'll just return the basic case info
        return jsonify({
            'success': True,
            **case.to_dict(),
            # Add mock data for demonstration
            'next_hearing_date': '2023-12-15',  # Replace with actual field
            'judgments': [  # Mock judgments
                {
                    'id': 1,
                    'title': 'Final Judgment',
                    'date': '2023-11-01',
                    'summary': 'Case disposed with costs.',
                    'document_url': '/static/sample-judgment.pdf'
                }
            ]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Initialize database
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)