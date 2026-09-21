"""
Database Layer for Vehicle Document Renewal Reminder System.
Features:
- Relational SQLite schema with Foreign Keys and Cascades.
- 100% Parameterized queries for SQL-Injection Security.
- Multiple Vehicles Management.
- Document Tracking (RC, Insurance, PUC, DL).
- Renewal History & Audit Logging.
- Multi-Level Reminder History.
- Search & Filter by Reg No, Owner, Doc Type, and Urgency.
- Input validation & Error Handling.
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vehicle_documents.db")


@contextmanager
def db_session():
    """Provides a transactional database connection that automatically commits and closes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


get_connection = db_session


def init_db():
    """Initializes tables for vehicles, documents, renewal history, reminders, and settings."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 1. Vehicles Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reg_no TEXT UNIQUE NOT NULL,
                make_model TEXT NOT NULL,
                vehicle_type TEXT DEFAULT 'Car',
                owner_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Documents Table (RC, Insurance, PUC, Driving Licence)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                doc_type TEXT NOT NULL,
                policy_no TEXT,
                issuer TEXT,
                issue_date TEXT,
                expiry_date TEXT NOT NULL,
                notes TEXT,
                status TEXT DEFAULT 'Active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
            )
        """)

        # 3. Renewal History Audit Trail
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS renewal_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                vehicle_id INTEGER NOT NULL,
                doc_type TEXT NOT NULL,
                old_expiry TEXT,
                new_expiry TEXT NOT NULL,
                policy_no TEXT,
                renewed_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
            )
        """)

        # 4. Multi-Level Automated Reminders Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER NOT NULL,
                channel TEXT NOT NULL,
                recipient TEXT,
                message TEXT,
                urgency TEXT DEFAULT 'NORMAL',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'SENT',
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
            )
        """)

        # 5. Application Settings & Secrets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)


# --- Vehicle CRUD & Multi-Vehicle Operations ---

def add_vehicle(reg_no: str, make_model: str, owner_name: str, vehicle_type: str = "Car",
                email: str = "", phone: str = "") -> int:
    """Inserts a new vehicle with sanitized inputs and uppercase registration."""
    reg_no = reg_no.strip().upper()
    if not reg_no or not make_model or not owner_name:
        raise ValueError("Registration Number, Make/Model, and Owner Name are required.")
    
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO vehicles (reg_no, make_model, vehicle_type, owner_name, email, phone)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(reg_no) DO UPDATE SET
                make_model = excluded.make_model,
                vehicle_type = excluded.vehicle_type,
                owner_name = excluded.owner_name,
                email = excluded.email,
                phone = excluded.phone
        """, (reg_no, make_model.strip(), vehicle_type.strip(), owner_name.strip(), email.strip(), phone.strip()))
        if cursor.lastrowid:
            return cursor.lastrowid
        cursor.execute("SELECT id FROM vehicles WHERE reg_no = ?", (reg_no,))
        row = cursor.fetchone()
        return row["id"]


def get_all_vehicles() -> List[Dict[str, Any]]:
    """Returns all registered vehicles."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles ORDER BY id ASC")
        return [dict(row) for row in cursor.fetchall()]


def get_vehicle_by_id(vehicle_id: int) -> Optional[Dict[str, Any]]:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_vehicle_by_reg(reg_no: str) -> Optional[Dict[str, Any]]:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM vehicles WHERE UPPER(reg_no) = ?", (reg_no.strip().upper(),))
        row = cursor.fetchone()
        return dict(row) if row else None


def delete_vehicle(vehicle_id: int) -> bool:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
        return cursor.rowcount > 0


# --- Document CRUD with Deterministic Expiry Categorization ---

def add_or_update_document(vehicle_id: int, doc_type: str, expiry_date: str,
                           policy_no: str = "", issuer: str = "", issue_date: str = "", notes: str = "") -> int:
    """Adds a document or updates an existing document of the same type for a vehicle."""
    expiry_date = expiry_date.strip()
    if not expiry_date:
        raise ValueError("Expiry Date is mandatory.")

    with db_session() as conn:
        cursor = conn.cursor()
        # Check if already exists for this vehicle
        cursor.execute("SELECT id FROM documents WHERE vehicle_id = ? AND doc_type = ?", (vehicle_id, doc_type.strip()))
        existing = cursor.fetchone()
        if existing:
            doc_id = existing["id"]
            cursor.execute("""
                UPDATE documents
                SET expiry_date = ?, policy_no = ?, issuer = ?, issue_date = ?, notes = ?
                WHERE id = ?
            """, (expiry_date, policy_no.strip(), issuer.strip(), issue_date.strip(), notes.strip(), doc_id))
            return doc_id
        else:
            cursor.execute("""
                INSERT INTO documents (vehicle_id, doc_type, policy_no, issuer, issue_date, expiry_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vehicle_id, doc_type.strip(), policy_no.strip(), issuer.strip(), issue_date.strip(), expiry_date, notes.strip()))
            return cursor.lastrowid


def get_documents_for_vehicle(vehicle_id: int) -> List[Dict[str, Any]]:
    """Fetches all documents for a given vehicle with Python-calculated days remaining and status."""
    today = date.today()
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, v.reg_no, v.make_model, v.owner_name, v.email, v.phone
            FROM documents d
            JOIN vehicles v ON d.vehicle_id = v.id
            WHERE d.vehicle_id = ?
            ORDER BY d.expiry_date ASC
        """, (vehicle_id,))
        rows = cursor.fetchall()
        
        result = []
        for r in rows:
            d = dict(r)
            _enrich_document_metrics(d, today)
            result.append(d)
        return result


def get_all_documents() -> List[Dict[str, Any]]:
    """Returns all documents across all vehicles with calculated metrics."""
    today = date.today()
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.*, v.reg_no, v.make_model, v.owner_name, v.email, v.phone
            FROM documents d
            JOIN vehicles v ON d.vehicle_id = v.id
            ORDER BY d.expiry_date ASC
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            _enrich_document_metrics(d, today)
            result.append(d)
        return result


def _enrich_document_metrics(d: Dict[str, Any], today: date):
    """Calculates days left and status in pure Python."""
    try:
        exp = datetime.strptime(d["expiry_date"], "%Y-%m-%d").date()
        days = (exp - today).days
        d["days_left"] = days
        if days < 0:
            d["urgency"] = "EXPIRED"
            d["display_days"] = f"Expired {abs(days)} day(s) ago"
        elif days <= 7:
            d["urgency"] = "URGENT"
            d["display_days"] = f"{days} day(s) remaining" if days > 0 else "Expires today!"
        elif days <= 30:
            d["urgency"] = "RENEW SOON"
            d["display_days"] = f"{days} day(s) remaining"
        else:
            d["urgency"] = "VALID"
            d["display_days"] = f"{days} day(s) remaining"
    except Exception:
        d["days_left"] = None
        d["urgency"] = "UNKNOWN"
        d["display_days"] = "Invalid date"


# --- Search & Filter ---

def search_and_filter_documents(query: str = "", status_filter: str = "ALL") -> List[Dict[str, Any]]:
    """Searches by vehicle reg, owner name, or doc type, and filters by status."""
    docs = get_all_documents()
    q = query.strip().lower()

    filtered = []
    for d in docs:
        # Text match
        text_match = (
            not q or
            q in d.get("reg_no", "").lower() or
            q in d.get("owner_name", "").lower() or
            q in d.get("doc_type", "").lower() or
            q in d.get("make_model", "").lower() or
            q in d.get("policy_no", "").lower()
        )
        if not text_match:
            continue

        # Status match
        st = d.get("urgency", "UNKNOWN")
        if status_filter == "ALL":
            status_match = True
        elif status_filter == "EXPIRED" and st == "EXPIRED":
            status_match = True
        elif status_filter == "URGENT" and st == "URGENT":
            status_match = True
        elif status_filter == "RENEW_SOON" and st == "RENEW SOON":
            status_match = True
        elif status_filter == "VALID" and st == "VALID":
            status_match = True
        elif status_filter == "ACTION_REQUIRED" and st in ("EXPIRED", "URGENT", "RENEW SOON"):
            status_match = True
        else:
            status_match = False

        if status_match:
            filtered.append(d)

    return filtered


# --- Renewal History Audit Logging ---

def record_document_renewal(doc_id: int, new_expiry_date: str, new_policy_no: str = "", notes: str = "") -> bool:
    """
    Updates the document with a new expiry date and logs the previous record into renewal_history.
    """
    new_expiry_date = new_expiry_date.strip()
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Fetch current state
        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        doc = cursor.fetchone()
        if not doc:
            raise ValueError(f"Document #{doc_id} not found.")

        old_expiry = doc["expiry_date"]
        vehicle_id = doc["vehicle_id"]
        doc_type = doc["doc_type"]
        policy = new_policy_no.strip() if new_policy_no.strip() else doc["policy_no"]

        # Insert audit trail
        cursor.execute("""
            INSERT INTO renewal_history (doc_id, vehicle_id, doc_type, old_expiry, new_expiry, policy_no, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (doc_id, vehicle_id, doc_type, old_expiry, new_expiry_date, policy, notes.strip()))

        # Update document
        today_str = date.today().strftime("%Y-%m-%d")
        cursor.execute("""
            UPDATE documents
            SET expiry_date = ?, policy_no = ?, issue_date = ?, notes = ?, status = 'Active'
            WHERE id = ?
        """, (new_expiry_date, policy, today_str, notes.strip(), doc_id))

        return True


def get_renewal_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Fetches past renewal records with vehicle registration details."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT rh.*, v.reg_no, v.make_model, v.owner_name
            FROM renewal_history rh
            JOIN vehicles v ON rh.vehicle_id = v.id
            ORDER BY rh.id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# --- Multi-Level Automated Reminders Logging ---

def log_reminder(doc_id: int, channel: str, recipient: str, message: str,
                 urgency: str = "NORMAL", status: str = "SENT") -> int:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO reminders (doc_id, channel, recipient, message, urgency, status)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (doc_id, channel, recipient, message, urgency, status))
        return cursor.lastrowid


def get_reminder_logs(limit: int = 50) -> List[Dict[str, Any]]:
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, d.doc_type, d.expiry_date, v.reg_no, v.owner_name
            FROM reminders r
            JOIN documents d ON r.doc_id = d.id
            JOIN vehicles v ON d.vehicle_id = v.id
            ORDER BY r.id DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# --- Pre-Seeding Multiple Vehicles ---

def seed_multi_vehicle_data(force_reset: bool = False):
    """Populates realistic multi-vehicle fleet records for demonstration."""
    init_db()
    existing = get_all_vehicles()
    if existing and not force_reset:
        return

    if force_reset:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders")
            cursor.execute("DELETE FROM renewal_history")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM vehicles")

    today = date.today()

    # Vehicle 1: Rahul Sharma's SUV (Mixed statuses: Expired PUC & Urgent Insurance)
    v1_id = add_vehicle(
        reg_no="MH-12-AB-1234",
        make_model="Hyundai Creta SX 2022",
        vehicle_type="SUV",
        owner_name="Rahul Sharma",
        email="rahul.sharma@example.com",
        phone="+91-98234-11223"
    )
    add_or_update_document(v1_id, "Registration Certificate (RC)", (today + timedelta(days=720)).strftime("%Y-%m-%d"), "RC-MH12-9901", "Pune RTO")
    add_or_update_document(v1_id, "Vehicle Insurance", (today + timedelta(days=4)).strftime("%Y-%m-%d"), "POL-HDFC-8812", "HDFC ERGO")
    add_or_update_document(v1_id, "Pollution Under Control (PUC)", (today - timedelta(days=14)).strftime("%Y-%m-%d"), "PUC-PUN-5541", "Authorized Testing Center")
    add_or_update_document(v1_id, "Driving Licence (DL)", (today + timedelta(days=22)).strftime("%Y-%m-%d"), "DL-MH12-2015-88", "RTO Pune")

    # Vehicle 2: Priya Patel's Motorcycle (Two-Wheeler with Renew Soon PUC)
    v2_id = add_vehicle(
        reg_no="DL-01-CA-9999",
        make_model="Royal Enfield Classic 350",
        vehicle_type="Two-Wheeler",
        owner_name="Priya Patel",
        email="priya.patel@example.com",
        phone="+91-99100-44556"
    )
    add_or_update_document(v2_id, "Registration Certificate (RC)", (today + timedelta(days=1800)).strftime("%Y-%m-%d"), "RC-DL01-3312", "Delhi Mall Road RTO")
    add_or_update_document(v2_id, "Vehicle Insurance", (today + timedelta(days=140)).strftime("%Y-%m-%d"), "ICICI-2W-9902", "ICICI Lombard")
    add_or_update_document(v2_id, "Pollution Under Control (PUC)", (today + timedelta(days=18)).strftime("%Y-%m-%d"), "PUC-DL-4481", "North Delhi Fuel Center")
    add_or_update_document(v2_id, "Driving Licence (DL)", (today + timedelta(days=950)).strftime("%Y-%m-%d"), "DL-01-2019-0012", "Delhi RTO")

    # Vehicle 3: Vikram Malhotra's Commercial Truck (Urgent Fitness / RC & Expired Insurance)
    v3_id = add_vehicle(
        reg_no="KA-03-MG-4521",
        make_model="Tata 407 Commercial Carrier",
        vehicle_type="Commercial",
        owner_name="Vikram Malhotra",
        email="vikram.logistics@example.com",
        phone="+91-98450-67890"
    )
    add_or_update_document(v3_id, "Registration Certificate (RC)", (today + timedelta(days=6)).strftime("%Y-%m-%d"), "RC-KA03-FIT-77", "Bengaluru RTO")
    add_or_update_document(v3_id, "Vehicle Insurance", (today - timedelta(days=5)).strftime("%Y-%m-%d"), "TATA-COMM-1120", "Tata AIG")
    add_or_update_document(v3_id, "Pollution Under Control (PUC)", (today + timedelta(days=45)).strftime("%Y-%m-%d"), "PUC-KA-8812", "Indiranagar Testing Center")
    add_or_update_document(v3_id, "Driving Licence (DL)", (today + timedelta(days=400)).strftime("%Y-%m-%d"), "DL-KA03-1998-33", "Karnataka Transport Dept")


# Initialize on import
init_db()
seed_multi_vehicle_data(force_reset=False)
