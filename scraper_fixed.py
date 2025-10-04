import os
import json
import time
import random
import re
import logging
import traceback
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# PDF Generation
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.units import inch

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
BASE_URLS = {
    'high_court': 'https://hcservices.ecourts.gov.in/hcservices/main.php',
    'district_court': 'https://services.ecourts.gov.in/ecourtindia_v6/'
}

# List of all High Courts in India
HIGH_COURTS = [
    'allahabad', 'andhra_pradesh', 'bombay', 'calcutta', 'chhattisgarh',
    'delhi', 'gauhati', 'gujarat', 'himachal_pradesh', 'jammu_kashmir',
    'jharkhand', 'karnataka', 'kerala', 'madras', 'madhyapradesh',
    'manipur', 'meghalaya', 'orissa', 'patna', 'punjab_haryana',
    'rajasthan', 'sikkim', 'tripura', 'uttarakhand', 'kolkata'
]

class CaptchaSolverError(Exception):
    """Custom exception for CAPTCHA solving errors"""
    pass

class CourtScraper:
    """Scraper for Indian court websites"""
    
    def __init__(self, headless=True):
        """Initialize the scraper with browser options"""
        self.session = requests.Session()
        self.setup_requests_session()
        self.driver = None
        self.headless = headless
        self.setup_selenium()
        
    def setup_requests_session(self):
        """Configure the requests session with appropriate headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://services.ecourts.gov.in/ecourtindia_v6/'
        })
    
    def setup_selenium(self):
        """Initialize Selenium WebDriver with options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Initialize WebDriver
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}")
            raise
    
    def close(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        self.session.close()
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

class CourtScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        self.high_court_url = "https://hcservices.ecourts.gov.in/hcservices/main.php"
        self.district_court_url = "https://services.ecourts.gov.in/ecourtindia_v6/"

    def fetch_case_details(self, case_type, case_number, year, court_type='high_court', state=None, district=None):
        """
        Fetch case details from the eCourts website
        
        Args:
            case_type (str): Type of case (e.g., 'CIVIL', 'CRIMINAL')
            case_number (str): Case number
            year (str): Year of filing
            court_type (str): Type of court ('high_court' or 'district_court')
            state (str, optional): State name for district court searches
            district (str, optional): District name for district court searches
            
        Returns:
            dict: Dictionary containing case details
        """
        try:
            logger.info(f"Searching for case: {case_type}/{case_number}/{year} in {court_type}")
            
            if court_type == 'high_court':
                return self._fetch_high_court_case(case_type, case_number, year)
            else:
                return self._fetch_district_court_case(case_type, case_number, year, state, district)
                
        except Exception as e:
            logger.error(f"Error fetching case details: {str(e)}", exc_info=True)
            raise
    
    def _fetch_high_court_case(self, case_type, case_number, year):
        """Fetch case details from High Court"""
        try:
            # Navigate to the High Court services page
            self.driver.get(BASE_URLS['high_court'])
            
            # Wait for the form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'sess_state'))
            )
            
            # Select the state (High Court)
            # Note: This is a simplified example - actual implementation will vary by High Court
            state_select = self.driver.find_element(By.ID, 'sess_state')
            # Implementation depends on the specific High Court's website structure
            
            # Fill in case details
            self.driver.find_element(By.NAME, 'case_type').send_keys(case_type)
            self.driver.find_element(By.NAME, 'case_no').send_keys(case_number)
            self.driver.find_element(By.NAME, 'year').send_keys(year)
            
            # Solve CAPTCHA if present
            self._solve_captcha()
            
            # Submit the form
            self.driver.find_element(By.NAME, 'submit').click()
            
            # Parse the results
            return self._parse_high_court_response()
            
        except Exception as e:
            logger.error(f"Error fetching High Court case: {str(e)}", exc_info=True)
            raise
    
    def _fetch_district_court_case(self, case_type, case_number, year, state=None, district=None):
        """Fetch case details from District Court"""
        try:
            # Navigate to the District Court services page
            self.driver.get(BASE_URLS['district_court'])
            
            # Wait for the form to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, 'sess_state_code'))
            )
            
            # Select state and district
            if state:
                state_select = self.driver.find_element(By.ID, 'sess_state_code')
                # Implementation depends on the specific website structure
            
            if district:
                # Wait for district dropdown to be populated
                time.sleep(2)  # Allow time for AJAX to load districts
                district_select = self.driver.find_element(By.ID, 'sess_dist_code')
                # Select the district
            
            # Fill in case details
            self.driver.find_element(By.NAME, 'case_type').send_keys(case_type)
            self.driver.find_element(By.NAME, 'case_no').send_keys(case_number)
            self.driver.find_element(By.NAME, 'year').send_keys(year)
            
            # Solve CAPTCHA if present
            self._solve_captcha()
            
            # Submit the form
            self.driver.find_element(By.NAME, 'submit').click()
            
            # Parse the results
            return self._parse_district_court_response()
            
        except Exception as e:
            logger.error(f"Error fetching District Court case: {str(e)}", exc_info=True)
            raise
    
    def _solve_captcha(self):
        """Handle CAPTCHA solving (placeholder for actual implementation)"""
        try:
            # Check if CAPTCHA is present
            captcha_elements = self.driver.find_elements(By.CLASS_NAME, 'captcha')
            if captcha_elements:
                logger.warning("CAPTCHA detected. Manual intervention may be required.")
                # In a real implementation, you might:
                # 1. Use a CAPTCHA solving service
                # 2. Download the CAPTCHA image and prompt the user
                # 3. Use browser automation to wait for manual CAPTCHA entry
                time.sleep(10)  # Give time for manual CAPTCHA entry
        except Exception as e:
            logger.warning(f"Error handling CAPTCHA: {str(e)}")
    
    def _parse_high_court_response(self):
        """Parse the response from High Court website"""
        # Implementation depends on the specific High Court's website structure
        # This is a simplified example
        
        # Wait for results to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'case-details'))
        )
        
        # Extract case details
        case_data = {
            'case_details': {
                'cnr_number': self._safe_extract_text('.cnr-number'),
                'filing_number': self._safe_extract_text('.filing-number'),
                'case_type': self._safe_extract_text('.case-type'),
                'status': self._safe_extract_text('.case-status'),
                'court_name': self._safe_extract_text('.court-name'),
                'judge_name': self._safe_extract_text('.judge-name'),
                'filing_date': self._safe_extract_text('.filing-date'),
                'next_hearing_date': self._safe_extract_text('.next-hearing-date'),
                'is_disposed': 'disposed' in self._safe_extract_text('.case-status', '').lower()
            },
            'parties': self._extract_parties(),
            'orders': self._extract_orders(),
            'hearing_dates': self._extract_hearing_dates()
        }
        
        # Generate PDF
        pdf_path = self.generate_pdf(case_data, case_data['case_details']['filing_number'], 
                                   case_data['case_details']['filing_date'][:4])
        case_data['pdf_path'] = pdf_path
        
        return case_data
    
    def _parse_district_court_response(self):
        """Parse the response from District Court website"""
        # Implementation similar to _parse_high_court_response but for District Court
        # This is a simplified example
        
        # Wait for results to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'case-details'))
        )
        
        # Extract case details
        case_data = {
            'case_details': {
                'cnr_number': self._safe_extract_text('.cnr-no'),
                'filing_number': self._safe_extract_text('.filing-no'),
                'case_type': self._safe_extract_text('.case-type'),
                'status': self._safe_extract_text('.status'),
                'court_name': self._safe_extract_text('.court-name'),
                'judge_name': self._safe_extract_text('.judge-name'),
                'filing_date': self._safe_extract_text('.filing-date'),
                'next_hearing_date': self._safe_extract_text('.next-date'),
                'is_disposed': 'disposed' in self._safe_extract_text('.status', '').lower()
            },
            'parties': self._extract_parties(),
            'orders': self._extract_orders(),
            'hearing_dates': self._extract_hearing_dates()
        }
        
        # Generate PDF
        pdf_path = self.generate_pdf(case_data, case_data['case_details']['filing_number'], 
                                   case_data['case_details']['filing_date'][:4])
        case_data['pdf_path'] = pdf_path
        
        return case_data
    
    def _safe_extract_text(self, selector, default='N/A'):
        """Safely extract text from an element using CSS selector"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return default
    
    def _extract_parties(self):
        """Extract party information from the page"""
        parties = []
        try:
            party_elements = self.driver.find_elements(By.CSS_SELECTOR, '.party-list .party')
            for party in party_elements:
                parties.append({
                    'type': self._safe_extract_text('.party-type', 'Party'),
                    'name': self._safe_extract_text('.party-name', 'Unknown'),
                    'advocate': self._safe_extract_text('.advocate-name', 'Not Available'),
                    'address': self._safe_extract_text('.party-address', 'Not Available')
                })
        except Exception as e:
            logger.warning(f"Error extracting parties: {str(e)}")
        
        return parties or [{
            'type': 'Petitioner',
            'name': 'Not Available',
            'advocate': 'Not Available',
            'address': 'Not Available'
        }]
    
    def _extract_orders(self):
        """Extract order information from the page"""
        orders = []
        try:
            order_elements = self.driver.find_elements(By.CSS_SELECTOR, '.order-list .order')
            for order in order_elements:
                orders.append({
                    'order_date': self._safe_extract_text('.order-date'),
                    'order_type': self._safe_extract_text('.order-type', 'Order'),
                    'order_text': self._safe_extract_text('.order-text', 'No details available'),
                    'pdf_url': order.find_element(By.CSS_SELECTOR, 'a[href$=".pdf"]').get_attribute('href') if order.find_elements(By.CSS_SELECTOR, 'a[href$=".pdf"]') else None
                })
                
                # Download order PDF if available
                if orders[-1]['pdf_url']:
                    try:
                        pdf_path = self.download_order(orders[-1]['pdf_url'])
                        orders[-1]['local_pdf_path'] = pdf_path
                    except Exception as e:
                        logger.warning(f"Failed to download order PDF: {str(e)}")
        except Exception as e:
            logger.warning(f"Error extracting orders: {str(e)}")
        
        return orders
    
    def _extract_hearing_dates(self):
        """Extract hearing dates from the page"""
        hearings = []
        try:
            hearing_elements = self.driver.find_elements(By.CSS_SELECTOR, '.hearing-list .hearing')
            for hearing in hearing_elements:
                hearings.append({
                    'date': self._safe_extract_text('.hearing-date'),
                    'purpose': self._safe_extract_text('.hearing-purpose', 'Hearing'),
                    'status': self._safe_extract_text('.hearing-status', 'Scheduled')
                })
        except Exception as e:
            logger.warning(f"Error extracting hearing dates: {str(e)}")
        
        return hearings
        
    def fetch_cause_list(self, date=None, court_type='high_court', state_code='dl', district_code='dl'):
        """
        Fetch cause list for a specific date and court type
        
        Args:
            date (str, optional): Date in YYYY-MM-DD format. Defaults to today.
            court_type (str): Type of court ('high_court' or 'district_court').
            state_code (str): State code (e.g., 'dl' for Delhi)
            district_code (str): District code
            
        Returns:
            list: List of cases with their details
        """
        try:
            logger.info(f"Starting to fetch cause list for {court_type} on date: {date}")
            
            # If no date provided, use today's date
            if not date:
                date = datetime.now().strftime('%Y-%m-%d')
                logger.info(f"No date provided, using today's date: {date}")
            
            # Convert date from YYYY-MM-DD to DD-MM-YYYY
            try:
                date_obj = datetime.strptime(date, '%Y-%m-%d')
                formatted_date = date_obj.strftime('%d-%m-%Y')
                logger.info(f"Formatted date: {formatted_date}")
            except ValueError as ve:
                logger.error(f"Invalid date format. Please use YYYY-MM-DD. Error: {str(ve)}")
                raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
            
            causes = []
            
            if court_type == 'high_court':
                try:
                    logger.info("Accessing High Court cause list page...")
                    # Navigate to High Court cause list page
                    self.driver.get('https://hcservices.ecourts.gov.in/hcservices/main.php')
                    
                    # Wait for the page to load
                    WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.ID, 's3'))
                    )
                    logger.info("Page loaded successfully")
                    
                    try:
                        # Select the cause list option from the dropdown
                        logger.info("Selecting 'Cause List' from dropdown...")
                        cause_list_option = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//option[contains(text(), 'Cause List')]"))
                        )
                        cause_list_option.click()
                        
                        # Enter the date
                        logger.info(f"Entering date: {formatted_date}")
                        date_input = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.ID, 's4'))
                        )
                        date_input.clear()
                        date_input.send_keys(formatted_date)
                        
                        # Submit the form
                        logger.info("Submitting the form...")
                        submit_btn = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.NAME, 'submit1'))
                        )
                        submit_btn.click()
                        
                        # Wait for results to load
                        logger.info("Waiting for results...")
                        try:
                            WebDriverWait(self.driver, 15).until(
                                lambda d: 'result' in d.page_source.lower() or 'no records found' in d.page_source.lower()
                            )
                            
                            # Check for no records found
                            if "no records found" in self.driver.page_source.lower():
                                logger.info(f"No cases found for date: {formatted_date}")
                                return []
                            
                            # Wait for the results table
                            WebDriverWait(self.driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, '.result, table'))
                            )
                            
                            # Extract case details
                            logger.info("Extracting case details...")
                            case_rows = self.driver.find_elements(By.CSS_SELECTOR, '.result tr, table tr')
                            logger.info(f"Found {len(case_rows)} rows in the result")
                            
                            for i, row in enumerate(case_rows[1:], 1):  # Skip header row
                                try:
                                    cols = row.find_elements(By.TAG_NAME, 'td')
                                    if len(cols) >= 6:  # Ensure we have enough columns
                                        case_data = {
                                            'case_number': cols[0].text.strip(),
                                            'petitioner': cols[1].text.strip(),
                                            'respondent': cols[2].text.strip(),
                                            'purpose': cols[3].text.strip(),
                                            'time': cols[4].text.strip(),
                                            'court_room': cols[5].text.strip() if len(cols) > 5 else 'N/A',
                                            'judge': cols[6].text.strip() if len(cols) > 6 else 'N/A'
                                        }
                                        causes.append(case_data)
                                        logger.debug(f"Processed case {i}: {case_data['case_number']}")
                                    else:
                                        logger.warning(f"Skipping row {i}: Insufficient columns ({len(cols)})")
                                except Exception as e:
                                    logger.warning(f"Error processing row {i}: {str(e)}")
                                    continue
                            
                            logger.info(f"Successfully extracted {len(causes)} cases")
                            
                        except Exception as e:
                            logger.error(f"Error loading cause list results: {str(e)}")
                            logger.error(f"Page source: {self.driver.page_source[:1000]}...")  # Log first 1000 chars of page
                            raise
                            
                    except Exception as e:
                        logger.error(f"Error interacting with the cause list form: {str(e)}")
                        raise
                        
                except Exception as e:
                    logger.error(f"Error accessing High Court website: {str(e)}")
                    # Take a screenshot for debugging
                    try:
                        screenshot_path = os.path.join('debug', 'high_court_error.png')
                        os.makedirs('debug', exist_ok=True)
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"Screenshot saved to {screenshot_path}")
                    except Exception as screenshot_error:
                        logger.error(f"Failed to take screenshot: {str(screenshot_error)}")
                    raise
                    
            else:
                # District court implementation would go here
                logger.warning("District court cause list not yet implemented")
                return []
            
            return causes
            
        except Exception as e:
            logger.error(f"Unexpected error in fetch_cause_list: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    def download_order(self, url, output_dir='downloads/orders'):
        """
        Download an order/judgment PDF
        
{{ ... }}
        Args:
            url (str): URL of the PDF to download
            output_dir (str): Directory to save the PDF
            
        Returns:
            str: Path to the downloaded file
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate filename from URL
            filename = os.path.basename(urlparse(url).path) or f"order_{int(time.time())}.pdf"
            filepath = os.path.join(output_dir, filename)
            
            # Download the file
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Downloaded order to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error downloading order: {str(e)}")
            raise
    
    def generate_pdf(self, case_data, case_number, year, output_dir='downloads'):
        """
        Generate a PDF file with case details
        
        Args:
            case_data (dict): Dictionary containing case details
            case_number (str): Case number
            year (str): Year of filing
            
        Returns:
            str: Path to the generated PDF file
        """
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate PDF filename (sanitize case number for filename)
            safe_case_number = re.sub(r'[\\/*?:"<>|]', '_', str(case_number))
            filename = f"case_{safe_case_number}_{year}.pdf"
            pdf_path = os.path.join(output_dir, filename)
            
            # Create PDF
            c = canvas.Canvas(pdf_path, pagesize=letter)
            width, height = letter
            
            # Set up styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=20,
                alignment=1  # Center aligned
            )
            
            # Add title
            title = f"Case Details: {case_number}/{year}"
            c.setFont("Helvetica-Bold", 16)
            c.drawCentredString(width/2, height-50, title)
            
            # Add case details
            y_position = height - 100
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "Case Details:")
            y_position -= 20
            
            # Add case information
            case_info = case_data['case_details']
            details = [
                ("CNR Number:", case_info.get('cnr_number', 'N/A')),
                ("Filing Number:", case_info.get('filing_number', 'N/A')),
                ("Case Type:", case_info.get('case_type', 'N/A')),
                ("Status:", case_info.get('status', 'N/A')),
                ("Court:", case_info.get('court_name', 'N/A')),
                ("Judge:", case_info.get('judge_name', 'N/A')),
                ("Filing Date:", case_info.get('filing_date', 'N/A')),
                ("Next Hearing:", case_info.get('next_hearing_date', 'N/A'))
            ]
            
            # Draw case details
            c.setFont("Helvetica", 10)
            for label, value in details:
                c.drawString(70, y_position, f"{label} {value}")
                y_position -= 15
            
            # Add parties section
            y_position -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "Parties:")
            y_position -= 20
            
            # Draw party information
            c.setFont("Helvetica", 10)
            for party in case_data.get('parties', []):
                c.drawString(70, y_position, f"{party.get('type', 'Party')}: {party.get('name', 'N/A')}")
                y_position -= 15
                c.drawString(90, y_position, f"Advocate: {party.get('advocate', 'N/A')}")
                y_position -= 15
                if y_position < 100:  # Add new page if running out of space
                    c.showPage()
                    y_position = height - 50
            
            # Add orders section
            y_position -= 20
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, "Orders:")
            y_position -= 20
            
            # Draw order information
            c.setFont("Helvetica", 10)
            for order in case_data.get('orders', []):
                c.drawString(70, y_position, f"Date: {order.get('order_date', 'N/A')} - {order.get('order_type', 'Order')}")
                y_position -= 15
                
                # Split long text into multiple lines
                text = order.get('order_text', '')
                words = text.split()
                line = []
                line_length = 0
                
                for word in words:
                    if line_length + len(word) < 80:  # Approximate characters per line
                        line.append(word)
                        line_length += len(word) + 1
                    else:
                        c.drawString(90, y_position, ' '.join(line))
                        y_position -= 15
                        line = [word]
                        line_length = len(word)
                        
                        if y_position < 50:  # Add new page if running out of space
                            c.showPage()
                            y_position = height - 50
                
                if line:
                    c.drawString(90, y_position, ' '.join(line))
                    y_position -= 15
                
                y_position -= 10  # Add some space between orders
                
                if y_position < 100:  # Add new page if running out of space
                    c.showPage()
                    y_position = height - 50
            
            # Add footer
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(50, 30, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Save the PDF
            c.save()
            
            print(f"PDF generated: {pdf_path}")
            return pdf_path
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            raise

# Example usage
if __name__ == "__main__":
    import argparse
    
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Fetch case details from eCourts')
    parser.add_argument('case_type', help='Type of case (e.g., CIVIL, CRIMINAL)')
    parser.add_argument('case_number', help='Case number')
    parser.add_argument('year', help='Year of filing')
    parser.add_argument('--court', choices=['high_court', 'district_court'], 
                       default='high_court', help='Type of court')
    
    args = parser.parse_args()
    
    # Initialize scraper
    scraper = CourtScraper()
    
    try:
        # Fetch case details
        case_data = scraper.fetch_case_details(
            args.case_type,
            args.case_number,
            args.year,
            args.court
        )
        
        # Print case data
        print("\nCase Details:")
        print("-" * 50)
        for key, value in case_data['case_details'].items():
            print(f"{key.replace('_', ' ').title()}: {value}")
        
        print("\nParties:")
        print("-" * 50)
        for party in case_data.get('parties', []):
            print(f"\n{party.get('type', 'Party')}:")
            print(f"  Name: {party.get('name', 'N/A')}")
            print(f"  Advocate: {party.get('advocate', 'N/A')}")
            print(f"  Address: {party.get('address', 'N/A')}")
        
        print("\nPDF generated at:", case_data.get('pdf_path', 'N/A'))
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
