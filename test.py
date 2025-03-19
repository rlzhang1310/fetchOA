import unittest
import json
from app import app
import uuid

class ReceiptTestCase(unittest.TestCase):    
    def setUp(self):
        """Set up the test client."""
        self.app = app.test_client()
        self.app.testing = True

    def process_receipt(self, receipt):
        """Helper method to POST a receipt and return its ID."""
        response = self.app.post(
            "/receipts/process", 
            data=json.dumps(receipt),
            content_type="application/json"
        )
        data = json.loads(response.data.decode())
        try:
            return data["id"], response.status_code
        except Exception: ## If data is not valid, we return entire data instead
            return data, response.status_code

    def get_points(self, receipt_id):
        """Helper method to GET points for a given receipt ID."""
        response = self.app.get(f"/receipts/{receipt_id}/points")
        data = json.loads(response.data.decode())
        try:
            return data["points"], response.status_code
        except KeyError: ## If data is not valid, we return entire data instead
            return data, response.status_code

    def test_receipt_m_and_m(self):
        """Test example m and m reciept given"""
        m_and_m_receipt = {
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
        receipt_id, post_status_code = self.process_receipt(m_and_m_receipt)
        points, get_status_code = self.get_points(receipt_id)
        self.assertEqual(points, 109)
        self.assertEqual(post_status_code, 200)
        self.assertEqual(get_status_code, 200)

    def test_receipt_target(self):
        """Test example target reciept given"""
        target_receipt = {
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
        receipt_id, post_status_code = self.process_receipt(target_receipt)
        points, get_status_code = self.get_points(receipt_id)
        self.assertEqual(points, 28)
        self.assertEqual(post_status_code, 200)
        self.assertEqual(get_status_code, 200)

    def test_receipt_walgreens(self):
        """Test example walgreens reciept given"""
        walgreens_receipt = {
            "retailer": "Walgreens",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "08:13",
            "total": "2.65",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"},
                {"shortDescription": "Dasani", "price": "1.40"}
            ]
        }
        receipt_id, post_status_code = self.process_receipt(walgreens_receipt)
        points, get_status_code = self.get_points(receipt_id)
        # Expected points:
        #   "Walgreens" -> 9 alphanumeric characters
        #   2 items -> 5 points
        #   "Dasani" has 6 characters (multiple of 3) ->  math.ceil(1.40*0.2)= math.ceil(0.28)=1 point
        #   Pepsi - 12-oz (13 characters) does not add bonus.
        #   No round total, no odd day, no time bonus.
        # Total = 9 + 5 + 1 = 15
        self.assertEqual(points, 15)
        self.assertEqual(post_status_code, 200)
        self.assertEqual(get_status_code, 200)

    def test_receipt_target_single_item(self):
        """Test example single item target reciept given"""
        single_target_receipt = {
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        receipt_id, post_status_code = self.process_receipt(single_target_receipt)
        points, get_status_code = self.get_points(receipt_id)
        # Expected points:
        #   "Target" -> 6 points
        #   Total "1.25" is a multiple of 0.25 -> 25 points
        #   Single item, so no pair bonus.
        #   "Pepsi - 12-oz" (13 characters) is not a multiple of 3.
        # Total = 6 + 25 = 31
        self.assertEqual(points, 31)
        self.assertEqual(post_status_code, 200)
        self.assertEqual(get_status_code, 200)

    def test_receipt_missing_retailer(self):
        """Test receipt with missing retailer field"""
        missing_retailer_receipt = {
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        response, status_code = self.process_receipt(missing_retailer_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_missing_purchase_date(self):
        """Test receipt with missing purchase date field"""
        missing_purchase_date_receipt = {
            "retailer": "Target",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        response, status_code = self.process_receipt(missing_purchase_date_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_missing_purchase_time(self):
        """Test receipt with missing purchase time field"""
        missing_purchase_time_receipt = {
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        response, status_code = self.process_receipt(missing_purchase_time_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_missing_total(self):
        """Test receipt with missing total field"""
        missing_total_receipt = {
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        response, status_code = self.process_receipt(missing_total_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_missing_items(self):
        """Test receipt with missing items field"""
        missing_items_receipt ={
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
        }
        response, status_code = self.process_receipt(missing_items_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_no_items(self):
        """Test receipt with empty items list"""
        missing_items_receipt ={
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
            ]
        }
        response, status_code = self.process_receipt(missing_items_receipt)
        self.assertEqual(status_code, 400)

    def test_receipt_missing_item_fields(self):
        """Test receipt with missing item fields"""
        missing_description_receipt ={
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz"}
            ]
        }

        missing_price_receipt ={
            "retailer": "Target",
            "purchaseDate": "2022-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"price": "1.25"}
            ]
        }
        response, status_code_one = self.process_receipt(missing_price_receipt)
        self.assertEqual(status_code_one, 400)
        response, status_code_two = self.process_receipt(missing_description_receipt)
        self.assertEqual(status_code_two, 400)

    def test_receipt_invalid_json(self):
        """Test receipt with invalid JSON"""
        invalid_json_receipt = '{"retailer": "Target","purchaseDate": "2022-01-02","purchaseTime": "13:13","total": "1.25","items": [{"shortDescription": "Pepsi - 12-oz", "price": "1.25"}]'
        response = self.app.post(
            "/receipts/process",
            data=invalid_json_receipt,
            content_type="application/json"
        )
        
        self.assertEqual(response.status_code, 400)

    def test_invalid_regex_matches(self):
        """Test invalid regex matches"""
        default_receipt = {
            "retailer": "Intel",
            "purchaseDate": "2023-01-02",
            "purchaseTime": "13:13",
            "total": "1.25",
            "items": [
                {"shortDescription": "Pepsi - 12-oz", "price": "1.25"}
            ]
        }
        response, status_code = self.process_receipt(default_receipt)
        self.assertEqual(status_code, 200)

        invalid_retailer = default_receipt.copy()
        invalid_retailer["retailer"] = "O'Reilly"
        response, status_code = self.process_receipt(invalid_retailer)
        self.assertEqual(status_code, 400)

        invalid_purchase_date = default_receipt.copy()
        invalid_purchase_date["purchaseDate"] = "2023-01-32"
        response, status_code = self.process_receipt(invalid_purchase_date)
        self.assertEqual(status_code, 400)

        invalid_purchase_time = default_receipt.copy()
        invalid_purchase_time["purchaseTime"] = "25:00"
        response, status_code = self.process_receipt(invalid_purchase_time)
        self.assertEqual(status_code, 400)

        invalid_items = default_receipt.copy()
        invalid_items["items"] = '[{"shortDescription": "Pepsi - 12-oz", "price": "1.25"}]'
        response, status_code = self.process_receipt(invalid_items)
        self.assertEqual(status_code, 400)

        invalid_item_description = default_receipt.copy()
        invalid_item_description["items"][0]["shortDescription"] = "Pepsi (12-oz)"
        response, status_code = self.process_receipt(invalid_item_description)
        self.assertEqual(status_code, 400)

        invalid_item_price = default_receipt.copy()
        invalid_item_price["items"][0]["price"] = "1.250"
        response, status_code = self.process_receipt(invalid_item_price)
        self.assertEqual(status_code, 400)

        invalid_total = default_receipt.copy()
        invalid_total["total"] = "1.250"
        response, status_code = self.process_receipt(invalid_total)
        self.assertEqual(status_code, 400)

    def test_invalid_id(self):
        """Test receipt with invalid ID"""
        id = str(uuid.uuid4())
        print(id)
        response, status_code = self.get_points(id)
        self.assertEqual(status_code, 404)
        
if __name__ == '__main__':
    unittest.main()