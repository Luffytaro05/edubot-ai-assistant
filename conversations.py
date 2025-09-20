# (conversations.py):
from flask import Blueprint, jsonify, Response
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
from datetime import datetime, date

# Create a Flask Blueprint
conversations_bp = Blueprint("conversations", __name__)

# MongoDB connection (use same connection string as your main app)
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
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
