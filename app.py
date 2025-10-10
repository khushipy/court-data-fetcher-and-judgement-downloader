from flask import Flask, request, jsonify, render_template, send_from_directory, session, send_file
from models import db, CaseSearch, CaseDetail, Party, CourtOrder
from config import Config
import os, traceback, logging, random, time, uuid
from datetime import datetime
from scraper_fixed import CourtScraper
# Import from the root directory since captcha.py is there
from captcha import generate_captcha

app = Flask(__name__)
app.config.from_object(Config)

# Add session secret key
app.secret_key = os.environ.get('SECRET_KEY') or 'dev-key-please-change-in-production'

# Configure upload and captcha directories
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['CAPTCHA_FOLDER'] = os.path.join('static', 'captcha')

# Ensure all required directories exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['CAPTCHA_FOLDER'], exist_ok=True)
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)

# Initialize database
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

# Initialize the database when the app starts
init_db()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_case():
    if not request.is_json:
        return jsonify({'success': False, 'error': 'Request must be JSON'}), 400
    data = request.get_json()
    case_type = data.get('case_type')
    case_number = data.get('case_number')
    year = data.get('year')
    court_type = data.get('court_type', 'high_court')
    state = data.get('state')

    if not all([case_type, case_number, year]):
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400

    try:
        search = CaseSearch(case_type=case_type, case_number=case_number, year=int(year), court_type=court_type)
        db.session.add(search)
        db.session.commit()

        scraper = CourtScraper(headless=True, download_dir=app.config['DOWNLOAD_FOLDER'])
        try:
            case_data = scraper.fetch_case_details(case_type, case_number, year, court_type=court_type, state=state)
        finally:
            scraper.close()

        raw_path = case_data.get('raw_response_path')
        if raw_path:
            search.raw_response_path = raw_path
            db.session.commit()

        try:
            saved_case = save_case_details(search.id, case_data.get('case_details', {}))
            for p in case_data.get('parties', []):
                party = Party(case_id=saved_case.id, party_type=p.get('type'), name=p.get('name'), advocate_name=p.get('advocate'))
                db.session.add(party)
            for o in case_data.get('orders', []):
                order = CourtOrder(case_id=saved_case.id, order_type=o.get('order_type'),
                                   order_text=o.get('order_text'), pdf_url=o.get('pdf_url'),
                                   local_pdf_path=o.get('local_pdf_path'))
                db.session.add(order)
            db.session.commit()
        except Exception:
            app.logger.error("Failed to save parsed details: %s", traceback.format_exc())

        return jsonify({'success': True, 'search_id': search.id, 'case': case_data.get('case_details', {}), 'raw_path': raw_path})

    except Exception as e:
        db.session.rollback()
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/search/<int:search_id>', methods=['GET'])
def get_search_details(search_id):
    try:
        search = CaseSearch.query.get_or_404(search_id)
        detail = None
        if search.details:
            d = search.details
            detail = {
                'cnr_number': d.cnr_number,
                'filing_number': d.filing_number,
                'case_status': d.case_status,
                'court_name': d.court_name,
                'judge_name': d.judge_name,
                'next_hearing_date': d.next_hearing_date.isoformat() if d.next_hearing_date else None,
                'is_disposed': d.is_disposed
            }
        return jsonify({'success': True, 'search_id': search.id, 'case': detail, 'raw_path': search.raw_response_path})
    except Exception:
        app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'error': 'Not found'}), 404

@app.route('/cause-list', endpoint='cause_list')
def cause_list_page():
    return render_template('cause_list.html')

def save_case_details(search_id, case_data):
    try:
        filing_date = None
        reg_date = None
        next_hearing = None
        if case_data.get('filing_date'):
            try: filing_date = datetime.strptime(case_data['filing_date'], '%Y-%m-%d')
            except: pass
        if case_data.get('registration_date'):
            try: reg_date = datetime.strptime(case_data['registration_date'], '%Y-%m-%d')
            except: pass
        if case_data.get('next_hearing_date'):
            try: next_hearing = datetime.strptime(case_data['next_hearing_date'], '%Y-%m-%d')
            except: pass

        case = CaseDetail(
            search_id=search_id,
            cnr_number=case_data.get('cnr_number'),
            filing_number=case_data.get('filing_number'),
            registration_number=case_data.get('registration_number'),
            filing_date=filing_date,
            registration_date=reg_date,
            case_status=case_data.get('status') or case_data.get('case_status'),
            next_hearing_date=next_hearing,
            court_name=case_data.get('court_name'),
            judge_name=case_data.get('judge_name'),
            is_disposed=case_data.get('is_disposed', False)
        )
        db.session.add(case)
        db.session.commit()
        return case
    except Exception:
        db.session.rollback()
        app.logger.error("Error saving case details: %s", traceback.format_exc())
        raise

@app.route('/api/causes', methods=['GET'])
def get_cause_list():
    try:
        app.logger.info("Received request for cause list")
        
        # Get query parameters
        date = request.args.get('date')
        court_type = request.args.get('court_type', 'high_court')
        state_code = request.args.get('state_code', 'dl')  # Default to Delhi
        district_code = request.args.get('district_code', 'dl')  # Default to Delhi

        app.logger.info(f"Parameters - date: {date}, court_type: {court_type}, state_code: {state_code}, district_code: {district_code}")

        # Initialize the scraper using context manager
        with CourtScraper() as scraper:
            app.logger.info("Initialized CourtScraper, fetching cause list...")
            
            # Fetch the cause list
            causes = scraper.fetch_cause_list(
                date=date,
                court_type=court_type,
                state_code=state_code,
                district_code=district_code
            )
            
            app.logger.info(f"Successfully fetched {len(causes) if causes else 0} cases")

            return jsonify({
                'success': True,
                'date': date,
                'court_type': court_type,
                'cases': causes if causes else []
            })

    except Exception as e:
        app.logger.error(f"Error in get_cause_list: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to fetch cause list',
            'details': str(e)
        }), 500

@app.route('/case/<int:search_id>')
def view_case(search_id):
    try:
        search = CaseSearch.query.get_or_404(search_id)
        details = search.details
        parties = Party.query.filter_by(case_id=details.id).all() if details else []
        orders = CourtOrder.query.filter_by(case_id=details.id).all() if details else []
        
        # Sample data - replace with actual data from your database
        case_details = {
            'cnr_number': getattr(details, 'cnr_number', 'DLHC010012342022'),
            'filing_number': getattr(details, 'filing_number', '1234/2022'),
            'registration_number': getattr(details, 'registration_number', '5678/2022'),
            'filing_date': getattr(details, 'filing_date', datetime(2022, 1, 1)),
            'registration_date': getattr(details, 'registration_date', datetime(2022, 1, 15)),
            'next_hearing_date': getattr(details, 'next_hearing_date', datetime(2023, 12, 15)),
            'case_status': getattr(details, 'case_status', 'Disposed'),
            'case_type': getattr(details, 'case_type', 'Criminal Appeal'),
            'category': getattr(details, 'category', 'Criminal'),
            'act': getattr(details, 'act', 'Indian Penal Code'),
            'court_name': getattr(details, 'court_name', 'High Court of Delhi'),
            'judge_name': getattr(details, 'judge_name', 'Honorable Justice Sharma'),
            'bench': getattr(details, 'bench', 'Bench 1'),
            'is_disposed': getattr(details, 'is_disposed', True),
            'summary': getattr(details, 'summary', 'This is a sample case summary. The case involves charges under IPC sections 302, 34. The case is currently under trial with the next hearing scheduled for December 15, 2023.'),
            'full_text': getattr(details, 'full_text', 'Full case text would be displayed here...')
        }
        
        return render_template(
            'case_details.html',
            search_id=search_id,
            case_details=case_details,
            parties=parties or [
                {'party_type': 'Petitioner', 'name': 'State of Delhi', 'advocate_name': 'Adv. Ramesh Kumar', 'address': 'New Delhi'},
                {'party_type': 'Respondent', 'name': 'Rahul Sharma', 'advocate_name': 'Adv. Sunil Mehta', 'address': 'New Delhi'}
            ],
            orders=orders or [
                {'order_type': 'Bail Order', 'order_date': datetime(2022, 3, 15), 'description': 'Bail granted', 'pdf_url': '#'},
                {'order_type': 'Charge Sheet', 'order_date': datetime(2022, 5, 22), 'description': 'Charge sheet filed', 'pdf_url': '#'}
            ]
        )
    except Exception as e:
        app.logger.error(f"Error viewing case {search_id}: {str(e)}")
        return render_template('error.html', error="Failed to load case details"), 500

@app.route('/api/case/<int:search_id>/download')
def download_case_details(search_id):
    try:
        search = CaseSearch.query.get_or_404(search_id)
        details = search.details
        
        # Generate a simple text file with case details
        case_text = f"""CASE DETAILS
================

Case Status:
------------
Status: {getattr(details, 'case_status', 'N/A')}
Next Hearing: {details.next_hearing_date.strftime('%d-%b-%Y') if details and details.next_hearing_date else 'N/A'}
Disposed: {'Yes' if getattr(details, 'is_disposed', False) else 'No'}

Case Information:
-----------------
CNR Number: {getattr(details, 'cnr_number', 'N/A')}
Filing Number: {getattr(details, 'filing_number', 'N/A')}
Registration Number: {getattr(details, 'registration_number', 'N/A')}
Filing Date: {details.filing_date.strftime('%d-%b-%Y') if details and details.filing_date else 'N/A'}
Registration Date: {details.registration_date.strftime('%d-%b-%Y') if details and details.registration_date else 'N/A'}

Court Information:
------------------
Court: {getattr(details, 'court_name', 'N/A')}
Judge: {getattr(details, 'judge_name', 'N/A')}
Case Type: {getattr(details, 'case_type', 'N/A')}
"""
        
        from io import StringIO
        from flask import make_response
        
        output = StringIO()
        output.write(case_text)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = f"attachment; filename=case_{search_id}_details.txt"
        response.headers["Content-type"] = "text/plain"
        return response
        
    except Exception as e:
        app.logger.error(f"Error downloading case {search_id}: {str(e)}")
        return jsonify({'success': False, 'error': 'Failed to generate download'}), 500

# app.py (add these routes to your existing file)
from flask import session, send_file
from io import BytesIO
import os
import uuid
from datetime import datetime

# CAPTCHA configuration is already set up at the top of the file
os.makedirs(app.config['CAPTCHA_FOLDER'], exist_ok=True)

@app.route('/search')
def search_page():
    return render_template('search.html')

@app.route('/api/init', methods=['GET'])
def init_session():
    """Initialize a new search session and return CAPTCHA"""
    try:
        # Generate CAPTCHA
        captcha_text, image_data = generate_captcha()
        captcha_id = str(uuid.uuid4())
        captcha_path = os.path.join(app.config['CAPTCHA_FOLDER'], f'captcha_{captcha_id}.png')
        
        # Save CAPTCHA image
        with open(captcha_path, 'wb') as f:
            f.write(image_data)
        
        # Store CAPTCHA text in session
        session['captcha'] = captcha_text.lower()
        session['captcha_id'] = captcha_id
        
        # Return CAPTCHA image URL
        captcha_url = f"/static/captcha/captcha_{captcha_id}.png"
        
        return jsonify({
            'success': True,
            'captcha_url': captcha_url
        })
    except Exception as e:
        app.logger.error(f"Error in init_session: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/districts/<state>')
def get_districts(state):
    """Get districts for a state"""
    # This is a simplified example - you'll want to replace with actual data
    districts = {
        'delhi': ['Central', 'East', 'New Delhi', 'North', 'North East', 
                 'North West', 'Shahdara', 'South', 'South East', 'South West', 'West'],
        'maharashtra': ['Mumbai', 'Pune', 'Nagpur', 'Thane', 'Nashik'],
        'karnataka': ['Bangalore Urban', 'Mysore', 'Hubli', 'Mangalore', 'Gulbarga']
    }
    return jsonify({
        'success': True,
        'districts': districts.get(state.lower(), [])
    })

@app.route('/api/case-types')
def get_case_types():
    """Get available case types"""
    case_types = [
        'Civil', 'Criminal', 'Writ Petition', 'First Appeal', 
        'Second Appeal', 'Arbitration', 'Company Petition'
    ]
    return jsonify({'success': True, 'case_types': case_types})

@app.route('/api/search', methods=['POST'])
def search_case_advanced():
    """Handle the advanced case search with all parameters"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['state', 'district', 'case_type', 'case_number', 'year', 'captcha']
        if not all(field in data for field in required_fields):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Verify CAPTCHA
        if 'captcha' not in session or data['captcha'].lower() != session.get('captcha', ''):
            return jsonify({'success': False, 'error': 'Invalid CAPTCHA'}), 400
        
        # Clean up CAPTCHA from session
        if 'captcha' in session:
            captcha_id = session.get('captcha_id')
            if captcha_id:
                captcha_path = os.path.join(app.config['CAPTCHA_FOLDER'], f'captcha_{captcha_id}.png')
                if os.path.exists(captcha_path):
                    try:
                        os.remove(captcha_path)
                    except:
                        pass
            session.pop('captcha', None)
            session.pop('captcha_id', None)
        
        # Here you would call your scraper with the provided parameters
        # For now, we'll return mock data
        mock_case = {
            'cnr_number': f"DLHC01{random.randint(100000, 999999)}2023",
            'filing_number': f"{data['case_number']}/{data['year']}",
            'registration_number': f"R{random.randint(1000, 9999)}/{data['year']}",
            'filing_date': '2023-01-15',
            'registration_date': '2023-02-01',
            'case_status': 'Pending',
            'case_type': data['case_type'],
            'next_hearing_date': '2023-12-15',
            'judge_name': 'HON\'BLE MR. JUSTICE SAMPLE JUDGE',
            'is_disposed': False,
            'court_name': f"{data['district'].title()} {data['court_type'].replace('_', ' ').title()}"
        }
        
        mock_parties = [
            {'party_type': 'Petitioner', 'name': 'Sample Petitioner', 'advocate': 'Adv. Sample Advocate'},
            {'party_type': 'Respondent', 'name': 'Sample Respondent', 'advocate': 'Adv. Another Advocate'}
        ]
        
        mock_orders = [
            {'order_type': 'Interim Order', 'order_date': '2023-03-10', 'description': 'Interim relief granted'},
            {'order_type': 'Hearing', 'order_date': '2023-06-20', 'description': 'Matter adjourned to next date'}
        ]
        
        # Generate a mock PDF (in real app, this would be generated from scraped data)
        pdf_filename = f"case_{int(time.time())}.pdf"
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_filename)
        
        # In a real app, you would generate the PDF here
        # For now, we'll just create an empty file
        with open(pdf_path, 'wb') as f:
            f.write(b'')  # Empty PDF
        
        return jsonify({
            'success': True,
            'case': mock_case,
            'parties': mock_parties,
            'orders': mock_orders,
            'pdf_url': f"/download/{pdf_filename}"
        })
        
    except Exception as e:
        app.logger.error(f"Error in search_case_advanced: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/download/<filename>')
def download_file(filename):
    """Serve the generated PDF file"""
    try:
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name=f"case_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({'success': False, 'error': 'File not found'}), 404

# API Endpoints (already defined above)
        return send_from_directory(
            app.config['UPLOAD_FOLDER'],
            filename,
            as_attachment=True,
            download_name=f"case_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
    except Exception as e:
        app.logger.error(f"Error serving file {filename}: {str(e)}")
        return jsonify({'success': False, 'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)
