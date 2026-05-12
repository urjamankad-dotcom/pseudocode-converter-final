import os
import json
import re
import requests
from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv

load_dotenv()

# Fix template and static folder paths for Vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

PROMPT_TEMPLATE = """Convert this pseudocode to Python, Java, and C++.

Pseudocode:
{pseudocode}

Reply with ONLY this JSON structure, no extra text before or after:

{{
  "python": "# python code here",
  "java": "// java code here",
  "cpp": "// cpp code here",
  "commentary": [
    {{"line": 1, "pseudo": "first line of pseudocode", "explanation": "what it does"}}
  ]
}}

Rules:
- Java must have: public class Main {{ public static void main(String[] args) {{ }} }}
- C++ must include headers like #include <iostream>
- One commentary entry per line of pseudocode
- Simple explanations for MCA students
- Return ONLY the JSON, nothing else"""


def extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        pass
    cleaned = re.sub(r"```(?:json)?", "", text).replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        pass
    return None


def call_groq(pseudocode):
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not configured.")

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {
                "role": "system",
                "content": "You are a programming expert. Always respond with only valid JSON, no markdown, no extra text."
            },
            {
                "role": "user",
                "content": PROMPT_TEMPLATE.format(pseudocode=pseudocode)
            }
        ],
        "temperature": 0.1,
        "max_tokens": 4000
    }

    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)

    if response.status_code == 401:
        raise ValueError("Invalid Groq API key.")
    elif response.status_code == 429:
        raise ValueError("Rate limit reached. Please wait and try again.")
    elif response.status_code != 200:
        raise ValueError(f"Groq API error {response.status_code}: {response.text[:200]}")

    result = response.json()
    raw = result["choices"][0]["message"]["content"].strip()

    parsed = extract_json(raw)
    if parsed is None:
        raise ValueError(f"Could not parse AI response: {raw[:200]}")

    return parsed


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
def convert():
    data = request.get_json()

    if not data or "pseudocode" not in data:
        return jsonify({"error": "No pseudocode provided."}), 400

    pseudocode = data["pseudocode"].strip()

    if not pseudocode:
        return jsonify({"error": "Pseudocode cannot be empty."}), 400

    if len(pseudocode) > 2000:
        return jsonify({"error": "Input too long. Please keep under 2000 characters."}), 400

    if not GROQ_API_KEY:
        return jsonify({"error": "API key not configured."}), 500

    try:
        result = call_groq(pseudocode)

        required_keys = {"python", "java", "cpp", "commentary"}
        if not required_keys.issubset(result.keys()):
            missing = required_keys - result.keys()
            return jsonify({"error": f"Incomplete response (missing: {missing}). Please try again."}), 500

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 500

    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot reach Groq servers. Check internet connection."}), 500

    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timed out. Please try again."}), 500

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
