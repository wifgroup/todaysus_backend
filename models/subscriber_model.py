from datetime import datetime

def create_subscriber(email, source, ip, user_agent):
    return {
        "email": email.lower().strip(),
        "status": "active",
        "source": source,
        "ip_address": ip,
        "user_agent": user_agent,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
