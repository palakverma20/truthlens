import google.genai as genai

client = genai.Client(api_key="AIzaSyCw231ZbF9OapwaTCNssqws_Ckke3FQ1w4")

# List available models
print("Available models:")
available = list(client.models.list())
for m in available:
    print(f"  - {m.name}")

# Prefer `models/gemini-2.5-flash` when available, otherwise fall back
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
    print("No generative Gemini model found for this API key. Exiting.")
    raise SystemExit(1)

print(f"\nUsing model: {model_name}")

try:
    response = client.models.generate_content(
        model=model_name,
        contents="Explain clouds to a kid"
    )
    print(response.text)
except Exception as e:
    # Print the full error so user can act on quota/billing/model issues
    print("Request failed:", e)
    raise