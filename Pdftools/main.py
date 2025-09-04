import os
import re
import io
import zipfile
from flask import Flask, request, render_template_string, send_file, flash
import fitz  # PyMuPDF
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# Initialize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key-for-a-cool-app'

# The entire frontend is packed into this single string.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Professional PDF Toolkit</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-color: #007bff;
            --primary-hover: #0056b3;
            --background-color: #f8f9fa;
            --card-background: #ffffff;
            --text-color: #343a40;
            --border-color: #dee2e6;
            --success-bg: #d1e7dd;
            --success-text: #0a3622;
            --error-bg: #f8d7da;
            --error-text: #842029;
        }
        body {
            font-family: 'Poppins', sans-serif;
            margin: 0;
            padding: 2rem 1rem;
            background-color: var(--background-color);
            color: var(--text-color);
            display: flex;
            justify-content: center;
            align-items: flex-start;
            min-height: 100vh;
        }
        .container {
            max-width: 700px;
            width: 100%;
        }
        .header {
            text-align: center;
            margin-bottom: 2.5rem;
        }
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            color: var(--primary-color);
            margin: 0;
        }
        .header p {
            font-size: 1.1rem;
            color: #6c757d;
        }
        .tool-card {
            background-color: var(--card-background);
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
            padding: 2.5rem;
            margin-bottom: 2rem;
            transition: transform 0.2s ease-in-out;
        }
        .tool-card:hover {
            transform: translateY(-5px);
        }
        .tool-card h2 {
            margin-top: 0;
            font-size: 1.75rem;
            font-weight: 600;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1rem;
            margin-bottom: 1.5rem;
        }
        .form-group {
            margin-bottom: 1.5rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.75rem;
            font-weight: 600;
            font-size: 1rem;
        }
        .form-control {
            width: 100%;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            border: 1px solid #ced4da;
            box-sizing: border-box;
            font-family: 'Poppins', sans-serif;
            font-size: 1rem;
            transition: border-color 0.2s, box-shadow 0.2s;
        }
        .form-control:focus {
            border-color: var(--primary-color);
            outline: 0;
            box-shadow: 0 0 0 0.25rem rgba(0, 123, 255, 0.25);
        }
        .file-upload-wrapper {
            position: relative;
            overflow: hidden;
            display: flex;
        }
        .file-upload-input {
            position: absolute;
            left: 0;
            top: 0;
            opacity: 0;
            width: 100%;
            height: 100%;
            cursor: pointer;
        }
        .file-upload-button {
            background-color: #6c757d;
            color: white;
            padding: 0.75rem 1rem;
            border-top-left-radius: 8px;
            border-bottom-left-radius: 8px;
            white-space: nowrap;
        }
        .file-name-display {
            flex-grow: 1;
            padding: 0.75rem 1rem;
            border: 1px solid #ced4da;
            border-left: none;
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            color: #6c757d;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .submit-btn {
            width: 100%;
            padding: 0.85rem 1.5rem;
            border: none;
            border-radius: 8px;
            background-color: var(--primary-color);
            color: white;
            font-size: 1.1rem;
            font-weight: 600;
            cursor: pointer;
            transition: background-color 0.2s, transform 0.1s;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        .submit-btn:hover:not(:disabled) {
            background-color: var(--primary-hover);
            transform: scale(1.02);
        }
        .submit-btn:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
            opacity: 0.8;
        }
        .spinner {
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 10px;
        }
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .message {
            text-align: center;
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            font-weight: 600;
        }
        .error {
            background-color: var(--error-bg);
            color: var(--error-text);
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Professional PDF Toolkit</h1>
            <p>Your one-stop solution for quick PDF modifications.</p>
        </div>
        
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="message {{ category }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}

        <div class="tool-card">
            <h2>Add Page Numbers</h2>
            <form action="/add_page_numbers" method="post" enctype="multipart/form-data" class="pdf-form">
                <div class="form-group">
                    <label for="pdf_file_numbers">Upload your PDF file</label>
                    <div class="file-upload-wrapper">
                        <span class="file-upload-button">Choose File</span>
                        <span class="file-name-display">No file selected...</span>
                        <input type="file" id="pdf_file_numbers" name="pdf_file" accept=".pdf" required class="file-upload-input">
                    </div>
                </div>
                <button type="submit" class="submit-btn">
                    <span class="btn-text">Add Numbers & Download</span>
                </button>
            </form>
        </div>

        <div class="tool-card">
            <h2>Split PDF into Multiple Files</h2>
            <form action="/split_pdf" method="post" enctype="multipart/form-data" class="pdf-form">
                <div class="form-group">
                    <label for="pdf_file_split">Upload your PDF file</label>
                     <div class="file-upload-wrapper">
                        <span class="file-upload-button">Choose File</span>
                        <span class="file-name-display">No file selected...</span>
                        <input type="file" id="pdf_file_split" name="pdf_file" accept=".pdf" required class="file-upload-input">
                    </div>
                </div>
                <div class="form-group">
                    <label for="page_ranges">Page Ranges to Split</label>
                    <input type="text" id="page_ranges" name="page_ranges" class="form-control" placeholder="e.g., 1-3, 5, 8-10" required>
                </div>
                <button type="submit" class="submit-btn">
                    <span class="btn-text">Split & Download ZIP</span>
                </button>
            </form>
        </div>
    </div>

    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Handle custom file input display
            const fileInputs = document.querySelectorAll('.file-upload-input');
            fileInputs.forEach(input => {
                input.addEventListener('change', function() {
                    const fileNameDisplay = this.parentElement.querySelector('.file-name-display');
                    if (this.files.length > 0) {
                        fileNameDisplay.textContent = this.files[0].name;
                    } else {
                        fileNameDisplay.textContent = 'No file selected...';
                    }
                });
            });

            // Handle form submission with loading state
            const forms = document.querySelectorAll('.pdf-form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    const submitBtn = this.querySelector('.submit-btn');
                    const btnText = submitBtn.querySelector('.btn-text');

                    // Basic validation
                    const fileInput = this.querySelector('input[type="file"]');
                    if (fileInput.files.length === 0) {
                        alert('Please select a PDF file first.');
                        e.preventDefault();
                        return;
                    }

                    // Show loading state
                    submitBtn.disabled = true;
                    btnText.textContent = 'Processing...';
                    const spinner = document.createElement('div');
                    spinner.className = 'spinner';
                    submitBtn.prepend(spinner);
                });
            });
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/add_page_numbers', methods=['POST'])
def add_page_numbers():
    if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
        flash('No file was selected. Please upload a PDF.', 'error')
        return index()

    file = request.files['pdf_file']
    if file and file.filename.endswith('.pdf'):
        original_pdf_bytes = file.read()
        original_doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
        
        page_one = original_doc[0]
        page_width, page_height = page_one.rect.width, page_one.rect.height

        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=(page_width, page_height))
        for page_num in range(1, len(original_doc) + 1):
            c.setFont("Helvetica", 12)
            c.drawRightString(page_width - 20, 20, str(page_num))
            c.showPage()
        c.save()
        
        packet.seek(0)
        numbers_pdf = fitz.open(stream=packet, filetype="pdf")

        for i, page in enumerate(original_doc):
            if i < len(numbers_pdf):
                page.show_pdf_page(page.rect, numbers_pdf, i)

        output_pdf_bytes = io.BytesIO()
        original_doc.save(output_pdf_bytes)
        original_doc.close()
        numbers_pdf.close()
        output_pdf_bytes.seek(0)

        return send_file(
            output_pdf_bytes,
            as_attachment=True,
            download_name='numbered_document.pdf',
            mimetype='application/pdf'
        )
        
    flash('Invalid file type. Please upload a PDF.', 'error')
    return index()

@app.route('/split_pdf', methods=['POST'])
def split_pdf():
    if 'pdf_file' not in request.files or request.files['pdf_file'].filename == '':
        flash('No file was selected. Please upload a PDF.', 'error')
        return index()
    
    file = request.files['pdf_file']
    page_ranges_str = request.form.get('page_ranges')
    
    if not page_ranges_str:
        flash('Page ranges were not provided.', 'error')
        return index()

    if file and file.filename.endswith('.pdf'):
        pdf_bytes = file.read()
        original_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        try:
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'a', zipfile.ZIP_DEFLATED, False) as zip_file:
                ranges = [r.strip() for r in page_ranges_str.split(',') if r.strip()]
                for r in ranges:
                    new_doc = fitz.open()
                    pages_in_range = []
                    if '-' in r:
                        start, end = map(int, r.split('-'))
                        pages_in_range = range(start - 1, end)
                    else:
                        pages_in_range = [int(r) - 1]
                    
                    for page_num in pages_in_range:
                        if 0 <= page_num < len(original_doc):
                            new_doc.insert_pdf(original_doc, from_page=page_num, to_page=page_num)
                    
                    if len(new_doc) > 0:
                        pdf_buffer = io.BytesIO()
                        new_doc.save(pdf_buffer)
                        pdf_buffer.seek(0)
                        zip_file.writestr(f'split_pages_{r}.pdf', pdf_buffer.getvalue())
                    new_doc.close()

            original_doc.close()

            if len(zip_file.infolist()) == 0:
                flash('The specified page ranges are not valid for this document.', 'error')
                return index()

            zip_buffer.seek(0)
            return send_file(
                zip_buffer,
                as_attachment=True,
                download_name='split_documents.zip',
                mimetype='application/zip'
            )
        except ValueError:
            flash('Invalid page range format. Please use formats like "1-3, 5, 8-10".', 'error')
            return index()
    
    flash('Invalid file type. Please upload a PDF.', 'error')
    return index()

if __name__ == '__main__':
    app.run(debug=True)
