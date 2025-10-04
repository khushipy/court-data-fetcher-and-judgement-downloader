from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, flash, redirect
from models import db, CaseSearch, CaseDetail, Party, CourtOrder
from config import Config
import os
import traceback
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Ensure static URL is set correctly
app.static_url_path = '/static'

# Create necessary directories
os.makedirs(app.config['DOWNLOAD_FOLDER'], exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'css'), exist_ok=True)
os.makedirs(os.path.join(app.root_path, 'static', 'js'), exist_ok=True)

@app.route('/')
def index():
    try:
        with app.app_context():
            db.create_all()
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error in index route: {str(e)}")
        app.logger.error(traceback.format_exc())
        return "An error occurred while loading the page. Please check the logs.", 500

@app.route('/api/search', methods=['POST'])
def search_case():
    try:
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Request must be JSON'
            }), 400
            
        data = request.get_json()
        case_type = data.get('case_type')
        case_number = data.get('case_number')
        year = data.get('year')
        court_type = data.get('court_type', 'high_court')
        
        if not all([case_type, case_number, year]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields (case_type, case_number, year)'
            }), 400
    
        try:
            # Save search query
            search = CaseSearch(
                case_type=case_type,
                case_number=case_number,
                year=year,
                court_type=court_type
            )
            db.session.add(search)
            db.session.commit()
            
            # For testing, return mock data
            mock_case = {
                'case_number': case_number,
                'case_type': case_type,
                'year': year,
                'status': 'Pending',
                'next_hearing': '2023-12-01',
                'parties': [
                    {
                        'name': 'John Doe',
                        'type': 'Petitioner',
                        'advocate': 'Jane Smith'
                    },
                    {
                        'name': 'State of Example',
                        'type': 'Respondent',
                        'advocate': 'Public Prosecutor'
                    }
                ]
            }
            
            return jsonify({
                'success': True,
                'search_id': search.id,
                'case': mock_case
            })
            
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error in search_case: {str(e)}")
            app.logger.error(traceback.format_exc())
            return jsonify({
                'success': False,
                'error': 'Failed to process case search. Please try again later.'
            }), 500

    except Exception as e:
        app.logger.error(f"Unexpected error in search_case: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred'
        }), 500

def save_case_details(search_id, case_data):
    """
    Save case details to the database
    """
    try:
        case = CaseDetail(
            search_id=search_id,
            cnr_number=case_data.get('cnr_number'),
            filing_number=case_data.get('filing_number'),
            registration_number=case_data.get('registration_number'),
            case_type=case_data.get('case_type'),
            case_status=case_data.get('status'),
            court_name=case_data.get('court_name'),
            judge_name=case_data.get('judge_name'),
            filing_date=datetime.strptime(case_data['filing_date'], '%Y-%m-%d') if case_data.get('filing_date') else None,
            registration_date=datetime.strptime(case_data['registration_date'], '%Y-%m-%d') if case_data.get('registration_date') else None,
            next_hearing_date=datetime.strptime(case_data['next_hearing_date'], '%Y-%m-%d') if case_data.get('next_hearing_date') else None,
            is_disposed=case_data.get('is_disposed', False)
        )
        
        db.session.add(case)
        db.session.commit()
        return case
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error saving case details: {str(e)}")
        app.logger.error(traceback.format_exc())
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
        
        # Initialize the scraper
        from scraper_fixed import CourtScraper
        app.logger.info("Successfully imported CourtScraper")
        
        try:
            # Initialize the scraper
            scraper = CourtScraper()
            app.logger.info("Initialized CourtScraper, fetching cause list...")
            
            # Fetch the cause list
            causes = scraper.fetch_cause_list(
                date=date,
                court_type=court_type,
                state_code=state_code,
                district_code=district_code
            )
            
            # Close the scraper
            if hasattr(scraper, 'driver'):
                scraper.driver.quit()
                
            app.logger.info(f"Successfully fetched {len(causes) if causes else 0} cases")
            
            return jsonify({
                'success': True,
                'date': date,
                'court_type': court_type,
                'cases': causes if causes else []
            })
            
        except Exception as e:
            # Ensure driver is closed even if there's an error
            if 'scraper' in locals() and hasattr(scraper, 'driver'):
                try:
                    scraper.driver.quit()
                except:
                    pass
            raise  # Re-raise the exception to be caught by the outer try-except
            
    except ImportError as ie:
        app.logger.error(f"Import error: {str(ie)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': f'Error importing required modules: {str(ie)}',
            'details': 'Make sure all dependencies are installed.'
        }), 500
    except Exception as e:
        app.logger.error(f"Unexpected error in get_cause_list: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'error': 'Failed to fetch cause list. Please try again later.',
            'details': str(e)
        }), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)