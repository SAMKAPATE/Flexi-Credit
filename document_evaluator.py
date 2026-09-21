"""
Document Evaluator Module.
Performs strictly deterministic Python-based date calculations and categorization
for the 4 mandatory vehicle documents: RC, Insurance, PUC, and Driving Licence.
"""

from datetime import datetime, date
from typing import Dict, Any, Tuple, Optional, List

DOCUMENT_KEYS = [
    ("rc", "Registration Certificate (RC)"),
    ("insurance", "Vehicle Insurance"),
    ("puc", "Pollution Under Control (PUC)"),
    ("dl", "Driving Licence (DL)")
]


def parse_date(date_input: Any) -> Optional[date]:
    """Parses various date inputs into a python date object."""
    if not date_input:
        return None
    if isinstance(date_input, date):
        return date_input
    if isinstance(date_input, datetime):
        return date_input.date()
    
    clean_str = str(date_input).strip()
    # Try ISO YYYY-MM-DD
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(clean_str, fmt).date()
        except ValueError:
            pass
    return None


def evaluate_document_expiry(date_input: Any, reference_date: Optional[date] = None) -> Dict[str, Any]:
    """
    Calculates days remaining and categorizes expiry:
    - EXPIRED: expiry date has already passed (< 0 days)
    - URGENT: expires within 7 days (0 to 7 days)
    - RENEW SOON: expires within 30 days (8 to 30 days)
    - VALID: more than 30 days remaining (> 30 days)
    """
    ref = reference_date or date.today()
    parsed = parse_date(date_input)

    if not parsed:
        return {
            "valid_date": False,
            "date_str": str(date_input or "").strip(),
            "days_remaining": None,
            "status": "INVALID_DATE",
            "display_days": "Invalid or missing date",
            "badge_color": "#94a3b8"
        }

    days = (parsed - ref).days

    if days < 0:
        status = "EXPIRED"
        display_days = f"Expired {abs(days)} day(s) ago"
        badge_color = "#ef4444"  # Red
    elif days == 0:
        status = "URGENT"
        display_days = "Expires today!"
        badge_color = "#f97316"  # Orange
    elif days <= 7:
        status = "URGENT"
        display_days = f"{days} day(s) remaining"
        badge_color = "#f97316"  # Orange
    elif days <= 30:
        status = "RENEW SOON"
        display_days = f"{days} day(s) remaining"
        badge_color = "#eab308"  # Yellow
    else:
        status = "VALID"
        display_days = f"{days} day(s) remaining"
        badge_color = "#10b981"  # Green

    return {
        "valid_date": True,
        "date_obj": parsed,
        "date_str": parsed.strftime("%Y-%m-%d"),
        "days_remaining": days,
        "status": status,
        "display_days": display_days,
        "badge_color": badge_color
    }


def evaluate_all_documents(
    owner_name: str,
    vehicle_reg: str,
    rc_date: Any,
    insurance_date: Any,
    puc_date: Any,
    dl_date: Any,
    reference_date: Optional[date] = None
) -> Dict[str, Any]:
    """
    Evaluates all 4 vehicle documents in pure Python.
    Calculates priority based on earliest expiry date.
    """
    ref = reference_date or date.today()

    eval_rc = evaluate_document_expiry(rc_date, ref)
    eval_ins = evaluate_document_expiry(insurance_date, ref)
    eval_puc = evaluate_document_expiry(puc_date, ref)
    eval_dl = evaluate_document_expiry(dl_date, ref)

    docs = {
        "RC": eval_rc,
        "Insurance": eval_ins,
        "PUC": eval_puc,
        "Driving Licence": eval_dl
    }

    # Identify priority document based on lowest days_remaining
    valid_docs = [
        (name, d) for name, d in docs.items()
        if d["valid_date"] and d["days_remaining"] is not None
    ]
    
    # Sort by days_remaining ascending (earliest expiry first)
    valid_docs.sort(key=lambda item: item[1]["days_remaining"])

    priority_name = None
    priority_doc = None
    priority_text = "All documents have valid future dates."

    if valid_docs:
        earliest_name, earliest_data = valid_docs[0]
        priority_name = earliest_name
        priority_doc = earliest_data
        days = earliest_data["days_remaining"]
        status = earliest_data["status"]

        if status == "EXPIRED":
            priority_text = f"{earliest_name} is already EXPIRED ({abs(days)} days ago on {earliest_data['date_str']}) and requires immediate renewal."
        elif status == "URGENT":
            priority_text = f"{earliest_name} is URGENT (expires in {days} days on {earliest_data['date_str']}) and should be renewed first."
        elif status == "RENEW SOON":
            priority_text = f"{earliest_name} is due to RENEW SOON (expires in {days} days on {earliest_data['date_str']}) and is next in line."
        else:
            priority_text = f"All documents are currently VALID. Earliest renewal is {earliest_name} in {days} days."

    # Immediate attention flags
    needs_immediate_renewal = [
        name for name, d in docs.items()
        if d["status"] in ("EXPIRED", "URGENT")
    ]

    return {
        "owner_name": (owner_name or "Vehicle Owner").strip(),
        "vehicle_reg": (vehicle_reg or "Not Specified").strip().upper(),
        "evaluation_date": ref.strftime("%Y-%m-%d"),
        "documents": docs,
        "priority_document": priority_name,
        "priority_text": priority_text,
        "needs_immediate_renewal": needs_immediate_renewal
    }
