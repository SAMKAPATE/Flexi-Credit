"""
Grok AI Client & Agent Engine.
Integrates with xAI's Grok API (https://api.x.ai/v1/chat/completions) with an intelligent fallback agent
for offline testing or when an API key is not yet provided.
"""

import json
import re
import httpx
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Tuple
from database import get_setting

XAI_BASE_URL = "https://api.x.ai/v1"
DEFAULT_MODEL = "grok-2-latest"


def get_active_api_key() -> str:
    """Retrieves API key from database setting or environment."""
    key = get_setting("grok_api_key", "")
    return key.strip() if key else ""


def get_active_model() -> str:
    """Retrieves selected Grok model name."""
    model = get_setting("grok_model", DEFAULT_MODEL)
    return model.strip() if model else DEFAULT_MODEL


def test_connection(api_key: str, model: str = DEFAULT_MODEL) -> Tuple[bool, str]:
    """Tests validity of the Grok API Key."""
    if not api_key:
        return False, "API key is empty."
    
    headers = {
        "Authorization": f"Bearer {api_key.strip()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a test agent."},
            {"role": "user", "content": "Respond with 'CONNECTED' if you receive this."}
        ],
        "max_tokens": 15
    }

    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(f"{XAI_BASE_URL}/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                reply = data["choices"][0]["message"]["content"].strip()
                return True, f"Success! Grok ({model}) connected: '{reply}'"
            elif resp.status_code == 401:
                return False, "Unauthorized (401): Invalid xAI Grok API key."
            elif resp.status_code == 404:
                return False, f"Model '{model}' not found or endpoint incorrect."
            else:
                return False, f"HTTP error {resp.status_code}: {resp.text}"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# --- AI Agent: Document Information Extraction ---

EXTRACTION_SYSTEM_PROMPT = """
You are an expert Vehicle Document Parser and OCR specialist.
Extract structured information from the provided vehicle document text, OCR output, or document details.
Return STRICTLY valid JSON with the following schema:
{
    "reg_no": "string (e.g. MH12AB1234 or empty)",
    "make_model": "string (vehicle name/model if found, else empty)",
    "doc_type": "Insurance" | "PUC" | "Registration (RC)" | "Road Tax" | "Fitness Certificate" | "Driving License",
    "policy_no": "string (policy, certificate or registration number)",
    "issuer": "string (insurance company, RTO, or issuing authority)",
    "issue_date": "YYYY-MM-DD (or empty)",
    "expiry_date": "YYYY-MM-DD (REQUIRED if discernible, or empty)",
    "notes": "string (any extra details like coverage type or remarks)"
}
Do not output markdown code blocks or any extraneous text. Just the raw JSON object.
"""

def extract_document_data(raw_text: str, api_key: Optional[str] = None) -> Dict[str, Any]:
    """Parses text into structured document fields using Grok AI, or fallback regex."""
    key = api_key if api_key is not None else get_active_api_key()
    model = get_active_model()
    
    if key:
        headers = {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Document text to extract:\n\n{raw_text}"}
            ],
            "temperature": 0.1
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(f"{XAI_BASE_URL}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    # Strip possible ```json blocks
                    cleaned = re.sub(r"^```json\s*", "", content)
                    cleaned = re.sub(r"```$", "", cleaned).strip()
                    return json.loads(cleaned)
        except Exception as e:
            print(f"[Grok Client] Extraction API call failed, using fallback parser: {e}")
    
    # Fallback heuristic parser
    return _fallback_extract(raw_text)


def _fallback_extract(text: str) -> Dict[str, Any]:
    """Heuristic rule/regex extractor when Grok API is not available."""
    text_lower = text.lower()
    
    # Document Type detection
    doc_type = "Insurance"
    if any(k in text_lower for k in ["puc", "pollution", "emission"]):
        doc_type = "PUC"
    elif any(k in text_lower for k in ["rc", "registration certificate", "chassis"]):
        doc_type = "Registration (RC)"
    elif any(k in text_lower for k in ["road tax", "tax token", "mv tax"]):
        doc_type = "Road Tax"
    elif any(k in text_lower for k in ["fitness", "cf"]):
        doc_type = "Fitness Certificate"
    elif any(k in text_lower for k in ["driving license", "dl "]):
        doc_type = "Driving License"

    # Vehicle Registration Number detection (Standard formats e.g. MH12AB1234 or DL 01 CA 9999 or US plate)
    reg_match = re.search(r'\b([A-Z]{2}[ -]?[0-9]{1,2}[ -]?[A-Z]{1,3}[ -]?[0-9]{4})\b', text, re.IGNORECASE)
    reg_no = reg_match.group(1).replace(" ", "").replace("-", "").upper() if reg_match else ""

    # Policy / Cert Number detection
    policy_match = re.search(r'(?:policy|cert(?:ificate)?|rc|no|number)[.:\s#]*([A-Z0-9\-\/]{6,25})', text, re.IGNORECASE)
    policy_no = policy_match.group(1) if policy_match else ""

    # Issuer detection
    issuer = ""
    for ins in ["HDFC ERGO", "ICICI Lombard", "Bajaj Allianz", "Tata AIG", "New India Assurance",
                "United India", "National Insurance", "Star Health", "Digit", "Acko", "Geico", "Progressive", "RTO Transport Dept"]:
        if ins.lower() in text_lower:
            issuer = ins
            break

    # Date detection (YYYY-MM-DD or DD/MM/YYYY or DD-MM-YYYY)
    dates_found = []
    # Pattern 1: YYYY-MM-DD
    for d in re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', text):
        dates_found.append(d)
    # Pattern 2: DD/MM/YYYY or DD-MM-YYYY
    for d, m, y in re.findall(r'\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b', text):
        try:
            formatted = f"{int(y):04d}-{int(m):02d}-{int(d):02d}"
            dates_found.append(formatted)
        except Exception:
            pass

    expiry_date = ""
    issue_date = ""
    if dates_found:
        dates_sorted = sorted(dates_found)
        if len(dates_sorted) == 1:
            expiry_date = dates_sorted[0]
        else:
            issue_date = dates_sorted[0]
            expiry_date = dates_sorted[-1]

    return {
        "reg_no": reg_no,
        "make_model": "",
        "doc_type": doc_type,
        "policy_no": policy_no,
        "issuer": issuer or ("Transport Dept" if "PUC" in doc_type or "RC" in doc_type else "Insurance Provider"),
        "issue_date": issue_date,
        "expiry_date": expiry_date,
        "notes": "Extracted via intelligent heuristic scanner (Grok fallback mode)."
    }


# --- AI Agent: Multi-Channel Reminder Generation ---

REMINDER_SYSTEM_PROMPT = """
You are an Automated Vehicle Document Renewal AI Agent.
Generate clear, urgent, legally informed, and highly persuasive renewal reminder notifications
for a vehicle owner whose document is expiring or expired.

Format your response as a JSON object with:
{
    "email_subject": "Urgent / Attention subject line with vehicle reg no",
    "email_body": "Polite yet firm email with document details, legal risks/fines, renewal instructions, and a checklist",
    "sms_text": "Crisp 160-char SMS with Reg No, Document Type, Expiry Date, and call to action",
    "whatsapp_text": "Engaging WhatsApp message formatted with emojis, bold highlights, and clear bullet points",
    "legal_implications": "Brief explanation of fines (e.g. Motor Vehicles Act Section 196 / 190(2) or equivalent penalties), insurance invalidation in case of accident, and impound risk"
}
Return ONLY valid JSON. No conversational chatter.
"""

def generate_multi_channel_reminders(doc_info: Dict[str, Any], api_key: Optional[str] = None) -> Dict[str, str]:
    """Generates customized reminder templates for Email, SMS, WhatsApp using Grok."""
    key = api_key if api_key is not None else get_active_api_key()
    model = get_active_model()
    
    if key:
        headers = {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        }
        prompt_data = json.dumps(doc_info, indent=2)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": REMINDER_SYSTEM_PROMPT},
                {"role": "user", "content": f"Vehicle Document Details:\n{prompt_data}"}
            ],
            "temperature": 0.3
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(f"{XAI_BASE_URL}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    content = resp.json()["choices"][0]["message"]["content"].strip()
                    cleaned = re.sub(r"^```json\s*", "", content)
                    cleaned = re.sub(r"```$", "", cleaned).strip()
                    return json.loads(cleaned)
        except Exception as e:
            print(f"[Grok Client] Reminder API call failed, using fallback templates: {e}")

    return _fallback_reminders(doc_info)


def _fallback_reminders(doc_info: Dict[str, Any]) -> Dict[str, str]:
    """Fallback generator for reminders with realistic legal info and urgency."""
    reg_no = doc_info.get("reg_no", "Your Vehicle")
    owner = doc_info.get("owner_name", "Valued Owner")
    doc_type = doc_info.get("doc_type", "Document")
    expiry = doc_info.get("expiry_date", "Soon")
    days_left = doc_info.get("days_left", 0)
    policy_no = doc_info.get("policy_no", "N/A")
    issuer = doc_info.get("issuer", "Issuing Authority")

    if days_left < 0:
        status_str = f"⚠️ EXPIRED ({abs(days_left)} days ago on {expiry})"
        urgency_level = "CRITICAL LEGAL VIOLATION"
        penalty_text = "Fines up to ₹2,000–₹10,000, 3-month license suspension, and complete zero-coverage liability in accident claims."
    elif days_left <= 7:
        status_str = f"🔴 URGENT: Expiring in {days_left} day(s) on {expiry}"
        urgency_level = "HIGH PRIORITY"
        penalty_text = "Avoid traffic enforcement penalties and lapse of No Claim Bonus (NCB) discounts."
    else:
        status_str = f"🟡 Upcoming Renewal: Expiring in {days_left} days on {expiry}"
        urgency_level = "SCHEDULED NOTICE"
        penalty_text = "Early renewal guarantees uninterrupted coverage and zero grace period penalties."

    email_subject = f"[{urgency_level}] Immediate Action: {doc_type} Renewal for {reg_no}"
    email_body = f"""Dear {owner},

This is an automated priority reminder from your Vehicle Document Management Agent.

The {doc_type} for your vehicle ({reg_no}) status:
{status_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DOCUMENT SUMMARY:
• Vehicle Registration: {reg_no}
• Document Type: {doc_type}
• Reference / Policy No: {policy_no}
• Issuing Authority / Company: {issuer}
• Expiry Date: {expiry}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LEGAL & SAFETY CONSEQUENCES:
{penalty_text}
Driving with an expired document violates motor vehicle regulations and leaves you financially exposed.

RECOMMENDED NEXT STEPS:
1. Online Renewal: Visit the official portal (Parivahan / mParivahan or your insurer's app).
2. Keep Documents Handy: Registration Certificate, previous policy copy, and odometer reading.
3. Once renewed, update your record in the Vehicle Renewal Dashboard to reset alerts.

Need help? Chat with our AI Vehicle Assistant directly in your dashboard.

Best regards,
Automated Vehicle Renewal Agent"""

    sms_text = f"ALERT: {doc_type} for {reg_no} ({status_str}). Renew immediately to avoid fines up to Rs 10k and claim denial. -VehicleAgent"
    
    whatsapp_text = f"""🚗 *VEHICLE DOCUMENT RENEWAL ALERT* 🚗

Hello *{owner}*,
Your *{doc_type}* for *{reg_no}* requires prompt attention!

📌 *Status*: {status_str}
📄 *Document*: {doc_type} ({policy_no})
🏢 *Issuer*: {issuer}
📅 *Expiry Date*: {expiry}

⚠️ *Consequences of Delay*:
{penalty_text}

👉 *Action Required*:
Renew online today via Parivahan Sewa or insurer portal. Keep your vehicle compliant and protected!

_Automated Alert from Vehicle AI Agent_"""

    return {
        "email_subject": email_subject,
        "email_body": email_body,
        "sms_text": sms_text[:160],
        "whatsapp_text": whatsapp_text,
        "legal_implications": penalty_text
    }


# --- AI Agent: Interactive Conversational Assistant ---

ASSISTANT_SYSTEM_PROMPT = """
You are the Grok AI Vehicle Document & Compliance Advisor.
You possess deep expertise in motor vehicle acts, document renewal procedures (Insurance, PUC / Emissions, RC Fitness, Road Tax, Driving Licenses),
traffic fines, dispute handling, insurance claim prerequisites, and state RTO / DMV compliance guidelines.

You have direct access to the user's active vehicle registry and document expiry states provided in the context.
When users ask questions:
1. Address their specific vehicles and impending expiry dates directly.
2. Provide step-by-step renewal instructions (documents needed, online portals like Parivahan / VAHAN / Sarathi / Insurers).
3. State precise penalties for expired documents (e.g. MV Act Section 190(2) for PUC: Rs. 10,000 fine / 3 months jail; Section 196 for Driving without Insurance: Rs. 2,000 to Rs. 4,000 fine / imprisonment).
4. Be structured, helpful, encouraging, and authoritative with clean formatting and markdown bullet points.
"""

def generate_chat_response(messages: List[Dict[str, str]], vehicle_context: str = "",
                           api_key: Optional[str] = None) -> str:
    """Answers vehicle renewal queries using Grok AI or fallback expert engine."""
    key = api_key if api_key is not None else get_active_api_key()
    model = get_active_model()
    
    system_content = ASSISTANT_SYSTEM_PROMPT
    if vehicle_context:
        system_content += f"\n\nCURRENT USER VEHICLES & STATUS CONTEXT:\n{vehicle_context}"

    if key:
        full_messages = [{"role": "system", "content": system_content}] + messages
        headers = {
            "Authorization": f"Bearer {key.strip()}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": model,
            "messages": full_messages,
            "temperature": 0.5
        }
        try:
            with httpx.Client(timeout=25.0) as client:
                resp = client.post(f"{XAI_BASE_URL}/chat/completions", headers=headers, json=payload)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                else:
                    return f"⚠️ Grok API Error ({resp.status_code}): {resp.text}\n\nFalling back to local advisor:\n\n" + _fallback_chat(messages[-1]["content"], vehicle_context)
        except Exception as e:
            return f"⚠️ Network/Grok connection error: {e}\n\n" + _fallback_chat(messages[-1]["content"], vehicle_context)

    # If no key set, use local fallback advisor
    last_user_msg = messages[-1]["content"] if messages else "Hello"
    return _fallback_chat(last_user_msg, vehicle_context)


def _fallback_chat(query: str, vehicle_context: str) -> str:
    """Expert rule-based fallback responses for motor vehicle compliance."""
    q = query.lower()
    
    if any(k in q for k in ["puc", "pollution", "emission"]):
        return f"""### 🌿 Pollution Under Control (PUC) Certificate Guide

**1. Legal Penalty (Motor Vehicles Act Sec 190(2)):**
- **Fine:** ₹10,000 (first offense) and potential imprisonment up to 3 months, or license disqualification for 3 months.
- **Insurance Impact:** Insurers can decline accidental claims if the PUC was invalid at the time of the incident.

**2. Validity Period:**
- **New Vehicles (BS-IV / BS-VI):** Valid for 1 year from vehicle registration date.
- **Subsequent Renewals:** Valid for 6 months (petrol/diesel/CNG) or 1 year depending on state rules.

**3. How to Renew:**
1. Drive to any authorized petrol pump or RTO-approved PUC testing center.
2. Technician inserts the probe into exhaust pipe and measures CO / HC / Smoke density.
3. Instant online upload to **Parivahan (vahan.parivahan.gov.in)**.
4. Nominal fee: ₹60 to ₹150 depending on 2-wheeler, 4-wheeler petrol or diesel.
5. Download digital certificate from mParivahan app.

{f"**Your Vehicles Status:**\n{vehicle_context}" if vehicle_context else ""}"""

    elif any(k in q for k in ["insurance", "policy", "premium", "claim"]):
        return f"""### 🛡️ Vehicle Insurance Renewal & Compliance

**1. Legal Penalty (Motor Vehicles Act Sec 196):**
- **First Offense:** ₹2,000 fine and/or imprisonment up to 3 months.
- **Second Offense:** ₹4,000 fine and/or imprisonment.
- **Worst Risk:** If an accident occurs with an uninsured vehicle, the owner is 100% personally liable for unlimited third-party damages and bodily injury compensation.

**2. What You Need for Renewal:**
- Previous Policy Number & Insurer Name.
- Vehicle Registration Certificate (RC).
- Valid PUC Certificate.
- Current Odometer reading.
- No Claim Bonus (NCB) proof if switching insurers.

**3. Grace Period Warning:**
- Most insurers give a **90-day grace period** to retain your accumulated No Claim Bonus (NCB) discount (up to 50% discount).
- However, during the grace period, **you have ZERO coverage** while driving.

{f"**Your Registered Vehicles:**\n{vehicle_context}" if vehicle_context else ""}"""

    elif any(k in q for k in ["rc", "registration", "fitness", "transfer"]):
        return f"""### 📋 Vehicle Registration (RC) & Fitness Certificate

**1. Validity:**
- **Private Vehicles (Cars & Bikes):** RC is valid for **15 years** from date of registration. After 15 years, it must be renewed for 5-year blocks.
- **Commercial Vehicles:** Fitness certificate must be renewed annually (or every 2 years for newer commercial vehicles).

**2. Required Documents for Renewal:**
- Form 25 (Application for renewal of RC).
- Original Registration Certificate.
- Valid Insurance Certificate.
- Valid PUC Certificate.
- Chassis imprint / physical vehicle inspection at RTO.
- Road Tax clearance receipt.

**3. Where to Apply:**
- Online portal: **parivahan.gov.in** -> Online Services -> Vehicle Related Services.
- Book an RTO inspection slot.

{f"**Your Vehicles Status:**\n{vehicle_context}" if vehicle_context else ""}"""

    elif any(k in q for k in ["status", "check", "my vehicle", "due", "expire"]):
        return f"""### 🔍 Your Vehicle Expiry Status Report

Based on the records in your database:
{vehicle_context if vehicle_context else "No vehicles currently registered. Add your vehicles in the 'Manage Vehicles & Documents' tab to track them!"}

**Action Plan:**
- If you have documents marked as **EXPIRED** or **CRITICAL (≤7 days)**, trigger the automated reminder in the **Automated Reminders** tab or renew them immediately to avoid traffic penalties!"""

    else:
        return f"""### 🤖 Grok AI Vehicle Compliance Advisor

I am your vehicle document compliance assistant. I can assist you with:
- 🚗 **Expiry tracking & penalties** for Insurance, PUC, RC, Road Tax, and Driving License.
- 💰 **Traffic fines & legal regulations** under the Motor Vehicles Act.
- 📝 **Renewal checklist & portals** (Parivahan Sewa, insurer portals, testing centers).
- ⚡ **No Claim Bonus (NCB) preservation** and cost-saving tips.

{f"**Current Status of Your Fleet:**\n{vehicle_context}\n\n" if vehicle_context else ""}
*Tip: Configure your xAI Grok API key in the 'Settings' tab to enable full real-time Grok-2 neural intelligence!*"""
