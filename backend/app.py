from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.genai as genai

from agents import emotion_agent, logic_agent, pattern_agent, explain_agent
from scoring import danger_score, calculate_mood

import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

import PyPDF2
from PIL import Image
import pytesseract

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
# Helper: extract text from file
# Supports TXT, PDF, IMAGE (OCR)
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
# Analyze route
# ---------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        text = ""

        # JSON text input
        if request.is_json:
            data = request.get_json()
            text = data.get("text", "").strip()

        # File upload
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
        # Scoring + AI analysis
        # ---------------------------
        score, reasons, confidence = danger_score(text)
        mood_emoji, mood_label, mood_class = calculate_mood(score)

        emotion = emotion_agent(text, model)
        logic = logic_agent(text, model)
        pattern = pattern_agent(text, model)
        explanation = explain_agent(emotion, logic, pattern, model)

        return jsonify({
            "input_text": text,
            "emotion": emotion,
            "logic": logic,
            "pattern": pattern,
            "explanation": explanation,
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
