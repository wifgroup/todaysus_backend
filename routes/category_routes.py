from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from db.mongo import mongo
from models.category_model import create_category

category_bp = Blueprint("categories", __name__)

# ---------------- ADMIN ---------------- #

@category_bp.route("/api/v1/admin/categories", methods=["POST"])
def create():
    data = request.json
    category = create_category(data)
    mongo.db.categories.insert_one(category)
    return jsonify({"message": "Category created"}), 201


@category_bp.route("/api/v1/admin/categories/<id>", methods=["PUT"])
def update(id):
    mongo.db.categories.update_one(
        {"_id": ObjectId(id)},
        {"$set": {**request.json, "updated_at": datetime.utcnow()}}
    )
    return jsonify({"message": "Category updated"})


@category_bp.route("/api/v1/admin/categories", methods=["GET"])
def admin_list():
    categories = list(mongo.db.categories.find().sort("order", 1))
    for c in categories:
        c["_id"] = str(c["_id"])
    return jsonify(categories)


@category_bp.route("/api/v1/admin/categories/<id>", methods=["DELETE"])
def delete(id):
    mongo.db.categories.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"is_active": False}}
    )
    return jsonify({"message": "Category disabled"})


# ---------------- PUBLIC ---------------- #

@category_bp.route("/api/v1/categories", methods=["GET"])
def list_categories():
    categories = list(
        mongo.db.categories.find(
            {"is_active": True}
        ).sort("order", 1)
    )
    for c in categories:
        c["_id"] = str(c["_id"])
    return jsonify(categories)


@category_bp.route("/api/v1/categories/<slug>/articles", methods=["GET"])
def category_articles(slug):
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    query = {
        "status": "published",
        "is_deleted": False,
        "category.slug": slug
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
        "category": slug,
        "page": page,
        "limit": limit,
        "total": total,
        "data": articles
    })
