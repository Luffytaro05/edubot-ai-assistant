# (conversations.py):
from flask import Blueprint, jsonify, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from datetime import datetime, date
import os

# Create a Flask Blueprint
conversations_bp = Blueprint("conversations", __name__)

# MongoDB connection with error handling
def get_mongo_client():
    """Get MongoDB client with proper error handling"""
    try:
        mongodb_uri = os.getenv('MONGODB_URI', 'mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/')
        client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        # Test connection
        client.admin.command('ping')
        return client
    except Exception as e:
        print(f"❌ MongoDB connection failed in conversations.py: {e}")
        return None

def get_db():
    """Get database with fallback"""
    client = get_mongo_client()
    if client:
        return client["chatbot_db"]
    else:
        # Return mock database for offline mode
        class MockDB:
            def __getattr__(self, name):
                return MockCollection()
        class MockCollection:
            def find_one(self, *args, **kwargs): return None
            def find(self, *args, **kwargs): return []
            def insert_one(self, *args, **kwargs): return type('Result', (), {'inserted_id': 'mock_id'})()
            def update_one(self, *args, **kwargs): return type('Result', (), {'modified_count': 1})()
            def delete_one(self, *args, **kwargs): return type('Result', (), {'deleted_count': 1})()
            def count_documents(self, *args, **kwargs): return 0
            def distinct(self, *args, **kwargs): return []
        return MockDB()

# Initialize collections with lazy loading
db = get_db()
conversations_collection = db["conversations"]

# Custom JSON encoder for ObjectId + datetime
class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)

# Routes
@conversations_bp.route("/api/conversations", methods=["GET"])
def get_conversations():
    conversations = list(conversations_collection.find())
    return Response(
        JSONEncoder().encode(conversations),
        mimetype="application/json"
    )

@conversations_bp.route("/api/conversations/<id>", methods=["DELETE"])
def delete_conversation(id):
    result = conversations_collection.delete_one({"_id": ObjectId(id)})
    return jsonify({"deleted": result.deleted_count})
