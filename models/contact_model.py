from datetime import datetime

def create_contact_message(data):
    return {
        "name": data["name"],
        "email": data["email"],
        "message": data["message"],

        # Metadata
        "ip_address": data.get("ip"),
        "user_agent": data.get("user_agent"),

        "status": "new",  # new | reviewed | replied
        "created_at": datetime.utcnow()
    }
