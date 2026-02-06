from flask import Flask, render_template, request, redirect, url_for
import os
import PyPDF2
from bs4 import BeautifulSoup
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Directory to store uploaded files

# Ensure the directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF file"""
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text += page.extract_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    return text

def extract_text_from_html(html_path):
    """Extract text from HTML file"""
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            text = soup.get_text()
    except Exception as e:
        print(f"Error reading HTML: {e}")
        return None
    return text

def normalize_text(text):
    """Normalize text for comparison by removing extra whitespace"""
    if text is None:
        return ""
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    # Convert to lowercase for case-insensitive comparison
    return text.lower()

def compare_content(pdf_text, html_text):
    """Compare PDF and HTML content"""
    pdf_normalized = normalize_text(pdf_text)
    html_normalized = normalize_text(html_text)

    # Calculate similarity (simple approach: check if main content matches)
    # For a more lenient comparison, we check if most of the content is present
    if not pdf_normalized or not html_normalized:
        return False, "Unable to extract content from one or both files."

    # Check if contents are similar (allowing for minor formatting differences)
    if pdf_normalized == html_normalized:
        return True, "Content matches perfectly."

    # Check if HTML contains most of the PDF content (or vice versa)
    similarity_threshold = 0.8
    if pdf_normalized in html_normalized or html_normalized in pdf_normalized:
        return True, "Content matches (with formatting differences)."

    # Calculate basic similarity
    common_chars = sum(1 for a, b in zip(pdf_normalized, html_normalized) if a == b)
    max_len = max(len(pdf_normalized), len(html_normalized))
    similarity = common_chars / max_len if max_len > 0 else 0

    if similarity >= similarity_threshold:
        return True, f"Content is sufficiently similar ({similarity*100:.1f}%)."

    return False, f"Content mismatch detected. The PDF and HTML files contain different content (similarity: {similarity*100:.1f}%)."

@app.route('/')
def upload_files():
    return render_template('upload.html')

@app.route('/process', methods=['POST'])
def process_files():
    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        html_file = request.files.get('html_file')

        # Validate that both files are provided
        if not pdf_file or not pdf_file.filename:
            return render_template('upload.html', error="Please select a PDF file.")

        if not html_file or not html_file.filename:
            return render_template('upload.html', error="Please select an HTML file.")

        # Validate file extensions
        if not pdf_file.filename.endswith('.pdf'):
            return render_template('upload.html', error="Invalid PDF file. Please upload a .pdf file.")

        if not html_file.filename.endswith('.html'):
            return render_template('upload.html', error="Invalid HTML file. Please upload a .html file.")

        # Save uploaded files
        pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_file.filename)
        html_path = os.path.join(app.config['UPLOAD_FOLDER'], html_file.filename)

        pdf_file.save(pdf_path)
        html_file.save(html_path)

        # Extract text from both files
        pdf_text = extract_text_from_pdf(pdf_path)
        html_text = extract_text_from_html(html_path)

        # Compare content
        is_match, message = compare_content(pdf_text, html_text)

        if not is_match:
            # Return error if content doesn't match
            return render_template('upload.html', error=message)

        # If content matches, proceed with processing
        return render_template('upload.html', success=f"Files uploaded successfully! {message} Ready to add breakup labels.")

    return redirect(url_for('upload_files'))

if __name__ == '__main__':
    app.run(debug=True)
