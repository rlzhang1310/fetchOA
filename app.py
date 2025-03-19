from flask import Flask, request, jsonify
import uuid
import re
from datetime import datetime
import math

app = Flask(__name__)

receipts = {}

def validate_receipt(data):
    RETAILER_REGEX = re.compile(r'^[\w\s\-&]+$')
    TOTAL_REGEX = re.compile(r'^\d+\.\d{2}$')
    ITEM_DESCRIPTION_REGEX = re.compile(r'^[\w\s\-]+$')
    ITEM_PRICE_REGEX = re.compile(r'^\d+\.\d{2}$')

    retailer = data.get('retailer')
    if not retailer:
        return False, "Missing required field: retailer"
    if not isinstance(retailer, str) or not RETAILER_REGEX.match(retailer):
        return False, "Invalid retailer format."


    purchase_date = data.get('purchaseDate')
    if not purchase_date:
        return False, "Missing required field: purchaseDate"
    try:
        datetime.strptime(purchase_date, "%Y-%m-%d")
    except ValueError:
        return False, "Invalid purchaseDate format."


    purchase_time = data.get('purchaseTime')
    if not purchase_time:
        return False, "Missing required field: purchaseTime"
    try:
        datetime.strptime(purchase_time, "%H:%M")   
    except ValueError:
        return False, "Invalid purchaseTime format."


    total = data.get('total')
    if not total:
        return False, "Missing required field: total"
    if not isinstance(total, str) or not TOTAL_REGEX.match(total):
        return False, "Invalid total format."


    items = data.get('items')
    if not items:
        return False, "Missing required field: items"
    if not isinstance(items, list):
        return False, "Invalid items format."

    for idx, item in enumerate(items):
        short_description = item.get('shortDescription')
        if not short_description:
            return False, f"Missing required field: item {idx + 1} description"
        if not isinstance(short_description, str) or not ITEM_DESCRIPTION_REGEX.match(short_description):
            return False, f"Invalid item description format at item {idx + 1} description"
        
        price = item.get('price')
        if not price:
            return False, f"Missing required field: item {idx + 1} price"
        if not isinstance(price, str) or not ITEM_PRICE_REGEX.match(price):
            return False, f"Invalid item price format at item {idx + 1}"
        
    return True, None
        
def award_points(receipt):
    points = 0

    # One point for every alphanumeric character in the retailer name.
    retailer = receipt.get("retailer")
    points += sum(1 for c in retailer if c.isalnum())

    # 50 points if the total is a round dollar amount (no cents).
    try:
        total = float(receipt.get("total"))
    except ValueError: ## shouldn't happen due to validation
        total = 0.0
    if total.is_integer():
        points += 50

    # 25 points if the total is a multiple of 0.25.
    if int(total * 100) % 25 == 0:
        points += 25

    # 5 points for every two items on the receipt.
    items = receipt.get("items")
    points += int(len(items) // 2) * 5

    # For each item, if the trimmed length of the description is a multiple of 3, multiply the price by 0.2 and round up to the nearest integer.
    for item in items:
        description = item.get("shortDescription").strip()
        if len(description) > 0 and len(description) % 3 == 0: ## shouldn't happen due to validation
            try:
                price = float(item.get("price"))
            except ValueError: ## shouldn't happen due to validation
                price = 0.0
            points += math.ceil(price * 0.2)

    # 6 points if the day in the purchase date is odd.
    try:
        purchase_date = datetime.strptime(receipt.get("purchaseDate"), "%Y-%m-%d")
        if purchase_date.day % 2 == 1:
            points += 6
    except ValueError: ## shouldn't happen due to validation
        pass

    # 10 points if the time of purchase is after 2:00pm and before 4:00pm.
    try:
        purchase_time = datetime.strptime(receipt.get("purchaseTime"), "%H:%M").time()
        if purchase_time > datetime.strptime("14:00", "%H:%M").time() and purchase_time < datetime.strptime("16:00", "%H:%M").time():
            points += 10
    except ValueError: ## shouldn't happen due to validation
        pass

    return points

@app.route('/receipts/process', methods=['POST'])
def process_receipt():
    if not request.is_json:
        return jsonify({"error": "The receipt is invalid."}), 400
    data = request.get_json()
    valid, error = validate_receipt(data)
    if not valid:
        return jsonify({"error": error}), 400
    
    receipt_id = str(uuid.uuid4())
    receipts[receipt_id] = data
    return jsonify({"id": receipt_id})

@app.route('/receipts/<receipt_id>/points', methods=['GET'])
def get_points(receipt_id):
    try:
        receipt = receipts.get(receipt_id)
    except KeyError:
        return jsonify({"error": "Receipt not found."}), 404
    points = award_points(receipt)
    return jsonify({"points": points})


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)