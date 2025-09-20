from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
from chat import (get_response, reset_user_context, clear_chat_history, 
                  get_active_announcements, add_announcement, get_announcement_by_id,
                  vector_store)
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from conversations import conversations_bp
from dashboard import init_app
from users import users_bp
import jwt
import os
import time
from functools import wraps
from bson import ObjectId
import re
# In-memory cache for user conversations

app = Flask(__name__)
app.register_blueprint(conversations_bp)
app.register_blueprint(users_bp)
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key-change-this-in-production'  # Change this in production

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
# Fix: Use a different name to avoid conflicts with the route function
conversations_collection = db["conversations"]  # Changed name here
users_collection = db["users"]
sessions_collection = db["sessions"]
init_app(app)

# JWT token expiration time
TOKEN_EXPIRATION_HOURS = 24

# ===========================
# AUTHENTICATION FUNCTIONS
# ===========================

def create_default_admin():
    """Create default admin user if it doesn't exist"""
    admin_user = users_collection.find_one({"email": "dxtrzpc26@gmail.com"})
    if not admin_user:
        admin_data = {
            "email": "dxtrzpc26@gmail.com",
            "password": generate_password_hash("dexterpogi123"),
            "name": "Super Admin",
            "role": "admin",
            "office": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        users_collection.insert_one(admin_data)
        print("Default admin user created")

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'message': 'Token format invalid'}), 401

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user_id = data['user_id']
            current_user = users_collection.find_one({"_id": ObjectId(current_user_id)})
            
            if not current_user or not current_user.get('is_active'):
                return jsonify({'message': 'User not found or inactive'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token is invalid'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated(current_user, *args, **kwargs):
        if current_user.get('role') != 'admin':
            return jsonify({'message': 'Admin access required'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password strength"""
    if len(password) < 6:
        return False, "Password must be at least 6 characters long"
    return True, "Password is valid"

def serialize_user(user):
    """Convert MongoDB user document to JSON serializable format"""
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)  # Remove password from response
        return user
    return None

# ===========================
# AUTHENTICATION API ROUTES
# ===========================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        role = data.get('role', '')
        office = data.get('office', '')

        # Validate input
        if not email or not password or not role:
            return jsonify({
                'success': False,
                'message': 'Email, password, and role are required'
            }), 400

        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        if role == 'sub-admin' and not office:
            return jsonify({
                'success': False,
                'message': 'Office is required for Sub-Admin role'
            }), 400

        # Find user in database
        user = users_collection.find_one({
            "email": email,
            "is_active": True
        })

        if not user:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401

        # Check password
        if not check_password_hash(user['password'], password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401

        # Check role match
        if user['role'] != role:
            return jsonify({
                'success': False,
                'message': 'Invalid role for this user'
            }), 401

        # Check office match for sub-admin
        if role == 'sub-admin' and user.get('office') != office:
            return jsonify({
                'success': False,
                'message': 'Invalid office for this user'
            }), 401

        # Generate JWT token
        token_payload = {
            'user_id': str(user['_id']),
            'email': user['email'],
            'role': user['role'],
            'exp': datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS)
        }
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')

        # Store session in database
        session_data = {
            "user_id": user['_id'],
            "token": token,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRATION_HOURS),
            "user_agent": request.headers.get('User-Agent', ''),
            "ip_address": request.remote_addr
        }
        sessions_collection.insert_one(session_data)

        # Update last login time
        users_collection.update_one(
            {"_id": user['_id']},
            {"$set": {"last_login": datetime.utcnow(), "updated_at": datetime.utcnow()}}
        )

        return jsonify({
            'success': True,
            'user': serialize_user(user),
            'token': token,
            'message': 'Login successful'
        })

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/register', methods=['POST'])
@token_required
@admin_required
def register(current_user):
    try:
        data = request.get_json()
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        name = data.get('name', '').strip()
        role = data.get('role', '')
        office = data.get('office', '')

        # Validate input
        if not email or not password or not name or not role:
            return jsonify({
                'success': False,
                'message': 'Email, password, name, and role are required'
            }), 400

        if not validate_email(email):
            return jsonify({
                'success': False,
                'message': 'Invalid email format'
            }), 400

        is_valid, message = validate_password(password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        if role not in ['admin', 'sub-admin']:
            return jsonify({
                'success': False,
                'message': 'Invalid role'
            }), 400

        if role == 'sub-admin' and not office:
            return jsonify({
                'success': False,
                'message': 'Office is required for Sub-Admin role'
            }), 400

        # Check if user already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'User with this email already exists'
            }), 400

        # Create new user
        user_data = {
            "email": email,
            "password": generate_password_hash(password),
            "name": name,
            "role": role,
            "office": office if role == 'sub-admin' else None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True,
            "created_by": current_user['_id']
        }

        result = users_collection.insert_one(user_data)
        user_data['_id'] = result.inserted_id

        return jsonify({
            'success': True,
            'user': serialize_user(user_data),
            'message': 'User created successfully'
        })

    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/logout', methods=['POST'])
@token_required
def logout(current_user):
    try:
        # Get token from header
        auth_header = request.headers.get('Authorization')
        token = auth_header.split(" ")[1] if auth_header else None

        if token:
            # Remove session tied to this user
            sessions_collection.delete_one({
                "user_id": current_user["_id"],
                "token": token
            })

        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200

    except Exception as e:
        print(f"Logout error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500


@app.route('/api/auth/verify', methods=['POST'])
@token_required
def verify_token(current_user):
    return jsonify({
        'valid': True,
        'user': serialize_user(current_user)
    })

@app.route('/api/auth/change-password', methods=['POST'])
@token_required
def change_password(current_user):
    try:
        data = request.get_json()
        current_password = data.get('currentPassword', '')
        new_password = data.get('newPassword', '')

        if not current_password or not new_password:
            return jsonify({
                'success': False,
                'message': 'Current and new password are required'
            }), 400

        # Verify current password
        if not check_password_hash(current_user['password'], current_password):
            return jsonify({
                'success': False,
                'message': 'Current password is incorrect'
            }), 400

        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # Update password
        users_collection.update_one(
            {"_id": current_user['_id']},
            {"$set": {
                "password": generate_password_hash(new_password),
                "updated_at": datetime.utcnow()
            }}
        )

        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })

    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        allowed_fields = ['name']
        
        update_data = {}
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field].strip() if isinstance(data[field], str) else data[field]

        if not update_data:
            return jsonify({
                'success': False,
                'message': 'No valid fields to update'
            }), 400

        update_data['updated_at'] = datetime.utcnow()

        # Update user
        users_collection.update_one(
            {"_id": current_user['_id']},
            {"$set": update_data}
        )

        # Get updated user
        updated_user = users_collection.find_one({"_id": current_user['_id']})

        return jsonify({
            'success': True,
            'user': serialize_user(updated_user),
            'message': 'Profile updated successfully'
        })

    except Exception as e:
        print(f"Update profile error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/users', methods=['GET'])
@token_required
@admin_required
def get_users(current_user):
    try:
        users = list(users_collection.find({"is_active": True}).sort("created_at", -1))
        serialized_users = [serialize_user(user) for user in users]

        return jsonify({
            'success': True,
            'users': serialized_users
        })

    except Exception as e:
        print(f"Get users error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/users/<user_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_user(current_user, user_id):
    try:
        if not ObjectId.is_valid(user_id):
            return jsonify({
                'success': False,
                'message': 'Invalid user ID'
            }), 400

        user_to_delete = users_collection.find_one({"_id": ObjectId(user_id)})
        if not user_to_delete:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Prevent deleting self
        if str(current_user['_id']) == user_id:
            return jsonify({
                'success': False,
                'message': 'Cannot delete your own account'
            }), 400

        # Soft delete (mark as inactive)
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )

        # Remove all sessions for this user
        sessions_collection.delete_many({"user_id": ObjectId(user_id)})

        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })

    except Exception as e:
        print(f"Delete user error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/reset-password', methods=['POST'])
@token_required
@admin_required
def reset_user_password(current_user):
    try:
        data = request.get_json()
        user_id = data.get('userId', '')
        new_password = data.get('newPassword', '')

        if not user_id or not new_password:
            return jsonify({
                'success': False,
                'message': 'User ID and new password are required'
            }), 400

        if not ObjectId.is_valid(user_id):
            return jsonify({
                'success': False,
                'message': 'Invalid user ID'
            }), 400

        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': message
            }), 400

        # Check if user exists
        user = users_collection.find_one({"_id": ObjectId(user_id), "is_active": True})
        if not user:
            return jsonify({
                'success': False,
                'message': 'User not found'
            }), 404

        # Update password
        users_collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {
                "password": generate_password_hash(new_password),
                "updated_at": datetime.utcnow()
            }}
        )

        # Remove all sessions for this user to force re-login
        sessions_collection.delete_many({"user_id": ObjectId(user_id)})

        return jsonify({
            'success': True,
            'message': 'Password reset successfully'
        })

    except Exception as e:
        print(f"Reset password error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# Cleanup expired sessions periodically
@app.route('/api/auth/cleanup-sessions', methods=['POST'])
def cleanup_expired_sessions():
    try:
        # Remove expired sessions
        result = sessions_collection.delete_many({
            "expires_at": {"$lt": datetime.utcnow()}
        })
        
        return jsonify({
            'success': True,
            'deleted_sessions': result.deleted_count
        })
    except Exception as e:
        print(f"Cleanup sessions error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

# ===========================
# EXISTING ROUTES (Updated with auth where needed)
# ===========================

@app.get("/")
def index_get():
    return render_template("base.html")

@app.get("/index")
def index_page():
    """Render the main index page"""
    return render_template("index.html")

user_contexts = {}  # Stores user_id → last detected office
office_tags = {     # Example mapping of office tags
   'admission_office': 'Admission Office',
    'registrar_office': "Registrar's Office",
    'ict_office': 'ICT Office',
    'guidance_office': 'Guidance Office',
    'osa_office': 'Office of Student Affairs',
    "general": "General"
}

def detect_office_from_message(msg):
    """Detect which office the user is asking about"""
    msg_lower = msg.lower()
    
    # Direct office mentions
    if 'admission' in msg_lower or 'apply' in msg_lower or 'enroll' in msg_lower:
        return 'admission_office'
    elif 'registrar' in msg_lower or 'transcript' in msg_lower or 'grades' in msg_lower or 'academic records' in msg_lower:
        return 'registrar_office'
    elif 'ict' in msg_lower or 'password' in msg_lower or 'wifi' in msg_lower or 'internet' in msg_lower or 'student portal' in msg_lower:
        return 'ict_office'
    elif 'guidance' in msg_lower or 'counseling' in msg_lower or 'scholarship' in msg_lower or 'career advice' in msg_lower:
        return 'guidance_office'
    elif 'osa' in msg_lower or 'student affairs' in msg_lower or 'clubs' in msg_lower or 'activities' in msg_lower or 'events' in msg_lower:
        return 'osa_office'
    return None

def save_message(user, sender, message, detected_office=None, status=None):
    """Save message to MongoDB with error handling and office detection + resolution status"""
    global conversations_collection
    
    if conversations_collection is None:
        print("MongoDB not available. Message not saved to database.")
        return None
    
    # Determine office based on context or detection
    office = None
    
    if detected_office:
        office = office_tags.get(detected_office, detected_office)
    elif user in user_contexts:
        office = office_tags.get(user_contexts[user], user_contexts[user])
    elif sender == "user":
        detected_tag = detect_office_from_message(message)
        if detected_tag:
            office = office_tags.get(detected_tag, detected_tag)
            user_contexts[user] = detected_tag
    if not office:
        office = "General"
    
    document = {
        "user": user,
        "sender": sender,
        "message": message,
        "office": office,
        "status": status,  # ✅ new field
        "date": datetime.now().isoformat()
    }
    
    try:
        conversations_collection.insert_one(document)
        print(f"Message saved (office={office}, status={status})")
    except Exception as e:
        print(f"Error saving message: {e}")
    
    return office
  # ✅ Return for reuse in predict()

@app.post("/predict")
def predict():
    data = request.get_json()
    text = data.get("message")
    user = data.get("user", "guest")

    if not text or not text.strip():
        return jsonify({"answer": "Please type something."})

    try:
        print(f"User {user} asked: {text}")

        # Get chatbot response
        response = get_response(text)

        # ✅ Common unresolved/fallback patterns
        unresolved_patterns = [
            "sorry",
            "contact support",
            "i'm not sure how to respond",
            "please try one of the suggested topics",
            "rephrase your question",
            "i'm not sure i understand",
            "could you rephrase your question",
            "sorry, i don't have that information yet",
            "i'm still learning",
            "i might not have understood that correctly",
            "i don't quite understand that",
            "would you like to try asking about a specific office or service",
            "i'm here to help with information about college offices and services"
        ]
        # ✅ Escalation patterns (hand-off to human/office)
        escalation_patterns = [
            "escalating to a human agent",
            "let me connect you to support",
            "please contact the registrar",
            "please contact admissions",
            "please reach out to guidance",
            "i'm forwarding this to ict",
            "i think you might be asking about",   # NEW
            "would you like me to connect you"     # NEW
        ]

        # Detect resolved/unresolved
        if response and any(p in response.lower() for p in escalation_patterns):
            status = "escalated"
        elif response and not any(p in response.lower() for p in unresolved_patterns):
            status = "resolved"
        else:
            status = "unresolved"

        # Save user query
        office = save_message(
            user=user,
            sender="user",
            message=text
        )

        # Save bot response with resolution status
        save_message(
            user=user,
            sender="bot",
            message=response,
            detected_office=office,
            status=status
        )

        return jsonify({
            "answer": response,
            "office": office,
            "status": status,  # ✅ shows on frontend/dashboard
            "context_in_memory": user_contexts.get(user),
            "vector_enabled": vector_store.index is not None,
            "vector_stats": vector_store.get_stats()
        })

    except Exception as e:
        print(f"Error in predict: {e}")
        return jsonify({
            "answer": "Sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500




cleared_users = set()

@app.post("/clear_history")
def clear_history():
    """Clear user's chat history from both in-memory and MongoDB with detailed feedback"""
    data = request.get_json()
    user = data.get("user") or "guest"
    clear_mongodb = data.get("clear_mongodb", True)  # Optional parameter

    try:
        global conversations
        
        # Initialize conversations as dict if it's not already
        if not isinstance(conversations, dict):
            conversations = {}

        # Count messages before deletion
        memory_count = 0
        if user in conversations:
            memory_count = len(conversations[user])
            
        # Clear in-memory
        if user in conversations:
            conversations[user] = []
            
        # Add user to cleared set for tracking
        cleared_users.add(user)
        
        # Clear MongoDB if requested (optional enhancement)
        mongo_count = 0
        if clear_mongodb:
            try:
                # Count MongoDB documents before deletion
                mongo_count = conversations_collection.count_documents({"user": user})
                if mongo_count == 0:
                    mongo_count = conversations_collection.count_documents({"user_id": user})
                
                # Delete from MongoDB
                result1 = conversations_collection.delete_many({"user": user})
                result2 = conversations_collection.delete_many({"user_id": user})
                mongo_deleted = result1.deleted_count + result2.deleted_count
                
            except Exception as mongo_err:
                print(f"MongoDB deletion error: {mongo_err}")
                mongo_deleted = 0
        else:
            mongo_deleted = 0

        # Simulate brief processing time for better UX
        time.sleep(0.2)

        return jsonify({
            "status": "success",
            "message": f"History cleared successfully",
            "details": {
                "memory_cleared": memory_count,
                "mongodb_cleared": mongo_deleted,
                "total_cleared": memory_count + mongo_deleted,
                "user": user,
                "timestamp": time.time()
            }
        })

    except Exception as e:
        print(f"Error clearing history: {e}")
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Failed to clear history"
        }), 500


@app.post("/history")
def history():
    """Load chat history with better error handling and status info"""
    data = request.get_json()
    user = data.get("user") or data.get("user_id") or "guest"

    try:
        global conversations

        # Initialize conversations as dict if it's not already
        if not isinstance(conversations, dict):
            conversations = {}

        history_data = []
        source = "none"

        # 1. If in-memory has data, return that
        if user in conversations and conversations[user]:
            history_data = conversations[user]
            source = "memory"
        else:
            # 2. Otherwise, fallback to MongoDB
            try:
                history_data = list(conversations_collection.find(
                    {"user": user}
                ).sort("timestamp", -1).limit(20))

                if not history_data:
                    history_data = list(conversations_collection.find(
                        {"user_id": user}
                    ).sort("timestamp", -1).limit(20))

                if history_data:
                    history_data.reverse()  # oldest first
                    source = "mongodb"
                    
            except Exception as mongo_err:
                print(f"MongoDB query error: {mongo_err}")
                history_data = []
                source = "error"

        # Format for frontend
        history_formatted = []
        for m in history_data:
            sender = m.get("sender", "unknown")
            message = m.get("message", "")

            if sender == "user":
                display_name = "user"
            elif sender in ["bot", "assistant"]:
                display_name = "Bot"
            else:
                if "response" in m and message == m.get("response", ""):
                    display_name = "Bot"
                else:
                    display_name = "user"

            history_formatted.append({
                "name": display_name,
                "message": message
            })

            if "response" in m and m["response"] and m["response"] != message:
                history_formatted.append({
                    "name": "Bot",
                    "message": m["response"]
                })

        return jsonify({
            "messages": history_formatted,
            "meta": {
                "count": len(history_formatted),
                "source": source,
                "user": user,
                "was_recently_cleared": user in cleared_users
            }
        })

    except Exception as e:
        print(f"Error loading history: {e}")
        return jsonify({
            "messages": [],
            "meta": {
                "count": 0,
                "source": "error",
                "error": str(e)
            }
        }), 500


@app.post("/clear_status")
def clear_status():
    """Check if user's history was recently cleared"""
    data = request.get_json()
    user = data.get("user") or "guest"
    
    return jsonify({
        "was_cleared": user in cleared_users,
        "user": user
    })

@app.route("/cleanup_cleared_users")
def cleanup_cleared_users():
    """Admin endpoint to clean up the cleared users tracking"""
    global cleared_users
    count = len(cleared_users)
    cleared_users.clear()
    return jsonify({"cleared_count": count})



# Global dictionary to store user contexts
# --- Context store ---
user_contexts = {}

def reset_user_context(user):
    """
    Clear stored office/context for a specific user
    without touching MongoDB history.
    """
    if user in user_contexts:
        last_office = user_contexts[user]
        del user_contexts[user]
        print(f"Context reset for user: {user} (last office was {last_office})")
    else:
        print(f"No context found for user: {user}")

@app.post("/reset_context")
def reset_context():
    """Reset user's conversation context"""
    data = request.get_json()
    user = data.get("user", "guest")
    
    try:
        reset_user_context(user)
        return jsonify({
            "status": "Context reset successfully",
            "user": user,
            "context_cleared": True  # ✅ frontend can use this flag
        })
    except Exception as e:
        print(f"Error resetting context: {e}")
        return jsonify({"error": str(e)}), 500



    




@app.get("/announcements")
def get_announcements():
    """Get all active announcements"""
    try:
        announcements = get_active_announcements()
        return jsonify({"announcements": announcements})
    except Exception as e:
        print(f"Error getting announcements: {e}")
        return jsonify({"announcements": []}), 500

@app.get("/announcements/<int:announcement_id>")
def get_announcement(announcement_id):
    """Get a specific announcement by ID"""
    try:
        announcement = get_announcement_by_id(announcement_id)
        if announcement:
            return jsonify({"announcement": announcement})
        else:
            return jsonify({"error": "Announcement not found"}), 404
    except Exception as e:
        print(f"Error getting announcement: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/announcements")
@token_required
def create_announcement_endpoint(current_user):
    """Create a new announcement (for admin use)"""
    data = request.get_json()
    
    try:
        required_fields = ["title", "date", "message"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "Missing required fields: title, date, message"}), 400
        
        title = data.get("title")
        date = data.get("date")
        message = data.get("message")
        priority = data.get("priority", "medium")
        category = data.get("category", "general")
        
        new_announcement = add_announcement(title, date, message, priority, category)
        return jsonify({
            "announcement": new_announcement, 
            "status": "Announcement created successfully"
        }), 201
    
    except Exception as e:
        print(f"Error creating announcement: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/search_announcements")
def search_announcements():
    """Search announcements using vector similarity"""
    data = request.get_json()
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    
    if not query.strip():
        return jsonify({"results": []})
    
    try:
        if vector_store.index:
            results = vector_store.search_announcements(query, top_k)
            return jsonify({
                "results": results,
                "query": query,
                "vector_enabled": True
            })
        else:
            return jsonify({
                "results": [],
                "query": query,
                "vector_enabled": False,
                "message": "Vector search not available"
            })
    
    except Exception as e:
        print(f"Error searching announcements: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/search_patterns")
def search_patterns():
    """Search similar patterns using vector database"""
    data = request.get_json()
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    tag = data.get("tag", None)
    
    if not query.strip():
        return jsonify({"results": []})
    
    try:
        if vector_store.index:
            if tag:
                results = vector_store.search_by_tag(query, tag, top_k)
            else:
                results = vector_store.search_similar(query, top_k)
            
            return jsonify({
                "results": results,
                "query": query,
                "tag": tag,
                "vector_enabled": True
            })
        else:
            return jsonify({
                "results": [],
                "query": query,
                "vector_enabled": False,
                "message": "Vector search not available"
            })
    
    except Exception as e:
        print(f"Error searching patterns: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/vector_stats")
def get_vector_stats():
    """Get vector database statistics"""
    try:
        stats = vector_store.get_stats()
        return jsonify({
            "stats": stats,
            "vector_enabled": vector_store.index is not None
        })
    except Exception as e:
        print(f"Error getting vector stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/reindex_vectors")
@token_required
@admin_required
def reindex_vectors(current_user):
    """Reindex all data in vector database (admin function)"""
    try:
        # This would typically be an admin-only function
        from train import main as retrain_model
        
        # Clear existing vectors
        if vector_store.index:
            vector_store.clear_index()
        
        # Retrain and reindex
        # Note: You might want to implement this differently based on your needs
        success = True  # Placeholder for actual reindexing logic
        
        if success:
            return jsonify({"status": "Vector database reindexed successfully"})
        else:
            return jsonify({"error": "Failed to reindex vector database"}), 500
    
    except Exception as e:
        print(f"Error reindexing vectors: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        return jsonify({
            "status": "healthy",
            "vector_enabled": vector_store.index is not None,
            "database_connected": conversations_collection is not None,
            "vector_stats": vector_store.get_stats()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.get("/admin")
def admin_panel():
    """Admin panel for managing announcements and vector database"""
    return render_template("admin.html")

@app.get("/admin/index")
def admin_index():
    """Alternative admin index route"""
    return render_template("index.html")

@app.get("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard for EduChat system analytics and management"""
    return render_template("dashboard.html")

@app.get("/dashboard")
def dashboard():
    """Direct dashboard route"""
    return render_template("dashboard.html", active_page="dashboard")

@app.get("/admin/users")
def admin_users():
    """Admin users management page"""
    return render_template("users.html")

@app.get("/users")
def users():
    """Direct users management route"""
    return render_template("users.html", active_page="users")

@app.get("/admin/usage")
def admin_usage():
    """Admin usage statistics page"""
    return render_template("usage.html")

@app.get("/usage")
def usage():
    """Direct usage statistics route"""
    return render_template("usage.html", active_page="usage")

@app.get("/admin/settings")
def admin_settings():
    """Admin settings page"""
    return render_template("settings.html")

@app.get("/settings")
def settings():
    """Direct settings route"""
    return render_template("settings.html", active_page="settings")

@app.get("/admin/conversations")
def admin_conversations():
    """Admin conversations page"""
    return render_template("conversations.html")

# Fix: Rename this function to avoid conflicts
@app.route("/conversations", endpoint='conversations')
def conversations():
    """Direct conversations route"""
    return render_template("conversations.html", active_page="conversations")

@app.get("/admin/faq")
def admin_faq():
    """Admin faq page"""
    return render_template("faq.html")

@app.get("/faq")
def faq():
    """Direct faq route"""
    return render_template("faq.html", active_page="faq")

@app.get("/admin/feedback")
def admin_feedback():
    """Admin feedback page"""
    return render_template("feedback.html")

@app.get("/feedback")
def feedback():
    """Direct feedback route"""
    return render_template("feedback.html", active_page="feedback")

@app.get("/admin/roles")
def admin_roles():
    """Admin roles page"""
    return render_template("roles.html")

@app.get("/roles")
def roles():
    """Direct roles route"""
    return render_template("roles.html", active_page="roles")

@app.get("/Sub-admin/Sub-dashboard")
def sub_admin_dashboard():
    """Sub-Admin dashboard for EduChat system analytics and management"""
    return render_template("Sub-dashboard.html")

@app.get("/Sub-dashboard")
def sub_dashboard():
    office = request.args.get("office", "Sub Admin")  # default fallback
    return render_template(
        "Sub-dashboard.html",
        active_page="sub_dashboard",
        office=office
    )

@app.get("/Sub-admin/Sub-conversations")
def sub_admin_conversations():
    """Sub-Admin conversations page"""
    return render_template("Sub-conversations.html")

@app.get("/Sub-conversations")
def sub_conversations():
    """Direct sub-conversations route"""
    return render_template("Sub-conversations.html", active_page="sub_conversations")

@app.get("/Sub-admin/Sub-faq")
def sub_admin_faq():
    """Sub-Admin faq page"""
    return render_template("Sub-faq.html")

@app.get("/Sub-faq")
def sub_faq():
    """Direct sub-faq route"""
    return render_template("Sub-faq.html", active_page="sub_faq")

@app.get("/Sub-admin/Sub-announcements")
def sub_admin_announcements():
    """Sub-Admin announcements page"""
    return render_template("Sub-announcements.html")

@app.get("/Sub-announcements")
def sub_announcements():
    """Direct sub-announcements route"""
    return render_template("Sub-announcements.html", active_page="sub_announcements")

@app.get("/Sub-admin/Sub-usage_stats")
def sub_admin_usage_stats():
    """Sub-Admin usage_stats page"""
    return render_template("Sub-usage.html")

@app.get("/Sub-usage_stats")
def sub_usage_stats():
    """Direct sub-usage_stats route"""
    return render_template("Sub-usage.html", active_page="sub_usage_stats")

@app.get("/Sub-admin/Sub-feedback")
def sub_admin_feedback():
    """Sub-Admin feedback page"""
    return render_template("Sub-feedback.html")

@app.get("/Sub-feedback")
def sub_feedback():
    """Direct sub-feedback route"""
    return render_template("Sub-feedback.html", active_page="sub_feedback")

# API endpoints for dashboard data
@app.get("/api/dashboard/stats")
@token_required
def get_dashboard_stats(current_user):
    """Get dashboard statistics"""
    try:
        # Fix: Use the correct collection name
        total_conversations = conversations_collection.count_documents({})
        active_users = len(conversations_collection.distinct("user"))
        
        # Calculate some basic metrics
        resolved_queries = int(total_conversations * 0.86)  # Assuming 86% resolution rate
        escalated_issues = total_conversations - resolved_queries
        
        # Recent activity
        recent_conversations = list(conversations_collection.find({}).sort("date", -1).limit(10))
        
        # Get user statistics
        total_users = users_collection.count_documents({"is_active": True})
        admin_count = users_collection.count_documents({"role": "admin", "is_active": True})
        sub_admin_count = users_collection.count_documents({"role": "sub-admin", "is_active": True})
        
        stats = {
            "total_users": active_users,
            "chatbot_sessions": total_conversations,
            "resolved_queries": resolved_queries,
            "escalated_issues": escalated_issues,
            "system_users": total_users,
            "admin_count": admin_count,
            "sub_admin_count": sub_admin_count,
            "recent_activity": recent_conversations,
            "vector_stats": vector_store.get_stats() if vector_store else {}
        }
        
        return jsonify({"stats": stats})
    
    except Exception as e:
        print(f"Error getting dashboard stats: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/dashboard/usage")
@token_required
def get_usage_data(current_user):
    """Get usage data for charts"""
    try:
        # Get usage data grouped by day of week or other time periods
        # This is a simplified example - you might want to implement more sophisticated analytics
        
        pipeline = [
            {
                "$group": {
                    "_id": {"$dayOfWeek": "$timestamp"},
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        # Fix: Use the correct collection name
        usage_data = list(conversations_collection.aggregate(pipeline))
        
        # Format data for chart
        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        formatted_data = []
        
        for i in range(7):
            day_data = next((item for item in usage_data if item["_id"] == i+1), {"count": 0})
            formatted_data.append({
                "day": days[i],
                "usage": day_data["count"]
            })
        
        return jsonify({"usage_data": formatted_data})
    
    except Exception as e:
        print(f"Error getting usage data: {e}")
        return jsonify({"error": str(e)}), 500

@app.get("/api/dashboard/activity")
@token_required
def get_recent_activity(current_user):
    """Get recent system activity"""
    try:
        # Fix: Use the correct collection name
        recent_conversations = list(conversations_collection.find({}).sort("timestamp", -1).limit(20))
        
        # Format activity data
        activities = []
        for conv in recent_conversations:
            activities.append({
                "type": "conversation",
                "user_id": conv.get("user_id", "Unknown"),
                "message": conv.get("message", "")[:50] + "..." if len(conv.get("message", "")) > 50 else conv.get("message", ""),
                "timestamp": conv.get("timestamp"),
                "sender": conv.get("sender", "unknown")
            })
        
        return jsonify({"activities": activities})
    
    except Exception as e:
        print(f"Error getting recent activity: {e}")
        return jsonify({"error": str(e)}), 500

# Additional API endpoints for user management
@app.get("/api/users/profile")
@token_required
def get_user_profile(current_user):
    """Get current user's profile"""
    try:
        return jsonify({
            'success': True,
            'user': serialize_user(current_user)
        })
    except Exception as e:
        print(f"Get profile error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.get("/api/users/sessions")
@token_required
def get_user_sessions(current_user):
    """Get current user's active sessions"""
    try:
        sessions = list(sessions_collection.find({
            "user_id": current_user['_id'],
            "expires_at": {"$gt": datetime.utcnow()}
        }).sort("created_at", -1))
        
        # Format sessions for response
        formatted_sessions = []
        for sess in sessions:
            formatted_sessions.append({
                "_id": str(sess['_id']),
                "created_at": sess['created_at'],
                "expires_at": sess['expires_at'],
                "user_agent": sess.get('user_agent', 'Unknown'),
                "ip_address": sess.get('ip_address', 'Unknown')
            })
        
        return jsonify({
            'success': True,
            'sessions': formatted_sessions
        })
    except Exception as e:
        print(f"Get sessions error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.delete("/api/users/sessions/<session_id>")
@token_required
def revoke_session(current_user, session_id):
    """Revoke a specific session"""
    try:
        if not ObjectId.is_valid(session_id):
            return jsonify({
                'success': False,
                'message': 'Invalid session ID'
            }), 400

        # Only allow users to revoke their own sessions
        result = sessions_collection.delete_one({
            "_id": ObjectId(session_id),
            "user_id": current_user['_id']
        })
        
        if result.deleted_count > 0:
            return jsonify({
                'success': True,
                'message': 'Session revoked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Session not found'
            }), 404
    except Exception as e:
        print(f"Revoke session error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.post("/api/users/revoke-all-sessions")
@token_required
def revoke_all_sessions(current_user):
    """Revoke all sessions for current user except current one"""
    try:
        # Get current token
        auth_header = request.headers.get('Authorization')
        current_token = auth_header.split(" ")[1] if auth_header else None
        
        # Remove all sessions except current one
        if current_token:
            result = sessions_collection.delete_many({
                "user_id": current_user['_id'],
                "token": {"$ne": current_token}
            })
        else:
            result = sessions_collection.delete_many({
                "user_id": current_user['_id']
            })
        
        return jsonify({
            'success': True,
            'message': f'Revoked {result.deleted_count} sessions'
        })
    except Exception as e:
        print(f"Revoke all sessions error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
# Get KPI Data
@app.route("/api/dashboard/kpi")
def get_kpi():
    total_users = len(conversations.distinct("user"))
    total_conversations = conversations.count_documents({})
    resolved_queries = conversations.count_documents({"status": "resolved"})
    escalated_issues = conversations.count_documents({"status": "escalated"})

    return jsonify({
        "uniqueUsers": total_users,
        "totalConversations": total_conversations,
        "resolvedQueries": resolved_queries,
        "escalatedIssues": escalated_issues
    })


# Get Usage by Time (daily/weekly/hourly)
@app.route("/api/dashboard/usage/<period>")
def get_usage(period):
    # Example: mock data — replace with real aggregation later
    if period == "daily":
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        data = [5, 10, 7, 12, 9, 3, 6]
    elif period == "weekly":
        labels = ["Week 1", "Week 2", "Week 3", "Week 4"]
        data = [30, 45, 50, 60]
    else:  # hourly
        labels = [f"{h}:00" for h in range(24)]
        data = [2, 3, 5, 4, 7, 9, 6, 8, 12, 14, 10, 11, 9, 8, 7, 6, 4, 5, 3, 2, 1, 0, 0, 1]

    return jsonify({"labels": labels, "data": data})


# Get Department Distribution
@app.route("/api/dashboard/departments")
def get_departments():
    pipeline = [
        {"$group": {"_id": "$detected_office", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    results = list(conversations.aggregate(pipeline))

    labels = [r["_id"] if r["_id"] else "Unknown" for r in results]
    data = [r["count"] for r in results]

    return jsonify({"labels": labels, "data": data})

# Sub-admin specific API endpoints
@app.get("/api/sub-admin/stats")
@token_required
def get_sub_admin_stats(current_user):
    """Get statistics for sub-admin dashboard"""
    try:
        if current_user.get('role') != 'sub-admin':
            return jsonify({'message': 'Sub-admin access required'}), 403
        
        office = current_user.get('office')
        
        # Get office-specific statistics
        # This is a placeholder - you might want to implement office-specific filtering
        # Fix: Use the correct collection name
        office_conversations = conversations_collection.count_documents({})
        office_users = len(conversations_collection.distinct("user_id"))
        
        stats = {
            "office": office,
            "office_conversations": office_conversations,
            "office_users": office_users,
            "office_resolved_queries": int(office_conversations * 0.86),
            "office_escalated_issues": int(office_conversations * 0.14)
        }
        
        return jsonify({"stats": stats})
    
    except Exception as e:
        print(f"Error getting sub-admin stats: {e}")
        return jsonify({"error": str(e)}), 500

# Add some debugging information on startup
def startup_info():
    print("=== TCC Assistant Starting ===")
    print(f"Vector Store Status: {vector_store.get_stats()}")
    print(f"Pinecone Available: {vector_store.index is not None}")
    print("===============================")

if __name__ == "__main__":
    # Create default admin user on startup
    create_default_admin()
    
    # Print startup information
    startup_info()
    print("=== TCC Assistant with Vector Search ===")
    print(f"Vector Store Status: {vector_store.get_stats()}")
    print(f"Pinecone Available: {vector_store.index is not None}")
    
    if not vector_store.index:
        print("\n⚠️  WARNING: Pinecone not available!")
        print("To enable vector search:")
        print("1. Set PINECONE_API_KEY environment variable")
        print("2. Run: export PINECONE_API_KEY='your-api-key'")
        print("3. Install required packages: pip install pinecone-client sentence-transformers")
    
    print("=========================================\n")
    print("Available routes:")
    print("- / : Main chatbot interface (base.html)")
    print("- /index : Index page (index.html)")
    print("- /admin : Admin panel (admin.html)")
    print("- /admin/index : Admin index (index.html)")
    print("- /admin/dashboard : Admin dashboard (dashboard.html)")
    print("- /dashboard : Direct dashboard access (dashboard.html)")
    print("- /admin/users : Admin users management (users.html)")
    print("- /users : Direct users management access (users.html)")
    print("- /admin/usage : Admin usage statistics (usage.html)")
    print("- /usage : Direct usage statistics access (usage.html)")
    print("\nAuthentication API routes:")
    print("- POST /api/auth/login : User login")
    print("- POST /api/auth/logout : User logout")
    print("- POST /api/auth/register : User registration (admin only)")
    print("- POST /api/auth/verify : Token verification")
    print("- POST /api/auth/change-password : Change password")
    print("- GET /api/auth/users : Get all users (admin only)")
    print("- DELETE /api/auth/users/<id> : Delete user (admin only)")
    print("- POST /api/auth/reset-password : Reset user password (admin only)")
    print("=========================================\n")
    
    app.run(debug=True)