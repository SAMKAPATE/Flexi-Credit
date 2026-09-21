"""
Unit test suite for the Automated Vehicle Document Renewal Reminder system.
Validates all requirements: date math, categorization, AI format, and chatbot queries.
"""

import unittest
from datetime import date, timedelta
from document_evaluator import evaluate_document_expiry, evaluate_all_documents
from grok_agent import generate_renewal_analysis, chat_with_assistant, format_fallback_response
from app import create_ui


class TestVehicleRenewalSystem(unittest.TestCase):

    def setUp(self):
        self.today = date.today()

    def test_date_categorization_rules(self):
        """Test the 4 required categories: EXPIRED, URGENT, RENEW SOON, VALID."""
        # 1. EXPIRED (< 0 days)
        past_date = (self.today - timedelta(days=5)).strftime("%Y-%m-%d")
        res_expired = evaluate_document_expiry(past_date, self.today)
        self.assertEqual(res_expired["status"], "EXPIRED")
        self.assertEqual(res_expired["days_remaining"], -5)

        # 2. URGENT (0 to 7 days)
        today_str = self.today.strftime("%Y-%m-%d")
        res_today = evaluate_document_expiry(today_str, self.today)
        self.assertEqual(res_today["status"], "URGENT")
        self.assertEqual(res_today["days_remaining"], 0)

        urgent_date = (self.today + timedelta(days=7)).strftime("%Y-%m-%d")
        res_urgent = evaluate_document_expiry(urgent_date, self.today)
        self.assertEqual(res_urgent["status"], "URGENT")
        self.assertEqual(res_urgent["days_remaining"], 7)

        # 3. RENEW SOON (8 to 30 days)
        soon_date = (self.today + timedelta(days=15)).strftime("%Y-%m-%d")
        res_soon = evaluate_document_expiry(soon_date, self.today)
        self.assertEqual(res_soon["status"], "RENEW SOON")
        self.assertEqual(res_soon["days_remaining"], 15)

        # 4. VALID (> 30 days)
        valid_date = (self.today + timedelta(days=45)).strftime("%Y-%m-%d")
        res_valid = evaluate_document_expiry(valid_date, self.today)
        self.assertEqual(res_valid["status"], "VALID")
        self.assertEqual(res_valid["days_remaining"], 45)

    def test_priority_identification(self):
        """Verify priority is assigned to the earliest expiring document."""
        eval_data = evaluate_all_documents(
            owner_name="Test Owner",
            vehicle_reg="DL-01-XX-0001",
            rc_date=(self.today + timedelta(days=365)).strftime("%Y-%m-%d"),
            insurance_date=(self.today + timedelta(days=3)).strftime("%Y-%m-%d"),    # URGENT
            puc_date=(self.today - timedelta(days=2)).strftime("%Y-%m-%d"),          # EXPIRED (Earliest!)
            dl_date=(self.today + timedelta(days=60)).strftime("%Y-%m-%d"),
            reference_date=self.today
        )

        self.assertEqual(eval_data["priority_document"], "PUC")
        self.assertIn("PUC is already EXPIRED", eval_data["priority_text"])
        self.assertIn("PUC", eval_data["needs_immediate_renewal"])
        self.assertIn("Insurance", eval_data["needs_immediate_renewal"])

    def test_strict_ai_response_format(self):
        """Verify the AI response contains all required sections and headers."""
        eval_data = evaluate_all_documents(
            owner_name="Rahul Sharma",
            vehicle_reg="MH-12-AB-1234",
            rc_date=(self.today + timedelta(days=500)).strftime("%Y-%m-%d"),
            insurance_date=(self.today + timedelta(days=4)).strftime("%Y-%m-%d"),
            puc_date=(self.today - timedelta(days=10)).strftime("%Y-%m-%d"),
            dl_date=(self.today + timedelta(days=20)).strftime("%Y-%m-%d"),
            reference_date=self.today
        )

        response = format_fallback_response(eval_data)

        # Assert mandatory structure
        self.assertIn("Vehicle: MH-12-AB-1234", response)
        self.assertIn("Document Status:", response)
        self.assertIn("- RC:", response)
        self.assertIn("- Insurance:", response)
        self.assertIn("- PUC:", response)
        self.assertIn("- Driving Licence:", response)
        self.assertIn("Priority:", response)
        self.assertIn("Reminder:", response)

    def test_chatbot_queries(self):
        """Test the specified chatbot inquiry questions."""
        eval_data = evaluate_all_documents(
            owner_name="Rahul",
            vehicle_reg="MH-12-AB-1234",
            rc_date=(self.today + timedelta(days=500)).strftime("%Y-%m-%d"),
            insurance_date=(self.today + timedelta(days=4)).strftime("%Y-%m-%d"),
            puc_date=(self.today - timedelta(days=10)).strftime("%Y-%m-%d"),
            dl_date=(self.today + timedelta(days=20)).strftime("%Y-%m-%d"),
            reference_date=self.today
        )

        # Query 1: Which document should I renew first?
        q1_res = chat_with_assistant("Which document should I renew first?", eval_data, [])
        self.assertIn("Priority", q1_res)
        self.assertIn("PUC", q1_res)

        # Query 2: Which documents are expiring soon?
        q2_res = chat_with_assistant("Which documents are expiring soon?", eval_data, [])
        self.assertTrue("PUC" in q2_res or "Insurance" in q2_res)

        # Query 3: Give me a renewal reminder
        q3_res = chat_with_assistant("Give me a renewal reminder.", eval_data, [])
        self.assertIn("Reminder", q3_res)
        self.assertIn("MH-12-AB-1234", q3_res)

        # Query 4: What is the status of my vehicle documents?
        q4_res = chat_with_assistant("What is the status of my vehicle documents?", eval_data, [])
        self.assertIn("RC", q4_res)
        self.assertIn("Insurance", q4_res)
        self.assertIn("PUC", q4_res)
        self.assertIn("Driving Licence", q4_res)

    def test_gradio_ui_instantiation(self):
        """Verify the Gradio UI creates cleanly without syntax/runtime issues."""
        demo = create_ui()
        self.assertIsNotNone(demo)


if __name__ == "__main__":
    unittest.main()
