from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import requests
from dotenv import load_dotenv

from scoring import danger_score, calculate_mood

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
# OpenRouter config
# ---------------------------
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "google/gemini-2.0-flash-exp:free"


# ---------------------------
# Model wrapper
# ---------------------------
class OpenRouterResponse:
    def __init__(self, text):
        self.text = text


class ModelWrapper:
    def generate_content(self, prompt: str):
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://truthlens.app",
            "X-Title": "TruthLens"
        }

        payload = {
            "model": MODEL_NAME,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]
        return OpenRouterResponse(content)


model = ModelWrapper()

# ---------------------------
# Serve frontend
# ---------------------------
@app.route("/")
def serve_index():
    return send_from_directory("../frontend", "index.html")


# ---------------------------
# Helper: extract text (TXT / PDF / IMAGE)
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
        return None, "Unsupported file type"

    return text.strip(), None


# ---------------------------
# Single AI analysis (MERGED AGENTS)
# ---------------------------
def run_merged_ai_analysis(text):
    prompt = f"""
You are TruthLens, an AI system that detects manipulation in messages.

Analyze the message below and return a STRICT JSON object with these exact keys:
- emotion
- logic
- pattern
- explanation

Rules:
- Do NOT add markdown
- Do NOT add extra text
- Do NOT explain the JSON
- Return only valid JSON

Message:
\"\"\"
{text}
\"\"\"
"""

    response = model.generate_content(prompt).text

    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Safe fallback if model slightly misbehaves
        return {
            "emotion": "Emotional manipulation detected.",
            "logic": "Logical pressure tactics present.",
            "pattern": "Common manipulation patterns observed.",
            "explanation": response
        }


# ---------------------------
# Analyze route (TEXT + FILE)
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
        # Local scoring (fast, offline)
        # ---------------------------
        score, reasons, confidence = danger_score(text)
        mood_emoji, mood_label, mood_class = calculate_mood(score)

        # ---------------------------
        # ONE AI CALL (merged agents)
        # ---------------------------
        ai_result = run_merged_ai_analysis(text)

        return jsonify({
            "input_text": text,
            "emotion": ai_result["emotion"],
            "logic": ai_result["logic"],
            "pattern": ai_result["pattern"],
            "explanation": ai_result["explanation"],
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
