from datetime import datetime

def create_author(data):
    return {
        "slug": data["slug"],
        "name": data["name"],
        "display_name": data.get("display_name", data["name"]),
        "role": data.get("role", ""),
        "type": data.get("type", "staff"),

        "bio": data.get("bio", ""),
        "short_bio": data.get("short_bio", ""),
        "expertise": data.get("expertise", []),

        "education": data.get("education", []),
        "experience_years": data.get("experience_years", 0),
        "credentials": data.get("credentials", []),

        "email": data.get("email", ""),
        "social": data.get("social", {}),

        "photo": data.get("photo", {
            "url": "",
            "alt": ""
        }),

        "seo_title": data.get("seo_title", data["name"]),
        "seo_description": data.get("seo_description", ""),

        "is_active": True,
        "is_verified": False,
        "is_public": True,

        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
