import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pymongo import MongoClient
from bson import ObjectId
from vector_store import VectorStore
import traceback

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
faqs_collection = db["faqs"]
sub_faqs_collection = db["sub_faqs"]  # Sub-admin FAQs collection
faq_versions_collection = db["faq_versions"]  # Version history collection
system_logs_collection = db["system_logs"]  # System logs for audit trail

# Initialize vector store
vector_store = VectorStore()

def add_faq(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a new FAQ to both MongoDB and Pinecone
    
    Args:
        data: Dictionary containing office, question, answer, status
        
    Returns:
        Dictionary with success status and message
    """
    try:
        # Validate required fields
        required_fields = ['office', 'question', 'answer']
        for field in required_fields:
            if not data.get(field):
                return {
                    'success': False,
                    'message': f'Missing required field: {field}'
                }
        
        # Prepare FAQ document for MongoDB
        faq_doc = {
            'office': data['office'],
            'question': data['question'],
            'answer': data['answer'],
            'status': data.get('status', 'published'),
            'created_at': datetime.today(),
            'updated_at': datetime.today()
        }
        
        # Insert into MongoDB
        result = faqs_collection.insert_one(faq_doc)
        faq_id = str(result.inserted_id)
        
        print(f"FAQ inserted into MongoDB with ID: {faq_id}")
        
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
                    'office': data['office'],
                    'question': data['question'],
                    'answer': data['answer'],
                    'status': data.get('status', 'published'),
                    'type': 'faq'
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
                # The FAQ is still saved in MongoDB
        
        return {
            'success': True,
            'message': 'FAQ added successfully',
            'faq_id': faq_id
        }
        
    except Exception as e:
        print(f"Error adding FAQ: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': f'Error adding FAQ: {str(e)}'
        }

def get_faqs(office: Optional[str] = None) -> Dict[str, Any]:
    """
    Get FAQs from MongoDB (includes both admin and sub-admin FAQs)
    
    Args:
        office: Optional office filter
        
    Returns:
        Dictionary with success status and FAQs list
    """
    try:
        # Build query
        query = {}
        if office and office != 'all':
            query['office'] = office
        
        # Get FAQs from admin collection
        admin_faqs = list(faqs_collection.find(query).sort('created_at', -1))
        
        # Get FAQs from sub-admin collection
        sub_faqs = list(sub_faqs_collection.find(query).sort('created_at', -1))
        
        # Combine both lists - use a dict to avoid duplicates (based on _id)
        faqs_dict = {}
        
        # Add admin FAQs
        for faq in admin_faqs:
            faq_id = str(faq['_id'])
            if faq_id not in faqs_dict:
                faq['_id'] = faq_id
                faq['source'] = faq.get('source', 'admin')  # Mark source
                # Convert datetime to ISO string
                if 'created_at' in faq:
                    faq['created_at'] = faq['created_at'].isoformat()
                if 'updated_at' in faq:
                    faq['updated_at'] = faq['updated_at'].isoformat()
                faqs_dict[faq_id] = faq
        
        # Add sub-admin FAQs (if not already added from admin collection)
        for faq in sub_faqs:
            faq_id = str(faq['_id'])
            if faq_id not in faqs_dict:
                faq['_id'] = faq_id
                faq['source'] = 'sub_admin'  # Mark as sub-admin source
                # Convert datetime to ISO string
                if 'created_at' in faq:
                    faq['created_at'] = faq['created_at'].isoformat()
                if 'updated_at' in faq:
                    faq['updated_at'] = faq['updated_at'].isoformat()
                faqs_dict[faq_id] = faq
        
        # Convert dict back to list and sort by created_at (descending)
        faqs = list(faqs_dict.values())
        faqs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            'success': True,
            'faqs': faqs
        }
        
    except Exception as e:
        print(f"Error getting FAQs: {e}")
        return {
            'success': False,
            'message': f'Error getting FAQs: {str(e)}',
            'faqs': []
        }

def save_faq_version(faq_id: str, edited_by: str = "admin") -> Dict[str, Any]:
    """
    Save current FAQ version to version history before updating
    
    Args:
        faq_id: FAQ ID to save version for
        edited_by: Username of the person editing
        
    Returns:
        Dictionary with success status and version number
    """
    try:
        # Get current FAQ data
        current_faq = faqs_collection.find_one({'_id': ObjectId(faq_id)})
        
        if not current_faq:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        # Get the latest version number for this FAQ
        latest_version = faq_versions_collection.find_one(
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
        faq_versions_collection.insert_one(version_doc)
        
        print(f"✅ Saved version {version_number} for FAQ {faq_id}")
        
        return {
            'success': True,
            'version_number': version_number
        }
        
    except Exception as e:
        print(f"Error saving FAQ version: {e}")
        return {
            'success': False,
            'message': f'Error saving version: {str(e)}'
        }

def update_faq(faq_id: str, data: Dict[str, Any], edited_by: str = "admin") -> Dict[str, Any]:
    """
    Update an existing FAQ in both MongoDB and Pinecone
    Saves previous version before updating
    
    Args:
        faq_id: FAQ ID to update
        data: Updated FAQ data
        edited_by: Username of the person editing
        
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
        
        # Save current version before updating
        version_result = save_faq_version(faq_id, edited_by)
        if not version_result['success']:
            print(f"Warning: Could not save version: {version_result.get('message')}")
        
        # Prepare update data
        update_data = {
            'office': data.get('office'),
            'question': data.get('question'),
            'answer': data.get('answer'),
            'status': data.get('status'),
            'updated_at': datetime.utcnow()
        }
        
        # Remove None values
        update_data = {k: v for k, v in update_data.items() if v is not None}
        
        # Update in MongoDB
        result = faqs_collection.update_one(
            {'_id': ObjectId(faq_id)},
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        print(f"FAQ updated in MongoDB with ID: {faq_id}")
        
        # Update in Pinecone if vector store is available
        if vector_store.index and 'question' in update_data and 'answer' in update_data:
            try:
                # Combine question and answer for embedding
                combined_text = f"{update_data['question']} {update_data['answer']}"
                
                # Generate new embedding
                embedding = vector_store.embedding_model.encode(combined_text)
                
                # Prepare updated metadata
                metadata = {
                    'faq_id': faq_id,
                    'office': update_data.get('office', data.get('office')),
                    'question': update_data['question'],
                    'answer': update_data['answer'],
                    'status': update_data.get('status', 'published'),
                    'type': 'faq'
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
                # Don't fail the whole operation if Pinecone fails
        
        return {
            'success': True,
            'message': 'FAQ updated successfully'
        }
        
    except Exception as e:
        print(f"Error updating FAQ: {e}")
        return {
            'success': False,
            'message': f'Error updating FAQ: {str(e)}'
        }

def delete_faq(faq_id: str) -> Dict[str, Any]:
    """
    Delete an FAQ from both MongoDB and Pinecone
    
    Args:
        faq_id: FAQ ID to delete
        
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
        
        # Delete from MongoDB
        result = faqs_collection.delete_one({'_id': ObjectId(faq_id)})
        
        if result.deleted_count == 0:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        print(f"FAQ deleted from MongoDB with ID: {faq_id}")
        
        # Delete from Pinecone if vector store is available
        if vector_store.index:
            try:
                vector_store.index.delete(ids=[faq_id])
                print(f"FAQ vector deleted from Pinecone with ID: {faq_id}")
            except Exception as e:
                print(f"Error deleting FAQ from Pinecone: {e}")
                # Don't fail the whole operation if Pinecone fails
        
        return {
            'success': True,
            'message': 'FAQ deleted successfully'
        }
        
    except Exception as e:
        print(f"Error deleting FAQ: {e}")
        return {
            'success': False,
            'message': f'Error deleting FAQ: {str(e)}'
        }

def search_faqs(query: str, office: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """
    Search FAQs using vector similarity
    
    Args:
        query: Search query
        office: Optional office filter
        top_k: Number of results to return
        
    Returns:
        Dictionary with success status and search results
    """
    try:
        if not vector_store.index:
            return {
                'success': False,
                'message': 'Vector search not available',
                'results': []
            }
        
        # Generate query embedding
        query_embedding = vector_store.embedding_model.encode(query)
        
        # Prepare filter for office if specified
        filter_dict = {'type': 'faq'}
        if office and office != 'all':
            filter_dict['office'] = office
        
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
        
        return {
            'success': True,
            'results': results,
            'query': query
        }
        
    except Exception as e:
        print(f"Error searching FAQs: {e}")
        return {
            'success': False,
            'message': f'Error searching FAQs: {str(e)}',
            'results': []
        }

def get_faq_by_id(faq_id: str) -> Dict[str, Any]:
    """
    Get a specific FAQ by ID
    
    Args:
        faq_id: FAQ ID
        
    Returns:
        Dictionary with success status and FAQ data
    """
    try:
        # Validate ObjectId
        if not ObjectId.is_valid(faq_id):
            return {
                'success': False,
                'message': 'Invalid FAQ ID'
            }
        
        # Get FAQ from MongoDB
        faq = faqs_collection.find_one({'_id': ObjectId(faq_id)})
        
        if not faq:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        # Convert ObjectId to string
        faq['_id'] = str(faq['_id'])
        
        # Convert datetime to ISO string
        if 'created_at' in faq:
            faq['created_at'] = faq['created_at'].isoformat()
        if 'updated_at' in faq:
            faq['updated_at'] = faq['updated_at'].isoformat()
        
        return {
            'success': True,
            'faq': faq
        }
        
    except Exception as e:
        print(f"Error getting FAQ: {e}")
        return {
            'success': False,
            'message': f'Error getting FAQ: {str(e)}'
        }

def get_faq_versions(faq_id: str) -> Dict[str, Any]:
    """
    Get version history for a specific FAQ
    
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
        versions = list(faq_versions_collection.find(
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
        print(f"Error getting FAQ versions: {e}")
        return {
            'success': False,
            'message': f'Error getting versions: {str(e)}',
            'versions': []
        }

def rollback_faq(faq_id: str, version_number: int, admin_user: str = "admin") -> Dict[str, Any]:
    """
    Rollback FAQ to a previous version
    
    Args:
        faq_id: FAQ ID to rollback
        version_number: Version number to restore
        admin_user: Username performing the rollback
        
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
        version = faq_versions_collection.find_one({
            'faq_id': faq_id,
            'version_number': version_number
        })
        
        if not version:
            return {
                'success': False,
                'message': f'Version {version_number} not found'
            }
        
        # Save current state before rollback (as a new version)
        save_result = save_faq_version(faq_id, f"{admin_user} (before rollback)")
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
        
        # Update FAQ in MongoDB
        result = faqs_collection.update_one(
            {'_id': ObjectId(faq_id)},
            {'$set': rollback_data}
        )
        
        if result.matched_count == 0:
            return {
                'success': False,
                'message': 'FAQ not found'
            }
        
        print(f"✅ Rolled back FAQ {faq_id} to version {version_number}")
        
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
                
                print(f"FAQ vector updated in Pinecone after rollback")
                
            except Exception as e:
                print(f"Error updating vector after rollback: {e}")
        
        # Log the rollback action
        try:
            log_entry = {
                'action': 'faq_rollback',
                'faq_id': faq_id,
                'version_restored': version_number,
                'admin': admin_user,
                'timestamp': datetime.utcnow(),
                'details': {
                    'question': rollback_data['question'],
                    'office': rollback_data['office']
                }
            }
            system_logs_collection.insert_one(log_entry)
            print(f"✅ Rollback action logged")
        except Exception as e:
            print(f"Warning: Could not log rollback action: {e}")
        
        return {
            'success': True,
            'message': f'Successfully rolled back to version {version_number}'
        }
        
    except Exception as e:
        print(f"Error rolling back FAQ: {e}")
        print(traceback.format_exc())
        return {
            'success': False,
            'message': f'Error rolling back FAQ: {str(e)}'
        }