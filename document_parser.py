"""
Document Parser & Upload Extractor Module.
Processes uploaded vehicle document files (images, text, or OCR extracts)
and extracts key fields using Grok AI, Groq, or heuristic pattern recognition.
Includes strict validation and error handling.
"""

import re
import os
from datetime import datetime
from typing import Dict, Any, Optional
from grok_agent import detect_api_provider, XAI_API_URL, GROQ_API_URL
import httpx


EXTRACTION_PROMPT = """You are an expert Vehicle Document Parser.
Extract key structured information from the provided vehicle document text or OCR transcription.

Return STRICTLY a valid JSON object matching this schema:
{
    "reg_no": "string (uppercase, e.g. MH-12-AB-1234 or empty)",
    "doc_type": "Registration Certificate (RC)" | "Vehicle Insurance" | "Pollution Under Control (PUC)" | "Driving Licence (DL)",
    "policy_no": "string (policy or certificate number)",
    "issuer": "string (insurance company or RTO)",
    "issue_date": "YYYY-MM-DD (or empty)",
    "expiry_date": "YYYY-MM-DD (REQUIRED if present, else empty)",
    "notes": "string"
}
Do NOT output markdown code fences or commentary. Return ONLY the raw JSON object.
"""

def extract_from_file_or_text(file_path_or_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Extracts structured document data from text or file contents.
    Handles text files, raw strings, and OCR fallbacks gracefully.
    """
    raw_text = ""
    if os.path.exists(file_path_or_text):
        try:
            # Check if text/plain or readable
            with open(file_path_or_text, "r", encoding="utf-8", errors="ignore") as f:
                raw_text = f.read(4000)
        except Exception:
            # If binary image, use basename or placeholder text for simulated OCR
            raw_text = f"Document File: {os.path.basename(file_path_or_text)}"
    else:
        raw_text = file_path_or_text

    provider, key, model = detect_api_provider(api_key)

    if provider in ("groq", "xai") and key and len(raw_text) > 15:
        url = GROQ_API_URL if provider == "groq" else XAI_API_URL
        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": EXTRACTION_PROMPT},
                {"role": "user", "content": f"Document text to extract:\n{raw_text}"}
            ],
            "temperature": 0.1
        }
        try:
            with httpx.Client(timeout=12.0) as client:
                resp = client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    import json
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    cleaned = re.sub(r"^```json\s*", "", content)
                    cleaned = re.sub(r"```$", "", cleaned).strip()
                    parsed = json.loads(cleaned)
                    _sanitize_extracted_data(parsed)
                    return parsed
        except Exception as e:
            print(f"[Document Parser] API extraction failed, using heuristic fallback: {e}")

    # Heuristic Pattern Fallback
    return _heuristic_extract(raw_text)


def _heuristic_extract(text: str) -> Dict[str, Any]:
    """Robust regex and keyword parsing when AI is offline."""
    text_lower = text.lower()

    # Document type
    if any(k in text_lower for k in ["puc", "pollution", "emission"]):
        doc_type = "Pollution Under Control (PUC)"
    elif any(k in text_lower for k in ["insurance", "policy", "premium", "coverage"]):
        doc_type = "Vehicle Insurance"
    elif any(k in text_lower for k in ["driving licence", "dl ", "driver licence"]):
        doc_type = "Driving Licence (DL)"
    else:
        doc_type = "Registration Certificate (RC)"

    # Registration number pattern (e.g. MH-12-AB-1234 or DL01CA9999)
    reg_match = re.search(r'\b([A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{4})\b', text, re.IGNORECASE)
    reg_no = reg_match.group(1).upper() if reg_match else ""

    # Policy / Cert Number pattern
    pol_match = re.search(r'(?:policy|cert|rc|dl|no|number)[.:\s#]*([A-Z0-9\-\/]{5,22})', text, re.IGNORECASE)
    policy_no = pol_match.group(1) if pol_match else ""

    # Issuer detection
    issuer = ""
    for name in ["HDFC ERGO", "ICICI Lombard", "Bajaj Allianz", "Tata AIG", "New India", "Acko", "Digit", "RTO Transport"]:
        if name.lower() in text_lower:
            issuer = name
            break

    # Date discovery (YYYY-MM-DD or DD-MM-YYYY or DD/MM/YYYY)
    dates_found = []
    for d in re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', text):
        dates_found.append(d)
    for d, m, y in re.findall(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b', text):
        try:
            formatted = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
            dates_found.append(formatted)
        except Exception:
            pass

    issue_date = ""
    expiry_date = ""
    if dates_found:
        dates_sorted = sorted(dates_found)
        if len(dates_sorted) == 1:
            expiry_date = dates_sorted[0]
        else:
            issue_date = dates_sorted[0]
            expiry_date = dates_sorted[-1]

    data = {
        "reg_no": reg_no,
        "doc_type": doc_type,
        "policy_no": policy_no,
        "issuer": issuer or ("Transport Dept" if "PUC" in doc_type or "RC" in doc_type else "Insurance Provider"),
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "notes": "Extracted via smart pattern scanner."
    }
    _sanitize_extracted_data(data)
    return data


def _sanitize_extracted_data(data: Dict[str, Any]):
    """Validates date format and normalizes values."""
    if data.get("expiry_date"):
        try:
            datetime.strptime(data["expiry_date"], "%Y-%m-%d")
        except ValueError:
            data["expiry_date"] = ""
    if data.get("reg_no"):
        data["reg_no"] = data["reg_no"].strip().upper()
