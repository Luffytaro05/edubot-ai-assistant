from flask import Blueprint, jsonify, request
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import re
import os

# Blueprint
roles_bp = Blueprint("roles", __name__, url_prefix="/api/roles")

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
        print(f"❌ MongoDB connection failed in roles.py: {e}")
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
            def __getitem__(self, name):
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
users_collection = db["users"]
roles_collection = db["roles"]
permissions_collection = db["sub_admin_permissions"]

# Available permissions
AVAILABLE_PERMISSIONS = [
    'dashboard',
    'conversations', 
    'faq',
    'announcements',
    'usage',
    'feedback'
]

# Default permissions for each office
DEFAULT_PERMISSIONS = {
    'Admission Office': {
        'dashboard': True,
        'conversations': True,
        'faq': True,
        'announcements': False,
        'usage': True,
        'feedback': True
    },
    "Registrar's Office": {
        'dashboard': True,
        'conversations': True,
        'faq': True,
        'announcements': False,
        'usage': True,
        'feedback': True
    },
    'ICT Office': {
        'dashboard': True,
        'conversations': True,
        'faq': True,
        'announcements': True,
        'usage': True,
        'feedback': True
    },
    'Guidance Office': {
        'dashboard': True,
        'conversations': True,
        'faq': True,
        'announcements': True,
        'usage': True,
        'feedback': True
    },
    'Office of the Student Affairs (OSA)': {
        'dashboard': True,
        'conversations': True,
        'faq': True,
        'announcements': True,
        'usage': True,
        'feedback': True
    }
}

def serialize_sub_admin(sub_admin, permissions=None):
    """Serialize sub-admin data for JSON response"""
    return {
        "_id": str(sub_admin["_id"]),
        "name": sub_admin.get("name", ""),
        "email": sub_admin.get("email", ""),
        "office": sub_admin.get("office", ""),
        "role": sub_admin.get("role", "sub-admin"),
        "is_active": sub_admin.get("is_active", True),
        "created_at": sub_admin.get("created_at"),
        "last_login": sub_admin.get("last_login"),
        "permissions": permissions or {}
    }

def validate_permissions(permissions):
    """Validate permissions object"""
    if not permissions or not isinstance(permissions, dict):
        return False
    
    for key in permissions:
        if key not in AVAILABLE_PERMISSIONS:
            return False
        if not isinstance(permissions[key], bool):
            return False
    
    return True

def get_default_permissions(office):
    """Get default permissions for an office"""
    return DEFAULT_PERMISSIONS.get(office, {
        'dashboard': True,
        'conversations': False,
        'faq': False,
        'announcements': False,
        'usage': False,
        'feedback': False
    })

def get_or_create_permissions(sub_admin_id):
    """Get permissions for a sub-admin, create default if not exists"""
    permissions_doc = permissions_collection.find_one({"sub_admin_id": sub_admin_id})
    
    if not permissions_doc:
        # Get sub-admin office to determine default permissions
        sub_admin = sub_users.find_one({"_id": ObjectId(sub_admin_id)})
        office = sub_admin.get("office", "") if sub_admin else ""
        default_perms = get_default_permissions(office)
        
        # Create default permissions document
        permissions_doc = {
            "sub_admin_id": sub_admin_id,
            "permissions": default_perms,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        permissions_collection.insert_one(permissions_doc)
    
    return permissions_doc.get("permissions", {})

@roles_bp.route("/sub-admins", methods=["GET"])
def get_all_sub_admins():
    """Get all sub-admins with their permissions"""
    try:
        # Get all sub-admin users
        sub_admins = list(sub_users.find({"role": {"$regex": "sub.*admin", "$options": "i"}}))
        
        if not sub_admins:
            return jsonify({
                "success": True,
                "message": "No sub-admins found",
                "subAdmins": []
            })
        
        # Get permissions for each sub-admin
        result_sub_admins = []
        for sub_admin in sub_admins:
            sub_admin_id = str(sub_admin["_id"])
            permissions = get_or_create_permissions(sub_admin_id)
            result_sub_admins.append(serialize_sub_admin(sub_admin, permissions))
        
        return jsonify({
            "success": True,
            "message": f"Found {len(result_sub_admins)} sub-admins",
            "subAdmins": result_sub_admins
        })
        
    except Exception as e:
        print(f"Error getting sub-admins: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "subAdmins": []
        }), 500

@roles_bp.route("/sub-admins/<sub_admin_id>/permissions", methods=["GET"])
def get_sub_admin_permissions(sub_admin_id):
    """Get permissions for a specific sub-admin"""
    try:
        if not ObjectId.is_valid(sub_admin_id):
            return jsonify({
                "success": False,
                "message": "Invalid sub-admin ID"
            }), 400
        
        # Check if sub-admin exists
        sub_admin = sub_users.find_one({"_id": ObjectId(sub_admin_id)})
        if not sub_admin:
            return jsonify({
                "success": False,
                "message": "Sub-admin not found"
            }), 404
        
        # Get permissions
        permissions = get_or_create_permissions(sub_admin_id)
        
        return jsonify({
            "success": True,
            "subAdminId": sub_admin_id,
            "permissions": permissions
        })
        
    except Exception as e:
        print(f"Error getting sub-admin permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/sub-admins/<sub_admin_id>/permissions", methods=["PUT"])
def update_sub_admin_permissions(sub_admin_id):
    """Update permissions for a specific sub-admin"""
    try:
        if not ObjectId.is_valid(sub_admin_id):
            return jsonify({
                "success": False,
                "message": "Invalid sub-admin ID"
            }), 400
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        permissions = data.get("permissions", {})
        if not validate_permissions(permissions):
            return jsonify({
                "success": False,
                "message": "Invalid permissions format"
            }), 400
        
        # Check if sub-admin exists
        sub_admin = sub_users.find_one({"_id": ObjectId(sub_admin_id)})
        if not sub_admin:
            return jsonify({
                "success": False,
                "message": "Sub-admin not found"
            }), 404
        
        # Update or create permissions
        permissions_doc = {
            "sub_admin_id": sub_admin_id,
            "permissions": permissions,
            "updated_at": datetime.utcnow()
        }
        
        existing_permissions = permissions_collection.find_one({"sub_admin_id": sub_admin_id})
        if existing_permissions:
            # Update existing
            result = permissions_collection.update_one(
                {"sub_admin_id": sub_admin_id},
                {"$set": permissions_doc}
            )
        else:
            # Create new
            permissions_doc["created_at"] = datetime.utcnow()
            result = permissions_collection.insert_one(permissions_doc)
        
        return jsonify({
            "success": True,
            "message": "Permissions updated successfully",
            "subAdminId": sub_admin_id,
            "permissions": permissions
        })
        
    except Exception as e:
        print(f"Error updating sub-admin permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/sub-admins/<sub_admin_id>/reset-permissions", methods=["POST"])
def reset_sub_admin_permissions(sub_admin_id):
    """Reset permissions to default for a sub-admin"""
    try:
        if not ObjectId.is_valid(sub_admin_id):
            return jsonify({
                "success": False,
                "message": "Invalid sub-admin ID"
            }), 400
        
        # Check if sub-admin exists
        sub_admin = sub_users.find_one({"_id": ObjectId(sub_admin_id)})
        if not sub_admin:
            return jsonify({
                "success": False,
                "message": "Sub-admin not found"
            }), 404
        
        # Get default permissions for the office
        office = sub_admin.get("office", "")
        default_permissions = get_default_permissions(office)
        
        # Update permissions
        permissions_doc = {
            "sub_admin_id": sub_admin_id,
            "permissions": default_permissions,
            "updated_at": datetime.utcnow()
        }
        
        existing_permissions = permissions_collection.find_one({"sub_admin_id": sub_admin_id})
        if existing_permissions:
            permissions_collection.update_one(
                {"sub_admin_id": sub_admin_id},
                {"$set": permissions_doc}
            )
        else:
            permissions_doc["created_at"] = datetime.utcnow()
            permissions_collection.insert_one(permissions_doc)
        
        return jsonify({
            "success": True,
            "message": "Permissions reset to default successfully",
            "subAdminId": sub_admin_id,
            "permissions": default_permissions
        })
        
    except Exception as e:
        print(f"Error resetting sub-admin permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/sub-admins/search", methods=["GET"])
def search_sub_admins():
    """Search sub-admins by name, email, or office"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({
                "success": False,
                "message": "Search query is required"
            }), 400
        
        # Create search regex
        search_regex = {"$regex": query, "$options": "i"}
        
        # Search in sub-users collection
        sub_admins = list(sub_users.find({
            "role": {"$regex": "sub.*admin", "$options": "i"},
            "$or": [
                {"name": search_regex},
                {"email": search_regex},
                {"office": search_regex}
            ]
        }))
        
        # Get permissions for each sub-admin
        result_sub_admins = []
        for sub_admin in sub_admins:
            sub_admin_id = str(sub_admin["_id"])
            permissions = get_or_create_permissions(sub_admin_id)
            result_sub_admins.append(serialize_sub_admin(sub_admin, permissions))
        
        return jsonify({
            "success": True,
            "message": f"Found {len(result_sub_admins)} sub-admins matching '{query}'",
            "subAdmins": result_sub_admins,
            "query": query
        })
        
    except Exception as e:
        print(f"Error searching sub-admins: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error",
            "subAdmins": []
        }), 500

@roles_bp.route("/bulk-update-permissions", methods=["PUT"])
def bulk_update_permissions():
    """Bulk update permissions for multiple sub-admins"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "message": "No data provided"
            }), 400
        
        updates = data.get("updates", [])
        if not updates or not isinstance(updates, list):
            return jsonify({
                "success": False,
                "message": "Updates must be a list"
            }), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        for update in updates:
            try:
                sub_admin_id = update.get("sub_admin_id")
                permissions = update.get("permissions", {})
                
                if not sub_admin_id or not validate_permissions(permissions):
                    error_count += 1
                    errors.append(f"Invalid data for sub-admin {sub_admin_id}")
                    continue
                
                # Update permissions
                permissions_doc = {
                    "sub_admin_id": sub_admin_id,
                    "permissions": permissions,
                    "updated_at": datetime.utcnow()
                }
                
                existing_permissions = permissions_collection.find_one({"sub_admin_id": sub_admin_id})
                if existing_permissions:
                    permissions_collection.update_one(
                        {"sub_admin_id": sub_admin_id},
                        {"$set": permissions_doc}
                    )
                else:
                    permissions_doc["created_at"] = datetime.utcnow()
                    permissions_collection.insert_one(permissions_doc)
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                errors.append(f"Error updating sub-admin {update.get('sub_admin_id', 'unknown')}: {str(e)}")
        
        return jsonify({
            "success": success_count > 0,
            "message": f"Updated {success_count} sub-admins, {error_count} failed",
            "successCount": success_count,
            "errorCount": error_count,
            "errors": errors
        })
        
    except Exception as e:
        print(f"Error bulk updating permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/default-permissions/<office>", methods=["GET"])
def get_default_permissions_for_office(office):
    """Get default permissions for a specific office"""
    try:
        office = office.replace('%20', ' ')  # URL decode spaces
        default_permissions = get_default_permissions(office)
        
        return jsonify({
            "success": True,
            "office": office,
            "permissions": default_permissions
        })
        
    except Exception as e:
        print(f"Error getting default permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/permission-stats", methods=["GET"])
def get_permission_stats():
    """Get permission statistics"""
    try:
        # Get all permissions
        all_permissions = list(permissions_collection.find())
        
        # Calculate stats
        total_sub_admins = len(all_permissions)
        permission_counts = {}
        
        for permission in AVAILABLE_PERMISSIONS:
            permission_counts[permission] = sum(1 for doc in all_permissions 
                                              if doc.get("permissions", {}).get(permission, False))
        
        # Calculate percentages
        permission_percentages = {}
        for permission, count in permission_counts.items():
            percentage = (count / total_sub_admins * 100) if total_sub_admins > 0 else 0
            permission_percentages[permission] = round(percentage, 1)
        
        return jsonify({
            "success": True,
            "stats": {
                "totalSubAdmins": total_sub_admins,
                "permissionCounts": permission_counts,
                "permissionPercentages": permission_percentages
            }
        })
        
    except Exception as e:
        print(f"Error getting permission stats: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/my-permissions", methods=["GET"])
def get_current_user_permissions():
    """Get current user's permissions (for sub-admin access control)"""
    try:
        from flask import session
        
        # Get current user from session
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "message": "User not authenticated"
            }), 401
        
        # Get permissions for the user
        permissions_doc = permissions_collection.find_one({"sub_admin_id": str(user_id)})
        
        if permissions_doc:
            permissions = permissions_doc.get("permissions", {})
        else:
            # Get default permissions based on office
            user = sub_users.find_one({"_id": ObjectId(user_id)})
            if user:
                office = user.get("office", "")
                permissions = get_default_permissions(office)
            else:
                permissions = {}
        
        return jsonify({
            "success": True,
            "permissions": permissions
        })
        
    except Exception as e:
        print(f"Error getting current user permissions: {e}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500

@roles_bp.route("/check-permission/<feature>", methods=["GET"])
def check_permission(feature):
    """Check if current user has permission for a specific feature"""
    try:
        from flask import session
        
        if feature not in AVAILABLE_PERMISSIONS:
            return jsonify({
                "success": False,
                "hasPermission": False,
                "message": "Invalid feature"
            }), 400
        
        # Get current user from session
        user_id = session.get("user_id")
        if not user_id:
            return jsonify({
                "success": False,
                "hasPermission": False,
                "message": "User not authenticated"
            }), 401
        
        # Get permissions for the user
        permissions_doc = permissions_collection.find_one({"sub_admin_id": str(user_id)})
        
        if permissions_doc:
            permissions = permissions_doc.get("permissions", {})
        else:
            # Get default permissions based on office
            user = sub_users.find_one({"_id": ObjectId(user_id)})
            if user:
                office = user.get("office", "")
                permissions = get_default_permissions(office)
            else:
                permissions = {}
        
        has_permission = permissions.get(feature, False)
        
        return jsonify({
            "success": True,
            "hasPermission": has_permission,
            "feature": feature,
            "permissions": permissions
        })
        
    except Exception as e:
        print(f"Error checking permission: {e}")
        return jsonify({
            "success": False,
            "hasPermission": False,
            "message": "Internal server error"
        }), 500

# Legacy endpoints for backward compatibility
@roles_bp.route("/all", methods=["GET"])
def get_all_roles():
    """Get all roles (legacy endpoint)"""
    try:
        roles = list(roles_collection.find())
        serialized_roles = []
        for role in roles:
            serialized_roles.append({
                "id": str(role["_id"]),
                "office": role.get("office", ""),
                "permissions": role.get("permissions", [])
            })
        return jsonify(serialized_roles)
    except Exception as e:
        print(f"Error getting roles: {e}")
        return jsonify([]), 500

@roles_bp.route("/get/<role_id>", methods=["GET"])
def get_role_by_id(role_id):
    """Get role by ID (legacy endpoint)"""
    try:
        if not ObjectId.is_valid(role_id):
            return jsonify({"success": False, "message": "Invalid role ID"}), 400
        
        role = roles_collection.find_one({"_id": ObjectId(role_id)})
        if not role:
            return jsonify({"success": False, "message": "Role not found"}), 404
        
        return jsonify({
            "id": str(role["_id"]),
            "office": role.get("office", ""),
            "permissions": role.get("permissions", [])
        })
    except Exception as e:
        print(f"Error getting role: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@roles_bp.route("/add", methods=["POST"])
def add_role():
    """Add new role (legacy endpoint)"""
    try:
        data = request.get_json()
        office = data.get("office")
        permissions = data.get("permissions", [])

        if not office or not permissions:
            return jsonify({"success": False, "message": "Office and permissions are required"}), 400

        new_role = {
            "office": office, 
            "permissions": permissions,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        result = roles_collection.insert_one(new_role)

        return jsonify({"success": True, "id": str(result.inserted_id)})
    except Exception as e:
        print(f"Error adding role: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500

@roles_bp.route("/update/<role_id>", methods=["PUT"])
def update_role(role_id):
    """Update role (legacy endpoint)"""
    try:
        if not ObjectId.is_valid(role_id):
            return jsonify({"success": False, "message": "Invalid role ID"}), 400
        
        data = request.get_json()
        data["updated_at"] = datetime.utcnow()
        
        result = roles_collection.update_one(
            {"_id": ObjectId(role_id)},
            {"$set": data}
        )
        if result.modified_count > 0:
            return jsonify({"success": True, "message": "Role updated"})
        return jsonify({"success": False, "message": "No changes made or role not found"}), 400
    except Exception as e:
        print(f"Error updating role: {e}")
        return jsonify({"success": False, "message": "Internal server error"}), 500