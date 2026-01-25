from flask import Blueprint, request, jsonify
from db.mongo import mongo
from datetime import datetime
from models.contact_model import create_contact_message

contact_bp = Blueprint("contact", __name__)
@contact_bp.route("/api/v1/contact", methods=["POST"])
def submit_contact():
    data = request.json

    if not data.get("name") or not data.get("email") or not data.get("message"):
        return jsonify({"error": "All fields are required"}), 400

    mongo.db.contact_messages.insert_one({
        "name": data["name"],
        "email": data["email"],
        "message": data["message"],
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent"),
        "status": "new",
        "created_at": datetime.utcnow()
    })

    return jsonify({"message": "Message received"}), 201
