# CLAUDE.md — PseudoCode Converter

## Project Overview
**App Name:** PseudoCode Converter  
**Tagline:** Paste pseudocode → get Python, Java & C++ instantly with explanations  
**Built by:** LJ University MCA Faculty (App Idea #22 from LJU MCA 30-day challenge)  
**Target Users:** MCA / BCA / IT students studying DSA and algorithms  
**Monetization:** 3 free conversions → ₹99 one-time unlock via UPI  

---

## What This App Does
1. User pastes pseudocode (e.g., bubble sort algorithm written in plain English steps)
2. App sends it to Claude API
3. Claude returns working code in **Python**, **Java**, and **C++** simultaneously
4. Each output includes **line-by-line commentary** explaining the translation
5. User can copy any code block with one click

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Flask (Python) |
| Frontend | HTML5 + CSS3 + Vanilla JS |
| AI | Anthropic Claude API (claude-sonnet-4-20250514) |
| Syntax Highlighting | Prism.js (CDN) |
| Deployment | Vercel (free tier) |
| Env Management | python-dotenv |
| Rate Limiting | Flask-Limiter |

---

## Project Structure
```
pseudocode-converter/
├── CLAUDE.md              ← You are here
├── app.py                 ← Flask app + API route
├── requirements.txt       ← Python dependencies
├── vercel.json            ← Vercel deployment config
├── .env.example           ← API key placeholder
├── .gitignore
├── README.md
├── templates/
│   └── index.html         ← Main UI (landing + converter)
└── static/
    ├── css/
    │   └── style.css      ← All styles
    └── js/
        └── script.js      ← Frontend logic
```

---

## API Contract
**Endpoint:** `POST /convert`  
**Request body:** `{ "pseudocode": "string" }`  
**Response:** 
```json
{
  "python": "# Python code here",
  "java": "// Java code here",
  "cpp": "// C++ code here",
  "commentary": [
    { "line": 1, "pseudo": "original pseudocode line", "explanation": "what this does" }
  ]
}
```
**Error response:** `{ "error": "user-friendly message" }`

---

## Claude API Prompt Instructions
- Model: `claude-sonnet-4-20250514`
- max_tokens: 4000
- The prompt must instruct Claude to return ONLY valid JSON — no markdown, no preamble
- Parse response safely with try/except — never crash on malformed JSON

---

## Constraints & Rules
- Input max: 2000 characters
- Rate limit: 10 requests per IP per hour
- Freemium: 3 free conversions tracked in localStorage, then UPI paywall
- UPI unlock passcode: `LJU2025` (hardcoded for MVP)
- NO user accounts, NO database for MVP — keep it stateless
- Must work on Vercel free tier (serverless functions)
- Mobile responsive — students use phones

---

## Deployment
- Platform: Vercel (free)
- Environment variable: `ANTHROPIC_API_KEY` set in Vercel Dashboard
- URL format: `pseudocode-converter.vercel.app`

---

## Things Already Decided — Do Not Change
- Three output languages: Python, Java, C++ (not JavaScript, not others)
- UPI payment flow (not Razorpay/Stripe — too complex for MVP)
- Prism.js for syntax highlighting (not CodeMirror — too heavy)
- Vercel for deployment (not Railway/Render — has free Flask support)
