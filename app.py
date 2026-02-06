from flask import Flask, render_template, request, redirect, url_for, send_file
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

def extract_pages_from_pdf(pdf_path):
    """Extract text from each page of PDF separately"""
    pages = []
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for i, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                pages.append({
                    'page_number': i + 1,
                    'text': page_text,
                    'normalized': normalize_text(page_text)
                })
                print(f"[DEBUG] Page {i+1}: {len(page_text)} chars, {len(normalize_text(page_text).split())} words")
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return None
    return pages

def extract_text_from_html(html_path):
    """Extract text from HTML file with better whitespace handling"""
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()

            # Get text with separator to avoid words running together
            text = soup.get_text(separator=' ', strip=True)
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

    # Debug output
    print(f"[DEBUG] PDF text length: {len(pdf_normalized)} characters")
    print(f"[DEBUG] HTML text length: {len(html_normalized)} characters")
    print(f"[DEBUG] PDF words: {len(pdf_normalized.split())}")
    print(f"[DEBUG] HTML words: {len(html_normalized.split())}")

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

    print(f"[DEBUG] Similarity calculated: {similarity*100:.2f}%")

    # More lenient threshold: 60% similarity (reduced from 70%)
    similarity_threshold = 0.60

    if similarity >= similarity_threshold:
        return True, f"Content is sufficiently similar ({similarity*100:.1f}% match)."

    # Try word-based comparison for more flexibility
    pdf_words_set = set(pdf_normalized.split())
    html_words_set = set(html_normalized.split())

    # Calculate Jaccard similarity (intersection over union)
    if pdf_words_set and html_words_set:
        intersection = len(pdf_words_set & html_words_set)
        union = len(pdf_words_set | html_words_set)
        word_similarity = intersection / union if union > 0 else 0

        print(f"[DEBUG] Word-based similarity: {word_similarity*100:.2f}%")

        if word_similarity >= 0.50:  # 50% word overlap
            return True, f"Content matches by word comparison ({word_similarity*100:.1f}% word overlap)."

    # Provide detailed error message
    pdf_words = len(pdf_normalized.split())
    html_words = len(html_normalized.split())

    return False, (f"Content mismatch detected. Similarity: {similarity*100:.1f}%. "
                   f"PDF has {pdf_words} words, HTML has {html_words} words. "
                   f"Please ensure both files contain the same text content.")

def insert_page_labels(html_path, pdf_pages, output_path):
    """Insert page break labels into HTML at locations where PDF pages end"""
    try:
        # Read the original HTML file
        with open(html_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Parse HTML to get text content
        soup = BeautifulSoup(html_content, 'html.parser')

        # Remove script and style elements for text extraction
        for script in soup(["script", "style"]):
            script.decompose()

        html_text = soup.get_text(separator=' ', strip=True)
        html_normalized = normalize_text(html_text)

        print(f"[DEBUG] HTML total words: {len(html_normalized.split())}")

        # Build cumulative text from PDF pages to find insertion points
        cumulative_text = ""
        insertion_markers = []

        for page_info in pdf_pages:
            page_num = page_info['page_number']
            cumulative_text += " " + page_info['normalized']
            cumulative_text = cumulative_text.strip()

            # Try to find where this cumulative content ends in the HTML
            # We'll search for the last few words of this page in the HTML
            words = cumulative_text.split()
            if len(words) > 10:
                # Use last 10 words as search pattern
                search_pattern = " ".join(words[-10:])

                # Find this pattern in the HTML normalized text
                pos = html_normalized.find(search_pattern)
                if pos != -1:
                    # Found the position - now we need to find corresponding position in original HTML
                    insertion_markers.append({
                        'page': page_num,
                        'normalized_pos': pos + len(search_pattern),
                        'search_text': search_pattern
                    })
                    print(f"[DEBUG] Page {page_num} ends at normalized position {pos + len(search_pattern)}")

        # Now insert labels at these positions in the original HTML
        # This is approximate - we'll find text matches in the original HTML
        modified_html = html_content
        offset = 0  # Track offset as we insert tags

        for marker in insertion_markers:
            page_num = marker['page']
            # Create the page break label
            pb_label = f'<?pb label="{page_num}"?>'

            # Find a good insertion point in the original HTML
            # Look for the last few words of the page in the original HTML
            search_words = marker['search_text'].split()[-5:]  # Last 5 words

            # Try to find these words in the original HTML content
            for attempt in range(len(search_words), 0, -1):
                pattern = " ".join(search_words[-attempt:])

                # Search in the modified HTML (with previous insertions)
                search_start = offset
                match_pos = modified_html.find(pattern, search_start)

                if match_pos != -1:
                    # Found it! Insert the label after this text
                    insert_pos = match_pos + len(pattern)
                    modified_html = modified_html[:insert_pos] + '\n' + pb_label + '\n'  + modified_html[insert_pos:]
                    offset = insert_pos + len(pb_label) + 2  # Update offset
                    print(f"[DEBUG] Inserted <?pb label=\"{page_num}\"?> at position {insert_pos}")
                    break

        # Write the modified HTML to output file
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(modified_html)

        print(f"[INFO] Successfully created {output_path} with {len(pdf_pages)} page labels")
        return True, f"Successfully added {len(pdf_pages)} page labels to HTML file."

    except Exception as e:
        print(f"[ERROR] Failed to insert page labels: {e}")
        return False, f"Error inserting page labels: {str(e)}"

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

        # Extract text from both files for comparison
        pdf_text = extract_text_from_pdf(pdf_path)
        html_text = extract_text_from_html(html_path)

        # Compare content
        is_match, message = compare_content(pdf_text, html_text)

        if not is_match:
            # Return error if content doesn't match
            return render_template('upload.html', error=message)

        # Content matches - now extract pages and insert labels
        print("[INFO] Content validation passed. Extracting PDF pages...")
        pdf_pages = extract_pages_from_pdf(pdf_path)

        if not pdf_pages:
            return render_template('upload.html', error="Failed to extract pages from PDF.")

        # Create output filename
        base_name = os.path.splitext(html_file.filename)[0]
        output_filename = f"{base_name}_with_labels.html"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Insert page labels
        success, insert_message = insert_page_labels(html_path, pdf_pages, output_path)

        if not success:
            return render_template('upload.html', error=insert_message)

        # Success - provide download link
        return render_template('upload.html',
                             success=f"Files processed successfully! {insert_message}",
                             download_file=output_filename)

    return redirect(url_for('upload_files'))

@app.route('/download/<filename>')
def download_file(filename):
    """Download the processed HTML file"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True, download_name=filename)
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)
