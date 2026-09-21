"""
Advanced AI Vehicle Document Renewal Assistant Engine.
Supports:
1. xAI Grok API (https://api.x.ai/v1)
2. Groq Cloud API (https://api.groq.com/openai/v1) - Ultra-fast Llama-3.3-70B
3. Enhanced Built-in AI Co-Pilot (Rich deterministic reasoning engine with zero setup required)
"""

import os
import json
import httpx
from datetime import date, datetime
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

# Endpoints
XAI_API_URL = "https://api.x.ai/v1/chat/completions"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def detect_api_provider(api_key: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Detects whether the key is Groq or xAI Grok, or returns ('builtin', '', '').
    Returns: (provider_name, api_key, model_name)
    """
    key = (api_key or "").strip()
    if not key:
        # Check environment variables
        key = os.getenv("GROQ_API_KEY", "").strip()
        if key:
            return "groq", key, "llama-3.3-70b-versatile"
        key = os.getenv("XAI_API_KEY", "").strip() or os.getenv("GROK_API_KEY", "").strip()
        if key:
            return "xai", key, "grok-2-latest"
        return "builtin", "", ""

    # Key explicitly passed
    if key.startswith("gsk_"):
        return "groq", key, "llama-3.3-70b-versatile"
    elif key.startswith("xai-"):
        return "xai", key, "grok-2-latest"
    else:
        # Default try xAI then Groq
        return "xai", key, "grok-2-latest"


def get_active_provider_info() -> Dict[str, str]:
    provider, key, model = detect_api_provider()
    masked = (key[:6] + "..." + key[-4:]) if len(key) > 10 else ("Configured" if key else "Not Configured")
    
    if provider == "groq":
        desc = f"Groq Cloud AI Active ({model})"
    elif provider == "xai":
        desc = f"xAI Grok Active ({model})"
    else:
        desc = "Enhanced Built-in AI Co-Pilot (Active & Ready)"
        
    return {
        "provider": provider,
        "model": model,
        "masked_key": masked,
        "description": desc
    }


# --- Required Strict Format Generator ---

def format_structured_report(eval_data: Dict[str, Any]) -> str:
    """Generates the required official schema."""
    veh_num = eval_data.get("vehicle_reg", "Not Specified")
    owner = eval_data.get("owner_name", "Vehicle Owner")
    docs = eval_data.get("documents", {})

    rc = docs.get("RC", {})
    ins = docs.get("Insurance", {})
    puc = docs.get("PUC", {})
    dl = docs.get("Driving Licence", {})

    status_lines = [
        f"- RC: {rc.get('status', 'UNKNOWN')} – {rc.get('display_days', 'N/A')}",
        f"- Insurance: {ins.get('status', 'UNKNOWN')} – {ins.get('display_days', 'N/A')}",
        f"- PUC: {puc.get('status', 'UNKNOWN')} – {puc.get('display_days', 'N/A')}",
        f"- Driving Licence: {dl.get('status', 'UNKNOWN')} – {dl.get('display_days', 'N/A')}"
    ]

    priority_text = eval_data.get("priority_text", "All documents have valid future dates.")
    immediate = eval_data.get("needs_immediate_renewal", [])

    if immediate:
        action_msg = (
            f"Urgent action is recommended for your {', '.join(immediate)}. "
            f"Prompt renewal protects you from statutory penalties, impound risks, "
            f"and ensures continuous insurance liability coverage."
        )
    else:
        action_msg = (
            f"Your vehicle compliance is in good standing. Keep the upcoming expiration dates "
            f"noted on your schedule for uninterrupted peace of mind."
        )

    reminder_text = (
        f"Dear {owner},\n"
        f"This is an automated priority reminder regarding your vehicle ({veh_num}).\n"
        f"{action_msg}\n"
        f"Official renewal services can be accessed via the central Parivahan portal (parivahan.gov.in) or your authorized insurance provider.\n"
        f"Note: This system is a reminder tool to assist you with renewal timelines, not a legal or government verification system."
    )

    return (
        f"Vehicle: {veh_num}\n\n"
        f"Document Status:\n"
        + "\n".join(status_lines) + "\n\n"
        f"Priority:\n"
        f"{priority_text}\n\n"
        f"Reminder:\n"
        f"{reminder_text}"
    )


def _json_safe(value: Any) -> Any:
    """Convert date-like and nested objects into JSON-safe values."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, set):
        return [_json_safe(v) for v in sorted(value, key=lambda item: str(item))]
    return value


# --- Grok / Groq Prompt Configuration ---

SYSTEM_PROMPT = """You are an AI Vehicle Document Renewal Assistant.

OBJECTIVE:
Help vehicle owners track important vehicle-related documents and automatically identify documents that are expired or approaching their expiry date.

DOCUMENTS TO TRACK:
1. Vehicle Registration Certificate (RC)
2. Vehicle Insurance
3. Pollution Under Control Certificate (PUC)
4. Driving Licence (DL)

CRITICAL RULES:
1. Never invent document dates or vehicle information.
2. Use the actual dates and statuses provided by the user in the context.
3. Date calculations have already been performed using Python; do not re-calculate or guess new dates.
4. Do not claim that a document is legally invalid unless the provided data supports that conclusion. The system is a reminder tool, not a legal or government verification system.
5. You MUST strictly format your output according to the format below:

Vehicle: [vehicle number]

Document Status:
- RC: [status] – [days remaining]
- Insurance: [status] – [days remaining]
- PUC: [status] – [days remaining]
- Driving Licence: [status] – [days remaining]

Priority:
Identify which document needs attention first based on the earliest expiry date.

Reminder:
Generate a short, clear and professional reminder for the vehicle owner.
"""


def generate_renewal_analysis(eval_data: Dict[str, Any], api_key: Optional[str] = None) -> str:
    """
    Generates structured renewal analysis via Grok API, Groq Cloud, or Enhanced Built-in AI Engine.
    """
    provider, key, model = detect_api_provider(api_key)

    if provider in ("groq", "xai") and key:
        url = GROQ_API_URL if provider == "groq" else XAI_API_URL
        veh_num = eval_data.get("vehicle_reg", "Not Specified")
        owner = eval_data.get("owner_name", "Vehicle Owner")
        docs = eval_data.get("documents", {})

        payload_context = {
            "owner_name": owner,
            "vehicle_number": veh_num,
            "evaluated_statuses": {
                "RC": docs.get("RC", {}),
                "Insurance": docs.get("Insurance", {}),
                "PUC": docs.get("PUC", {}),
                "Driving Licence": docs.get("Driving Licence", {})
            },
            "priority": eval_data.get("priority_text")
        }

        safe_payload = _json_safe(payload_context)

        user_content = (
            f"Here is the pre-calculated vehicle compliance data:\n"
            f"{json.dumps(safe_payload, indent=2)}\n\n"
            f"Please generate the official response in the EXACT required format strictly."
        )

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2
        }

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    data = resp.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[{provider.upper()} API] Exception during analysis: {e}")

    # High-quality deterministic generation
    return format_structured_report(eval_data)


# --- Intelligent Chatbot Assistant ---

CHATBOT_SYSTEM_PROMPT = """You are an articulate, professional AI Vehicle Document Renewal Assistant.
Your objective is to advise the vehicle owner regarding vehicle document renewals (RC, Insurance, PUC, Driving Licence),
statutory penalties, renewal checklists, and prioritisation.

RULES:
1. Never invent document dates or vehicle registration details.
2. Rely strictly on the actual evaluated dates and statuses in the user context.
3. Keep answers clear, structured, encouraging, and authoritative with markdown formatting.
4. Reminder: Always include a note that this is a reminder tool, not a legal or government verification system.
"""

def chat_with_assistant(
    user_query: str,
    eval_data: Dict[str, Any],
    history: List[Dict[str, str]],
    api_key: Optional[str] = None
) -> str:
    """Answers user queries using Grok, Groq, or the Enhanced Built-in AI Co-Pilot."""
    provider, key, model = detect_api_provider(api_key)

    veh_num = eval_data.get("vehicle_reg", "Not Specified")
    owner = eval_data.get("owner_name", "Vehicle Owner")
    docs = eval_data.get("documents", {})

    context_summary = (
        f"Vehicle: {veh_num}\n"
        f"Owner: {owner}\n"
        f"Evaluation Date: {eval_data.get('evaluation_date')}\n"
        f"- RC: {docs.get('RC', {}).get('status')} ({docs.get('RC', {}).get('display_days')}, Expiry: {docs.get('RC', {}).get('date_str')})\n"
        f"- Insurance: {docs.get('Insurance', {}).get('status')} ({docs.get('Insurance', {}).get('display_days')}, Expiry: {docs.get('Insurance', {}).get('date_str')})\n"
        f"- PUC: {docs.get('PUC', {}).get('status')} ({docs.get('PUC', {}).get('display_days')}, Expiry: {docs.get('PUC', {}).get('date_str')})\n"
        f"- Driving Licence: {docs.get('Driving Licence', {}).get('status')} ({docs.get('Driving Licence', {}).get('display_days')}, Expiry: {docs.get('Driving Licence', {}).get('date_str')})\n"
        f"Priority Document: {eval_data.get('priority_text')}\n"
    )

    if provider in ("groq", "xai") and key:
        url = GROQ_API_URL if provider == "groq" else XAI_API_URL
        system_content = f"{CHATBOT_SYSTEM_PROMPT}\n\nCURRENT VEHICLE STATUS:\n{context_summary}"
        
        messages = [{"role": "system", "content": system_content}]
        for h in history[-6:]:
            messages.append(h)
        messages.append({"role": "user", "content": user_query})

        headers = {
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }
        body = {
            "model": model,
            "messages": messages,
            "temperature": 0.4
        }
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, headers=headers, json=body)
                if resp.status_code == 200:
                    return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"[{provider.upper()} API] Exception during chat: {e}")

    # Enhanced Built-in AI Co-Pilot Reasoning
    return _enhanced_builtin_ai_chat(user_query, eval_data, context_summary)


def _enhanced_builtin_ai_chat(query: str, eval_data: Dict[str, Any], context_summary: str) -> str:
    """Rich conversational response generator when running without an external key."""
    q = query.lower()
    veh_num = eval_data.get("vehicle_reg", "Your Vehicle")
    owner = eval_data.get("owner_name", "Valued Owner")
    docs = eval_data.get("documents", {})
    priority_text = eval_data.get("priority_text", "All documents are in good standing.")
    immediate = eval_data.get("needs_immediate_renewal", [])

    if "first" in q or "priority" in q:
        return f"""### Recommended Renewal Priority for {veh_num}

Based on the chronological expiry dates evaluated:

**{priority_text}**

#### Why address this first?
- **Immediate Risk:** Driving with an expired document exposes the driver to immediate roadside penalties, vehicle impoundment, or insurance claim invalidation.
- **Grace Period Alert:** Documents like Insurance must be renewed within the prescribed window to prevent loss of your **No Claim Bonus (NCB)** discount (which can save up to 50% on premiums).

*Next Step:* Prepare your previous certificate copy and visit the official Parivahan Sewa portal (`parivahan.gov.in`) or your designated insurer app.

*(Note: This is an automated reminder tool, not a legal or government verification system.)*"""

    elif "expiring" in q or "soon" in q or "urgent" in q:
        items = []
        for name, d in docs.items():
            st = d.get("status")
            if st in ("EXPIRED", "URGENT", "RENEW SOON"):
                icon = "" if st == "EXPIRED" else ("" if st == "URGENT" else "")
                items.append(f"{icon} **{name}:** {st} — *{d.get('display_days')}* (Expiry: `{d.get('date_str')}`)")

        if items:
            return f"""### Notice: Documents Requiring Attention for {veh_num}

Here is the breakdown of documents that are either expired or approaching their deadlines:

{chr(10).join(items)}

#### Action Recommendations:
1. **PUC (Pollution Certificate):** Can be tested and renewed instantly (10-15 mins) at any authorized fuel station or testing kiosk.
2. **Vehicle Insurance:** Can be renewed online instantly with your policy number without requiring vehicle pre-inspection if done before the expiration date.
3. **Driving Licence / RC:** Requires booking a slot on the Parivahan portal."""
        else:
            return f"""### All Documents Compliant!

Good news, {owner}! None of your vehicle documents for **{veh_num}** are expired or expiring within the next 30 days.

All documents are currently in **VALID** status. Continue monitoring periodically."""

    elif "penalty" in q or "fine" in q or "cost" in q:
        return f"""### Motor Vehicle Statutory Penalties Overview

Under the Motor Vehicles Act regulations:

| Document | Statutory Section | Typical Penalty |
| :--- | :--- | :--- |
| **PUC (Emissions)** | Section 190(2) | **₹10,000 fine** and/or up to 3 months license disqualification |
| **Vehicle Insurance** | Section 196 | **₹2,000 fine** (first offense) / ₹4,000 & community service / imprisonment |
| **Driving Licence** | Section 181 | **₹5,000 fine** for driving without a valid driving licence |
| **Registration (RC)** | Section 192 | **₹5,000 to ₹10,000 fine** for unregistered vehicle usage |

*Critical Precaution:* If a vehicle is involved in a collision while uninsured or with an invalid PUC, insurance companies can legally repudiate accidental and third-party claims, leaving the vehicle owner personally liable for damages.

*(Reminder tool disclaimer: Verify specific local state amendments on parivahan.gov.in)*"""

    elif "checklist" in q or "steps" in q or "how" in q:
        return f"""### Step-by-Step Renewal Checklist for {owner}

Here is your renewal roadmap for **{veh_num}**:

1. **For Pollution Under Control (PUC):**
   - [ ] Drive vehicle to nearest authorized fuel station testing center.
   - [ ] Pay standard nominal fee (approx. ₹60–₹120).
   - [ ] Ensure certificate is uploaded to the national VAHAN database.

2. **For Vehicle Insurance:**
   - [ ] Keep previous policy document and RC copy ready.
   - [ ] Compare quotes on aggregator portals or renew directly with your existing insurer.
   - [ ] Ensure your **No Claim Bonus (NCB)** percentage is correctly carried forward.

3. **For Registration Certificate (RC) / Fitness:**
   - [ ] Submit Form 25 on `parivahan.gov.in`.
   - [ ] Schedule vehicle fitness inspection at local RTO.
   - [ ] Clear pending road taxes or traffic challans before inspection.

4. **For Driving Licence (DL):**
   - [ ] Submit renewal application on Sarathi Parivahan (`sarathi.parivahan.gov.in`).
   - [ ] Upload Form 1A (Medical Certificate) if above 40 years of age."""

    elif "reminder" in q:
        return f"""### Personalized Renewal Reminder

**TO:** {owner}
**VEHICLE:** {veh_num}
**DATE:** {eval_data.get('evaluation_date')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dear {owner},

This is an automated priority advisory regarding your vehicle **{veh_num}**.

**Current Priority:**
{priority_text}

**Document Health Summary:**
- RC: {docs.get('RC', {}).get('status')} ({docs.get('RC', {}).get('display_days')})
- Insurance: {docs.get('Insurance', {}).get('status')} ({docs.get('Insurance', {}).get('display_days')})
- PUC: {docs.get('PUC', {}).get('status')} ({docs.get('PUC', {}).get('display_days')})
- Driving Licence: {docs.get('Driving Licence', {}).get('status')} ({docs.get('Driving Licence', {}).get('display_days')})

Please arrange for timely renewals to ensure your vehicle remains legal, safe, and fully insured on public roads.

Best regards,
**AI Vehicle Document Renewal Assistant**
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*(Note: This is an automated reminder tool, not a government certification)*"""

    elif "status" in q:
        return f"""### Official Compliance Summary for {veh_num}

**Owner:** {owner}
**Evaluation Date:** {eval_data.get('evaluation_date')}

- **Registration Certificate (RC):** `{docs.get('RC', {}).get('status')}` — {docs.get('RC', {}).get('display_days')} (Expires: {docs.get('RC', {}).get('date_str')})
- **Vehicle Insurance:** `{docs.get('Insurance', {}).get('status')}` — {docs.get('Insurance', {}).get('display_days')} (Expires: {docs.get('Insurance', {}).get('date_str')})
- **Pollution Certificate (PUC):** `{docs.get('PUC', {}).get('status')}` — {docs.get('PUC', {}).get('display_days')} (Expires: {docs.get('PUC', {}).get('date_str')})
- **Driving Licence (DL):** `{docs.get('Driving Licence', {}).get('status')}` — {docs.get('Driving Licence', {}).get('display_days')} (Expires: {docs.get('Driving Licence', {}).get('date_str')})

**Top Action Item:**
{priority_text}"""

    else:
        return f"""Hello {owner}! I am your **AI Vehicle Document Renewal Assistant** for **{veh_num}**.

Here is what I can assist you with:
- **"Which document should I renew first?"** — Identify the most critical deadline.
- **"Which documents are expiring soon?"** — List all upcoming or expired records.
- **"Statutory penalties & fines"** — Review legal provisions under the Motor Vehicles Act.
- **"Step-by-step renewal checklist"** — Detailed instructions for Parivahan & insurer portals.
- **"Give me a renewal reminder"** — Generate an official reminder draft.

What would you like to check?"""


def format_fallback_response(eval_data: Dict[str, Any]) -> str:
    """Backward compatibility alias."""
    return format_structured_report(eval_data)


def get_xai_api_key() -> str:
    """Helper to retrieve active key."""
    provider, key, _ = detect_api_provider()
    return key
