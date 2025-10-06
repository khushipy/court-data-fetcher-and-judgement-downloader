import os, time, logging, traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler('scraper.log'), logging.StreamHandler()])

BASE_URLS = {
    'high_court': 'https://hcservices.ecourts.gov.in/hcservices/main.php',
    'district_court': 'https://services.ecourts.gov.in/ecourtindia_v6/'
}

class CourtScraper:
    def __init__(self, headless=True, download_dir='downloads'):
        self.headless = headless
        self.driver = None
        self.download_dir = download_dir
        os.makedirs(os.path.join(self.download_dir, 'raw'), exist_ok=True)
        self._init_driver()

    def _init_driver(self):
        try:
            opts = Options()
            if self.headless:
                opts.add_argument("--headless=new")
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-dev-shm-usage')
            opts.add_argument('--window-size=1920,1080')
            
            # Try to use ChromeDriverManager to get the appropriate ChromeDriver
            try:
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=opts)
            except Exception as e:
                logger.warning(f"Failed to use ChromeDriverManager: {e}")
                # Fallback: Try to find ChromeDriver in the system PATH
                self.driver = webdriver.Chrome(options=opts)
            
            self.driver.set_page_load_timeout(30)
            logger.info("Selenium driver started")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            logger.error(traceback.format_exc())
            raise

    def close(self):
        try:
            if self.driver: 
                self.driver.quit()
        except Exception as e:
            logger.error(f"Error closing driver: {str(e)}")
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _save_page(self, html, prefix='case'):
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{ts}.html"
        path = os.path.join(self.download_dir, 'raw', filename)
        with open(path, 'w', encoding='utf-8') as f: f.write(html)
        return path

    def fetch_case_details(self, case_type, case_number, year, court_type='high_court', state=None, district=None):
        try:
            logger.info("Fetching case %s/%s/%s on %s", case_type, case_number, year, court_type)
            url = BASE_URLS.get(court_type, BASE_URLS['high_court'])
            self.driver.get(url)
            time.sleep(2)
            html = self.driver.page_source
            raw_path = self._save_page(html, prefix=f"{court_type}_{case_number}")
            case_data = {
                'case_details': {
                    'case_number': case_number,
                    'case_type': case_type,
                    'year': year,
                    'status': 'RAW_SAVED',
                    'filing_date': None,
                    'court_name': None,
                    'judge_name': None,
                    'is_disposed': False
                },
                'parties': [],
                'orders': [],
                'raw_response_path': raw_path,
                'pdf_path': None
            }
            return case_data
        except Exception:
            logger.error("Error in fetch_case_details: %s", traceback.format_exc())
            raise

    def fetch_cause_list(self, date=None, court_type='high_court', state_code='dl', district_code='dl'):
        """
        Fetches the cause list for the given date and court type.
        
        Args:
            date (str, optional): Date in YYYY-MM-DD format. Defaults to today.
            court_type (str, optional): 'high_court' or 'district_court'. Defaults to 'high_court'.
            state_code (str, optional): State code. Defaults to 'dl' (Delhi).
            district_code (str, optional): District code. Defaults to 'dl' (Delhi).
            
        Returns:
            list: List of cause list entries, each containing case details
        """
        try:
            logger.info(f"Fetching cause list for {date} from {court_type}")
            
            # Format date if provided
            formatted_date = datetime.now().strftime('%d-%m-%Y')
            if date:
                try:
                    # Convert from YYYY-MM-DD to DD-MM-YYYY
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    formatted_date = date_obj.strftime('%d-%m-%Y')
                except ValueError:
                    logger.warning(f"Invalid date format: {date}. Using current date.")
            
            # Get the base URL based on court type
            base_url = BASE_URLS.get(court_type, BASE_URLS['high_court'])
            
            # Navigate to the cause list page
            self.driver.get(base_url)
            logger.info(f"Opened {base_url}")
            
            # Add a small delay to let the page load
            time.sleep(3)
            
            # Save the raw HTML for debugging
            html = self.driver.page_source
            raw_path = self._save_page(html, prefix=f"causelist_{court_type}_{formatted_date}")
            
            # TODO: Implement actual scraping logic here
            # This is a placeholder that returns sample data
            # In a real implementation, you would parse the HTML to extract the cause list
            
            sample_cases = [
                {
                    'case_number': 'CRL.A. 123/2023',
                    'parties': 'State vs. John Doe',
                    'court_name': 'High Court of Delhi',
                    'judge_name': "Hon'ble Mr. Justice Smith",
                    'hearing_time': '10:30 AM',
                    'case_type': 'Criminal Appeal',
                    'bench': 'Bench 1',
                    'status': 'Fresh',
                    'section': '302 IPC'
                },
                {
                    'case_number': 'W.P.(C) 456/2023',
                    'parties': 'ABC Ltd. vs. XYZ Corporation',
                    'court_name': 'High Court of Delhi',
                    'judge_name': "Hon'ble Ms. Justice Johnson",
                    'hearing_time': '02:15 PM',
                    'case_type': 'Writ Petition',
                    'bench': 'Bench 2',
                    'status': 'Fresh',
                    'section': 'Article 226'
                }
            ]
            
            logger.info(f"Successfully fetched {len(sample_cases)} sample cases")
            return sample_cases
            
        except Exception as e:
            logger.error(f"Error in fetch_cause_list: {str(e)}")
            logger.error(traceback.format_exc())
            # Return an empty list in case of error
            return []
