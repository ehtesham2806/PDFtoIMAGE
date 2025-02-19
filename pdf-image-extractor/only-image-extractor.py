from flask import Flask, request, send_file, render_template_string
from PyPDF2 import PdfReader
from PIL import Image
import io
import base64
import fitz  # PyMuPDF

app = Flask(__name__)

# HTML template with file upload form
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PDF First Page Extractor</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .upload-form {
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            margin: 20px 0;
        }
        .result {
            margin-top: 20px;
            text-align: center;
        }
        .error {
            background-color: #ffe6e6;
            border: 1px solid #ff9999;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        img {
            max-width: 100%;
            height: auto;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <h1>PDF First Page Extractor</h1>
    
    {% if error %}
    <div class="error">
        <h3>Error:</h3>
        <p>{{ error }}</p>
    </div>
    {% endif %}

    <div class="upload-form">
        <form method="post" enctype="multipart/form-data">
            <input type="file" name="pdf" accept=".pdf" required>
            <button type="submit">Extract First Page</button>
        </form>
    </div>
    
    {% if image_data %}
    <div class="result">
        <h2>First Page Preview</h2>
        <img src="data:image/jpeg;base64,{{ image_data }}" alt="First page">
        <p><a href="/download" download="first_page.jpg">Download JPG</a></p>
    </div>
    {% endif %}
</body>
</html>
'''

def extract_first_page(pdf_bytes):
    """Extract the first page of a PDF and convert it to an image"""
    # Open the PDF using PyMuPDF
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    
    # Get the first page
    first_page = pdf_document[0]
    
    # Convert page to image
    pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))  # 300 DPI
    
    # Convert to PIL Image
    img_data = pix.tobytes("jpeg")
    
    # Clean up
    pdf_document.close()
    
    return img_data

@app.route('/', methods=['GET', 'POST'])
def index():
    image_data = None
    error = None

    if request.method == 'POST':
        if 'pdf' not in request.files:
            error = 'No file uploaded'
        else:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                error = 'No file selected'
            else:
                try:
                    # Read PDF file
                    pdf_bytes = pdf_file.read()
                    
                    # Extract and convert first page
                    img_bytes = extract_first_page(pdf_bytes)
                    
                    # Store in session for download
                    app.config['LAST_IMAGE'] = img_bytes
                    
                    # Convert to base64 for preview
                    image_data = base64.b64encode(img_bytes).decode()
                    
                except Exception as e:
                    error = f'An error occurred: {str(e)}'

    return render_template_string(HTML_TEMPLATE, 
                                image_data=image_data, 
                                error=error)

@app.route('/download')
def download():
    if 'LAST_IMAGE' not in app.config:
        return 'No image available', 404
    
    return send_file(
        io.BytesIO(app.config['LAST_IMAGE']),
        mimetype='image/jpeg',
        as_attachment=True,
        download_name='first_page.jpg'
    )

if __name__ == '__main__':
    app.run(debug=True)