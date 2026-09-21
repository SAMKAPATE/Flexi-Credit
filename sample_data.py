"""
Sample Data Seeder.
Provides realistic pre-configured vehicle and document records with diverse expiry timelines
to immediately demonstrate the automated reminder and Grok AI agent capabilities.
"""

from datetime import date, timedelta
from database import (
    init_db,
    add_vehicle,
    add_document,
    get_all_vehicles,
    get_connection
)


def seed_sample_data(force_reset: bool = False):
    """Populates initial demo vehicles and documents."""
    init_db()
    existing_vehicles = get_all_vehicles()
    
    if existing_vehicles and not force_reset:
        return

    if force_reset:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM reminders")
            cursor.execute("DELETE FROM documents")
            cursor.execute("DELETE FROM vehicles")
            conn.commit()

    today = date.today()

    # 1. Rahul Sharma's Hyundai Creta (Has Expired PUC & Urgent Insurance)
    v1_id = add_vehicle(
        reg_no="MH12AB1234",
        make_model="Hyundai Creta SX 2022",
        vehicle_type="SUV",
        owner_name="Rahul Sharma",
        email="rahul.sharma@example.com",
        phone="+91 98234 11223"
    )
    # PUC Expired 12 days ago
    puc_exp = (today - timedelta(days=12)).strftime("%Y-%m-%d")
    puc_issue = (today - timedelta(days=192)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v1_id,
        doc_type="PUC",
        policy_no="PUC-MH12-99812",
        issuer="RTO Authorized Emission Center Pune",
        issue_date=puc_issue,
        expiry_date=puc_exp,
        notes="Petrol BS-VI Emission standard. Urgent testing required to avoid ₹10,000 fine."
    )
    # Insurance Expiring in 4 days
    ins_exp = (today + timedelta(days=4)).strftime("%Y-%m-%d")
    ins_issue = (today - timedelta(days=361)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v1_id,
        doc_type="Insurance",
        policy_no="POL-HDFC-8871234",
        issuer="HDFC ERGO General Insurance",
        issue_date=ins_issue,
        expiry_date=ins_exp,
        notes="Comprehensive Bumper-to-Bumper policy. 35% No Claim Bonus at stake."
    )
    # RC Valid till 2037
    rc_exp = (today + timedelta(days=4000)).strftime("%Y-%m-%d")
    rc_issue = (today - timedelta(days=730)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v1_id,
        doc_type="Registration (RC)",
        policy_no="RC-MH12-2022-0091",
        issuer="Pune RTO (MH-12)",
        issue_date=rc_issue,
        expiry_date=rc_exp,
        notes="Private vehicle 15-year registration validity."
    )

    # 2. Priya Patel's Royal Enfield (PUC Expiring Soon)
    v2_id = add_vehicle(
        reg_no="DL01CA9999",
        make_model="Royal Enfield Classic 350",
        vehicle_type="Two-Wheeler",
        owner_name="Priya Patel",
        email="priya.patel@example.com",
        phone="+91 99100 44556"
    )
    # PUC Expiring in 18 days
    puc2_exp = (today + timedelta(days=18)).strftime("%Y-%m-%d")
    puc2_issue = (today - timedelta(days=162)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v2_id,
        doc_type="PUC",
        policy_no="PUC-DL01-3341",
        issuer="Mall Road Petrol Pump Testing Center",
        issue_date=puc2_issue,
        expiry_date=puc2_exp,
        notes="Half-yearly pollution testing."
    )
    # Insurance Valid for 140 days
    ins2_exp = (today + timedelta(days=140)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v2_id,
        doc_type="Insurance",
        policy_no="ICICI-TWO-554219",
        issuer="ICICI Lombard",
        issue_date=(today - timedelta(days=225)).strftime("%Y-%m-%d"),
        expiry_date=ins2_exp,
        notes="Two-wheeler standalone own damage + 5-yr mandatory third party."
    )

    # 3. Rajesh Verma's Commercial Bolero Pickup (Urgent Fitness & Expired Permit)
    v3_id = add_vehicle(
        reg_no="HR26DQ7788",
        make_model="Mahindra Bolero Maxi Truck",
        vehicle_type="Commercial",
        owner_name="Rajesh Verma",
        email="rajesh.logistics@example.com",
        phone="+91 98111 88990"
    )
    # Fitness expiring in 2 days
    fit_exp = (today + timedelta(days=2)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v3_id,
        doc_type="Fitness Certificate",
        policy_no="FIT-HR26-2023-77",
        issuer="Gurugram Commercial RTO",
        issue_date=(today - timedelta(days=363)).strftime("%Y-%m-%d"),
        expiry_date=fit_exp,
        notes="Annual roadworthiness inspection required immediately for commercial transport."
    )
    # State Permit expired 6 days ago
    permit_exp = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v3_id,
        doc_type="Road Tax",
        policy_no="TAX-HR-Q4-889",
        issuer="Haryana Transport Authority",
        issue_date=(today - timedelta(days=96)).strftime("%Y-%m-%d"),
        expiry_date=permit_exp,
        notes="Quarterly commercial goods tax token. Penalty accruing daily."
    )

    # 4. Vikram Malhotra's Tata Nexon EV (All documents in good health)
    v4_id = add_vehicle(
        reg_no="KA03MG4521",
        make_model="Tata Nexon EV Max 2023",
        vehicle_type="EV",
        owner_name="Vikram Malhotra",
        email="vikram.m@example.com",
        phone="+91 98450 67890"
    )
    ins4_exp = (today + timedelta(days=280)).strftime("%Y-%m-%d")
    add_document(
        vehicle_id=v4_id,
        doc_type="Insurance",
        policy_no="TATA-AIG-EV-990123",
        issuer="Tata AIG General Insurance",
        issue_date=(today - timedelta(days=85)).strftime("%Y-%m-%d"),
        expiry_date=ins4_exp,
        notes="Zero depreciation EV battery pack & motor cover."
    )


if __name__ == "__main__":
    seed_sample_data(force_reset=True)
    print("Database successfully seeded with realistic sample vehicles and documents.")
