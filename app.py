"""
AI Agent for Automated Vehicle Document Renewal Reminder.
Includes all core & extra requirements:
- Modern tactile UI styling with responsive cards and feedback
- Document upload & AI extraction
- AI chatbot with contextual awareness
- Automated multi-tier reminder levels (Email, SMS, WhatsApp)
- Persistent Renewal History audit trail
- Multiple Vehicles Fleet Management
- Live Search & Filter
- AI Priority Analysis (Strict Required Format)
- SQLite Relational Database with Transactions
- Security & Parameterized SQL
- Comprehensive Error Handling
"""

import os
import json
from datetime import date, timedelta, datetime
import gradio as gr
from dotenv import load_dotenv

from database import (
    init_db,
    add_vehicle,
    get_all_vehicles,
    get_vehicle_by_id,
    get_documents_for_vehicle,
    get_all_documents,
    add_or_update_document,
    record_document_renewal,
    get_renewal_history,
    search_and_filter_documents,
    log_reminder,
    get_reminder_logs,
    seed_multi_vehicle_data
)
from document_evaluator import evaluate_all_documents, parse_date
from grok_agent import (
    generate_renewal_analysis,
    chat_with_assistant,
    get_active_provider_info,
    get_xai_api_key
)
from document_parser import extract_from_file_or_text

load_dotenv()

# Initialize Database & Multi-Vehicle Data
init_db()
seed_multi_vehicle_data(force_reset=False)


# --- 3D Spatial & Neomorphic Styling ---
THREE_D_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

:root {
    --bg-base: #060911;
    --card-3d-bg: linear-gradient(145deg, rgba(20, 29, 52, 0.85) 0%, rgba(10, 16, 30, 0.95) 100%);
    --card-3d-border: rgba(99, 102, 241, 0.25);
    --shadow-3d: 0 20px 45px -10px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.08), inset 0 2px 0 rgba(255, 255, 255, 0.15), inset 0 -2px 0 rgba(0, 0, 0, 0.5);
    --shadow-3d-hover: 0 30px 60px -12px rgba(0, 0, 0, 0.9), 0 0 0 1px rgba(99, 102, 241, 0.4), inset 0 2px 0 rgba(255, 255, 255, 0.25);
}

.gradio-container {
    max-width: 1340px !important;
    margin: 0 auto !important;
    padding: 16px 22px !important;
    font-family: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif !important;
    background: radial-gradient(circle at 15% 15%, rgba(79, 70, 229, 0.16) 0%, transparent 45%),
                radial-gradient(circle at 85% 20%, rgba(6, 182, 212, 0.14) 0%, transparent 40%),
                radial-gradient(circle at 50% 85%, rgba(236, 72, 153, 0.09) 0%, transparent 50%),
                var(--bg-base) !important;
    color: #f1f5f9 !important;
    min-height: 100vh;
}

/* Header Banner - Clean Title Only with 3D Depth */
.hero-header {
    background: linear-gradient(135deg, rgba(30, 27, 75, 0.95) 0%, rgba(15, 23, 42, 0.98) 60%, rgba(14, 116, 144, 0.3) 100%);
    border: 1px solid rgba(99, 102, 241, 0.4);
    border-radius: 20px;
    padding: 24px 32px;
    margin-bottom: 22px;
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.7), inset 0 2px 0 rgba(255, 255, 255, 0.15), inset 0 -2px 0 rgba(0, 0, 0, 0.5);
    transform: perspective(1000px) translateZ(0);
}

.hero-title {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.6px;
    margin: 0;
    background: linear-gradient(90deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
}

/* 3D Physical Pushable Buttons */
.btn-3d-primary {
    background: linear-gradient(180deg, #4f46e5 0%, #3730a3 100%) !important;
    border: none !important;
    border-bottom: 4px solid #1e1b4b !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: 12px !important;
    box-shadow: 0 10px 25px -5px rgba(79, 70, 229, 0.5) !important;
    transition: all 0.12s ease !important;
}

.btn-3d-primary:hover {
    transform: translateY(2px) !important;
    border-bottom: 2px solid #1e1b4b !important;
    box-shadow: 0 6px 15px -3px rgba(79, 70, 229, 0.6) !important;
}

.btn-3d-primary:active {
    transform: translateY(4px) !important;
    border-bottom: 0px solid transparent !important;
}

/* 3D Floating Document Cards */
.doc-cards-3d-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 18px;
    margin: 18px 0;
    perspective: 1200px;
}

.doc-card-3d {
    background: var(--card-3d-bg);
    border: 1px solid var(--card-3d-border);
    border-radius: 18px;
    padding: 20px 22px;
    position: relative;
    box-shadow: var(--shadow-3d);
    transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    transform: rotateX(2deg);
}

.doc-card-3d:hover {
    transform: translateY(-5px) rotateX(0deg) scale(1.02);
    box-shadow: var(--shadow-3d-hover);
    border-color: rgba(99, 102, 241, 0.5);
}

.doc-card-title {
    font-size: 14px;
    font-weight: 700;
    color: #e2e8f0;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.doc-days-badge {
    font-size: 18px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-bottom: 6px;
}

.doc-date-sub {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 14px;
}

.meter-track-3d {
    width: 100%;
    height: 8px;
    background: rgba(0, 0, 0, 0.5);
    border-radius: 999px;
    overflow: hidden;
    box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

.meter-fill-3d {
    height: 100%;
    border-radius: 999px;
    box-shadow: 0 0 10px currentColor;
    transition: width 0.6s ease;
}

/* Category Badges */
.badge-tag-3d {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
    text-transform: uppercase;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.badge-expired-3d { background: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.5); }
.badge-urgent-3d { background: rgba(249, 115, 22, 0.2); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.5); }
.badge-soon-3d { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.5); }
.badge-valid-3d { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.5); }

/* Urgent Banner with 3D Bevel */
.urgent-banner-3d {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.22) 0%, rgba(15, 23, 42, 0.9) 100%);
    border: 1px solid rgba(239, 68, 68, 0.5);
    border-left: 6px solid #ef4444;
    border-radius: 14px;
    padding: 16px 22px;
    color: #fecaca;
    font-size: 14px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    gap: 14px;
    box-shadow: 0 10px 25px -5px rgba(239, 68, 68, 0.3);
}

/* 3D Car Viewport Frame */
.car-3d-frame {
    border-radius: 18px;
    overflow: hidden;
    border: 1px solid rgba(99, 102, 241, 0.3);
    box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.1);
    margin-bottom: 20px;
    background: #090e1a;
}

/* Tables */
.custom-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0 8px;
}
.custom-table th {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 600;
    text-align: left;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}
.custom-table tr.table-row {
    background: rgba(20, 29, 52, 0.6);
    border-radius: 10px;
    transition: background 0.15s ease;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}
.custom-table tr.table-row:hover { background: rgba(30, 41, 59, 0.85); }
.custom-table td {
    padding: 12px 14px;
    font-size: 13px;
    color: #e2e8f0;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.custom-table td:first-child { border-left: 1px solid rgba(255, 255, 255, 0.05); border-top-left-radius: 10px; border-bottom-left-radius: 10px; }
.custom-table td:last-child { border-right: 1px solid rgba(255, 255, 255, 0.05); border-top-right-radius: 10px; border-bottom-right-radius: 10px; }

/* Footer */
.footer-disclaimer {
    text-align: center;
    padding: 16px 20px;
    color: #64748b;
    font-size: 12px;
    border-top: 1px solid rgba(148, 163, 184, 0.1);
    margin-top: 30px;
}
"""


# --- UI Helpers ---

def get_vehicle_dropdown_choices():
    vehicles = get_all_vehicles()
    return [(f"{v['reg_no']} ({v['make_model']} - {v['owner_name']})", v["id"]) for v in vehicles]


def render_cards_html_3d(eval_data: dict) -> str:
    """Renders 3D tactile cards with depth elevation and real-time countdown meters."""
    docs = eval_data.get("documents", {})
    immediate = eval_data.get("needs_immediate_renewal", [])
    veh_reg = eval_data.get("vehicle_reg", "MH-12-AB-1234")

    banner_html = ""
    if immediate:
        banner_html = f"""
        <div class="urgent-banner-3d">
            <span style="font-size: 24px;"></span>
            <div>
                <strong style="color: #ffffff; font-size: 15px;">Urgent Renewal Action for {veh_reg}:</strong><br>
                <span>The following document(s) have expired or expire within 7 days: <strong style="color: #fca5a5;">{', '.join(immediate)}</strong>. Action required immediately.</span>
            </div>
        </div>
        """

    cards = []
    card_meta = [
        ("RC", "Registration Certificate (RC)", "", 100),
        ("Insurance", "Vehicle Insurance", "", 35),
        ("PUC", "Pollution Certificate (PUC)", "", 15),
        ("Driving Licence", "Driving Licence (DL)", "", 65)
    ]

    for key, title, icon, default_meter in card_meta:
        d = docs.get(key, {})
        status = d.get("status", "UNKNOWN")
        days_str = d.get("display_days", "N/A")
        date_str = d.get("date_str", "Not Provided")

        if status == "EXPIRED":
            badge_class = "badge-expired-3d"
            accent_color = "#f43f5e"
            meter_val = 5
        elif status == "URGENT":
            badge_class = "badge-urgent-3d"
            accent_color = "#f97316"
            meter_val = 20
        elif status == "RENEW SOON":
            badge_class = "badge-soon-3d"
            accent_color = "#f59e0b"
            meter_val = 50
        elif status == "VALID":
            badge_class = "badge-valid-3d"
            accent_color = "#10b981"
            meter_val = 90
        else:
            badge_class = ""
            accent_color = "#94a3b8"
            meter_val = 0

        card_html = f"""
        <div class="doc-card-3d" style="border-top: 4px solid {accent_color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div class="doc-card-title">{icon} {title}</div>
                <span class="badge-tag-3d {badge_class}">{status}</span>
            </div>
            <div class="doc-days-badge" style="color: {accent_color};">
                {days_str}
            </div>
            <div class="doc-date-sub">
                Official Expiry: <strong style="color: #cbd5e1;">{date_str}</strong>
            </div>
            <div class="meter-track-3d">
                <div class="meter-fill-3d" style="width: {meter_val}%; background: {accent_color}; color: {accent_color};"></div>
            </div>
        </div>
        """
        cards.append(card_html)

    return f"{banner_html}<div class='doc-cards-3d-grid'>{''.join(cards)}</div>"


def render_search_table_html(query: str = "", status_filter: str = "ALL") -> str:
    """Renders searchable document table."""
    docs = search_and_filter_documents(query, status_filter)
    if not docs:
        return "<div style='color: #94a3b8; text-align: center; padding: 30px; background: rgba(20,29,52,0.4); border-radius: 12px;'>No documents match the search criteria.</div>"

    rows = []
    for d in docs:
        st = d.get("urgency", "UNKNOWN")
        badge_cls = (
            "badge-expired-3d" if st == "EXPIRED" else
            "badge-urgent-3d" if st == "URGENT" else
            "badge-soon-3d" if st == "RENEW SOON" else
            "badge-valid-3d"
        )
        rows.append(f"""
        <tr class="table-row">
            <td><strong style="color: #38bdf8;">{d.get('reg_no')}</strong><br><span style="font-size: 11px; color: #94a3b8;">{d.get('make_model')}</span></td>
            <td><strong>{d.get('owner_name')}</strong></td>
            <td><strong>{d.get('doc_type')}</strong><br><span style="font-size: 11px; color: #94a3b8;">{d.get('issuer') or '—'}</span></td>
            <td><code>{d.get('policy_no') or '—'}</code></td>
            <td style="font-weight: 600;">{d.get('expiry_date')}</td>
            <td><span class="badge-tag-3d {badge_cls}">{st}</span></td>
            <td style="font-weight: 600;">{d.get('display_days')}</td>
        </tr>
        """)

    return f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>Vehicle</th>
                <th>Owner</th>
                <th>Document Type</th>
                <th>Policy / Ref No</th>
                <th>Expiry Date</th>
                <th>Status</th>
                <th>Days Remaining</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


def render_renewal_history_html() -> str:
    """Renders table of past renewals."""
    history = get_renewal_history(limit=25)
    if not history:
        return "<div style='color: #94a3b8; text-align: center; padding: 30px;'>No renewal records logged yet. Renew any document to create an audit record.</div>"

    rows = []
    for h in history:
        rows.append(f"""
        <tr class="table-row">
            <td>#{h['id']}</td>
            <td><strong style="color: #38bdf8;">{h.get('reg_no')}</strong> ({h.get('owner_name')})</td>
            <td><strong>{h.get('doc_type')}</strong></td>
            <td style="color: #f87171;">{h.get('old_expiry') or '—'}</td>
            <td style="color: #34d399; font-weight: 700;">{h.get('new_expiry')}</td>
            <td><code>{h.get('policy_no') or '—'}</code></td>
            <td style="color: #94a3b8; font-size: 12px;">{h.get('renewed_on')}</td>
            <td><span style="font-size: 12px; color: #cbd5e1;">{h.get('notes') or '—'}</span></td>
        </tr>
        """)

    return f"""
    <table class="custom-table">
        <thead>
            <tr>
                <th>ID</th>
                <th>Vehicle & Owner</th>
                <th>Document</th>
                <th>Previous Expiry</th>
                <th>New Expiry</th>
                <th>Policy No</th>
                <th>Date Renewed</th>
                <th>Notes</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """


# --- Core Logic & Event Handlers ---

def evaluate_selected_vehicle(vehicle_id, api_key_override):
    """Loads a registered vehicle from SQLite, evaluates documents, and populates entry fields."""
    if not vehicle_id:
        return (
            "Notice: Please select a vehicle from the dropdown.",
            "<div style='color: #94a3b8; padding: 20px; text-align: center;'>Select a vehicle from the dropdown above.</div>",
            "",
            {},
            [],
            "", "", "", "", "", ""
        )

    v = get_vehicle_by_id(int(vehicle_id))
    if not v:
        return (
            "Notice: Vehicle not found in database.",
            "<div style='color: #ef4444; padding: 20px; text-align: center;'>Vehicle not found.</div>",
            "",
            {},
            [],
            "", "", "", "", "", ""
        )

    docs = get_documents_for_vehicle(int(vehicle_id))
    rc_date = next((d["expiry_date"] for d in docs if "RC" in d["doc_type"] or "Registration" in d["doc_type"]), "")
    ins_date = next((d["expiry_date"] for d in docs if "Insurance" in d["doc_type"]), "")
    puc_date = next((d["expiry_date"] for d in docs if "PUC" in d["doc_type"] or "Pollution" in d["doc_type"]), "")
    dl_date = next((d["expiry_date"] for d in docs if "Driving" in d["doc_type"] or "DL" in d["doc_type"]), "")

    eval_result = evaluate_all_documents(
        owner_name=v["owner_name"],
        vehicle_reg=v["reg_no"],
        rc_date=rc_date,
        insurance_date=ins_date,
        puc_date=puc_date,
        dl_date=dl_date
    )

    cards_html = render_cards_html_3d(eval_result)
    ai_report = generate_renewal_analysis(eval_result, api_key=api_key_override)

    initial_chat = [
        {"role": "assistant", "content": f"Hello **{v['owner_name']}**! I am your AI Vehicle Document Renewal Assistant for vehicle **{v['reg_no']}** ({v['make_model']}).\n\n**Immediate Priority:** {eval_result['priority_text']}\n\nAsk me any question below or click the quick action chips!"}
    ]

    status_msg = f"Success: **Loaded Fleet Vehicle:** Successfully populated records for `{v['reg_no']}` ({v['owner_name']})."
    return status_msg, cards_html, ai_report, eval_result, initial_chat, v["owner_name"], v["reg_no"], rc_date, ins_date, puc_date, dl_date


def on_manual_analyze(owner_name, reg_no, rc_date, ins_date, puc_date, dl_date, api_key_override):
    """
    Evaluates user input directly from registration form.
    Validates dates, detects invalid/missing values, categorizes using pure Python,
    saves to SQLite database, and generates official Grok/Groq AI response.
    """
    if not reg_no or not reg_no.strip():
        empty_html = """
        <div style='color: #f87171; padding: 22px; text-align: center; background: rgba(239, 68, 68, 0.12); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 14px;'>
            
            <strong style='font-size: 15px;'>Vehicle Registration Number is required.</strong><br>
            <span style='font-size: 13px; color: #cbd5e1;'>Please enter a vehicle registration number (e.g. MH-12-AB-1234).</span>
        </div>
        """
        return (
            "Notice: **Validation Error:** Vehicle Registration Number is required. Please provide a registration number.",
            empty_html,
            "Error: Vehicle Registration Number is required.",
            {},
            [],
            gr.update()
        )

    # Validate dates
    invalid_dates = []
    date_inputs = [
        ("Registration (RC)", rc_date),
        ("Insurance", ins_date),
        ("Pollution (PUC)", puc_date),
        ("Driving Licence (DL)", dl_date)
    ]
    for d_name, d_val in date_inputs:
        if d_val and d_val.strip():
            if not parse_date(d_val):
                invalid_dates.append(f"**{d_name}** (`{d_val}`)")
        else:
            invalid_dates.append(f"**{d_name}** (missing)")

    eval_result = evaluate_all_documents(
        owner_name=owner_name,
        vehicle_reg=reg_no,
        rc_date=rc_date,
        insurance_date=ins_date,
        puc_date=puc_date,
        dl_date=dl_date
    )
    cards_html = render_cards_html_3d(eval_result)
    ai_report = generate_renewal_analysis(eval_result, api_key=api_key_override)

    if invalid_dates:
        status_msg = f"Notice: **Date Notice:** Some dates are missing or not in standard YYYY-MM-DD format: {', '.join(invalid_dates)}. Python evaluation completed for available dates."
    else:
        status_msg = f"Success: **Calculation Complete:** Evaluated 4 documents for vehicle `{reg_no.strip().upper()}`. Categorization and priority determined in pure Python."

    # Automatically save / update to database so all fleet tabs stay synced
    try:
        reg_clean = reg_no.strip().upper()
        owner_clean = (owner_name or "Vehicle Owner").strip()
        vid = add_vehicle(reg_clean, make_model="Registered Vehicle", owner_name=owner_clean)
        if eval_result["documents"]["RC"]["valid_date"]:
            add_or_update_document(vid, "Registration Certificate (RC)", rc_date.strip())
        if eval_result["documents"]["Insurance"]["valid_date"]:
            add_or_update_document(vid, "Vehicle Insurance", ins_date.strip())
        if eval_result["documents"]["PUC"]["valid_date"]:
            add_or_update_document(vid, "Pollution Under Control (PUC)", puc_date.strip())
        if eval_result["documents"]["Driving Licence"]["valid_date"]:
            add_or_update_document(vid, "Driving Licence (DL)", dl_date.strip())
    except Exception:
        pass

    initial_chat = [
        {"role": "assistant", "content": f"Loaded vehicle **{eval_result['vehicle_reg']}** (Owner: {eval_result['owner_name']}).\n\n**Immediate Priority:** {eval_result['priority_text']}"}
    ]
    choices = get_vehicle_dropdown_choices()
    return status_msg, cards_html, ai_report, eval_result, initial_chat, gr.update(choices=choices)


def on_load_sample_data(api_key_override):
    """Generates realistic demo dates for quick college project presentation."""
    today = date.today()
    rc_val = (today + timedelta(days=720)).strftime("%Y-%m-%d")
    ins_val = (today + timedelta(days=4)).strftime("%Y-%m-%d")
    puc_val = (today - timedelta(days=14)).strftime("%Y-%m-%d")
    dl_val = (today + timedelta(days=22)).strftime("%Y-%m-%d")
    owner_val = "Rahul Sharma"
    reg_val = "MH-12-AB-1234"

    eval_result = evaluate_all_documents(
        owner_name=owner_val,
        vehicle_reg=reg_val,
        rc_date=rc_val,
        insurance_date=ins_val,
        puc_date=puc_val,
        dl_date=dl_val
    )
    cards_html = render_cards_html_3d(eval_result)
    ai_report = generate_renewal_analysis(eval_result, api_key=api_key_override)
    initial_chat = [
        {"role": "assistant", "content": f"Sample demo loaded for **{reg_val}** (Owner: {owner_val}).\n\n**Immediate Priority:** {eval_result['priority_text']}"}
    ]
    status_msg = "**Demo Sample Loaded:** Populated sample vehicle `MH-12-AB-1234` with representative EXPIRED, URGENT, RENEW SOON, and VALID documents."
    choices = get_vehicle_dropdown_choices()
    return owner_val, reg_val, rc_val, ins_val, puc_val, dl_val, status_msg, cards_html, ai_report, eval_result, initial_chat, gr.update(choices=choices)


def on_reset_clear_form():
    """Resets all input fields and cleared displays."""
    cleared_html = """
    <div style='text-align: center; padding: 32px; background: rgba(15, 23, 42, 0.6); border-radius: 14px; border: 1px dashed rgba(99, 102, 241, 0.3);'>
        
        <h4 style='color: #cbd5e1; margin: 10px 0 6px 0; font-size: 16px;'>Form Cleared & Reset</h4>
        <p style='color: #64748b; font-size: 13px; margin: 0;'>Enter owner name, vehicle registration number, and document expiry dates above and click <strong>'Calculate Expiry & Generate AI Reminder'</strong>.</p>
    </div>
    """
    return (
        "", "", "", "", "", "",
        "",
        cleared_html,
        "",
        {},
        [{"role": "assistant", "content": "Hello! Please enter your vehicle details and document expiry dates in the first tab to begin."}]
    )


def on_add_new_vehicle_to_db(reg_no, make_model, vehicle_type, owner_name, email, phone):
    if not reg_no or not make_model or not owner_name:
        return "Notice: Error: Registration Number, Model, and Owner Name are required.", gr.update()
    try:
        new_id = add_vehicle(reg_no, make_model, owner_name, vehicle_type, email, phone)
        choices = get_vehicle_dropdown_choices()
        return f"Success: Vehicle '{reg_no.upper()}' registered successfully! (ID: {new_id})", gr.update(choices=choices, value=new_id)
    except Exception as e:
        return f"Notice: Error adding vehicle: {e}", gr.update()


def on_extract_document_upload(file_obj, raw_text, api_key_override):
    input_source = file_obj.name if file_obj else raw_text
    if not input_source or not str(input_source).strip():
        return "Notice: Please upload a document file or paste document/OCR text.", "", "", "", "", "", ""
    
    extracted = extract_from_file_or_text(input_source, api_key=api_key_override)
    status_msg = f"Document Analyzed: Extracted {extracted.get('doc_type')} for vehicle '{extracted.get('reg_no') or 'Unspecified'}'"
    return (
        status_msg,
        extracted.get("reg_no", ""),
        extracted.get("doc_type", "Registration Certificate (RC)"),
        extracted.get("policy_no", ""),
        extracted.get("issuer", ""),
        extracted.get("issue_date", ""),
        extracted.get("expiry_date", "")
    )


def on_save_extracted_to_db(reg_no, doc_type, policy_no, issuer, issue_date, expiry_date):
    if not expiry_date:
        return "Notice: Expiry Date is mandatory to record document."
    try:
        datetime.strptime(expiry_date.strip(), "%Y-%m-%d")
    except ValueError:
        return "Notice: Invalid Expiry Date format. Must be YYYY-MM-DD."

    reg_clean = (reg_no or "NEW-VEHICLE").strip().upper()
    vehicles = get_all_vehicles()
    v = next((item for item in vehicles if item["reg_no"] == reg_clean), None)
    if not v:
        vid = add_vehicle(reg_clean, "Auto-detected Vehicle", "Fleet Owner")
    else:
        vid = v["id"]

    add_or_update_document(
        vehicle_id=vid,
        doc_type=doc_type,
        expiry_date=expiry_date.strip(),
        policy_no=policy_no.strip(),
        issuer=issuer.strip(),
        issue_date=issue_date.strip(),
        notes="Saved via Document Upload AI Extractor"
    )
    return f"Success: Document successfully saved to database for vehicle '{reg_clean}'!"


def on_execute_document_renewal(doc_id, extension_term, new_policy_no, notes):
    if not doc_id:
        return "Notice: Please select a document to renew.", render_renewal_history_html(), gr.update()
    
    today = date.today()
    if "6 Months" in extension_term:
        new_exp = today + timedelta(days=180)
    elif "1 Year" in extension_term:
        new_exp = today + timedelta(days=365)
    elif "3 Years" in extension_term:
        new_exp = today + timedelta(days=365 * 3)
    elif "5 Years" in extension_term:
        new_exp = today + timedelta(days=365 * 5)
    else:
        new_exp = today + timedelta(days=365)

    new_expiry_str = new_exp.strftime("%Y-%m-%d")
    try:
        record_document_renewal(
            doc_id=int(doc_id),
            new_expiry_date=new_expiry_str,
            new_policy_no=new_policy_no,
            notes=notes or f"Renewed for {extension_term} on {today.strftime('%Y-%m-%d')}"
        )
        msg = f"Renewal Successful! New Expiry Date: {new_expiry_str}. Audit record created in SQLite."
        return msg, render_renewal_history_html(), gr.update(choices=_get_renewable_doc_choices())
    except Exception as e:
        return f"Notice: Renewal failed: {e}", render_renewal_history_html(), gr.update()


def _get_renewable_doc_choices():
    docs = get_all_documents()
    choices = []
    for d in docs:
        choices.append((f"#{d['id']} [{d.get('urgency')}] {d.get('reg_no')} - {d.get('doc_type')} (Expires: {d.get('expiry_date')})", d["id"]))
    return choices


def on_run_automated_reminder_scan(threshold_days, api_key_override):
    docs = get_all_documents()
    expiring_items = [d for d in docs if d.get("days_left") is not None and d.get("days_left") <= int(threshold_days)]
    
    if not expiring_items:
        return "All documents across your fleet are compliant! No documents expiring within this window.", "", render_search_table_html()

    cards_html = []
    for item in expiring_items:
        urgency = item.get("urgency", "NORMAL")
        urgency_color = "#ef4444" if urgency == "EXPIRED" else ("#f97316" if urgency == "URGENT" else "#eab308")
        reg_no = item.get("reg_no")
        owner = item.get("owner_name")
        doc_type = item.get("doc_type")
        days = item.get("days_left")
        expiry = item.get("expiry_date")

        sms_text = f"ALERT: {doc_type} for {reg_no} expires on {expiry} ({item.get('display_days')}). Renew now to avoid fines. -VehicleAgent"
        whatsapp_text = f"*VEHICLE RENEWAL ALERT*\n\nHello *{owner}*,\nYour *{doc_type}* for *{reg_no}* status is *{urgency}* ({item.get('display_days')}).\nExpiry: {expiry}\n\nPlease renew via Parivahan Sewa today."
        email_body = f"Dear {owner},\n\nThis is an automated renewal reminder for your vehicle ({reg_no}).\nDocument: {doc_type}\nStatus: {urgency} ({item.get('display_days')})\nExpiry: {expiry}\n\nTimely renewal ensures legal compliance and insurance protection.\n\nBest regards,\nAutomated Vehicle Renewal Agent"

        log_reminder(item["id"], "Email", item.get("email") or "owner@example.com", email_body, urgency=urgency)
        log_reminder(item["id"], "SMS", item.get("phone") or "+91-9876543210", sms_text, urgency=urgency)
        log_reminder(item["id"], "WhatsApp", item.get("phone") or "+91-9876543210", whatsapp_text, urgency=urgency)

        cards_html.append(f"""
        <div style="background: rgba(15, 23, 42, 0.9); border: 1px solid rgba(255, 255, 255, 0.08); border-left: 5px solid {urgency_color}; border-radius: 14px; padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.4);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h4 style="margin: 0; color: #f8fafc; font-size: 16px;">{reg_no} ({item.get('make_model')}) — <span style="color: #38bdf8;">{doc_type}</span></h4>
                <span class="badge-tag-3d" style="background: {urgency_color}22; color: {urgency_color}; border: 1px solid {urgency_color}55;">{urgency} ({item.get('display_days')})</span>
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; margin-top: 10px;">
                <div style="background: rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 12px;">
                    <div style="font-size: 11px; font-weight: 700; color: #22c55e; text-transform: uppercase;">WhatsApp Notification</div>
                    <pre style="white-space: pre-wrap; font-family: inherit; font-size: 12px; color: #cbd5e1; margin: 6px 0 0 0;">{whatsapp_text}</pre>
                </div>
                <div style="background: rgba(30, 41, 59, 0.6); border-radius: 8px; padding: 12px;">
                    <div style="font-size: 11px; font-weight: 700; color: #eab308; text-transform: uppercase;">SMS Snippet</div>
                    <div style="font-size: 12px; color: #cbd5e1; margin-top: 6px; font-family: monospace;">{sms_text}</div>
                </div>
            </div>
        </div>
        """)

    summary_banner = f"Automated Scan Complete: Triggered {len(expiring_items)} multi-channel reminders across the fleet. Logged to SQLite audit history."
    return summary_banner, "".join(cards_html), render_search_table_html()


def handle_chat_wrapper(message, history, eval_data, api_key_override):
    if not message or not message.strip():
        return "", history
    if not eval_data:
        eval_data = evaluate_all_documents("Vehicle Owner", "Your Vehicle", "", "", "", "")
    reply = chat_with_assistant(message, eval_data, history, api_key=api_key_override)
    return "", history + [{"role": "user", "content": message}, {"role": "assistant", "content": reply}]


# --- Gradio UI Assembly with 3D Spatial Layout ---

def create_ui():
    with gr.Blocks(title="AI Agent for Automated Vehicle Document Renewal Reminder") as demo:
        gr.HTML(f"<style>{THREE_D_CSS}</style>")

        # Clean Header Banner - Clean Title Only
        gr.HTML("""
        <div class="hero-header">
            <h1 class="hero-title">AI Agent for Automated Vehicle Document Renewal Reminder</h1>
        </div>
        """)

        # State to store current evaluated vehicle
        current_eval_state = gr.State({})

        with gr.Tabs() as main_tabs:

            # -------------------------------------------------------------
            # TAB 1: VEHICLE REGISTRATION & DOCUMENT EXPIRY TRACKER
            # -------------------------------------------------------------
            with gr.Tab("Vehicle Registration & Document Tracker", id="tab_dashboard"):
                gr.Markdown("### Vehicle & Document Expiry Registration")

                with gr.Row():
                    in_owner = gr.Textbox(
                        label="Owner Name *",
                        placeholder="Enter Owner Full Name (e.g. Rahul Sharma)",
                        value="Rahul Sharma",
                        scale=1
                    )
                    in_reg = gr.Textbox(
                        label="Vehicle Registration Number *",
                        placeholder="Enter Registration No (e.g. MH-12-AB-1234)",
                        value="MH-12-AB-1234",
                        scale=1
                    )

                with gr.Row():
                    in_rc = gr.Textbox(
                        label="1. Vehicle Registration Certificate (RC) Expiry *",
                        placeholder="YYYY-MM-DD (e.g. 2028-09-15)",
                        value=(date.today() + timedelta(days=720)).strftime("%Y-%m-%d"),
                        scale=1
                    )
                    in_ins = gr.Textbox(
                        label="2. Vehicle Insurance Expiry *",
                        placeholder="YYYY-MM-DD (e.g. 2026-09-24)",
                        value=(date.today() + timedelta(days=4)).strftime("%Y-%m-%d"),
                        scale=1
                    )

                with gr.Row():
                    in_puc = gr.Textbox(
                        label="3. Pollution Under Control Certificate (PUC) Expiry *",
                        placeholder="YYYY-MM-DD (e.g. 2026-09-06)",
                        value=(date.today() - timedelta(days=14)).strftime("%Y-%m-%d"),
                        scale=1
                    )
                    in_dl = gr.Textbox(
                        label="4. Driving Licence (DL) Expiry *",
                        placeholder="YYYY-MM-DD (e.g. 2026-10-12)",
                        value=(date.today() + timedelta(days=22)).strftime("%Y-%m-%d"),
                        scale=1
                    )

                with gr.Row():
                    btn_analyze = gr.Button("Calculate Expiry & Generate AI Reminder", variant="primary", scale=3, elem_classes=["btn-3d-primary"])
                    btn_clear = gr.Button("Reset / Clear Form", variant="stop", scale=1)
                    btn_sample = gr.Button("Load Demo Sample Dates", variant="secondary", scale=1)

                with gr.Accordion("Or Quick-Load from Saved Fleet Vehicles", open=False):
                    with gr.Row():
                        vehicle_selector = gr.Dropdown(
                            label="Select Saved Fleet Vehicle to Auto-Fill",
                            choices=get_vehicle_dropdown_choices(),
                            value=get_vehicle_dropdown_choices()[0][1] if get_vehicle_dropdown_choices() else None,
                            scale=4
                        )
                        btn_load_selected = gr.Button("Auto-Fill from Selected", variant="secondary", scale=2)

                status_feedback = gr.Markdown()

                # Document Status Display Cards (Urgent Banner + 4 Document Cards)
                gr.Markdown("### Document Compliance Status")
                initial_eval = evaluate_all_documents(
                    "Rahul Sharma",
                    "MH-12-AB-1234",
                    (date.today() + timedelta(days=720)).strftime("%Y-%m-%d"),
                    (date.today() + timedelta(days=4)).strftime("%Y-%m-%d"),
                    (date.today() - timedelta(days=14)).strftime("%Y-%m-%d"),
                    (date.today() + timedelta(days=22)).strftime("%Y-%m-%d")
                )
                cards_view = gr.HTML(value=render_cards_html_3d(initial_eval))

                gr.Markdown("---")
                gr.Markdown("### Grok AI Agent Analysis & Priority Reminder")
                output_ai_format = gr.Textbox(
                    label="Official AI Response Schema",
                    lines=14,
                    value=generate_renewal_analysis(initial_eval)
                )

            # -------------------------------------------------------------
            # TAB 2: AI VEHICLE RENEWAL ASSISTANT (CHATBOT)
            # -------------------------------------------------------------
            with gr.Tab("AI Vehicle Renewal Assistant", id="tab_chat"):
                gr.Markdown("""
                ### Automotive Compliance Co-Pilot
                Ask any questions about your vehicle documents, renewal priorities, statutory penalties, or step-by-step procedures.
                """)
                chatbot = gr.Chatbot(
                    height=380,
                    layout="bubble",
                    avatar_images=(None, "https://api.iconify.design/lucide:bot.svg?color=%23818cf8")
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        placeholder="Ask: 'Which document should I renew first?' or 'Give me a renewal reminder'...",
                        label="Your Question to AI Assistant",
                        scale=5
                    )
                    btn_chat_send = gr.Button("Send Query", variant="primary", scale=1, elem_classes=["btn-3d-primary"])

                gr.Markdown("**Quick Question Prompts:**")
                with gr.Row():
                    q1 = gr.Button("Which document should I renew first?", size="sm")
                    q2 = gr.Button("Which documents are expiring soon?", size="sm")
                with gr.Row():
                    q3 = gr.Button("Give me a renewal reminder.", size="sm")
                    q4 = gr.Button("What is the status of my vehicle documents?", size="sm")
                with gr.Row():
                    q5 = gr.Button("What are the legal statutory penalties and fines?", size="sm")
                    q6 = gr.Button("Give me a step-by-step renewal checklist", size="sm")

            # -------------------------------------------------------------
            # TAB 3: FLEET SEARCH & FILTER
            # -------------------------------------------------------------
            with gr.Tab("Fleet Search & Filter", id="tab_search"):
                gr.Markdown("###  Real-Time Document Search & Urgency Filtering")
                with gr.Row():
                    search_box = gr.Textbox(
                        label="Search Fleet",
                        placeholder="Search by Registration (e.g. MH-12, DL-01), Owner Name, or Document Type...",
                        scale=3
                    )
                    status_filter = gr.Dropdown(
                        label="Filter by Status",
                        choices=[
                            ("All Documents", "ALL"),
                            ("Action Required (Expired / Urgent / Soon)", "ACTION_REQUIRED"),
                            ("Expired Only", "EXPIRED"),
                            ("Urgent (≤7 Days)", "URGENT"),
                            ("Renew Soon (≤30 Days)", "RENEW_SOON"),
                            ("Valid Only", "VALID")
                        ],
                        value="ALL",
                        scale=2
                    )
                    btn_search = gr.Button("Filter", variant="secondary", scale=1)

                search_table = gr.HTML(value=render_search_table_html())

                search_box.change(render_search_table_html, [search_box, status_filter], [search_table])
                status_filter.change(render_search_table_html, [search_box, status_filter], [search_table])
                btn_search.click(render_search_table_html, [search_box, status_filter], [search_table])

            # -------------------------------------------------------------
            # TAB 4: DOCUMENT UPLOAD & AI SCANNER
            # -------------------------------------------------------------
            with gr.Tab("Document Upload & AI Scanner", id="tab_upload"):
                gr.Markdown("""
                ### Upload Document & AI Field Extraction
                Upload an image or document file, or paste raw policy / PUC text.
                The AI Agent will parse the Registration Number, Document Type, Issuer, and Expiry Date with validation.
                """)
                with gr.Row():
                    with gr.Column(scale=1):
                        file_input = gr.File(label="Upload Document File (Image, PDF, or TXT)")
                        ocr_text_input = gr.Textbox(
                            label="Or Paste OCR / Document Text",
                            placeholder="Paste text from insurance policy schedule, emission testing slip, or RC copy...",
                            lines=6,
                            value="HDFC ERGO General Insurance Policy Schedule\nVehicle Reg No: DL-04-XY-9988\nVehicle Make: Honda Elevate 2024\nPolicy No: HDFC-CAR-2024-990\nPeriod of Cover: Valid until 2026-11-15\nInsured: Pooja Sundaram"
                        )
                        btn_extract = gr.Button("Extract Document Details", variant="primary", elem_classes=["btn-3d-primary"])
                        upload_status = gr.Markdown()

                    with gr.Column(scale=1):
                        gr.Markdown("#### Extracted Structured Fields")
                        ext_reg = gr.Textbox(label="Vehicle Registration Number")
                        ext_type = gr.Dropdown(label="Document Type", choices=["Registration Certificate (RC)", "Vehicle Insurance", "Pollution Under Control (PUC)", "Driving Licence (DL)"])
                        ext_pol = gr.Textbox(label="Policy / Certificate Number")
                        ext_issuer = gr.Textbox(label="Issuer / Authority")
                        ext_issue = gr.Textbox(label="Issue Date (YYYY-MM-DD)")
                        ext_exp = gr.Textbox(label="Expiry Date (YYYY-MM-DD) *")
                        btn_save_db = gr.Button("Save Document Directly to SQLite Database", variant="secondary")
                        save_status = gr.Markdown()

                btn_extract.click(
                    fn=on_extract_document_upload,
                    inputs=[file_input, ocr_text_input, gr.State("")],
                    outputs=[upload_status, ext_reg, ext_type, ext_pol, ext_issuer, ext_issue, ext_exp]
                )
                btn_save_db.click(
                    fn=on_save_extracted_to_db,
                    inputs=[ext_reg, ext_type, ext_pol, ext_issuer, ext_issue, ext_exp],
                    outputs=[save_status]
                ).then(
                    fn=lambda: gr.update(choices=get_vehicle_dropdown_choices()),
                    inputs=[],
                    outputs=[vehicle_selector]
                )

            # -------------------------------------------------------------
            # TAB 5: AUTOMATED REMINDER LEVELS
            # -------------------------------------------------------------
            with gr.Tab("Automated Reminder Levels", id="tab_reminders"):
                gr.Markdown("""
                ### Multi-Tier Automated Reminder Engine
                Scans all fleet vehicles against your desired threshold window.
                Generates multi-level alerts (**Email**, **WhatsApp**, and **SMS**) with statutory penalty warnings.
                """)
                with gr.Row():
                    slider_threshold = gr.Slider(
                        minimum=1,
                        maximum=60,
                        value=30,
                        step=1,
                        label="Urgency Trigger Window (Days)",
                        info="Documents expiring within this number of days (or already expired) will trigger multi-channel alerts.",
                        scale=4
                    )
                    btn_run_reminders = gr.Button("Run Fleet Expiry Scan & Dispatch Alerts", variant="primary", scale=2, elem_classes=["btn-3d-primary"])

                reminder_banner = gr.Markdown()
                reminder_cards_view = gr.HTML()

                btn_run_reminders.click(
                    fn=on_run_automated_reminder_scan,
                    inputs=[slider_threshold, gr.State("")],
                    outputs=[reminder_banner, reminder_cards_view, search_table]
                )

            # -------------------------------------------------------------
            # TAB 6: RENEWAL HISTORY & 1-CLICK RENEW
            # -------------------------------------------------------------
            with gr.Tab("Renewal History & 1-Click Renew", id="tab_history"):
                gr.Markdown("### Execute 1-Click Renewal & Audit Trail")
                with gr.Row():
                    renew_doc_select = gr.Dropdown(
                        label="Select Document to Renew",
                        choices=_get_renewable_doc_choices(),
                        scale=3
                    )
                    renew_duration = gr.Dropdown(
                        label="Extension Period",
                        choices=["6 Months (PUC)", "1 Year (Standard)", "3 Years", "5 Years (Commercial/RC)"],
                        value="1 Year (Standard)",
                        scale=2
                    )
                    renew_new_policy = gr.Textbox(label="New Policy / Cert # (Optional)", scale=2)
                    btn_execute_renew = gr.Button("Mark as Renewed", variant="primary", scale=2, elem_classes=["btn-3d-primary"])

                renew_action_status = gr.Markdown()
                gr.Markdown("---")
                gr.Markdown("### Persistent Renewal History Audit Trail")
                history_table = gr.HTML(value=render_renewal_history_html())

                btn_execute_renew.click(
                    fn=on_execute_document_renewal,
                    inputs=[renew_doc_select, renew_duration, renew_new_policy, gr.State("")],
                    outputs=[renew_action_status, history_table, renew_doc_select]
                )

            # -------------------------------------------------------------
            # TAB 7: SECURITY & ADVANCED SETTINGS
            # -------------------------------------------------------------
            with gr.Tab("Security & Settings", id="tab_settings"):
                gr.Markdown("### Security, Database & Multi-Provider AI Settings")
                info = get_active_provider_info()
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown(f"""
                        #### Built-in Security Architecture:
                        - **100% Parameterized SQL Queries:** Immune to SQL Injection attacks.
                        - **Foreign Key Constraints & Cascades:** Enforced in SQLite with `PRAGMA foreign_keys = ON`.
                        - **Input Sanitization:** Dates parsed and validated using Python's `datetime.date`.
                        - **Protected Key Storage:** Secret API keys loaded via `python-dotenv` from local `.env`.
                        """)
                        gr.Markdown(f"**Current AI Engine Status:** `{info['description']}`")

                    with gr.Column(scale=1):
                        gr.Markdown("#### Add a New Vehicle to Fleet")
                        new_v_reg = gr.Textbox(label="Registration Number *", placeholder="e.g. MH-04-DE-5678")
                        new_v_model = gr.Textbox(label="Make & Model *", placeholder="e.g. Tata Harrier 2023")
                        new_v_type = gr.Dropdown(label="Category", choices=["Car", "Two-Wheeler", "Commercial", "SUV", "EV"], value="SUV")
                        new_v_owner = gr.Textbox(label="Owner Name *", placeholder="e.g. Priya Nair")
                        new_v_email = gr.Textbox(label="Email", placeholder="e.g. priya@example.com")
                        new_v_phone = gr.Textbox(label="Phone", placeholder="e.g. +91 98200 12345")
                        btn_register_v = gr.Button("Register Vehicle", variant="primary", elem_classes=["btn-3d-primary"])
                        register_status = gr.Markdown()

                btn_register_v.click(
                    fn=on_add_new_vehicle_to_db,
                    inputs=[new_v_reg, new_v_model, new_v_type, new_v_owner, new_v_email, new_v_phone],
                    outputs=[register_status, vehicle_selector]
                )



        # -----------------------------------------------------------------
        # Event Handlers for Registration Tracker & Chat
        # -----------------------------------------------------------------
        btn_analyze.click(
            fn=on_manual_analyze,
            inputs=[in_owner, in_reg, in_rc, in_ins, in_puc, in_dl, gr.State("")],
            outputs=[status_feedback, cards_view, output_ai_format, current_eval_state, chatbot, vehicle_selector]
        )

        btn_sample.click(
            fn=on_load_sample_data,
            inputs=[gr.State("")],
            outputs=[in_owner, in_reg, in_rc, in_ins, in_puc, in_dl, status_feedback, cards_view, output_ai_format, current_eval_state, chatbot, vehicle_selector]
        )

        btn_clear.click(
            fn=on_reset_clear_form,
            inputs=[],
            outputs=[in_owner, in_reg, in_rc, in_ins, in_puc, in_dl, status_feedback, cards_view, output_ai_format, current_eval_state, chatbot]
        )

        btn_load_selected.click(
            fn=evaluate_selected_vehicle,
            inputs=[vehicle_selector, gr.State("")],
            outputs=[status_feedback, cards_view, output_ai_format, current_eval_state, chatbot, in_owner, in_reg, in_rc, in_ins, in_puc, in_dl]
        )

        vehicle_selector.change(
            fn=evaluate_selected_vehicle,
            inputs=[vehicle_selector, gr.State("")],
            outputs=[status_feedback, cards_view, output_ai_format, current_eval_state, chatbot, in_owner, in_reg, in_rc, in_ins, in_puc, in_dl]
        )

        # Chat Events
        btn_chat_send.click(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        chat_input.submit(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )

        # Quick Intelligence Buttons
        q1.click(lambda: "Which document should I renew first?", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        q2.click(lambda: "Which documents are expiring soon?", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        q3.click(lambda: "What are the legal statutory penalties and fines?", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        q4.click(lambda: "Give me a step-by-step renewal checklist", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        q5.click(lambda: "Give me a renewal reminder.", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )
        q6.click(lambda: "What is the status of my vehicle documents?", None, chat_input).then(
            fn=handle_chat_wrapper,
            inputs=[chat_input, chatbot, current_eval_state, gr.State("")],
            outputs=[chat_input, chatbot]
        )

    return demo


if __name__ == "__main__":
    app = create_ui()
    port = int(os.environ.get("PORT", 7860))
    app.launch(
        server_name="0.0.0.0",
        server_port=port,
        show_error=True
    )