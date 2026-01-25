from datetime import datetime

def create_page(data):
    return {
        "slug": data["slug"],
        "title": data["title"],
        "seo_title": data.get("seo_title", data["title"]),
        "seo_description": data.get("seo_description", ""),
        "content": data.get("content", {}),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "is_active": True
    }
