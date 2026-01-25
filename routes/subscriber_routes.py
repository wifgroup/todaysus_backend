from flask import Blueprint, request, jsonify
from datetime import datetime
from db.mongo import mongo
from models.subscriber_model import create_subscriber

subscriber_bp = Blueprint("subscribers", __name__)


@subscriber_bp.route("/api/v1/subscribe", methods=["POST"])
def subscribe():

    data = request.json
    email = data.get("email")

    if not email:
        return jsonify({"error": "Email is required"}), 400

    existing = mongo.db.subscribers.find_one(
        {"email": email.lower().strip()}
    )

    if existing:
        if existing["status"] == "unsubscribed":
            mongo.db.subscribers.update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "status": "active",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            return jsonify({"message": "Subscription reactivated"}), 200

        return jsonify({"message": "You are already subscribed"}), 200

    subscriber = create_subscriber(
        email=email,
        source=data.get("source", "homepage"),
        ip=request.remote_addr,
        user_agent=request.headers.get("User-Agent")
    )

    mongo.db.subscribers.insert_one(subscriber)

    return jsonify({"message": "Subscribed successfully"}), 201


@subscriber_bp.route("/api/v1/admin/subscribers", methods=["GET"])
def list_subscribers():
    subs = list(mongo.db.subscribers.find().sort("created_at", -1))
    for s in subs:
        s["_id"] = str(s["_id"])
    return jsonify(subs)
