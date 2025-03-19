import unittest
import json
from app import app

class ReceiptTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def process_receipt(self, receipt):
        """Helper method to POST a receipt and return its ID."""
        response = self.app.post(
            "/receipts/process", 
            data=json.dumps(receipt),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertIn("id", data)
        return data["id"]

    def get_points(self, receipt_id):
        """Helper method to GET points for a given receipt ID."""
        response = self.app.get(f"/receipts/{receipt_id}/points")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data.decode())
        self.assertIn("points", data)
        return data["points"]

    def test_receipt_m_and_m(self):
        # Receipt for M&M Corner Market
        receipt = {
            "retailer": "M&M Corner Market",
            "purchaseDate": "2022-03-20",
            "purchaseTime": "14:33",
            "items": [
                {"shortDescription": "Gatorade", "price": "2.25"},
                {"shortDescription": "Gatorade", "price": "2.25"},
                {"shortDescription": "Gatorade", "price": "2.25"},
                {"shortDescription": "Gatorade", "price": "2.25"}
            ],
            "total": "9.00"
        }
        receipt_id = self.process_receipt(receipt)
        points = self.get_points(receipt_id)
        self.assertEqual(points, 109)

    def test_receipt_target(self):
        # Receipt for Target with multiple items
        receipt = {
            "retailer": "Target",
            "purchaseDate": "2022-01-01",
            "purchaseTime": "13:01",
            "items": [
                {"shortDescription": "Mountain Dew 12PK", "price": "6.49"},
                {"shortDescription": "Emils Cheese Pizza", "price": "12.25"},
                {"shortDescription": "Knorr Creamy Chicken", "price": "1.26"},
                {"shortDescription": "Doritos Nacho Cheese", "price": "3.35"},
                {"shortDescription": "   Klarbrunn 12-PK 12 FL OZ  ", "price": "12.00"}
            ],
            "total": "35.35"
        }
        receipt_id = self.process_receipt(receipt)
        points = self.get_points(receipt_id)
        self.assertEqual(points, 28)

    def test_receipt_walgreens(self):
        # Receipt for Walgreens
        receipt = {
            "retailer": "Walgreens",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "08:13",
            "total": "2.65",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"},
                {"shortDescription": "Dasani", "price": "1.40"}
            ]
        }
        receipt_id = self.process_receipt(receipt)
        points = self.get_points(receipt_id)
        # Expected points calculated as:
        #   Retailer "Walgreens" -> 9 alphanumeric characters
        #   2 items => 5 points (for one pair)
        #   "Dasani" has 6 characters (multiple of 3) ->  math.ceil(1.40*0.2)= math.ceil(0.28)=1 point
        #   Pepsi - 12-oz (13 characters) does not add bonus.
        #   No round total, no odd day, no time bonus.
        # Total = 9 + 5 + 1 = 15
        self.assertEqual(points, 15)

    def test_receipt_target_single_item(self):
        # Receipt for Target with a single item
        receipt = {
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        receipt_id = self.process_receipt(receipt)
        points = self.get_points(receipt_id)
        # Expected points:
        #   Retailer "Target" -> 6 points
        #   Total "1.25" is a multiple of 0.25 -> 25 points
        #   Single item, so no pair bonus.
        #   "Pepsi - 12-oz" (13 characters) is not a multiple of 3.
        # Total = 6 + 25 = 31
        self.assertEqual(points, 31)

if __name__ == '__main__':
    unittest.main()