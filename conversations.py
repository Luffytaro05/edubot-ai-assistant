"""
conversations.py - MongoDB integration for EduChat conversations functionality
Provides REST API endpoints for managing chatbot conversations with MongoDB backend
"""

from flask import Blueprint, request, jsonify
from pymongo import MongoClient
from datetime import datetime, timedelta
import uuid
from bson import ObjectId
import re
from functools import wraps

# Create Blueprint for conversations
conversations_bp = Blueprint('conversations', __name__)

# MongoDB connection - should match your app.py configuration
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations_collection = db["conversations"]
users_collection = db["users"]

# Utility functions
def serialize_conversation(conversation):
    """Convert MongoDB conversation document to JSON serializable format"""
    if conversation:
        conversation['_id'] = str(conversation['_id'])
        if 'timestamp' in conversation and hasattr(conversation['timestamp'], 'isoformat'):
            conversation['timestamp'] = conversation['timestamp'].isoformat()
        return conversation
    return None

def validate_conversation_data(data):
    """Validate conversation data"""
    required_fields = ['user', 'message', 'response']
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"{field} is required"
    
    if 'user' in data:
        user_required = ['name', 'email']
        for field in user_required:
            if field not in data['user'] or not data['user'][field]:
                return False, f"user.{field} is required"
    
    return True, "Valid"

def token_required_conversations(f):
    """Decorator to require valid JWT token for conversation endpoints"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Import here to avoid circular imports
        from app import token_required as app_token_required
        return app_token_required(f)(*args, **kwargs)
    return decorated

# ===========================
# CONVERSATION API ENDPOINTS
# ===========================

@conversations_bp.route('/api/conversations', methods=['GET'])
@token_required_conversations
def get_conversations(current_user):
    """Get all conversations with filtering and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        search = request.args.get('search', '')
        sentiment = request.args.get('sentiment', '')
        status = request.args.get('status', '')
        user_type = request.args.get('user_type', '')
        date_range = request.args.get('date_range', '')
        start_date = request.args.get('start_date', '')
        end_date = request.args.get('end_date', '')
        
        # Build MongoDB query
        query = {}
        
        # Search filter
        if search:
            query['$or'] = [
                {'user.name': {'$regex': search, '$options': 'i'}},
                {'user.email': {'$regex': search, '$options': 'i'}},
                {'message': {'$regex': search, '$options': 'i'}},
                {'response': {'$regex': search, '$options': 'i'}},
                {'department': {'$regex': search, '$options': 'i'}}
            ]
        
        # Sentiment filter
        if sentiment:
            query['sentiment'] = {'$regex': f'^{sentiment}$', '$options': 'i'}
        
        # Status filter
        if status:
            query['status'] = {'$regex': f'^{status}$', '$options': 'i'}
        
        # User type filter
        if user_type:
            query['user.type'] = {'$regex': f'^{user_type}$', '$options': 'i'}
        
        # Date range filter
        if date_range or (start_date and end_date):
            date_filter = {}
            
            if date_range:
                now = datetime.now()
                if date_range == 'today':
                    start = datetime(now.year, now.month, now.day)
                elif date_range == 'week':
                    start = now - timedelta(days=7)
                elif date_range == 'month':
                    start = datetime(now.year, now.month, 1)
                elif date_range == 'quarter':
                    quarter_start = (now.month - 1) // 3 * 3 + 1
                    start = datetime(now.year, quarter_start, 1)
                elif date_range == 'year':
                    start = datetime(now.year, 1, 1)
                else:
                    start = None
                
                if start:
                    date_filter['$gte'] = start
            
            if start_date and end_date:
                date_filter['$gte'] = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                date_filter['$lte'] = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            
            if date_filter:
                query['timestamp'] = date_filter
        
        # Role-based filtering for sub-admins
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office:
                query['department'] = office
        
        # Get total count
        total = conversations_collection.count_documents(query)
        
        # Calculate pagination
        skip = (page - 1) * per_page
        
        # Get conversations
        conversations = list(conversations_collection.find(query)
                           .sort('timestamp', -1)
                           .skip(skip)
                           .limit(per_page))
        
        # Serialize conversations
        serialized_conversations = [serialize_conversation(conv) for conv in conversations]
        
        return jsonify({
            'success': True,
            'conversations': serialized_conversations,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            },
            'filters': {
                'search': search,
                'sentiment': sentiment,
                'status': status,
                'user_type': user_type,
                'date_range': date_range
            }
        })
    
    except Exception as e:
        print(f"Error getting conversations: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve conversations',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/<conversation_id>', methods=['GET'])
@token_required_conversations
def get_conversation(current_user, conversation_id):
    """Get a specific conversation by ID"""
    try:
        if not ObjectId.is_valid(conversation_id):
            return jsonify({
                'success': False,
                'message': 'Invalid conversation ID'
            }), 400
        
        conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        
        if not conversation:
            return jsonify({
                'success': False,
                'message': 'Conversation not found'
            }), 404
        
        # Role-based access control
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office and conversation.get('department') != office:
                return jsonify({
                    'success': False,
                    'message': 'Access denied'
                }), 403
        
        return jsonify({
            'success': True,
            'conversation': serialize_conversation(conversation)
        })
    
    except Exception as e:
        print(f"Error getting conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to retrieve conversation',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations', methods=['POST'])
@token_required_conversations
def create_conversation(current_user):
    """Create a new conversation"""
    try:
        data = request.get_json()
        
        # Validate data
        is_valid, message = validate_conversation_data(data)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400
        
        # Create conversation document
        conversation = {
            'id': str(uuid.uuid4()),  # Keep string ID for compatibility
            'user': {
                'name': data['user']['name'],
                'email': data['user']['email'].lower(),
                'type': data['user'].get('type', 'student')
            },
            'message': data['message'],
            'response': data['response'],
            'sentiment': data.get('sentiment', 'Neutral'),
            'status': data.get('status', 'Resolved'),
            'department': data.get('department', 'General'),
            'timestamp': datetime.now(),
            'created_at': datetime.now(),
            'created_by': current_user['_id']
        }
        
        # Insert conversation
        result = conversations_collection.insert_one(conversation)
        conversation['_id'] = result.inserted_id
        
        return jsonify({
            'success': True,
            'conversation': serialize_conversation(conversation),
            'message': 'Conversation created successfully'
        }), 201
    
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to create conversation',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/<conversation_id>', methods=['PUT'])
@token_required_conversations
def update_conversation(current_user, conversation_id):
    """Update a conversation"""
    try:
        if not ObjectId.is_valid(conversation_id):
            return jsonify({
                'success': False,
                'message': 'Invalid conversation ID'
            }), 400
        
        data = request.get_json()
        
        # Find existing conversation
        conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        if not conversation:
            return jsonify({
                'success': False,
                'message': 'Conversation not found'
            }), 404
        
        # Role-based access control
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office and conversation.get('department') != office:
                return jsonify({
                    'success': False,
                    'message': 'Access denied'
                }), 403
        
        # Prepare update data
        update_data = {}
        allowed_fields = ['sentiment', 'status', 'department', 'message', 'response']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if 'user' in data:
            user_fields = ['name', 'email', 'type']
            for field in user_fields:
                if field in data['user']:
                    update_data[f'user.{field}'] = data['user'][field]
        
        if not update_data:
            return jsonify({
                'success': False,
                'message': 'No valid fields to update'
            }), 400
        
        update_data['updated_at'] = datetime.now()
        update_data['updated_by'] = current_user['_id']
        
        # Update conversation
        conversations_collection.update_one(
            {'_id': ObjectId(conversation_id)},
            {'$set': update_data}
        )
        
        # Get updated conversation
        updated_conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        
        return jsonify({
            'success': True,
            'conversation': serialize_conversation(updated_conversation),
            'message': 'Conversation updated successfully'
        })
    
    except Exception as e:
        print(f"Error updating conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to update conversation',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/<conversation_id>', methods=['DELETE'])
@token_required_conversations
def delete_conversation(current_user, conversation_id):
    """Delete a conversation (admin only)"""
    try:
        # Only admins can delete conversations
        if current_user.get('role') not in ['admin']:
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        if not ObjectId.is_valid(conversation_id):
            return jsonify({
                'success': False,
                'message': 'Invalid conversation ID'
            }), 400
        
        result = conversations_collection.delete_one({'_id': ObjectId(conversation_id)})
        
        if result.deleted_count == 0:
            return jsonify({
                'success': False,
                'message': 'Conversation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Conversation deleted successfully'
        })
    
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to delete conversation',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/<conversation_id>/escalate', methods=['POST'])
@token_required_conversations
def escalate_conversation(current_user, conversation_id):
    """Escalate a conversation"""
    try:
        if not ObjectId.is_valid(conversation_id):
            return jsonify({
                'success': False,
                'message': 'Invalid conversation ID'
            }), 400
        
        # Find conversation
        conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        if not conversation:
            return jsonify({
                'success': False,
                'message': 'Conversation not found'
            }), 404
        
        # Role-based access control
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office and conversation.get('department') != office:
                return jsonify({
                    'success': False,
                    'message': 'Access denied'
                }), 403
        
        # Update status to escalated
        conversations_collection.update_one(
            {'_id': ObjectId(conversation_id)},
            {'$set': {
                'status': 'Escalated',
                'escalated_at': datetime.now(),
                'escalated_by': current_user['_id'],
                'updated_at': datetime.now()
            }}
        )
        
        # Get updated conversation
        updated_conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        
        return jsonify({
            'success': True,
            'conversation': serialize_conversation(updated_conversation),
            'message': 'Conversation escalated successfully'
        })
    
    except Exception as e:
        print(f"Error escalating conversation: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to escalate conversation',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/export', methods=['GET'])
@token_required_conversations
def export_conversations(current_user):
    """Export conversations to CSV"""
    try:
        from io import StringIO
        import csv
        
        # Get conversations based on user role
        query = {}
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office:
                query['department'] = office
        
        conversations = list(conversations_collection.find(query).sort('timestamp', -1))
        
        if not conversations:
            return jsonify({
                'success': False,
                'message': 'No conversations to export'
            }), 404
        
        # Create CSV content
        output = StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'ID', 'User Name', 'User Email', 'User Type', 'Message', 
            'Response', 'Sentiment', 'Status', 'Department', 'Timestamp'
        ])
        
        # Write data
        for conv in conversations:
            writer.writerow([
                conv.get('id', str(conv['_id'])),
                conv['user']['name'],
                conv['user']['email'],
                conv['user'].get('type', 'student'),
                conv['message'],
                conv['response'],
                conv.get('sentiment', 'Neutral'),
                conv.get('status', 'Resolved'),
                conv.get('department', 'General'),
                conv['timestamp'].isoformat() if hasattr(conv['timestamp'], 'isoformat') else str(conv['timestamp'])
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return jsonify({
            'success': True,
            'csv_content': csv_content,
            'filename': f'conversations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        })
    
    except Exception as e:
        print(f"Error exporting conversations: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to export conversations',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/stats', methods=['GET'])
@token_required_conversations
def get_conversation_stats(current_user):
    """Get conversation statistics"""
    try:
        # Base query for role-based filtering
        base_query = {}
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office:
                base_query['department'] = office
        
        # Total conversations
        total = conversations_collection.count_documents(base_query)
        
        # Sentiment statistics
        sentiment_pipeline = [
            {'$match': base_query},
            {'$group': {
                '_id': '$sentiment',
                'count': {'$sum': 1}
            }}
        ]
        sentiment_results = list(conversations_collection.aggregate(sentiment_pipeline))
        sentiment_stats = {result['_id']: result['count'] for result in sentiment_results}
        
        # Status statistics
        status_pipeline = [
            {'$match': base_query},
            {'$group': {
                '_id': '$status',
                'count': {'$sum': 1}
            }}
        ]
        status_results = list(conversations_collection.aggregate(status_pipeline))
        status_stats = {result['_id']: result['count'] for result in status_results}
        
        # User type statistics
        user_type_pipeline = [
            {'$match': base_query},
            {'$group': {
                '_id': '$user.type',
                'count': {'$sum': 1}
            }}
        ]
        user_type_results = list(conversations_collection.aggregate(user_type_pipeline))
        user_type_stats = {result['_id']: result['count'] for result in user_type_results}
        
        # Department statistics
        department_pipeline = [
            {'$match': base_query},
            {'$group': {
                '_id': '$department',
                'count': {'$sum': 1}
            }}
        ]
        department_results = list(conversations_collection.aggregate(department_pipeline))
        department_stats = {result['_id']: result['count'] for result in department_results}
        
        # Recent activity (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_query = {**base_query, 'timestamp': {'$gte': thirty_days_ago}}
        recent_count = conversations_collection.count_documents(recent_query)
        
        stats = {
            'total': total,
            'recent_30_days': recent_count,
            'by_sentiment': {
                'positive': sentiment_stats.get('Positive', 0),
                'neutral': sentiment_stats.get('Neutral', 0),
                'negative': sentiment_stats.get('Negative', 0)
            },
            'by_status': {
                'resolved': status_stats.get('Resolved', 0),
                'pending': status_stats.get('Pending', 0),
                'escalated': status_stats.get('Escalated', 0)
            },
            'by_user_type': {
                'student': user_type_stats.get('student', 0),
                'faculty': user_type_stats.get('faculty', 0),
                'staff': user_type_stats.get('staff', 0)
            },
            'by_department': department_stats
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    
    except Exception as e:
        print(f"Error getting conversation stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get conversation statistics',
            'error': str(e)
        }), 500

@conversations_bp.route('/api/conversations/trends', methods=['GET'])
@token_required_conversations
def get_conversation_trends(current_user):
    """Get conversation trends over time"""
    try:
        period = request.args.get('period', 'week')  # day, week, month
        
        # Base query for role-based filtering
        base_query = {}
        if current_user.get('role') == 'sub-admin':
            office = current_user.get('office')
            if office:
                base_query['department'] = office
        
        # Determine date range
        now = datetime.now()
        if period == 'day':
            days = 7
            date_format = '%Y-%m-%d'
        elif period == 'week':
            days = 30
            date_format = '%Y-W%U'
        else:  # month
            days = 365
            date_format = '%Y-%m'
        
        start_date = now - timedelta(days=days)
        base_query['timestamp'] = {'$gte': start_date}
        
        # Aggregation pipeline for trends
        pipeline = [
            {'$match': base_query},
            {'$group': {
                '_id': {
                    'date': {'$dateToString': {'format': date_format, 'date': '$timestamp'}},
                    'sentiment': '$sentiment'
                },
                'count': {'$sum': 1}
            }},
            {'$sort': {'_id.date': 1}}
        ]
        
        results = list(conversations_collection.aggregate(pipeline))
        
        # Format results
        trends = {}
        for result in results:
            date = result['_id']['date']
            sentiment = result['_id']['sentiment']
            count = result['count']
            
            if date not in trends:
                trends[date] = {'date': date, 'total': 0, 'positive': 0, 'neutral': 0, 'negative': 0}
            
            trends[date]['total'] += count
            trends[date][sentiment.lower()] += count
        
        # Convert to list and sort
        trend_list = list(trends.values())
        trend_list.sort(key=lambda x: x['date'])
        
        return jsonify({
            'success': True,
            'trends': trend_list,
            'period': period
        })
    
    except Exception as e:
        print(f"Error getting conversation trends: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to get conversation trends',
            'error': str(e)
        }), 500

# Initialize sample data (run once)
@conversations_bp.route('/api/conversations/initialize-sample-data', methods=['POST'])
@token_required_conversations
def initialize_sample_data(current_user):
    """Initialize sample conversation data (admin only)"""
    try:
        # Only admins can initialize sample data
        if current_user.get('role') != 'admin':
            return jsonify({
                'success': False,
                'message': 'Admin access required'
            }), 403
        
        # Check if data already exists
        if conversations_collection.count_documents({}) > 0:
            return jsonify({
                'success': False,
                'message': 'Sample data already exists'
            }), 400
        
        # Sample conversations data
        sample_conversations = [
            {
                'id': str(uuid.uuid4()),
                'user': {
                    'name': 'John Doe',
                    'email': 'john.doe@university.edu',
                    'type': 'student'
                },
                'message': 'What are the admission requirements for the Computer Science program?',
                'response': 'To be admitted to the Computer Science program, you need a high school diploma with at least 85% in Mathematics and English, SAT scores of 1200+, and a completed application form. The deadline for Fall 2024 is March 1st.',
                'sentiment': 'Positive',
                'status': 'Resolved',
                'department': 'Admissions Office',
                'timestamp': datetime.now() - timedelta(days=1),
                'created_at': datetime.now()
            },
            {
                'id': str(uuid.uuid4()),
                'user': {
                    'name': 'Sarah Johnson',
                    'email': 'sarah.johnson@university.edu',
                    'type': 'student'
                },
                'message': 'I need help with my course registration. The system keeps showing an error.',
                'response': 'I understand you\'re having trouble with course registration. This could be due to a hold on your account, missing prerequisites, or a system issue. Please check your student portal for any holds, and if the problem persists, contact the Registrar\'s Office directly.',
                'sentiment': 'Negative',
                'status': 'Escalated',
                'department': 'Registrar Office',
                'timestamp': datetime.now() - timedelta(hours=6),
                'created_at': datetime.now()
            },
            {
                'id': str(uuid.uuid4()),
                'user': {
                    'name': 'Michael Chen',
                    'email': 'michael.chen@university.edu',
                    'type': 'student'
                },
                'message': 'When does the library close during exam week?',
                'response': 'During exam week, the library extends its hours and is open from 7:00 AM to 2:00 AM Monday through Friday, and 9:00 AM to 10:00 PM on weekends. Study rooms can be reserved online through the library website.',
                'sentiment': 'Neutral',
                'status': 'Resolved',
                'department': 'Library',
                'timestamp': datetime.now() - timedelta(hours=3),
                'created_at': datetime.now()
            },
            # Add more sample data as needed...
        ]
        
        # Insert sample data
        result = conversations_collection.insert_many(sample_conversations)
        
        return jsonify({
            'success': True,
            'message': f'Successfully initialized {len(result.inserted_ids)} sample conversations',
            'inserted_count': len(result.inserted_ids)
        })
    
    except Exception as e:
        print(f"Error initializing sample data: {e}")
        return jsonify({
            'success': False,
            'message': 'Failed to initialize sample data',
            'error': str(e)
        }), 500