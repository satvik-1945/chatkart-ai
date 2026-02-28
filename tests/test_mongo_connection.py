from pymongo import MongoClient
try:
    client = MongoClient("mongodb://localhost:27017/")
    db = client["test"]
    print("MongoDB connected successfully!")
    print(f"Collections: {db.list_collection_names()}")
except Exception as e:
    print(f"MongoDB connection failed: {e}")