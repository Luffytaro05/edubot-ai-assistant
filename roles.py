from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from bson import ObjectId

# Blueprint
roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
sub_users = db["sub_users"]
roles_collection = db["roles"]

# Exclude password field globally
EXCLUDE_FIELDS = {"password": 0}

def serialize_role(role):
    return {
        "id": str(role["_id"]),
        "office": role.get("office"),
        "permissions": role.get("permissions", [])
    }
# Get all roles
@roles_bp.route("/all", methods=["GET"])
def get_roles():
    roles = list(roles_collection.find())
    return jsonify([serialize_role(r) for r in roles])
@roles_bp.route("/get/<role_id>", methods=["GET"])
def get_role_by_id(role_id):
    role = roles_collection.find_one({"_id": ObjectId(role_id)})
    if not role:
        return jsonify({"success": False, "message": "Role not found"}), 404
    return jsonify(serialize_role(role))

# Get all users (exclude password)
@roles_bp.route("/users", methods=["GET"])
def get_all_users():
    users = list(sub_users.find({}, EXCLUDE_FIELDS))
    for u in users:
        u["_id"] = str(u["_id"])
    return jsonify(users)

# Add role and assign office
@roles_bp.route("/add", methods=["POST"])
def add_role():
    data = request.json
    office = data.get("office")
    permissions = data.get("permissions", [])

    if not office or not permissions:
        return jsonify({"success": False, "message": "Office and permissions are required"}), 400

    new_role = {"office": office, "permissions": permissions}
    result = roles_collection.insert_one(new_role)

    return jsonify({"success": True, "id": str(result.inserted_id)})


# Update role
@roles_bp.route("/update/<role_id>", methods=["PUT"])
def update_role(role_id):
    data = request.json
    result = roles_collection.update_one(
        {"_id": ObjectId(role_id)},
        {"$set": data}
    )
    if result.modified_count > 0:
        return jsonify({"success": True, "message": "Role updated"})
    return jsonify({"success": False, "message": "No changes made or role not found"}), 400


# Get role by ID
@roles_bp.route("/get/<role_id>", methods=["GET"])
def get_role(role_id):
    role = roles_collection.find_one({"_id": ObjectId(role_id)}, {"password": 0})
    if not role:
        return jsonify({"error": "Role not found"}), 404

    role["_id"] = str(role["_id"])
    return jsonify(role)

# Detect and assign office for user
@roles_bp.route("/detect-office/<user_id>", methods=["GET"])
def detect_office(user_id):
    user = sub_users.find_one({"_id": ObjectId(user_id)}, EXCLUDE_FIELDS)
    if not user:
        return jsonify({"error": "User not found"}), 404

    office = user.get("office", "Unassigned")
    return jsonify({"user_id": user_id, "office": office})
