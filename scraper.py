import time
import random
import os
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)

class CourtScraper:
    def __init__(self, headless=True):
        """Initialize the CourtScraper with optional headless mode"""
        self.logger = logging.getLogger(__name__)
        self.setup_driver(headless)
    
    def setup_driver(self, headless=True):
        """Initialize the Chrome WebDriver with options"""
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.logger.info("WebDriver initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise

    def _random_delay(self, min_seconds=1, max_seconds=3):
        """Random delay to mimic human behavior"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def _take_screenshot(self, prefix='error'):
        """Take screenshot for debugging"""
        try:
            if not os.path.exists('screenshots'):
                os.makedirs('screenshots')
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshots/{prefix}_{timestamp}.png"
            self.driver.save_screenshot(filename)
            self.logger.info(f"Screenshot saved: {filename}")
            return filename
        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {str(e)}")
            return None

    def _fill_field(self, field_name, value):
        """Safely fill a form field with random delays"""
        try:
            self._random_delay(0.5, 1.5)
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, field_name))
            )
            element.clear()
            element.send_keys(value)
        except Exception as e:
            self._take_screenshot(f'field_error_{field_name}')
            raise Exception(f"Failed to fill field {field_name}: {str(e)}")

    def fetch_high_court_case(self, case_type, case_number, year):
        """
        Fetch case details from High Court website
        
        Args:
            case_type (str): Type of the case (e.g., 'CIVIL', 'CRIMINAL')
            case_number (str): Case number
            year (str): Year of case filing
            
        Returns:
            dict: Case details
        """
        self.logger.info(f"Fetching case: Type={case_type}, Number={case_number}, Year={year}")
        
        try:
            # Navigate to the main page
            self.driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
            self._random_delay(2, 3)

            # State selection
            try:
                state_dropdown = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, 'sess_state'))
                )
                state_select = Select(state_dropdown)
                state_select.select_by_visible_text('Delhi High Court')
                self._random_delay(1, 2)
                
                # Submit state selection
                self.driver.find_element(By.NAME, 'submit1').click()
                self._random_delay(2, 3)
                
            except Exception as e:
                self._take_screenshot('state_selection_error')
                raise Exception(f"Failed to select state: {str(e)}")

            # Fill case details
            try:
                # Wait for form to be ready
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.NAME, 'case_type'))
                )
                
                # Fill form fields
                self._fill_field('case_type', case_type)
                self._fill_field('case_no', case_number)
                self._fill_field('rgyear', year)
                
                # Submit form
                submit_btn = self.driver.find_element(By.NAME, 'search_submit')
                submit_btn.click()
                self._random_delay(3, 5)
                
            except Exception as e:
                self._take_screenshot('form_submission_error')
                raise Exception(f"Form submission failed: {str(e)}")

            # Process results
            try:
                # Wait for results to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'result_table'))
                )
                
                # Parse the results
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find('table', {'class': 'result_table'})
                
                if not table:
                    self.logger.warning("No results table found")
                    return {"status": "No results found"}
                
                # Extract case details
                case_details = self._parse_case_details(table)
                self.logger.info("Successfully fetched case details")
                return case_details
                
            except Exception as e:
                self._take_screenshot('results_processing_error')
                raise Exception(f"Failed to process results: {str(e)}")
                
        except Exception as e:
            self.logger.error(f"Error in fetch_high_court_case: {str(e)}")
            raise

    def _parse_case_details(self, table):
        """Parse the HTML table with case details"""
        case_details = {
            'case_number': '',
            'filing_date': '',
            'registration_date': '',
            'cnr_number': '',
            'petitioner': '',
            'respondent': '',
            'advocates': [],
            'status': '',
            'next_hearing': '',
            'history': []
        }
        
        try:
            # Parse basic case details
            rows = table.find_all('tr')
            for row in rows[1:]:  # Skip header row
                cols = row.find_all('td')
                if len(cols) >= 2:
                    header = cols[0].text.strip().lower()
                    value = cols[1].text.strip()
                    
                    if 'case no' in header:
                        case_details['case_number'] = value
                    elif 'filing date' in header:
                        case_details['filing_date'] = value
                    elif 'registration date' in header:
                        case_details['registration_date'] = value
                    elif 'cnr no' in header:
                        case_details['cnr_number'] = value
                    elif 'petitioner' in header:
                        case_details['petitioner'] = value
                    elif 'respondent' in header:
                        case_details['respondent'] = value
                    elif 'status' in header:
                        case_details['status'] = value
                    elif 'next date' in header.lower():
                        case_details['next_hearing'] = value
            
            # Parse advocates
            advocate_section = table.find('th', text=lambda x: x and 'advocate' in x.lower())
            if advocate_section:
                advocate_rows = advocate_section.find_parent('table').find_all('tr')[1:]
                for row in advocate_rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:
                        case_details['advocates'].append({
                            'name': cols[0].text.strip(),
                            'type': cols[1].text.strip(),
                            'party': cols[2].text.strip()
                        })
            
            # Parse case history if available
            history_section = table.find('th', text=lambda x: x and 'history' in x.lower())
            if history_section:
                history_rows = history_section.find_parent('table').find_all('tr')[1:]
                for row in history_rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:
                        case_details['history'].append({
                            'date': cols[0].text.strip(),
                            'stage': cols[1].text.strip(),
                            'purpose': cols[2].text.strip(),
                            'remarks': cols[3].text.strip() if len(cols) > 3 else ''
                        })
            
            return case_details
            
        except Exception as e:
            self.logger.error(f"Error parsing case details: {str(e)}")
            raise

    def close(self):
        """Close the WebDriver"""
        try:
            if hasattr(self, 'driver'):
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
        except Exception as e:
            self.logger.error(f"Error closing WebDriver: {str(e)}")

    def __enter__(self):
        """Support for 'with' statement"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure resources are cleaned up when exiting 'with' block"""
        self.close()


def main():
    """Example usage of the CourtScraper"""
    try:
        # Example case details
        case_type = 'CIVIL'  # Change as needed
        case_number = '1234'  # Change to actual case number
        year = '2023'        # Change to actual year
        
        with CourtScraper(headless=False) as scraper:
            results = scraper.fetch_high_court_case(case_type, case_number, year)
            print("\nCase Details:")
            print(json.dumps(results, indent=2, ensure_ascii=False))
            
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())