from flask import Flask, request, jsonify
from flask_cors import CORS
import hmac
import hashlib
import time
import uuid

app = Flask(__name__)
CORS(app)

WEBHOOK_SECRET = b"quick_commerce_secret_key_123"

orders_db = {}
idempotency_store = {}

@app.route("/api/v1/orders", methods=["POST"])
def place_order():
    idempotency_key = request.headers.get("Idempotency-Key")
    if idempotency_key and idempotency_key in idempotency_store:
        return jsonify({
            "message": "Duplicate request detected (Idempotent replay)",
            "data": idempotency_store[idempotency_key]
        }), 200

    data = request.get_json()
    
    if not data or "customer_id" not in data or "items" not in data:
        return jsonify({"error": "Invalid payload, customer_id and items are required"}), 400
    
    order_id = "ord_" + uuid.uuid4().hex[:8]
    
    order_record = {
        "order_id": order_id,
        "customer_id": data["customer_id"],
        "dark_store_id": data.get("dark_store_id", "ds_default"),
        "items": data["items"],
        "total_amount_in_paise": data.get("total_amount_in_paise", 0),
        "status": "order_placed",
        "created_at": time.time()
    }
    
    orders_db[order_id] = order_record
    
    payload = f'{{"order_id": "{order_id}", "status": "dispatch_ready"}}'
    signature = hmac.new(WEBHOOK_SECRET, payload.encode(), hashlib.sha256).hexdigest()
    
    response_data = {
        "status": "success",
        "order_id": order_id,
        "assigned_picker_id": "picker_07",
        "estimated_dispatch_seconds": 180,
        "webhook_signature": signature
    }
    
    if idempotency_key:
        idempotency_store[idempotency_key] = response_data
        
    return jsonify(response_data), 201

if __name__ == "__main__":
    app.run(debug=True, port=5000)