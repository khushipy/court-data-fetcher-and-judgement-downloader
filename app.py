from flask import Flask, request, jsonify, render_template
from models import db, CaseSearch, CaseDetail, Party, CourtOrder
from config import Config
import os, traceback, logging
from datetime import datetime
from scraper_fixed import CourtScraper

app = Flask(__name__)
app.config.from_object(Config)

# logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.INFO)

db.init_app(app)

# create directories
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()

# Initialize the database when the app starts
init_db()

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
