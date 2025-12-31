from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import google.genai as genai

# from backend.agents import emotion_agent, logic_agent, pattern_agent, explain_agent
# from backend.scoring import danger_score, calculate_mood
from agents import emotion_agent, logic_agent, pattern_agent, explain_agent
from scoring import danger_score, calculate_mood

import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()


# app = Flask(__name__, static_folder='frontend', static_url_path='')
app = Flask(
    __name__,
    static_folder='../frontend',
    static_url_path=''
)

CORS(app)

# Initialize Gemini client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY")
)

# Discover available models
available = list(client.models.list())

# Prefer `models/gemini-2.5-flash`
model_name = None
if any(m.name == "models/gemini-2.5-flash" for m in available):
    model_name = "models/gemini-2.5-flash"
else:
    preferred = [
        "models/gemini-3-pro-preview",
        "models/gemini-2.5-pro",
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
        "models/gemini-2.0-flash",
    ]
    for p in preferred:
        if any(m.name == p for m in available):
            model_name = p
            break
    if not model_name:
        for m in available:
            if "gemini" in m.name:
                model_name = m.name
                break

if not model_name:
    raise SystemExit("No generative Gemini model found for this API key.")


class ModelWrapper:
    def __init__(self, client, model_name):
        self._client = client
        self._model = model_name

    def generate_content(self, prompt: str):
        return self._client.models.generate_content(model=self._model, contents=prompt)


model = ModelWrapper(client, model_name)


# @app.route('/')
# def serve_index():
#     return send_from_directory('frontend', 'index.html')
@app.route('/')
def serve_index():
    return send_from_directory('../frontend', 'index.html')



@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json()
        text = data.get('text', '').strip()

        if not text:
            return jsonify({'error': 'Text field is required'}), 400

        if len(text) > 5000:
            return jsonify({'error': 'Text exceeds 5000 character limit'}), 400

        # Calculate score immediately (fast, local operation)
        score, reasons, confidence = danger_score(text)
        
        # Calculate mood based on score
        mood_emoji, mood_label, mood_class = calculate_mood(score)

        # Run emotion, logic, and pattern agents in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            emotion_future = executor.submit(emotion_agent, text, model)
            logic_future = executor.submit(logic_agent, text, model)
            pattern_future = executor.submit(pattern_agent, text, model)

            # Get results as they complete (don't wait for all)
            emotion = emotion_future.result(timeout=30)
            logic = logic_future.result(timeout=30)
            pattern = pattern_future.result(timeout=30)

        # Generate explanation with combined results
        explanation = explain_agent(emotion, logic, pattern, model)

        return jsonify({
            'emotion': emotion,
            'logic': logic,
            'pattern': pattern,
            'explanation': explanation,
            'score': score,
            'reasons': reasons,
            'confidence': confidence,
            'mood': {
                'emoji': mood_emoji,
                'label': mood_label,
                'class': mood_class
            }
        })

    except concurrent.futures.TimeoutError:
        return jsonify({'error': 'Request timeout. Please try again.'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500


#if __name__ == '__main__':
#    app.run(debug=True, port=5000)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


