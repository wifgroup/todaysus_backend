from datetime import datetime
from slugify import slugify

def create_category(data):
    return {
        "name": data["name"],
        "slug": slugify(data["name"]),
        "description": data.get("description"),
        "seo_title": data.get("seo_title"),
        "seo_description": data.get("seo_description"),
        "order": data.get("order", 0),
        "is_active": data.get("is_active", True),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
