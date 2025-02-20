from flask import Flask, request, send_file, render_template_string
from PyPDF2 import PdfReader
from PIL import Image
import io
import base64
import fitz  # PyMuPDF
from dropdowns import DROPDOWN_OPTIONS  # Import dropdown options

app = Flask(__name__)

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PDF First Page Extractor</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <!-- Add jQuery (required for Select2) -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <!-- Add Select2 CSS and JS -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
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
            text-align: left;
            padding: 0 20%;
        }
        .form-group label {
            display: block;
            margin-bottom: 5px;
        }
        .select2-container {
            width: 100% !important;
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
            height: auto;
            width: auto;
            max-height: 100%;
        }
    </style>
    <script>
    function updateDimensions() {
        let dropdown = document.getElementById("templateSelect");
        let selectedOption = dropdown.value;
        let widthInput = document.getElementById("width");
        let heightInput = document.getElementById("height");

        let dimensions = JSON.parse(dropdown.options[dropdown.selectedIndex].getAttribute("data-dimensions"));
        widthInput.value = dimensions.width;
        heightInput.value = dimensions.height;
    }

    // Initialize Select2 when document is ready
    $(document).ready(function() {
        $('#templateSelect').select2({
            placeholder: "Search and select a template",
            allowClear: true,
            width: '100%'
        });

        // Update dimensions when Select2 selection changes
        $('#templateSelect').on('select2:select', function (e) {
            updateDimensions();
        });
    });
    </script>
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
                <label for="pdf">Upload PDF:</label>
                <input type="file" name="pdf" accept=".pdf" required>
            </div>
            <div class="form-group">
                <label for="templateSelect">Select Template:</label>
                <select id="templateSelect" name="templateSelect">
                    <option value="">-- Select an option --</option>
                    {% for key, values in dropdown_options.items() %}
                        <option value="{{ key }}" data-dimensions='{{ values | tojson }}'>{{ values.name }}</option>
                    {% endfor %}
                </select>
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
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page = pdf_document[0]
    pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
    img_data = pix.tobytes("jpeg")
    pdf_document.close()
    return img_data

@app.route('/', methods=['GET', 'POST'])
def index():
    image_data = None
    error = None
    width = 800
    height = 600
    bgcolor = "#ffffff"

    if request.method == 'POST':
        if 'pdf' not in request.files:
            error = 'No file uploaded'
        else:
            pdf_file = request.files['pdf']
            if pdf_file.filename == '':
                error = 'No file selected'
            else:
                try:
                    template = request.form.get("templateSelect")
                    if template in DROPDOWN_OPTIONS:
                        width = DROPDOWN_OPTIONS[template]["width"]
                        height = DROPDOWN_OPTIONS[template]["height"]

                    width = int(request.form.get('width', width))
                    height = int(request.form.get('height', height))
                    bgcolor = request.form.get('bgcolor', bgcolor)

                    pdf_bytes = pdf_file.read()
                    img_bytes = extract_first_page(pdf_bytes)
                    image_data = base64.b64encode(img_bytes).decode()
                except Exception as e:
                    error = f'An error occurred: {str(e)}'

    return render_template_string(HTML_TEMPLATE, 
                                image_data=image_data, 
                                error=error,
                                width=width,
                                height=height,
                                bgcolor=bgcolor,
                                dropdown_options=DROPDOWN_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)