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
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Resource Creative Generator!</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/css/select2.min.css" rel="stylesheet" />
    <script src="https://cdnjs.cloudflare.com/ajax/libs/select2/4.0.13/js/select2.min.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .upload-form {
            border: 2px dashed #ccc;
            padding: 20px;
            text-align: center;
            margin: 0px 0px 20px 0;
        }
        .form-group {
            margin: 10px 0;
            text-align: left;
            padding: 0 20px;
        }
        .select2-container {
            width: 100% !important;
        }
        .background {
            display: flex;
            justify-content: center;
            padding: 50px;
            margin: 0 auto;
            box-sizing: border-box;
        }
        .background.landscape {
            align-items: center;
        }
        .background.portrait {
            align-items: flex-end;
            padding: 50px 50px 0px 50px;
        }
        .preview-image {
            max-width: 90%;
            height: auto;
            width: auto;
            max-height: 100%;
        }
    </style>
</head>
<body class="bg-gray-50 min-h-screen">
    <div class="max-w-7xl mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold text-center mb-8 text-gray-800">Resource Creative Generator!</h1>
        
        {% if error %}
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6">
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <h3 class="text-sm font-medium text-red-800">Error</h3>
                    <p class="text-sm text-red-700">{{ error }}</p>
                </div>
            </div>
        </div>
        {% endif %}

        <div class="flex flex-col lg:flex-row gap-8">
            <!-- Left side - Form -->
            <div class="lg:w-1/3">
                <div class="bg-white rounded-xl shadow-md p-6">
                    <form method="post" enctype="multipart/form-data">
                        <div class="mt-0 upload-form bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 hover:border-blue-500 transition-colors">
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Upload PDF</label>
                                <input type="file" name="pdf" accept=".pdf" required
                                    class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100">
                            </div>
                            
                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Select DP</label>
                                <select id="templateSelect" name="templateSelect" class="block appearance-none w-full bg-gray-200 border border-gray-200 text-gray-700 py-3 px-4 pr-8 rounded leading-tight focus:outline-none focus:bg-white focus:border-gray-500">
                                    <option value="">-- Select an option --</option>
                                    {% for key, values in dropdown_options.items() %}
                                        <option value="{{ key }}" data-dimensions='{{ values | tojson }}'>{{ values.name }}</option>
                                    {% endfor %}
                                </select>
                            </div>

                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Width (px)</label>
                                <input type="number" name="width" id="width" value="800" min="100" max="2000"
                                    class="bg-gray-200 appearance-none border-2 border-gray-200 rounded w-full py-2 px-4 text-gray-700 leading-tight focus:outline-none focus:bg-white focus:border-purple-500">
                            </div>

                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Height (px)</label>
                                <input type="number" name="height" id="height" value="600" min="100" max="2000"
                                    class="bg-gray-200 appearance-none border-2 border-gray-200 rounded w-full py-2 px-4 text-gray-700 leading-tight focus:outline-none focus:bg-white focus:border-purple-500">
                            </div>

                            <div class="form-group">
                                <label class="block text-sm font-medium text-gray-700 mb-2">Background Color</label>
                                <input type="color" name="bgcolor" id="bgcolor" value="#ffffff"
                                    class="mt-1 block w-full h-10 rounded-md border-gray-300 shadow-sm">
                            </div>
                        </div>

                        <button type="submit" 
                            class="w-full bg-blue-600 text-white text-xs py-3 px-4 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors">
                            Extract First Page
                        </button>
                    </form>
                </div>
            </div>

            <!-- Right side - Preview -->
            <div class="lg:w-2/3">
                <div class="bg-white rounded-xl shadow-md p-6">
                    {% if image_data %}
                    <div class="space-y-6">
                        <div class="flex items-center justify-between">
                            <h2 class="text-xl font-semibold text-gray-800">First Page Preview</h2>
                            <button onclick="downloadImage()"
                                class="inline-flex items-center px-6 py-3 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2 transition-colors">
                                <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"/>
                                </svg>
                                Download Complete Image
                            </button>
                        </div>
                        <div class="preview-container border rounded-lg overflow-hidden p-5">
                            <div id="capture" 
                                 class="background {{ 'landscape' if is_landscape else 'portrait' }}"
                                 style="background-color: {{ bgcolor }}; width: {{ width }}px; height: {{ height }}px;">
                                <img src="data:image/jpeg;base64,{{ image_data }}"
                                     alt="First page"
                                     class="preview-image">
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex flex-col items-center justify-center h-[500px] text-gray-500">
                        <svg class="w-16 h-16 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"/>
                        </svg>
                        <p class="text-lg">Upload a PDF to see the preview here</p>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>

    <script>
    function updateDimensions() {
        let dropdown = document.getElementById("templateSelect");
        let selectedOption = dropdown.value;
        let widthInput = document.getElementById("width");
        let heightInput = document.getElementById("height");
        let bgcolorInput = document.getElementById("bgcolor");

        if (selectedOption) {
            let dimensions = JSON.parse(dropdown.options[dropdown.selectedIndex].getAttribute("data-dimensions"));
            widthInput.value = dimensions.width;
            heightInput.value = dimensions.height;
            bgcolorInput.value = dimensions.bgcolor;
            
            // Update the preview background color if it exists
            let previewBg = document.querySelector('.background');
            if (previewBg) {
                previewBg.style.backgroundColor = dimensions.bgcolor;
            }
        }
    }

    $(document).ready(function() {
        $('#templateSelect').select2({
            placeholder: "Search and select a template",
            allowClear: true,
            width: '100%'
        });

        $('#templateSelect').on('select2:select', function (e) {
            updateDimensions();
        });
    });

    async function downloadImage() {
        const element = document.getElementById('capture');
        const canvas = await html2canvas(element, {
            backgroundColor: null,
            scale: 1
        });
        
        const link = document.createElement('a');
        link.download = 'complete_image.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    }
    </script>
</body>
</html>
'''

def extract_first_page(pdf_bytes):
    pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
    first_page = pdf_document[0]
    pix = first_page.get_pixmap(matrix=fitz.Matrix(300/72, 300/72))
    img_data = pix.tobytes("jpeg")
    img = Image.open(io.BytesIO(img_data))
    width, height = img.size
    is_landscape = width > height
    pdf_document.close()
    return img_data, is_landscape

@app.route('/', methods=['GET', 'POST'])
def index():
    image_data = None
    error = None
    width = 800
    height = 600
    bgcolor = "#ffffff"
    is_landscape = False

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
                    img_bytes, is_landscape = extract_first_page(pdf_bytes)
                    image_data = base64.b64encode(img_bytes).decode()
                except Exception as e:
                    error = f'An error occurred: {str(e)}'

    return render_template_string(HTML_TEMPLATE, 
                                image_data=image_data, 
                                error=error,
                                width=width,
                                height=height,
                                bgcolor=bgcolor,
                                is_landscape=is_landscape,
                                dropdown_options=DROPDOWN_OPTIONS)

if __name__ == '__main__':
    app.run(debug=True)