from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.genai as genai

from scoring import danger_score, calculate_mood

import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import PyPDF2
from PIL import Image
import pytesseract
import json

load_dotenv()

app = Flask(
    __name__,
    static_folder="../frontend",
    static_url_path=""
)

CORS(app)

# ---------------------------
# Gemini initialization
# ---------------------------
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

available = list(client.models.list())

model_name = None
if any(m.name == "models/gemini-2.5-flash" for m in available):
    model_name = "models/gemini-2.5-flash"
else:
    for m in available:
        if "gemini" in m.name:
            model_name = m.name
            break

if not model_name:
    raise SystemExit("No generative Gemini model found.")

class ModelWrapper:
    def __init__(self, client, model_name):
        self._client = client
        self._model = model_name

    def generate_content(self, prompt: str):
        return self._client.models.generate_content(
            model=self._model,
            contents=prompt
        )

model = ModelWrapper(client, model_name)

# ---------------------------
# Serve frontend
# ---------------------------
@app.route("/")
def serve_index():
    return send_from_directory("../frontend", "index.html")

# ---------------------------
# Helper: extract text
# ---------------------------
def extract_text_from_file(file):
    filename = secure_filename(file.filename)
    ext = filename.lower().split(".")[-1]

    text = ""

    if ext == "txt":
        text = file.read().decode("utf-8", errors="ignore")

    elif ext == "pdf":
        reader = PyPDF2.PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""

    elif ext in ["png", "jpg", "jpeg"]:
        image = Image.open(file)
        text = pytesseract.image_to_string(image)

    else:
        return None, "Unsupported file type. Please upload TXT, PDF, or Image."

    return text.strip(), None

# ---------------------------
# Analyze route (MERGED AI)
# ---------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        text = ""

        if request.is_json:
            data = request.get_json()
            text = data.get("text", "").strip()

        elif "file" in request.files:
            file = request.files["file"]
            if file.filename == "":
                return jsonify({"error": "No file uploaded"}), 400

            extracted_text, err = extract_text_from_file(file)
            if err:
                return jsonify({"error": err}), 400

            text = extracted_text

        else:
            return jsonify({"error": "No input provided"}), 400

        if not text:
            return jsonify({"error": "Extracted text is empty"}), 400

        if len(text) > 5000:
            return jsonify({"error": "Text exceeds 5000 character limit"}), 400

        # ---------------------------
        # Local scoring (FAST)
        # ---------------------------
        score, reasons, confidence = danger_score(text)
        mood_emoji, mood_label, mood_class = calculate_mood(score)

        # ---------------------------
        # ONE Gemini call
        # ---------------------------
        prompt = f"""
You are an AI assistant that analyzes messages for manipulation.

Analyze the following message and respond ONLY in valid JSON with these keys:
- emotion: emotional tone and pressure
- logic: logical fallacies or reasoning issues
- pattern: manipulation or scam patterns
- explanation: a clear human-readable explanation

Message:
\"\"\"{text}\"\"\"
"""

        response = model.generate_content(prompt)

        raw_output = response.text.strip()

        # Try to safely parse JSON
        try:
            ai_result = json.loads(raw_output)
        except:
            return jsonify({
                "error": "AI response parsing failed",
                "raw_response": raw_output
            }), 500

        return jsonify({
            "input_text": text,
            "emotion": ai_result.get("emotion", ""),
            "logic": ai_result.get("logic", ""),
            "pattern": ai_result.get("pattern", ""),
            "explanation": ai_result.get("explanation", ""),
            "score": score,
            "reasons": reasons,
            "confidence": confidence,
            "mood": {
                "emoji": mood_emoji,
                "label": mood_label,
                "class": mood_class
            }
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---------------------------
# Run server
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
