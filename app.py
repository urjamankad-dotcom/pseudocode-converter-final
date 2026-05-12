"""
PseudoCode Converter — app.py
Flask backend with Google Gemini API integration.
LJ University MCA · App #22
"""

import os
import json
import re
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

load_dotenv()

# ── App Setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per hour"],
    storage_uri="memory://"
)

# ── Valid Pseudocode Keywords (for server-side validation) ────────────────────

VALID_KEYWORDS = [
    "function", "if", "for", "while", "repeat",
    "set", "return", "print", "input", "swap", "call", "end"
]

# ── Gemini Model Config ───────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a code generation engine for a student learning tool at LJ University.
You convert pseudocode (written in a defined grammar) into working code in Python, Java, and C++.
Your output must always be valid, runnable code — not pseudocode approximations or sketches.
You always respond with ONLY valid JSON, nothing else. No markdown. No explanation."""

GENERATION_CONFIG = {
    "temperature":        0.1,
    "max_output_tokens":  4000,
    "response_mime_type": "application/json"   # ← Gemini returns strict JSON natively
}


def build_prompt(pseudocode: str) -> str:
    return f"""Convert the following pseudocode into Python, Java, and C++.

The pseudocode uses this grammar:
- FUNCTION name(params) / END FUNCTION
- SET variable = value
- ARRAY name[size]
- INPUT variable  |  PRINT expression
- IF condition THEN / ELSE IF / ELSE / END IF
- FOR variable FROM start TO end (inclusive) / END FOR
- WHILE condition DO / END WHILE
- REPEAT / UNTIL condition
- RETURN value  |  BREAK  |  CONTINUE
- SWAP a AND b  |  CALL functionName(args)
- // This is a comment

Rules for your output:
1. Python  : clean, idiomatic Python 3
2. Java    : all code inside  public class Main {{ public static void main(String[] args) {{ ... }} }}
3. C++     : include all required headers (#include <iostream>, #include <vector>, etc.) and use namespace std;
4. All three versions must be functionally CORRECT and RUNNABLE as-is
5. Commentary: plain-English explanation for each non-obvious pseudocode line.
   Audience: first-year MCA/BCA students.
   SKIP trivial lines like simple variable initialisation (SET i = 0) or obvious loop counters.
   INCLUDE commentary for: conditions, swaps, recursive calls, algorithmic decisions.
6. Return ONLY the JSON below — no markdown fences, no text before or after.

Pseudocode:
{pseudocode}

Return ONLY this JSON:
{{
  "python": "complete python code as one string, use \\n for newlines",
  "java":   "complete java code as one string, use \\n for newlines",
  "cpp":    "complete c++ code as one string, use \\n for newlines",
  "commentary": [
    {{"line": 1, "pseudo": "pseudocode line text", "explanation": "plain-English explanation"}}
  ]
}}"""


# ── JSON Extraction (fallback strategies if needed) ───────────────────────────

def extract_json(text: str):
    """
    Gemini JSON mode returns clean JSON directly (Strategy 1 always works).
    Fallback strategies kept for safety in edge cases.
    """
    # Strategy 1: direct parse — works almost always with Gemini JSON mode
    try:
        return json.loads(text)
    except Exception:
        pass

    # Strategy 2: strip any accidental markdown fences
    cleaned = re.sub(r"```(?:json)?", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # Strategy 3: find first { to last }
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except Exception:
        pass

    # Strategy 4: strip control characters, then retry Strategy 3
    try:
        cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
        start = cleaned.index("{")
        end = cleaned.rindex("}") + 1
        return json.loads(cleaned[start:end])
    except Exception:
        pass

    return None


# ── Input Validation ──────────────────────────────────────────────────────────

def validate_pseudocode(pseudocode: str):
    """Server-side validation. Returns error string if invalid, else None."""
    if not pseudocode:
        return "Please enter some pseudocode first."
    if len(pseudocode) > 2000:
        return "Input exceeds 2000 characters. Please shorten it."
    lower = pseudocode.lower()
    if not any(kw in lower for kw in VALID_KEYWORDS):
        return "This doesn't look like pseudocode. Please follow the grammar guide."
    return None  # valid


# ── Gemini API Call ───────────────────────────────────────────────────────────

def call_gemini(pseudocode: str) -> dict:
    """
    Send validated pseudocode to Gemini 2.0 Flash.
    Returns parsed JSON dict. Raises on any error.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("API key not configured")

    # Configure Gemini with API key
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config=GENERATION_CONFIG
    )

    response = model.generate_content(build_prompt(pseudocode))
    raw = response.text.strip()

    parsed = extract_json(raw)
    if parsed is None:
        raise ValueError(f"Could not parse JSON from Gemini. Snippet: {raw[:300]}")

    return parsed


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/convert", methods=["POST"])
@limiter.limit("10 per hour")
def convert():
    data = request.get_json(silent=True)

    if not data or "pseudocode" not in data:
        return jsonify({"error": "No pseudocode provided."}), 400

    pseudocode = data["pseudocode"].strip()

    # Server-side validation
    error = validate_pseudocode(pseudocode)
    if error:
        return jsonify({"error": error}), 400

    try:
        result = call_gemini(pseudocode)

        # Verify all required keys are present
        required_keys = {"python", "java", "cpp", "commentary"}
        missing = required_keys - result.keys()
        if missing:
            return jsonify({
                "error": f"Incomplete response from AI (missing: {missing}). Please try again."
            }), 500

        return jsonify(result)

    except ValueError as e:
        msg = str(e)
        if "API key not configured" in msg:
            return jsonify({"error": "Service not configured. Contact the administrator."}), 500
        return jsonify({"error": "Conversion failed. Please try again."}), 500

    except Exception as e:
        msg = str(e).lower()
        if "api_key_invalid" in msg or "api key not valid" in msg:
            return jsonify({"error": "Invalid Gemini API key. Please check your .env file."}), 500
        if "quota" in msg or "resource_exhausted" in msg:
            return jsonify({"error": "Gemini free limit reached. Please try again in a minute."}), 429
        if "connection" in msg or "timeout" in msg:
            return jsonify({"error": "Connection error. Check your internet and retry."}), 500
        return jsonify({"error": "Unexpected error. Please try again."}), 500


@app.errorhandler(429)
def ratelimit_handler(e):
    return jsonify({"error": "Too many requests. You can make up to 10 conversions per hour."}), 429


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
