from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from db.mongo import mongo
from models.article_model import create_article
from utils.helper import sync_topics

article_bp = Blueprint("articles", __name__)

# ---------------- ADMIN CRUD ---------------- #

@article_bp.route("/api/v1/admin/articles", methods=["POST"])
def create():
    data = request.json
    article = create_article(data)
    mongo.db.articles.insert_one(article)
    if article.get("topics"):
        sync_topics(article["topics"])
    return jsonify({"message": "Article created"}), 201


@article_bp.route("/api/v1/admin/articles/<id>", methods=["PUT"])
def update(id):
    data = request.json

    update_data = {
        **data,
        "updated_at": datetime.utcnow()
    }

    # If content is updated, mark as editorial update
    if "content_html" in data:
        update_data["has_update"] = True
        update_data["update_note"] = data.get(
            "update_note",
            "Article updated for clarity"
        )

    mongo.db.articles.update_one(
        {"_id": ObjectId(id), "is_deleted": False},
        {"$set": update_data}
    )

    return jsonify({"message": "Article updated"})



@article_bp.route("/api/v1/admin/articles/<id>", methods=["DELETE"])
def delete(id):
    mongo.db.articles.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_deleted": True}}
    )
    return jsonify({"message": "Article deleted"})


@article_bp.route("/api/v1/admin/articles", methods=["GET"])
def admin_list():
    status = request.args.get("status")
    query = {"is_deleted": False}

    if status:
        query["status"] = status

    articles = list(mongo.db.articles.find(query).sort("created_at", -1))
    for a in articles:
        a["_id"] = str(a["_id"])

    return jsonify(articles)


# ---------------- PUBLIC ---------------- #

@article_bp.route("/api/v1/articles", methods=["GET"])
def list_articles():
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    query = {"status": "published", "is_deleted": False}

    cursor = (
        mongo.db.articles
        .find(query)
        .sort("published_at", -1)
        .skip(skip)
        .limit(limit)
    )

    articles = []
    for a in cursor:
        a["_id"] = str(a["_id"])
        articles.append(a)

    total = mongo.db.articles.count_documents(query)

    return jsonify({
        "data": articles,
        "page": page,
        "limit": limit,
        "total": total
    })



@article_bp.route("/api/v1/articles/<slug>", methods=["GET"])
def single_article(slug):
    # Find the article
    article = mongo.db.articles.find_one_and_update(
        {
            "slug": slug,
            "status": "published",
            "is_deleted": False
        },
        {
            "$inc": {"view_count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        },
        return_document=True
    )

    if not article:
        return jsonify({"error": "Not found"}), 404

    article["_id"] = str(article["_id"])
    return jsonify(article)



@article_bp.route("/api/v1/articles/latest")
def latest():
    articles = mongo.db.articles.find(
        {"status": "published"}
    ).sort("published_at", -1).limit(10)

    return jsonify([{**a, "_id": str(a["_id"])} for a in articles])


@article_bp.route("/api/v1/articles/most-read")
def most_read():
    articles = mongo.db.articles.find(
        {
            "status": "published",
            "is_deleted": False
        }
    ).sort("view_count", -1).limit(10)

    return jsonify([{**a, "_id": str(a["_id"])} for a in articles])


