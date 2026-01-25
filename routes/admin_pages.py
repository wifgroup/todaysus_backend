from flask import Blueprint, request, jsonify
from datetime import datetime
from bson import ObjectId
from db.mongo import mongo

admin_pages_bp = Blueprint("admin_pages", __name__)


# @admin_pages_bp.route("/api/v1/admin/pages", methods=["POST"])
# def create_page():

#     data = request.json

#     required_fields = ["slug", "title", "content"]
#     for field in required_fields:
#         if field not in data:
#             return jsonify({"error": f"{field} is required"}), 400

#     # prevent duplicate slug
#     if mongo.db.pages.find_one({"slug": data["slug"]}):
#         return jsonify({"error": "Page with this slug already exists"}), 409

#     page = {
#         "slug": data["slug"],
#         "title": data["title"],
#         "seo_title": data.get("seo_title", data["title"]),
#         "seo_description": data.get("seo_description", ""),
#         "content": data["content"],
#         "is_active": True,
#         "created_at": datetime.utcnow(),
#         "updated_at": datetime.utcnow()
#     }

#     mongo.db.pages.insert_one(page)

#     return jsonify({
#         "message": "Page created successfully",
#         "slug": data["slug"]
#     }), 201


# @admin_pages_bp.route("/api/v1/admin/pages/<slug>", methods=["PUT"])
# def update_page(slug):

#     data = request.json

#     update = {
#         "updated_at": datetime.utcnow()
#     }

#     for field in ["title", "seo_title", "seo_description", "content", "is_active"]:
#         if field in data:
#             update[field] = data[field]

#     result = mongo.db.pages.update_one(
#         {"slug": slug},
#         {"$set": update}
#     )

#     if result.matched_count == 0:
#         return jsonify({"error": "Page not found"}), 404

#     return jsonify({"message": "Page updated successfully"})


@admin_pages_bp.route("/api/v1/admin/pages", methods=["POST"])
def create_page():
    data = request.json

    required = ["slug", "title", "content"]
    for f in required:
        if f not in data:
            return jsonify({"error": f"{f} is required"}), 400

    if mongo.db.pages.find_one({"slug": data["slug"]}):
        return jsonify({"error": "Page already exists"}), 409

    page = {
        "slug": data["slug"],
        "title": data["title"],
        "seo_title": data.get("seo_title", data["title"]),
        "seo_description": data.get("seo_description", ""),
        "content": data["content"],
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    mongo.db.pages.insert_one(page)

    return jsonify({"message": "Page created", "slug": page["slug"]}), 201


@admin_pages_bp.route("/api/v1/admin/pages/<slug>", methods=["PUT"])
def update_page(slug):
    data = request.json

    update = {"updated_at": datetime.utcnow()}
    for f in ["title", "seo_title", "seo_description", "content", "is_active"]:
        if f in data:
            update[f] = data[f]

    res = mongo.db.pages.update_one({"slug": slug}, {"$set": update})

    if res.matched_count == 0:
        return jsonify({"error": "Page not found"}), 404

    return jsonify({"message": "Page updated"})

@admin_pages_bp.route("/api/v1/admin/pages", methods=["GET"])
def list_pages():

    pages = list(
        mongo.db.pages.find({}, {"content": 0})
    )

    for p in pages:
        p["_id"] = str(p["_id"])

    return jsonify(pages)
