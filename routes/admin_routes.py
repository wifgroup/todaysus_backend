from flask import Blueprint, jsonify
from pymongo import TEXT
from db.mongo import mongo


admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/api/v1/admin/create-search-index", methods=["POST"])
def create_search_index():
    try:
        mongo.db.articles.create_index(
            [
                ("title", TEXT),
                ("excerpt", TEXT),
                # ("author", TEXT),
                ("content_html", TEXT)
            ],
            weights={
                "title": 10,
                "excerpt": 5,
                # "author": 6,
                "content_html": 1
            },
            name="articles_text_search_index"
        )

        return jsonify({"message": "Text index created successfully"}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
