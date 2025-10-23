"""
sub_conversations.py
Handles storing and retrieving chatbot conversations per office
"""

from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations = db["conversations"]

sub_conversations_bp = Blueprint("sub_conversations", __name__)

# Serialize MongoDB documents
def serialize_conversation(conv):
    return {
        "_id": str(conv["_id"]),
        "user": conv.get("user"),
        "email": conv.get("email", ""),   # Added for UI
        "message": conv.get("message"),
        "sender": conv.get("sender"),
        "office": conv.get("office"),
        "timestamp": conv.get("timestamp"),
        "date": conv.get("date"),  # ✅ Added date field from MongoDB
        "messages": conv.get("messages", []),
        "start_time": conv.get("start_time"),
        "duration": conv.get("duration"),
        "category": conv.get("category"),
        "sentiment": conv.get("sentiment"),
        "escalated": conv.get("escalated", False),
        "status": conv.get("status")  # ✅ Added status field
    }

# -------------------------------
# Fetch conversations per office
# -------------------------------
@sub_conversations_bp.route("/subadmin/conversations", methods=["GET"])
def get_conversations():
    office = request.args.get("office")
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    search = request.args.get("search", "")

    query = {"office": office} if office else {}

    if search:
        query["message"] = {"$regex": search, "$options": "i"}

    total = conversations.count_documents(query)
    cursor = (
        conversations.find(query)
        .sort("timestamp", -1)
        .skip((page - 1) * limit)
        .limit(limit)
    )

    conv_list = [serialize_conversation(conv) for conv in cursor]
    return jsonify({"conversations": conv_list, "total": total})

# -------------------------------
# Get a single conversation by ID
# -------------------------------
@sub_conversations_bp.route("/subadmin/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    try:
        conv = conversations.find_one({"_id": ObjectId(conversation_id)})
    except Exception:
        return jsonify({"error": "Invalid conversation ID"}), 400

    if not conv:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(serialize_conversation(conv))

# -------------------------------
# Store a new conversation
# -------------------------------
@sub_conversations_bp.route("/subadmin/conversations", methods=["POST"])
def add_conversation():
    data = request.json
    if not data.get("office") or not data.get("message"):
        return jsonify({"error": "Office and message required"}), 400
    
    # Detect sender
    sender = "bot" if data.get("is_bot", False) else data.get("sender", "user")

    conversation = {
        "user": data.get("user", "Anonymous"),
        "email": data.get("email", ""),  # Capture email if available
        "message": data["message"],
        "sender": sender,
        "office": data["office"],
        "date": datetime.utcnow(),
        "messages": data.get("messages", []),
        "start_time": datetime.utcnow(),
        "duration": data.get("duration"),
        "category": data.get("category", "General"),
        "sentiment": data.get("sentiment", "Neutral"),
        "escalated": data.get("escalated", False)
    }

    result = conversations.insert_one(conversation)
    return jsonify({"message": "Conversation stored", "id": str(result.inserted_id)})

# -------------------------------
# Escalate a conversation
# -------------------------------
@sub_conversations_bp.route("/subadmin/conversations/<conversation_id>/escalate", methods=["PUT"])
def escalate_conversation(conversation_id):
    try:
        result = conversations.update_one(
            {"_id": ObjectId(conversation_id)},
            {"$set": {"escalated": True}}
        )
    except Exception:
        return jsonify({"error": "Invalid conversation ID"}), 400

    if result.matched_count == 0:
        return jsonify({"error": "Conversation not found"}), 404

    return jsonify({"message": "Conversation escalated", "id": conversation_id})

# -------------------------------
# Delete a conversation
# -------------------------------
@sub_conversations_bp.route("/subadmin/conversations/<conversation_id>", methods=["DELETE"])
def delete_conversation(conversation_id):
    try:
        result = conversations.delete_one({"_id": ObjectId(conversation_id)})
    except Exception:
        return jsonify({"error": "Invalid conversation ID"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Conversation not found"}), 404

    return jsonify({"message": "Conversation deleted", "id": conversation_id})
