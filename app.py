from flask import Flask, request, send_file, render_template_string
from PyPDF2 import PdfReader
from PIL import Image
import io
import base64
import fitz  # PyMuPDF

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PDF First Page Extractor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
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
        .form-group {
            margin: 10px 0;
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
        .preview-container {
            position: relative;
            margin: 20px auto;
        }
        .background {
            display: flex;
            justify-content: center;
            align-items: flex-end;
            padding: 50px 50px 0px 50px;
            margin: 0 auto;
        }
        .preview-image {
            max-width: 90%;
            height: 100%;
            width: auto;
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
            <div class="form-group">
                <input type="file" name="pdf" accept=".pdf" required>
            </div>
            <div class="form-group">
                <label for="width">Container Width (px):</label>
                <input type="number" name="width" id="width" value="800" min="100" max="2000">
            </div>
            <div class="form-group">
                <label for="height">Container Height (px):</label>
                <input type="number" name="height" id="height" value="600" min="100" max="2000">
            </div>
            <div class="form-group">
                <label for="bgcolor">Background Color:</label>
                <input type="color" name="bgcolor" id="bgcolor" value="#ffffff">
            </div>
            <button type="submit">Extract First Page</button>
        </form>
    </div>
    
    {% if image_data %}
    <div class="result">
        <h2>First Page Preview</h2>
        <div class="preview-container">
            <div id="capture" class="background" style="background-color: {{ bgcolor }}; width: {{ width }}px; height: {{ height }}px;">
                <img src="data:image/jpeg;base64,{{ image_data }}" 
                     alt="First page"
                     class="preview-image">
            </div>
        </div>
        <p><button onclick="downloadImage()">Download Complete Image</button></p>
    </div>

    <script>
    async function downloadImage() {
        const element = document.getElementById('capture');
        const canvas = await html2canvas(element, {
            backgroundColor: null,
            scale: 2
        });
        
        const link = document.createElement('a');
        link.download = 'complete_image.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
    </script>
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
    
    # Convert to JPEG bytes
    img_data = pix.tobytes("jpeg")
    
    # Clean up
    pdf_document.close()
    
    return img_data

@app.route('/', methods=['GET', 'POST'])
def index():
    image_data = None
    error = None
    width = 800  # default width
    height = 600  # default height
    bgcolor = "#ffffff"  # default background color

    if request.method == 'POST':
        if 'pdf' not in request.files:
            error = 'No file uploaded'
        else:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                error = 'No file selected'
            else:
                try:
                    # Get form values
                    width = int(request.form.get('width', width))
                    height = int(request.form.get('height', height))
                    bgcolor = request.form.get('bgcolor', bgcolor)
                    
                    # Read PDF file
                    pdf_bytes = pdf_file.read()
                    
                    # Extract and convert first page
                    img_bytes = extract_first_page(pdf_bytes)
                    
                    # Convert to base64 for preview
                    image_data = base64.b64encode(img_bytes).decode()
                    
                except Exception as e:
                    error = f'An error occurred: {str(e)}'

    return render_template_string(HTML_TEMPLATE, 
                                image_data=image_data, 
                                error=error,
                                width=width,
                                height=height,
                                bgcolor=bgcolor)

if __name__ == '__main__':
    app.run(debug=True)