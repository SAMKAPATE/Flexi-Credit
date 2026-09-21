"""
Automated Reminder Engine.
Scans registered vehicles and documents, evaluates urgency thresholds,
generates multi-channel notifications via Grok AI Agent, and logs notification history.
"""

from datetime import datetime, date
from typing import List, Dict, Any
from database import (
    get_all_documents,
    log_reminder,
    get_all_vehicles
)
from grok_client import generate_multi_channel_reminders


def build_vehicle_context_string() -> str:
    """Creates a concise textual overview of all vehicles and their document statuses for the AI Agent."""
    docs = get_all_documents()
    if not docs:
        return "No vehicles or documents currently recorded in database."

    summary_lines = []
    for d in docs:
        reg = d.get("reg_no", "Unknown")
        model = d.get("make_model", "")
        owner = d.get("owner_name", "")
        doc = d.get("doc_type", "")
        expiry = d.get("expiry_date", "")
        days = d.get("days_left")
        urgency = d.get("urgency", "UNKNOWN")
        
        if days is not None:
            if days < 0:
                day_str = f"EXPIRED ({abs(days)} days ago)"
            elif days == 0:
                day_str = "EXPIRES TODAY!"
            else:
                day_str = f"{days} days remaining"
        else:
            day_str = "Unknown"

        summary_lines.append(f"• [{urgency}] {reg} ({model}, Owner: {owner}) - {doc} expires on {expiry} ({day_str})")

    return "\n".join(summary_lines)


def scan_and_generate_reminders(threshold_days: int = 30) -> Dict[str, Any]:
    """
    Scans all documents in the database. For any document that is EXPIRED, CRITICAL (<=7 days),
    or EXPIRING_SOON (<= threshold_days), it asks the Grok AI Agent to draft tailored
    Email, SMS, and WhatsApp notifications and records them in the database.
    """
    docs = get_all_documents()
    candidates = []

    for d in docs:
        days = d.get("days_left")
        if days is not None and days <= threshold_days:
            candidates.append(d)

    dispatched = []
    for doc in candidates:
        # Call Grok AI Agent to craft notifications
        notifications = generate_multi_channel_reminders(doc)
        
        urgency_level = doc.get("urgency", "NORMAL")
        doc_id = doc["id"]
        owner_name = doc.get("owner_name", "Owner")
        email = doc.get("email", "") or f"{owner_name.lower().replace(' ', '.')}@example.com"
        phone = doc.get("phone", "") or "+91-9876543210"

        # Log Email reminder
        log_reminder(
            doc_id=doc_id,
            channel="Email",
            recipient=email,
            message=f"Subject: {notifications.get('email_subject')}\n\n{notifications.get('email_body')}",
            urgency=urgency_level,
            status="SIMULATED"
        )

        # Log SMS reminder
        log_reminder(
            doc_id=doc_id,
            channel="SMS",
            recipient=phone,
            message=notifications.get("sms_text", ""),
            urgency=urgency_level,
            status="SIMULATED"
        )

        # Log WhatsApp reminder
        log_reminder(
            doc_id=doc_id,
            channel="WhatsApp",
            recipient=phone,
            message=notifications.get("whatsapp_text", ""),
            urgency=urgency_level,
            status="SIMULATED"
        )

        dispatched.append({
            "doc_id": doc_id,
            "vehicle": f"{doc.get('reg_no')} ({doc.get('make_model')})",
            "owner": owner_name,
            "doc_type": doc.get("doc_type"),
            "expiry_date": doc.get("expiry_date"),
            "days_left": doc.get("days_left"),
            "urgency": urgency_level,
            "notifications": notifications
        })

    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "scanned_total": len(docs),
        "alerts_triggered": len(dispatched),
        "items": dispatched
    }
