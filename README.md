# HTML Page Labels

A Flask web application that validates and processes PDF files with corresponding HTML content by adding breakup labels.

## Features

- Upload PDF and HTML files via web interface
- Automatic content validation and comparison between PDF and HTML
- Smart matching with 80% similarity threshold
- Error handling with user-friendly messages
- Modern, responsive UI design

## Requirements

- Python 3.12 or higher
- Flask 3.1.2
- PyPDF2 3.0.1
- BeautifulSoup4 4.14.3

## Quick Start

### Windows

**Option 1: Automated Setup (Recommended)**

1. Run the setup script (first time only):
   ```bash
   setup.bat
   ```

2. Start the application:
   ```bash
   start.bat
   ```

**Option 2: Manual Setup**

1. Create virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate virtual environment:
   ```bash
   venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open browser to: http://127.0.0.1:5000

### Linux/Mac

1. Create virtual environment:
   ```bash
   python3 -m venv venv
   ```

2. Activate virtual environment:
   ```bash
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Open browser to: http://127.0.0.1:5000

## Usage

1. Open the application in your browser
2. Upload a PDF file
3. Upload the corresponding HTML file
4. Click "Add BreakUp Labels"
5. The application will validate that the content matches
6. If content matches, you'll see a success message
7. If content doesn't match, you'll see an error with details

## Project Structure

```
HtmlPageLabels/
├── app.py                  # Main Flask application
├── extract_and_insert.py  # PDF/HTML processing utilities
├── requirements.txt        # Python dependencies
├── setup.bat              # Windows setup script
├── start.bat              # Windows startup script
├── templates/
│   └── upload.html        # Web interface template
├── uploads/               # Uploaded files directory (auto-created)
└── README.md             # This file
```

## Development

### Running in Debug Mode

The application runs in debug mode by default, which enables:
- Auto-reload on code changes
- Detailed error messages
- Debug toolbar

To disable debug mode, edit `app.py`:
```python
app.run(debug=False)
```

### Adding Features

1. Modify `app.py` for backend logic
2. Edit `templates/upload.html` for UI changes
3. Update `extract_and_insert.py` for PDF/HTML processing

## Troubleshooting

**Application won't start:**
- Ensure Python is installed and in PATH
- Check that port 5000 is not in use
- Verify all dependencies are installed

**File upload errors:**
- Ensure files are actual PDF/HTML formats
- Check file permissions
- Verify uploads directory exists and is writable

**Content mismatch errors:**
- Verify PDF and HTML contain the same text
- Check for encoding issues
- Review similarity threshold in `app.py`

## License

This project is for internal use.

## Author

Developed with Claude Code
