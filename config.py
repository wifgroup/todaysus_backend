import os

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://harshilbmk_db_user:harshilbmk@todaysus.jn6ekbs.mongodb.net/todaysus")
