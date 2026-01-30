from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from db.mongo import mongo
from models.author_model import create_author

admin_authors_bp = Blueprint("admin_authors", __name__)

@admin_authors_bp.route("/api/v1/admin/authors", methods=["POST"])
def create_author_api():
    data = request.json

    required = ["slug", "name"]
    for field in required:
        if field not in data:
            return jsonify({"error": f"{field} is required"}), 400

    # Prevent duplicate slug
    if mongo.db.authors.find_one({"slug": data["slug"]}):
        return jsonify({"error": "Author with this slug already exists"}), 409

    author = create_author(data)
    mongo.db.authors.insert_one(author)

    return jsonify({
        "message": "Author created successfully",
        "slug": author["slug"]
    }), 201

@admin_authors_bp.route("/api/v1/admin/authors", methods=["GET"])
def list_authors():
    authors = list(mongo.db.authors.find())

    for a in authors:
        a["_id"] = str(a["_id"])

    return jsonify(authors)

@admin_authors_bp.route("/api/v1/admin/authors/<slug>", methods=["GET"])
def get_author(slug):
    author = mongo.db.authors.find_one({"slug": slug})

    if not author:
        return jsonify({"error": "Author not found"}), 404

    author["_id"] = str(author["_id"])
    return jsonify(author)

@admin_authors_bp.route("/api/v1/admin/authors/<slug>", methods=["PUT"])
def update_author(slug):
    data = request.json

    update = {
        "updated_at": datetime.utcnow()
    }

    allowed_fields = [
        "name", "display_name", "role", "type",
        "bio", "short_bio", "expertise",
        "education", "experience_years", "credentials",
        "email", "social", "photo",
        "seo_title", "seo_description",
        "is_active", "is_verified", "is_public"
    ]

    for field in allowed_fields:
        if field in data:
            update[field] = data[field]

    result = mongo.db.authors.update_one(
        {"slug": slug},
        {"$set": update}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Author not found"}), 404

    return jsonify({"message": "Author updated successfully"})

@admin_authors_bp.route("/api/v1/admin/authors/<slug>", methods=["DELETE"])
def delete_author(slug):
    result = mongo.db.authors.update_one(
        {"slug": slug},
        {"$set": {
            "is_active": False,
            "is_public": False,
            "updated_at": datetime.utcnow()
        }}
    )

    if result.matched_count == 0:
        return jsonify({"error": "Author not found"}), 404

    return jsonify({"message": "Author deactivated successfully"})
