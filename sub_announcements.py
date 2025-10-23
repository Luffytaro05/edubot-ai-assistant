#(sub_announcements.py):
from flask import Blueprint, jsonify, request, session
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
from vector_store import VectorStore
import traceback

# Create Blueprint
sub_announcements_bp = Blueprint('sub_announcements', __name__)

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
sub_announcements_collection = db["sub_announcements"]
admin_announcements_collection = db["admin_announcements"]

# Initialize Vector Store
vector_store = VectorStore()

def serialize_announcement(announcement):
    """Convert MongoDB document to JSON-serializable format"""
    if announcement:
        announcement['_id'] = str(announcement['_id'])
        if 'created_at' in announcement:
            announcement['created_at'] = announcement['created_at'].isoformat() if hasattr(announcement['created_at'], 'isoformat') else str(announcement['created_at'])
        if 'updated_at' in announcement:
            announcement['updated_at'] = announcement['updated_at'].isoformat() if hasattr(announcement['updated_at'], 'isoformat') else str(announcement['updated_at'])
    return announcement

@sub_announcements_bp.route('/api/sub-announcements/add', methods=['POST'])
def add_announcement():
    """Add a new announcement to MongoDB and Pinecone"""
    try:
        data = request.json
        
        # Get sub-admin info from session
        office = session.get('office', 'General')
        sub_admin_name = session.get('name', 'Unknown')
        
        # Validate required fields
        required_fields = ['title', 'content', 'startDate', 'endDate', 'priority']
        for field in required_fields:
            if field not in data:
                return jsonify({"success": False, "message": f"Missing required field: {field}"}), 400
        
        title = data.get('title')
        description = data.get('content')  # Note: frontend sends 'content', we treat it as description
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        priority = data.get('priority', 'medium').lower()
        status = data.get('status', 'active')
        
        # Create announcement document for MongoDB
        announcement_doc = {
            "title": title,
            "description": description,
            "start_date": start_date,
            "end_date": end_date,
            "priority": priority,
            "status": status,
            "office": office,
            "created_by": sub_admin_name,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": "sub_admin"
        }
        
        # Save to MongoDB sub_announcements collection
        result = sub_announcements_collection.insert_one(announcement_doc)
        announcement_id = str(result.inserted_id)
        
        print(f"Announcement saved to MongoDB with ID: {announcement_id}")
        
        # Create embedding text for Pinecone (combine all relevant fields)
        embed_text = f"Title: {title}\nDescription: {description}\nOffice: {office}\nPriority: {priority}\nStart Date: {start_date}\nEnd Date: {end_date}"
        
        # Store in Pinecone with metadata
        try:
            metadata = {
                "type": "announcement",
                "intent_type": "announcement",  # For consistency with JSON announcements
                "announcement_id": announcement_id,
                "title": title,
                "description": description,
                "office": office,
                "priority": priority,
                "start_date": start_date,
                "end_date": end_date,
                "status": status,
                "created_by": sub_admin_name,
                "tag": "announcements"  # For chatbot integration
            }
            
            vector_id = vector_store.store_text(embed_text, metadata)
            print(f"Announcement stored in Pinecone with vector ID: {vector_id}")
            
            # Update MongoDB document with vector_id
            sub_announcements_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"vector_id": vector_id}}
            )
            
        except Exception as e:
            print(f"Error storing in Pinecone: {e}")
            print(traceback.format_exc())
            # Continue even if Pinecone fails
        
        # Mirror to admin announcements collection for dashboard visibility
        try:
            admin_announcement_doc = {
                "_id": result.inserted_id,  # Use same ID
                "title": title,
                "description": description,
                "start_date": start_date,
                "end_date": end_date,
                "priority": priority,
                "status": status,
                "office": office,
                "created_by": sub_admin_name,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "source": "sub_admin"
            }
            admin_announcements_collection.insert_one(admin_announcement_doc)
            print(f"Announcement mirrored to admin collection")
        except Exception as e:
            print(f"Error mirroring to admin collection: {e}")
            # Continue even if mirroring fails
        
        return jsonify({
            "success": True,
            "message": "Announcement added successfully and synced to chatbot",
            "announcement_id": announcement_id
        }), 201
        
    except Exception as e:
        print(f"Error adding announcement: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error adding announcement: {str(e)}"}), 500

@sub_announcements_bp.route('/api/sub-announcements/list', methods=['GET'])
def list_announcements():
    """Get all announcements for the current sub-admin's office"""
    try:
        office = session.get('office', 'General')
        
        # Get all announcements for this office
        announcements = list(sub_announcements_collection.find({"office": office}).sort("created_at", -1))
        
        # Serialize announcements
        for announcement in announcements:
            serialize_announcement(announcement)
        
        return jsonify({
            "success": True,
            "announcements": announcements
        }), 200
        
    except Exception as e:
        print(f"Error listing announcements: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error listing announcements: {str(e)}"}), 500

@sub_announcements_bp.route('/api/sub-announcements/get/<announcement_id>', methods=['GET'])
def get_announcement(announcement_id):
    """Get a specific announcement by ID"""
    try:
        announcement = sub_announcements_collection.find_one({"_id": ObjectId(announcement_id)})
        
        if not announcement:
            return jsonify({"success": False, "message": "Announcement not found"}), 404
        
        serialize_announcement(announcement)
        
        return jsonify({
            "success": True,
            "announcement": announcement
        }), 200
        
    except Exception as e:
        print(f"Error getting announcement: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error getting announcement: {str(e)}"}), 500

@sub_announcements_bp.route('/api/sub-announcements/update/<announcement_id>', methods=['PUT'])
def update_announcement(announcement_id):
    """Update an existing announcement"""
    try:
        data = request.json
        office = session.get('office', 'General')
        
        # Check if announcement exists and belongs to this office
        existing = sub_announcements_collection.find_one({"_id": ObjectId(announcement_id), "office": office})
        
        if not existing:
            return jsonify({"success": False, "message": "Announcement not found or access denied"}), 404
        
        # Update fields
        update_doc = {
            "title": data.get('title', existing['title']),
            "description": data.get('content', existing['description']),
            "start_date": data.get('startDate', existing['start_date']),
            "end_date": data.get('endDate', existing['end_date']),
            "priority": data.get('priority', existing['priority']).lower(),
            "status": data.get('status', existing['status']),
            "updated_at": datetime.utcnow()
        }
        
        # Update in MongoDB
        sub_announcements_collection.update_one(
            {"_id": ObjectId(announcement_id)},
            {"$set": update_doc}
        )
        
        # Update in Pinecone if vector_id exists
        if 'vector_id' in existing and existing['vector_id']:
            try:
                # Delete old vector
                vector_store.index.delete(ids=[existing['vector_id']])
                
                # Create new embedding
                embed_text = f"Title: {update_doc['title']}\nDescription: {update_doc['description']}\nOffice: {office}\nPriority: {update_doc['priority']}\nStart Date: {update_doc['start_date']}\nEnd Date: {update_doc['end_date']}"
                
                metadata = {
                    "type": "announcement",
                    "intent_type": "announcement",  # For consistency with JSON announcements
                    "announcement_id": announcement_id,
                    "title": update_doc['title'],
                    "description": update_doc['description'],
                    "office": office,
                    "priority": update_doc['priority'],
                    "start_date": update_doc['start_date'],
                    "end_date": update_doc['end_date'],
                    "status": update_doc['status'],
                    "tag": "announcements"
                }
                
                new_vector_id = vector_store.store_text(embed_text, metadata)
                
                # Update vector_id in MongoDB
                sub_announcements_collection.update_one(
                    {"_id": ObjectId(announcement_id)},
                    {"$set": {"vector_id": new_vector_id}}
                )
                
            except Exception as e:
                print(f"Error updating Pinecone: {e}")
        
        # Update in admin collection
        try:
            admin_announcements_collection.update_one(
                {"_id": ObjectId(announcement_id)},
                {"$set": update_doc}
            )
        except Exception as e:
            print(f"Error updating admin collection: {e}")
        
        return jsonify({
            "success": True,
            "message": "Announcement updated successfully"
        }), 200
        
    except Exception as e:
        print(f"Error updating announcement: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error updating announcement: {str(e)}"}), 500

@sub_announcements_bp.route('/api/sub-announcements/delete/<announcement_id>', methods=['DELETE'])
def delete_announcement(announcement_id):
    """Delete an announcement"""
    try:
        office = session.get('office', 'General')
        
        # Check if announcement exists and belongs to this office
        existing = sub_announcements_collection.find_one({"_id": ObjectId(announcement_id), "office": office})
        
        if not existing:
            return jsonify({"success": False, "message": "Announcement not found or access denied"}), 404
        
        # Delete from Pinecone if vector_id exists
        if 'vector_id' in existing and existing['vector_id']:
            try:
                vector_store.index.delete(ids=[existing['vector_id']])
                print(f"Deleted vector from Pinecone: {existing['vector_id']}")
            except Exception as e:
                print(f"Error deleting from Pinecone: {e}")
        
        # Delete from MongoDB
        sub_announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
        
        # Delete from admin collection
        try:
            admin_announcements_collection.delete_one({"_id": ObjectId(announcement_id)})
        except Exception as e:
            print(f"Error deleting from admin collection: {e}")
        
        return jsonify({
            "success": True,
            "message": "Announcement deleted successfully"
        }), 200
        
    except Exception as e:
        print(f"Error deleting announcement: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error deleting announcement: {str(e)}"}), 500

