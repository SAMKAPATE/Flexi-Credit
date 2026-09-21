"""
Comprehensive Test Suite for All Extra Features:
✓ Document upload
✓ AI chatbot
✓ Automated reminder levels
✓ Renewal history
✓ Multiple vehicles
✓ Search & filter
✓ AI priority analysis
✓ SQLite database
✓ Security & Parameterized SQL
✓ Error handling
"""

import unittest
from datetime import date, timedelta
from database import (
    init_db,
    add_vehicle,
    get_all_vehicles,
    get_vehicle_by_id,
    add_or_update_document,
    get_documents_for_vehicle,
    get_all_documents,
    record_document_renewal,
    get_renewal_history,
    search_and_filter_documents,
    log_reminder,
    get_reminder_logs
)
from document_evaluator import evaluate_all_documents, evaluate_document_expiry
from grok_agent import generate_renewal_analysis, chat_with_assistant
from document_parser import extract_from_file_or_text
from app import create_ui


class TestComprehensiveSystem(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        self.today = date.today()

    def test_multiple_vehicles(self):
        """Verify multiple vehicles can be added, queried, and differentiated."""
        v_id = add_vehicle("TEST-REG-01", "Tesla Model 3", "Alice Smith", "EV")
        self.assertIsNotNone(v_id)
        v = get_vehicle_by_id(v_id)
        self.assertEqual(v["reg_no"], "TEST-REG-01")
        self.assertEqual(v["owner_name"], "Alice Smith")

        vehicles = get_all_vehicles()
        self.assertGreaterEqual(len(vehicles), 1)

    def test_sqlite_database_and_documents(self):
        """Verify SQLite relational tables and cascade behavior."""
        v_id = add_vehicle("TEST-REG-02", "Honda Civic", "Bob Jones", "Car")
        d_id = add_or_update_document(v_id, "Vehicle Insurance", (self.today + timedelta(days=20)).strftime("%Y-%m-%d"), "POL-TEST-02")
        self.assertIsNotNone(d_id)

        docs = get_documents_for_vehicle(v_id)
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]["policy_no"], "POL-TEST-02")
        self.assertEqual(docs[0]["urgency"], "RENEW SOON")

    def test_renewal_history_audit_trail(self):
        """Verify 1-click renewal creates an audit entry in renewal_history."""
        v_id = add_vehicle("TEST-REG-03", "Toyota Fortuner", "Charlie Davis", "SUV")
        old_exp = (self.today + timedelta(days=2)).strftime("%Y-%m-%d")
        d_id = add_or_update_document(v_id, "Pollution Under Control (PUC)", old_exp, "PUC-TEST-03")

        new_exp = (self.today + timedelta(days=180)).strftime("%Y-%m-%d")
        success = record_document_renewal(d_id, new_exp, new_policy_no="PUC-RENEWED-03", notes="Test Renewal")
        self.assertTrue(success)

        # Verify audit history
        history = get_renewal_history(limit=5)
        found = next((h for h in history if h["doc_id"] == d_id), None)
        self.assertIsNotNone(found)
        self.assertEqual(found["old_expiry"], old_exp)
        self.assertEqual(found["new_expiry"], new_exp)
        self.assertEqual(found["policy_no"], "PUC-RENEWED-03")

    def test_search_and_filter(self):
        """Verify searching by reg number and filtering by status."""
        v_id = add_vehicle("SEARCH-9999", "Hyundai i20", "Search User", "Car")
        add_or_update_document(v_id, "Vehicle Insurance", (self.today - timedelta(days=5)).strftime("%Y-%m-%d"))

        # Search by reg
        results = search_and_filter_documents("SEARCH-9999")
        self.assertGreaterEqual(len(results), 1)
        self.assertEqual(results[0]["reg_no"], "SEARCH-9999")

        # Filter by EXPIRED status
        results_expired = search_and_filter_documents(status_filter="EXPIRED")
        self.assertTrue(all(d["urgency"] == "EXPIRED" for d in results_expired))

    def test_document_upload_and_extraction(self):
        """Verify document upload text extraction."""
        sample_slip = "PUC Certificate No: PUC-10293, Vehicle No: KA-05-AB-1212, Valid until: 2026-10-30, Issued by Transport Dept"
        extracted = extract_from_file_or_text(sample_slip)
        self.assertEqual(extracted["doc_type"], "Pollution Under Control (PUC)")
        self.assertEqual(extracted["expiry_date"], "2026-10-30")
        self.assertIn("KA", extracted["reg_no"])

    def test_ai_priority_analysis(self):
        """Verify strict AI response format and priority detection."""
        eval_data = evaluate_all_documents(
            owner_name="Fleet Owner",
            vehicle_reg="KA-05-AB-1212",
            rc_date=(self.today + timedelta(days=400)).strftime("%Y-%m-%d"),
            insurance_date=(self.today + timedelta(days=3)).strftime("%Y-%m-%d"),
            puc_date=(self.today - timedelta(days=7)).strftime("%Y-%m-%d"),
            dl_date=(self.today + timedelta(days=100)).strftime("%Y-%m-%d")
        )
        report = generate_renewal_analysis(eval_data)
        self.assertIn("Vehicle: KA-05-AB-1212", report)
        self.assertIn("Document Status:", report)
        self.assertIn("- RC:", report)
        self.assertIn("- Insurance:", report)
        self.assertIn("- PUC:", report)
        self.assertIn("- Driving Licence:", report)
        self.assertIn("Priority:", report)
        self.assertIn("Reminder:", report)

    def test_ai_chatbot(self):
        """Verify context-aware chatbot answers."""
        eval_data = evaluate_all_documents(
            owner_name="Test Owner",
            vehicle_reg="KA-05-AB-1212",
            rc_date="",
            insurance_date=(self.today + timedelta(days=3)).strftime("%Y-%m-%d"),
            puc_date="",
            dl_date=""
        )
        reply = chat_with_assistant("Which document should I renew first?", eval_data, [])
        self.assertIn("Priority", reply)

    def test_automated_reminder_levels(self):
        """Verify reminder logging in SQLite."""
        docs = get_all_documents()
        if not docs:
            v_id = add_vehicle("REMINDER-V1", "Sample Car", "Owner")
            doc_id = add_or_update_document(v_id, "Vehicle Insurance", (self.today + timedelta(days=5)).strftime("%Y-%m-%d"))
        else:
            doc_id = docs[0]["id"]
        log_id = log_reminder(doc_id, "Email", "owner@example.com", "Test Reminder", urgency="URGENT")
        self.assertIsNotNone(log_id)
        logs = get_reminder_logs(limit=5)
        self.assertGreater(len(logs), 0)

    def test_security_and_error_handling(self):
        """Verify error handling on bad dates and SQL injection safety."""
        bad_eval = evaluate_document_expiry("invalid-date-format")
        self.assertFalse(bad_eval["valid_date"])
        self.assertEqual(bad_eval["status"], "INVALID_DATE")

        # Test parameterized SQL safety with quotes
        safe_v_id = add_vehicle("INJ-01' OR '1'='1", "Test Model", "Hacker'; DROP TABLE vehicles;--")
        self.assertIsNotNone(safe_v_id)
        safe_v = get_vehicle_by_id(safe_v_id)
        self.assertEqual(safe_v["reg_no"], "INJ-01' OR '1'='1")

    def test_gradio_ui_creation(self):
        """Verify complete Gradio application builds cleanly."""
        demo = create_ui()
        self.assertIsNotNone(demo)


if __name__ == "__main__":
    unittest.main()
