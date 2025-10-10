# Court Data Fetcher and Judgement Downloader

A web application for searching and downloading court case details and judgments from Indian courts. This tool provides an easy-to-use interface for legal professionals, researchers, and the general public to access court records.

## Features

- **Advanced Case Search**: Search for cases by case number, year, and court type
- **Multi-step Search Form**: User-friendly interface with step-by-step case search
- **CAPTCHA Verification**: Secure search functionality with CAPTCHA verification
- **Case Details View**: Comprehensive view of case information including parties and orders
- **PDF Download**: Download case details as PDF for offline reference
- **Responsive Design**: Works on desktop and mobile devices

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/court-data-fetcher-and-judgement-downloader.git
   cd court-data-fetcher-and-judgement-downloader
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   python -c "from app import app, db; app.app_context().push(); db.create_all()"
   ```

5. **Create required directories**
   ```bash
   mkdir -p static/uploads static/captcha static/css static/js
   ```

## Configuration

Create a `.env` file in the root directory with the following variables:

```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///court_data.db
UPLOAD_FOLDER=static/uploads
CAPTCHA_FOLDER=static/captcha
```

## Running the Application

1. **Start the development server**
   ```bash
   python app.py
   ```

2. **Access the application**
   Open your web browser and navigate to `http://localhost:5000`

## Project Structure

```
court-data-fetcher-and-judgement-downloader/
├── app.py                  # Main application file
├── captcha.py              # CAPTCHA generation utility
├── config.py               # Configuration settings
├── models.py               # Database models
├── requirements.txt        # Project dependencies
├── static/                 # Static files
│   ├── css/               # CSS stylesheets
│   ├── js/                # JavaScript files
│   ├── uploads/           # Uploaded files
│   └── captcha/           # Generated CAPTCHA images
└── templates/             # HTML templates
    ├── base.html          # Base template
    ├── index.html         # Home page
    ├── search.html        # Search interface
    └── cause_list.html    # Cause list view
```

## API Endpoints

- `GET /` - Home page
- `GET /search` - Advanced search interface
- `GET /api/init` - Initialize search session and get CAPTCHA
- `GET /api/districts/<state>` - Get districts for a state
- `GET /api/case-types` - Get available case types
- `POST /api/search` - Search for cases
- `GET /case/<int:search_id>` - View case details
- `GET /api/case/<int:search_id>/download` - Download case details as PDF

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Flask](https://flask.palletsprojects.com/) - The web framework used
- [Bootstrap](https://getbootstrap.com/) - For responsive design
- [Pillow](https://python-pillow.org/) - For image processing

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.

---

*This project is for educational purposes only. Please ensure you have the right to access and download the court data in accordance with applicable laws and regulations.*
