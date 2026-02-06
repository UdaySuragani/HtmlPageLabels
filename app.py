from flask import Flask, render_template, request, redirect, url_for
import os
import PyPDF2
from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher

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
    """Normalize text for comparison by removing extra whitespace and special characters"""
    if text is None:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove special Unicode characters and normalize whitespace
    text = re.sub(r'[\u00A0\u1680\u2000-\u200B\u202F\u205F\u3000]', ' ', text)  # Various space chars
    text = re.sub(r'[\u2018\u2019]', "'", text)  # Smart quotes to regular quotes
    text = re.sub(r'[\u201C\u201D]', '"', text)  # Smart double quotes
    text = re.sub(r'[\u2013\u2014]', '-', text)  # Dashes

    # Remove non-alphanumeric characters except spaces (keeps only letters, numbers, and spaces)
    text = re.sub(r'[^a-z0-9\s]', ' ', text)

    # Collapse multiple spaces into one
    text = re.sub(r'\s+', ' ', text)

    # Remove leading/trailing whitespace
    text = text.strip()

    return text

def calculate_similarity(text1, text2):
    """Calculate similarity between two texts using SequenceMatcher"""
    if not text1 or not text2:
        return 0.0

    # Use SequenceMatcher for better text comparison
    matcher = SequenceMatcher(None, text1, text2)
    return matcher.ratio()

def compare_content(pdf_text, html_text):
    """Compare PDF and HTML content with improved fuzzy matching"""
    pdf_normalized = normalize_text(pdf_text)
    html_normalized = normalize_text(html_text)

    # Check if we extracted content from both files
    if not pdf_normalized or not html_normalized:
        return False, "Unable to extract content from one or both files."

    # Check for exact match
    if pdf_normalized == html_normalized:
        return True, "Content matches perfectly."

    # Check if one contains the other (for subset matches)
    if pdf_normalized in html_normalized or html_normalized in pdf_normalized:
        return True, "Content matches (with formatting differences)."

    # Calculate similarity using SequenceMatcher (better algorithm)
    similarity = calculate_similarity(pdf_normalized, html_normalized)

    # More lenient threshold: 70% similarity
    similarity_threshold = 0.70

    if similarity >= similarity_threshold:
        return True, f"Content is sufficiently similar ({similarity*100:.1f}% match)."

    # Provide detailed error message
    pdf_words = len(pdf_normalized.split())
    html_words = len(html_normalized.split())

    return False, (f"Content mismatch detected. Similarity: {similarity*100:.1f}%. "
                   f"PDF has {pdf_words} words, HTML has {html_words} words. "
                   f"Please ensure both files contain the same text content.")

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
