import unittest
import httpx

class TestLiveUIStructure(unittest.TestCase):
    def test_live_ui_endpoints_and_labels(self):
        res = httpx.get("http://127.0.0.1:7860/config")
        self.assertEqual(res.status_code, 200)
        cfg = res.json()
        labels = [c.get("props", {}).get("label") for c in cfg.get("components", []) if c.get("props", {}).get("label")]
        
        # Verify the primary user registration input fields are directly present
        self.assertTrue(any("Owner Name" in str(l) for l in labels), "Owner Name input not found")
        self.assertTrue(any("Registration Number" in str(l) for l in labels), "Reg Number input not found")
        self.assertTrue(any("Registration Certificate (RC)" in str(l) for l in labels), "RC input not found")
        self.assertTrue(any("Vehicle Insurance" in str(l) for l in labels), "Insurance input not found")
        self.assertTrue(any("Pollution Under Control" in str(l) for l in labels), "PUC input not found")
        self.assertTrue(any("Driving Licence" in str(l) for l in labels), "DL input not found")
        self.assertTrue(any("Official AI Response Schema" in str(l) for l in labels), "AI response schema box not found")

if __name__ == "__main__":
    unittest.main()
