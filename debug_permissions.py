#!/usr/bin/env python3
"""
Debug script to check permissions in the database
"""

from pymongo import MongoClient
from bson import ObjectId
import json

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
sub_users = db["sub_users"]
users_collection = db["users"]
permissions_collection = db["sub_admin_permissions"]

def check_sub_admin_permissions():
    """Check all sub-admin permissions"""
    print("🔍 Debugging Sub-Admin Permissions")
    print("=" * 50)
    
    # Get all sub-admin users
    print("\n1. Sub-Admin Users:")
    sub_admins = list(sub_users.find({"role": {"$regex": "sub.*admin", "$options": "i"}}))
    
    if not sub_admins:
        print("   No sub-admin users found!")
        return
    
    for user in sub_admins:
        user_id = str(user["_id"])
        print(f"\n   📋 User: {user.get('name', 'N/A')} ({user.get('email', 'N/A')})")
        print(f"      ID: {user_id}")
        print(f"      Office: {user.get('office', 'N/A')}")
        print(f"      Active: {user.get('is_active', 'N/A')}")
        
        # Check permissions in database
        permissions_doc = permissions_collection.find_one({"sub_admin_id": user_id})
        if permissions_doc:
            permissions = permissions_doc.get("permissions", {})
            print(f"      Database Permissions: {json.dumps(permissions, indent=8)}")
        else:
            print(f"      Database Permissions: No permissions document found")
            
            # Show what default permissions would be
            office = user.get("office", "")
            default_permissions = get_default_permissions(office)
            print(f"      Default Permissions: {json.dumps(default_permissions, indent=8)}")
    
    # Check permissions collection
    print(f"\n2. Permissions Collection:")
    all_permissions = list(permissions_collection.find())
    print(f"   Total permission documents: {len(all_permissions)}")
    
    for perm_doc in all_permissions:
        print(f"   📄 {perm_doc.get('sub_admin_id')}: {perm_doc.get('permissions', {})}")

def get_default_permissions(office):
    """Get default permissions for an office"""
    default_permissions = {
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
    return default_permissions.get(office, {
        'dashboard': True,
        'conversations': False,
        'faq': False,
        'announcements': False,
        'usage': False,
        'feedback': False
    })

def create_test_permissions():
    """Create test permissions for debugging"""
    print(f"\n3. Creating Test Permissions:")
    
    # Get first sub-admin
    sub_admin = sub_users.find_one({"role": {"$regex": "sub.*admin", "$options": "i"}})
    if not sub_admin:
        print("   No sub-admin found to create test permissions")
        return
    
    user_id = str(sub_admin["_id"])
    office = sub_admin.get("office", "")
    
    # Create test permissions (disable some features)
    test_permissions = {
        'dashboard': True,
        'conversations': False,  # Disable conversations
        'faq': True,
        'announcements': False,  # Disable announcements
        'usage': False,          # Disable usage
        'feedback': True
    }
    
    # Check if permissions document exists
    existing = permissions_collection.find_one({"sub_admin_id": user_id})
    if existing:
        # Update existing
        permissions_collection.update_one(
            {"sub_admin_id": user_id},
            {"$set": {"permissions": test_permissions}}
        )
        print(f"   ✅ Updated permissions for {sub_admin.get('name', 'Unknown')}")
    else:
        # Create new
        permissions_collection.insert_one({
            "sub_admin_id": user_id,
            "permissions": test_permissions
        })
        print(f"   ✅ Created permissions for {sub_admin.get('name', 'Unknown')}")
    
    print(f"   Test permissions: {json.dumps(test_permissions, indent=6)}")

def clear_all_permissions():
    """Clear all permissions to test default behavior"""
    print(f"\n4. Clearing All Permissions:")
    
    result = permissions_collection.delete_many({})
    print(f"   ✅ Deleted {result.deleted_count} permission documents")
    print(f"   Now all users will use default permissions based on their office")

if __name__ == "__main__":
    check_sub_admin_permissions()
    
    print(f"\n" + "=" * 50)
    print("🛠️ Debug Options:")
    print("1. create_test_permissions() - Create test permissions with some disabled")
    print("2. clear_all_permissions() - Clear all permissions to test defaults")
    print("3. check_sub_admin_permissions() - Show current permissions")
    
    # Uncomment the line below to create test permissions
    # create_test_permissions()
    
    # Uncomment the line below to clear all permissions
    # clear_all_permissions()
