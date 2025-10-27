from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
import datetime
import os

# Blueprint for user routes
users_bp = Blueprint("users", __name__, url_prefix="/api/users")

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
        print(f"❌ MongoDB connection failed in users.py: {e}")
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

# ➝ Authenticate user for Sub-Admin login
def authenticate_user(email, password):
    """
    Authenticate user credentials and return user data if valid
    Returns: dict with success, user data, and redirect info
    """
    try:
        # Find user by email
        user = sub_users.find_one({"email": email.lower().strip()})
        
        if not user:
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Check if user is active
        if user.get("status") != "Active":
            return {
                "success": False,
                "message": "Account is inactive"
            }
        
        # Verify password
        if not check_password_hash(user["password"], password):
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Update last login
        sub_users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.utcnow().isoformat()}}
        )
        
        # Prepare user data (without password)
        user_data = {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "User"),
            "status": user.get("status", "Active"),
            "last_login": user.get("last_login", "Never")
        }
        
        # Determine redirect URL based on role
        redirect_url = "/"
        if user.get("role") == "Sub-Admin":
            redirect_url = "/Sub-dashboard.html"
        elif user.get("role") == "Admin":
            redirect_url = "/dashboard.html"
        
        return {
            "success": True,
            "user": user_data,
            "role": user.get("role", "User"),
            "office": user.get("office", "-"),
            "redirect": redirect_url
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }

def authenticate_user_with_office(email, password, office=None, required_role=None):
    """
    Enhanced authentication with office and role validation
    """
    try:
        # Find user by email
        user = sub_users.find_one({"email": email.lower().strip()})
        
        if not user:
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Check if user is active
        if user.get("status") != "Active":
            return {
                "success": False,
                "message": "Account is inactive"
            }
        
        # Verify password
        if not check_password_hash(user["password"], password):
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Check role if specified
        if required_role and user.get("role") != required_role:
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Check office if specified
        if office and user.get("office") != office:
            return {
                "success": False,
                "message": "Invalid credentials"
            }
        
        # Update last login
        sub_users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.datetime.utcnow().isoformat()}}
        )
        
        # Prepare user data (without password)
        user_data = {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user.get("email", ""),
            "role": user.get("role", "User"),
            "office": user.get("office", "-"),
            "status": user.get("status", "Active"),
            "last_login": user.get("last_login", "Never")
        }
        
        return {
            "success": True,
            "user": user_data,
            "role": user.get("role", "User"),
            "office": user.get("office", "-")
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Authentication error: {str(e)}"
        }
@users_bp.route("/subadmin/login", methods=["POST"])
def subadmin_login():
    """Sub Admin login endpoint"""
    data = request.json
    email = data.get('email', '').strip()
    password = data.get('password', '')
    office = data.get('office', '').strip()
    
    if not email or not password or not office:
        return jsonify({
            "success": False,
            "message": "Invalid office, email, or password"
        }), 400
    
    # Authenticate with office and role validation
    result = authenticate_user_with_office(
        email=email, 
        password=password, 
        office=office, 
        required_role="Sub-Admin"
    )
    
    if result['success']:
        return jsonify({
            "success": True,
            "user": result['user'],
            "office": result['office'],
            "message": "Login successful"
        })
    else:
        return jsonify({
            "success": False,
            "message": "Invalid office, email, or password"
        }), 401