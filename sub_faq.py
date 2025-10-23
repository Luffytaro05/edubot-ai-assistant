"""
Sub Admin FAQ Management Module
Handles FAQ operations for Sub-Admins with MongoDB and Pinecone integration
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Blueprint, request, jsonify, session
from pymongo import MongoClient
from bson import ObjectId
from vector_store import VectorStore
import traceback
from functools import wraps

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
sub_faqs_collection = db["sub_faqs"]  # Sub-admin specific FAQs
faqs_collection = db["faqs"]  # Admin FAQ collection (for mirroring)
sub_faq_versions_collection = db["sub_faq_versions"]  # Version history for sub-admin FAQs
sub_system_logs_collection = db["sub_system_logs"]  # System logs for sub-admin actions

# Initialize vector store
vector_store = VectorStore()

# Create Blueprint
sub_faq_bp = Blueprint('sub_faq', __name__)

def require_sub_admin_auth(f):
    """Decorator to require sub-admin authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not (session.get("role") == "sub-admin" and session.get("office")):
            return jsonify({
                'success': False,
                'message': 'Sub-admin authentication required'
            }), 401
        return f(*args, **kwargs)
    return decorated

def save_sub_faq_version(faq_id: str, edited_by: str = "sub-admin") -> Dict[str, Any]:
    """
    Save current sub-admin FAQ version to version history before updating
    
    Args:
        faq_id: FAQ ID to save version for
        edited_by: Username of the person editing
        
    Returns:
        Dictionary with success status and version number
    """
    try:
        # Get current FAQ data
        current_faq = sub_faqs_collection.find_one({'_id': ObjectId(faq_id)})
        
        if not current_faq:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        # Get the latest version number for this FAQ
        latest_version = sub_faq_versions_collection.find_one(
            {'faq_id': faq_id},
            sort=[('version_number', -1)]
        )
        
        version_number = 1
        if latest_version:
            version_number = latest_version['version_number'] + 1
        
        # Create version document
        version_doc = {
            'faq_id': faq_id,
            'version_number': version_number,
            'office': current_faq.get('office'),
            'question': current_faq.get('question'),
            'answer': current_faq.get('answer'),
            'status': current_faq.get('status'),
            'edited_by': edited_by,
            'timestamp': datetime.utcnow()
        }
        
        # Insert version
        sub_faq_versions_collection.insert_one(version_doc)
        
        print(f"✅ Saved version {version_number} for Sub-FAQ {faq_id}")
        
        return {
            'success': True,
            'version_number': version_number
        }
        
    except Exception as e:
        print(f"Error saving Sub-FAQ version: {e}")
        return {
            'success': False,
            'message': f'Error saving version: {str(e)}'
        }

def get_sub_faq_versions(faq_id: str) -> Dict[str, Any]:
    """
    Get version history for a specific sub-admin FAQ
    
    Args:
        faq_id: FAQ ID
        
    Returns:
        Dictionary with success status and versions list
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return {
                'success': False,
                'message': 'Invalid FAQ ID',
                'versions': []
            }
        
        # Get all versions for this FAQ, sorted by version number (newest first)
        versions = list(sub_faq_versions_collection.find(
            {'faq_id': faq_id}
        ).sort('version_number', -1))
        
        # Convert ObjectId to string and format timestamps
        for version in versions:
            if '_id' in version:
                version['_id'] = str(version['_id'])
            if 'timestamp' in version:
                version['timestamp'] = version['timestamp'].isoformat()
        
        return {
            'success': True,
            'versions': versions,
            'total': len(versions)
        }
        
    except Exception as e:
        print(f"Error getting Sub-FAQ versions: {e}")
        return {
            'success': False,
            'message': f'Error getting versions: {str(e)}',
            'versions': []
        }

def rollback_sub_faq(faq_id: str, version_number: int, subadmin_user: str = "sub-admin") -> Dict[str, Any]:
    """
    Rollback sub-admin FAQ to a previous version
    
    Args:
        faq_id: FAQ ID to rollback
        version_number: Version number to restore
        subadmin_user: Username performing the rollback
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return {
                'success': False,
                'message': 'Invalid FAQ ID'
            }
        
        # Get the specified version
        version = sub_faq_versions_collection.find_one({
            'faq_id': faq_id,
            'version_number': version_number
        })
        
        if not version:
            return {
                'success': False,
                'message': f'Version {version_number} not found'
            }
        
        # Save current state before rollback (as a new version)
        save_result = save_sub_faq_version(faq_id, f"{subadmin_user} (before rollback)")
        if not save_result['success']:
            print(f"Warning: Could not save current state before rollback")
        
        # Prepare rollback data
        rollback_data = {
            'office': version.get('office'),
            'question': version.get('question'),
            'answer': version.get('answer'),
            'status': version.get('status'),
            'updated_at': datetime.utcnow()
        }
        
        # Update FAQ in sub_faqs collection
        result = sub_faqs_collection.update_one(
            {'_id': ObjectId(faq_id)},
            {'$set': rollback_data}
        )
        
        if result.matched_count == 0:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        # Also update in main faqs collection if it exists there
        faqs_collection.update_one(
            {'_id': ObjectId(faq_id)},
            {'$set': rollback_data}
        )
        
        print(f"✅ Rolled back Sub-FAQ {faq_id} to version {version_number}")
        
        # Update in Pinecone
        if vector_store.index:
            try:
                combined_text = f"{rollback_data['question']} {rollback_data['answer']}"
                embedding = vector_store.embedding_model.encode(combined_text)
                
                metadata = {
                    'faq_id': faq_id,
                    'office': rollback_data['office'],
                    'question': rollback_data['question'],
                    'answer': rollback_data['answer'],
                    'status': rollback_data['status'],
                    'type': 'faq'
                }
                
                vector_store.index.upsert(
                    vectors=[{
                        'id': faq_id,
                        'values': embedding.tolist(),
                        'metadata': metadata
                    }]
                )
                
                print(f"Sub-FAQ vector updated in Pinecone after rollback")
                
            except Exception as e:
                print(f"Error updating vector after rollback: {e}")
        
        # Log the rollback action
        try:
            log_entry = {
                'action': 'sub_faq_rollback',
                'faq_id': faq_id,
                'version_restored': version_number,
                'subadmin': subadmin_user,
                'timestamp': datetime.utcnow(),
                'details': {
                    'question': rollback_data['question'],
                    'office': rollback_data['office']
                }
            }
            sub_system_logs_collection.insert_one(log_entry)
            print(f"✅ Sub-FAQ rollback action logged")
        except Exception as e:
            print(f"Warning: Could not log rollback action: {e}")
        
        return {
            'success': True,
            'message': f'Successfully rolled back to version {version_number}'
        }
        
    except Exception as e:
        print(f"Error rolling back Sub-FAQ: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': f'Error rolling back FAQ: {str(e)}'
        }

@sub_faq_bp.route('/api/sub-faq/list', methods=['GET'])
@require_sub_admin_auth
def get_sub_faqs():
    """
    Get all FAQs for the current sub-admin's office
    """
    try:
        office = session.get("office")
        
        # Get FAQs from sub_faqs collection filtered by office
        query = {"office": office}
        faqs = list(sub_faqs_collection.find(query).sort('created_at', -1))
        
        # Convert ObjectId to string for JSON serialization
        for faq in faqs:
            faq['_id'] = str(faq['_id'])
            # Convert datetime to ISO string
            if 'created_at' in faq:
                faq['created_at'] = faq['created_at'].isoformat()
            if 'updated_at' in faq:
                faq['updated_at'] = faq['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'faqs': faqs,
            'office': office
        })
        
    except Exception as e:
        print(f"Error getting sub-admin FAQs: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error getting FAQs: {str(e)}',
            'faqs': []
        }), 500

@sub_faq_bp.route('/api/sub-faq/add', methods=['POST'])
@require_sub_admin_auth
def add_sub_faq():
    """
    Add a new FAQ from Sub-Admin
    Stores in both MongoDB (sub_faqs and faqs) and Pinecone
    """
    try:
        data = request.get_json()
        office = session.get("office")
        user_name = session.get("name", "Sub Admin")
        
        # Validate required fields
        if not data.get('question') or not data.get('answer'):
            return jsonify({
                'success': False,
                'message': 'Question and answer are required'
            }), 400
        
        # Prepare FAQ document for MongoDB
        faq_doc = {
            'office': office,
            'question': data['question'].strip(),
            'answer': data['answer'].strip(),
            'status': data.get('status', 'published'),
            'source': 'sub_admin',
            'created_by': user_name,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Insert into sub_faqs collection
        result = sub_faqs_collection.insert_one(faq_doc.copy())
        faq_id = str(result.inserted_id)
        
        print(f"FAQ inserted into sub_faqs collection with ID: {faq_id}")
        
        # Mirror to admin faqs collection for centralized monitoring
        try:
            admin_faq_doc = faq_doc.copy()
            admin_faq_doc['_id'] = ObjectId(faq_id)  # Use same ID for tracking
            faqs_collection.insert_one(admin_faq_doc)
            print(f"FAQ mirrored to admin faqs collection with ID: {faq_id}")
        except Exception as mirror_error:
            print(f"Warning: Could not mirror to admin collection: {mirror_error}")
            # Continue even if mirroring fails
        
        # Create embedding and store in Pinecone
        if vector_store.index:
            try:
                # Combine question and answer for embedding
                combined_text = f"{data['question']} {data['answer']}"
                
                # Generate embedding
                embedding = vector_store.embedding_model.encode(combined_text)
                
                # Prepare metadata for Pinecone
                metadata = {
                    'faq_id': faq_id,
                    'office': office,
                    'question': data['question'].strip(),
                    'answer': data['answer'].strip(),
                    'status': data.get('status', 'published'),
                    'type': 'faq',
                    'source': 'sub_admin',
                    'created_by': user_name
                }
                
                # Upsert to Pinecone
                vector_store.index.upsert(
                    vectors=[{
                        'id': faq_id,
                        'values': embedding.tolist(),
                        'metadata': metadata
                    }]
                )
                
                print(f"FAQ vector stored in Pinecone with ID: {faq_id}")
                
            except Exception as e:
                print(f"Error storing FAQ in Pinecone: {e}")
                print(traceback.format_exc())
                # Don't fail the whole operation if Pinecone fails
        else:
            print("Warning: Pinecone not available, FAQ not indexed for search")
        
        return jsonify({
            'success': True,
            'message': 'FAQ added successfully and synced to chatbot',
            'faq_id': faq_id
        }), 201
        
    except Exception as e:
        print(f"Error adding sub-admin FAQ: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error adding FAQ: {str(e)}'
        }), 500

@sub_faq_bp.route('/api/sub-faq/<faq_id>', methods=['GET'])
@require_sub_admin_auth
def get_sub_faq(faq_id):
    """
    Get a specific FAQ by ID
    """
    try:
        office = session.get("office")
        
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return jsonify({
                'success': False,
                'message': 'Invalid FAQ ID'
            }), 400
        
        # Get FAQ from sub_faqs collection, verify it belongs to this office
        faq = sub_faqs_collection.find_one({
            '_id': ObjectId(faq_id),
            'office': office
        })
        
        if not faq:
            return jsonify({
                'success': False,
                'message': 'FAQ not found or access denied'
            }), 404
        
        # Convert ObjectId to string
        faq['_id'] = str(faq['_id'])
        
        # Convert datetime to ISO string
        if 'created_at' in faq:
            faq['created_at'] = faq['created_at'].isoformat()
        if 'updated_at' in faq:
            faq['updated_at'] = faq['updated_at'].isoformat()
        
        return jsonify({
            'success': True,
            'faq': faq
        })
        
    except Exception as e:
        print(f"Error getting FAQ: {e}")
        return jsonify({
            'success': False,
            'message': f'Error getting FAQ: {str(e)}'
        }), 500

@sub_faq_bp.route('/api/sub-faq/<faq_id>', methods=['PUT'])
@require_sub_admin_auth
def update_sub_faq(faq_id):
    """
    Update an existing FAQ
    Updates in both MongoDB (sub_faqs and faqs) and Pinecone
    """
    try:
        office = session.get("office")
        data = request.get_json()
        
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return jsonify({
                'success': False,
                'message': 'Invalid FAQ ID'
            }), 400
        
        # Check if FAQ exists and belongs to this office
        existing_faq = sub_faqs_collection.find_one({
            '_id': ObjectId(faq_id),
            'office': office
        })
        
        if not existing_faq:
            return jsonify({
                'success': False,
                'message': 'FAQ not found or access denied'
            }), 404
        
        # Save current version before updating
        user_name = session.get("name", "sub-admin")
        version_result = save_sub_faq_version(faq_id, user_name)
        if not version_result['success']:
            print(f"Warning: Could not save version: {version_result.get('message')}")
        
        # Prepare update data
        update_data = {
            'updated_at': datetime.utcnow()
        }
        
        if 'question' in data:
            update_data['question'] = data['question'].strip()
        if 'answer' in data:
            update_data['answer'] = data['answer'].strip()
        if 'status' in data:
            update_data['status'] = data['status']
        
        # Update in sub_faqs collection
        sub_faqs_collection.update_one(
            {'_id': ObjectId(faq_id)},
            {'$set': update_data}
        )
        
        # Update in admin faqs collection
        try:
            faqs_collection.update_one(
                {'_id': ObjectId(faq_id)},
                {'$set': update_data}
            )
        except Exception as mirror_error:
            print(f"Warning: Could not update admin collection: {mirror_error}")
        
        print(f"FAQ updated in MongoDB with ID: {faq_id}")
        
        # Update in Pinecone if question or answer changed
        if vector_store.index and ('question' in update_data or 'answer' in update_data):
            try:
                # Get the updated FAQ
                updated_faq = sub_faqs_collection.find_one({'_id': ObjectId(faq_id)})
                
                # Combine question and answer for embedding
                combined_text = f"{updated_faq['question']} {updated_faq['answer']}"
                
                # Generate new embedding
                embedding = vector_store.embedding_model.encode(combined_text)
                
                # Prepare updated metadata
                metadata = {
                    'faq_id': faq_id,
                    'office': office,
                    'question': updated_faq['question'],
                    'answer': updated_faq['answer'],
                    'status': updated_faq.get('status', 'published'),
                    'type': 'faq',
                    'source': 'sub_admin',
                    'created_by': updated_faq.get('created_by', 'Sub Admin')
                }
                
                # Update in Pinecone
                vector_store.index.upsert(
                    vectors=[{
                        'id': faq_id,
                        'values': embedding.tolist(),
                        'metadata': metadata
                    }]
                )
                
                print(f"FAQ vector updated in Pinecone with ID: {faq_id}")
                
            except Exception as e:
                print(f"Error updating FAQ in Pinecone: {e}")
                print(traceback.format_exc())
        
        return jsonify({
            'success': True,
            'message': 'FAQ updated successfully'
        })
        
    except Exception as e:
        print(f"Error updating FAQ: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error updating FAQ: {str(e)}'
        }), 500

@sub_faq_bp.route('/api/sub-faq/<faq_id>', methods=['DELETE'])
@require_sub_admin_auth
def delete_sub_faq(faq_id):
    """
    Delete an FAQ
    Deletes from both MongoDB (sub_faqs and faqs) and Pinecone
    """
    try:
        office = session.get("office")
        
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return jsonify({
                'success': False,
                'message': 'Invalid FAQ ID'
            }), 400
        
        # Check if FAQ exists and belongs to this office
        existing_faq = sub_faqs_collection.find_one({
            '_id': ObjectId(faq_id),
            'office': office
        })
        
        if not existing_faq:
            return jsonify({
                'success': False,
                'message': 'FAQ not found or access denied'
            }), 404
        
        # Delete from sub_faqs collection
        sub_faqs_collection.delete_one({'_id': ObjectId(faq_id)})
        
        # Delete from admin faqs collection
        try:
            faqs_collection.delete_one({'_id': ObjectId(faq_id)})
        except Exception as mirror_error:
            print(f"Warning: Could not delete from admin collection: {mirror_error}")
        
        print(f"FAQ deleted from MongoDB with ID: {faq_id}")
        
        # Delete from Pinecone
        if vector_store.index:
            try:
                vector_store.index.delete(ids=[faq_id])
                print(f"FAQ vector deleted from Pinecone with ID: {faq_id}")
            except Exception as e:
                print(f"Error deleting FAQ from Pinecone: {e}")
        
        return jsonify({
            'success': True,
            'message': 'FAQ deleted successfully'
        })
        
    except Exception as e:
        print(f"Error deleting FAQ: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error deleting FAQ: {str(e)}'
        }), 500

@sub_faq_bp.route('/api/sub-faq/search', methods=['POST'])
@require_sub_admin_auth
def search_sub_faqs():
    """
    Search FAQs using vector similarity for the current office
    """
    try:
        data = request.get_json()
        office = session.get("office")
        
        if not data or not data.get('query'):
            return jsonify({
                'success': False,
                'message': 'Query is required'
            }), 400
        
        query = data.get('query')
        top_k = data.get('top_k', 5)
        
        if not vector_store.index:
            return jsonify({
                'success': False,
                'message': 'Vector search not available',
                'results': []
            }), 503
        
        # Generate query embedding
        query_embedding = vector_store.embedding_model.encode(query)
        
        # Prepare filter for office
        filter_dict = {
            'type': 'faq',
            'office': office
        }
        
        # Search in Pinecone
        search_results = vector_store.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )
        
        # Format results
        results = []
        for match in search_results.matches:
            results.append({
                'id': match.id,
                'score': match.score,
                'question': match.metadata.get('question', ''),
                'answer': match.metadata.get('answer', ''),
                'office': match.metadata.get('office', ''),
                'status': match.metadata.get('status', 'published')
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'query': query,
            'office': office
        })
        
    except Exception as e:
        print(f"Error searching FAQs: {e}")
        print(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'Error searching FAQs: {str(e)}',
            'results': []
        }), 500

@sub_faq_bp.route('/api/sub-faq/<faq_id>/versions', methods=['GET'])
@require_sub_admin_auth
def get_sub_faq_versions_route(faq_id):
    """Get version history for a specific sub-admin FAQ"""
    try:
        office = session.get("office")
        
        # Verify FAQ belongs to this office
        faq = sub_faqs_collection.find_one({
            '_id': ObjectId(faq_id),
            'office': office
        })
        
        if not faq:
            return jsonify({
                'success': False,
                'message': 'FAQ not found or access denied',
                'versions': []
            }), 404
        
        result = get_sub_faq_versions(faq_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_sub_faq_versions_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'versions': []
        }), 500

@sub_faq_bp.route('/api/sub-faq/<faq_id>/rollback/<int:version_number>', methods=['POST'])
@require_sub_admin_auth
def rollback_sub_faq_route(faq_id, version_number):
    """Rollback sub-admin FAQ to a previous version"""
    try:
        office = session.get("office")
        user_name = session.get("name", "sub-admin")
        
        # Verify FAQ belongs to this office
        faq = sub_faqs_collection.find_one({
            '_id': ObjectId(faq_id),
            'office': office
        })
        
        if not faq:
            return jsonify({
                'success': False,
                'message': 'FAQ not found or access denied'
            }), 404
        
        result = rollback_sub_faq(faq_id, version_number, user_name)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in rollback_sub_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
