from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from bson import ObjectId
import datetime

# Blueprint for user routes
users_bp = Blueprint("users", __name__, url_prefix="/api/users")

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
sub_users = db["sub_users"]

# Helper: Convert Mongo document to JSON
def serialize_user(user):
    return {
        "id": str(user["_id"]),
        "name": user.get("name", ""),
        "email": user.get("email", ""),
        "role": user.get("role", "User"),
        "office": user.get("office", "-"),
        "status": user.get("status", "Inactive"),
        "last_login": user.get("last_login", "Never")  # 🔹 unified key
    }

# ➝ Create new user
# ➝ Create new user (with validation + password hashing)
@users_bp.route("", methods=["POST"])
def add_user():
    data = request.json
    required = ["name", "email", "password", "status"]

    # 🔹 Check required fields
    if not all(field in data for field in required):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    # 🔹 Check duplicate email
    if sub_users.find_one({"email": data["email"]}):
        return jsonify({"success": False, "message": "Email already exists"}), 400

    # 🔹 Hash password
    hashed_pw = generate_password_hash(data["password"])

    try:
        new_user = {
            "name": data["name"],
            "email": data["email"],
            "password": hashed_pw,
            "role": data.get("role", "User"),
            "office": data.get("office", "-"),
            "status": data["status"],
            "createdAt": datetime.datetime.utcnow(),
            "last_login": None
        }
        result = sub_users.insert_one(new_user)
        new_user["id"] = str(result.inserted_id)
        del new_user["_id"]

        return jsonify({
            "success": True,
            "message": "User added successfully",
            "user": {
                "id": new_user["id"],
                "name": new_user["name"],
                "email": new_user["email"],
                "role": new_user["role"],
                "office": new_user["office"],
                "status": new_user["status"],
                "last_login": new_user["last_login"]
            }
        }), 201
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Error adding user: {str(e)}"
        }), 500


# ➝ Get all users
# Get all users
@users_bp.route("", methods=["GET"])
def get_users():
    users_list = [serialize_user(user) for user in sub_users.find()]
    return jsonify(users_list)


# ➝ Get user by ID
@users_bp.route("/<user_id>", methods=["GET"])
def get_user(user_id):
    user = sub_users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify(serialize_user(user))

# ➝ Update user
# ➝ Update user
@users_bp.route("/<user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    updates = {}

    # Editable fields
    if "name" in data and data["name"]:
        updates["name"] = data["name"]
    if "email" in data and data["email"]:
        # check duplicate email
        existing = sub_users.find_one({"email": data["email"], "_id": {"$ne": ObjectId(user_id)}})
        if existing:
            return jsonify({"success": False, "message": "Email already exists"}), 400
        updates["email"] = data["email"]
    if "role" in data and data["role"]:
        updates["role"] = data["role"]
    if "status" in data and data["status"]:
        updates["status"] = data["status"]
    if "office" in data:
        updates["office"] = data["office"]
    if "password" in data and data["password"]:  # optional password change
        updates["password"] = generate_password_hash(data["password"])

    if not updates:
        return jsonify({"success": False, "message": "No valid fields to update"}), 400

    result = sub_users.update_one({"_id": ObjectId(user_id)}, {"$set": updates})

    if result.matched_count == 0:
        return jsonify({"success": False, "message": "User not found"}), 404

    return jsonify({"success": True, "message": "User updated successfully"})


# ➝ Toggle user status
@users_bp.route("/<user_id>/toggle", methods=["PATCH"])
def toggle_user_status(user_id):
    user = sub_users.find_one({"_id": ObjectId(user_id)})
    if not user:
        return jsonify({"success": False, "message": "User not found"}), 404

    new_status = "Inactive" if user["status"] == "Active" else "Active"
    sub_users.update_one({"_id": ObjectId(user_id)}, {"$set": {"status": new_status}})

    return jsonify({"success": True, "newStatus": new_status})

# ➝ Delete user
@users_bp.route("/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    result = sub_users.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        return jsonify({"success": False, "message": "User not found"}), 404
    return jsonify({"success": True, "message": "User deleted"})

