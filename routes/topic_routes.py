from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from db.mongo import mongo

topic_bp = Blueprint("topics", __name__)

# ---------------- ADMIN ---------------- #

@topic_bp.route("/api/v1/admin/topics", methods=["GET"])
def admin_list():
    topics = list(mongo.db.topics.find().sort("name", 1))
    for t in topics:
        t["_id"] = str(t["_id"])
    return jsonify(topics)


@topic_bp.route("/api/v1/admin/topics/<id>", methods=["PUT"])
def update(id):
    mongo.db.topics.update_one(
        {"_id": ObjectId(id)},
        {"$set": {**request.json, "updated_at": datetime.utcnow()}}
    )
    return jsonify({"message": "Topic updated"})


@topic_bp.route("/api/v1/admin/topics/<id>", methods=["DELETE"])
def disable(id):
    mongo.db.topics.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_active": False}}
    )
    return jsonify({"message": "Topic disabled"})


@topic_bp.route("/api/v1/topics", methods=["GET"])
def list_topics():
    topics = list(
        mongo.db.topics.find({"is_active": True}).sort("name", 1)
    )
    for t in topics:
        t["_id"] = str(t["_id"])
    return jsonify(topics)


@topic_bp.route("/api/v1/topics/<slug>/articles", methods=["GET"])
def topic_articles(slug):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    query = {
        "status": "published",
        "is_deleted": False,
        "topics.slug": slug
    }

    articles = list(
        mongo.db.articles
        .find(query)
        .sort("published_at", -1)
        .skip(skip)
        .limit(limit)
    )

    total = mongo.db.articles.count_documents(query)

    for a in articles:
        a["_id"] = str(a["_id"])

    return jsonify({
        "topic": slug,
        "page": page,
        "limit": limit,
        "total": total,
        "data": articles
    })
