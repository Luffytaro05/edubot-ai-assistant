#(app.py)
from collections import UserDict
from flask import Flask, render_template, request, jsonify, session, current_app, redirect, url_for
from flask_cors import CORS
from chat import (get_response, reset_user_context, clear_chat_history, 
                  get_active_announcements, add_announcement, get_announcement_by_id,
                  vector_store, get_chatbot_response,
                  user_contexts, office_tags, detect_office_from_message as chat_detect_office,
                  get_openai_fallback, get_tcc_guarded_response, DOMAIN_REFUSAL_MESSAGE)
import requests
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date, UTC, timezone
from conversations import conversations_bp
from dashboard import init_app
from users import users_bp, authenticate_user
from roles import roles_bp
from sub_conversations import sub_conversations_bp
from sub_dashboard import sub_dashboard_bp
from sub_usage import sub_usage_bp
from sub_feedback import sub_feedback_bp
from sub_faq import sub_faq_bp
from sub_announcements import sub_announcements_bp
from usage import usage_bp
from feedback import save_feedback, get_feedback_stats, get_recent_feedback, get_feedback_analytics
from vector_store import VectorStore
from flask_moment import Moment
from settings import (
    get_settings as get_bot_settings,
    update_settings as update_bot_settings,
    reset_settings as reset_bot_settings,
)
from faq import add_faq, get_faqs, update_faq, delete_faq, search_faqs, get_faq_by_id, get_faq_versions, rollback_faq
try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    print("[WARNING] JWT module not available. Authentication features will be disabled.")
    JWT_AVAILABLE = False
import os
from dotenv import load_dotenv
import certifi
load_dotenv()
import time
from functools import wraps
from bson import ObjectId
import re
import traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Resend email service integration
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    print("[WARNING] Resend module not available. Email features will be disabled.")
    RESEND_AVAILABLE = False
# Google Translate API integration (using deep-translator for stability)
from deep_translator import GoogleTranslator
from deep_translator.exceptions import LanguageNotSupportedException
from langdetect import detect, DetectorFactory
# Ensure consistent language detection results
DetectorFactory.seed = 0
# In-memory cache for user conversations

app = Flask(__name__)
moment = Moment(app)

# Pinecone Configuration (needed before VectorStore initialization)
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_ENV = os.getenv('PINECONE_ENV', 'us-east-1')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME', 'chatbot-vectors')

# Initialize VectorStore with Pinecone configuration
vs = VectorStore(
    index_name=PINECONE_INDEX_NAME,
    model_name="all-MiniLM-L6-v2",
    dimension=384,
    enhanced_embeddings=True
)
app.register_blueprint(conversations_bp)
app.register_blueprint(users_bp)
app.register_blueprint(roles_bp)
app.register_blueprint(sub_conversations_bp)
app.register_blueprint(sub_dashboard_bp)
app.register_blueprint(sub_usage_bp)
app.register_blueprint(sub_feedback_bp)
app.register_blueprint(sub_faq_bp)
app.register_blueprint(sub_announcements_bp)
app.register_blueprint(usage_bp)
CORS(app)
# Railway-compatible configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-change-this-in-production')

# Initialize Pinecone client
pinecone_client = None
pinecone_index = None
pinecone_available = False

try:
    if PINECONE_API_KEY:
        from pinecone import Pinecone, ServerlessSpec
        pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if not
        existing_indexes = [idx.name for idx in pinecone_client.list_indexes()]
        
        if PINECONE_INDEX_NAME not in existing_indexes:
            print(f"Creating new Pinecone index: {PINECONE_INDEX_NAME}")
            pinecone_client.create_index(
                name=PINECONE_INDEX_NAME,
                dimension=384,  # For all-MiniLM-L6-v2 model
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=PINECONE_ENV
                )
            )
            print(f"Waiting for index {PINECONE_INDEX_NAME} to be ready...")
            import time
            time.sleep(10)
        
        # Connect to index
        pinecone_index = pinecone_client.Index(PINECONE_INDEX_NAME)
        pinecone_available = True
        print(f"✅ Pinecone connected successfully - Index: {PINECONE_INDEX_NAME}, Region: {PINECONE_ENV}")
        
except Exception as e:
    print(f"❌ Pinecone initialization failed: {e}")
    print("⚠️ Running without Pinecone vector search capabilities")
    pinecone_available = False

# MongoDB connection with environment variable and TLS
MONGODB_URI = os.getenv('MONGODB_URI')
try:
    if not MONGODB_URI:
        raise RuntimeError('MONGODB_URI is not set')
    client = MongoClient(
        MONGODB_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=15000,
        connectTimeoutMS=10000,
        socketTimeoutMS=10000,
        maxPoolSize=5,
        retryWrites=True
    )
    client.admin.command('ping')
    db = client["chatbot_db"]
    print("✅ MongoDB connected securely (TLS enabled)")
except Exception as e:
    print(f"❌ Secure MongoDB connection failed: {e}")
    # Create a mock database for Railway deployment without MongoDB
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
    db = MockDB()
    client = None
# Fix: Use a different name to avoid conflicts with the route function
conversations_collection = db["conversations"]  # Changed name here
users_collection = db["users"]
sessions_collection = db["sessions"]
sub_users = db["sub_users"]
init_app(app)

# JWT token expiration time
TOKEN_EXPIRATION_HOURS = 24

# ===========================
# EMAIL CONFIGURATION - RESEND
# ===========================
# Use environment variables for production, fallback to config for development
EMAIL_CONFIG = {
    'RESEND_API_KEY': os.getenv('RESEND_API_KEY', 're_8KwS33NS_Bx2zWqU4gXHNMyUMpc9LUHVG'),
    'SENDER_EMAIL': os.getenv('SENDER_EMAIL', 'noreply@tanauancitycollege.com'),  # Use Resend's test domain
    'SENDER_NAME': os.getenv('SENDER_NAME', 'EduChat Admin System'),
    'ENABLE_EMAIL': os.getenv('ENABLE_EMAIL', 'True').lower() == 'true',  # Toggle email on/off
    'USE_RESEND': True  # Use Resend instead of SMTP
}


# ===========================
# 🔧 RESEND API SETUP INSTRUCTIONS
# ===========================
# STEP 1: Go to https://resend.com/signup
# STEP 2: Create an account and verify your email
# STEP 3: Go to https://resend.com/api-keys
# STEP 4: Create a new API key
# STEP 5: Copy the API key
# STEP 6: Set RESEND_API_KEY environment variable
# STEP 7: Set SENDER_EMAIL to a verified email in Resend
# ===========================

# Initialize Resend with API key
if RESEND_AVAILABLE and EMAIL_CONFIG['RESEND_API_KEY']:
    resend.api_key = EMAIL_CONFIG['RESEND_API_KEY']

# Email should only be enabled if credentials are provided via environment variables
if EMAIL_CONFIG['RESEND_API_KEY'] and EMAIL_CONFIG['ENABLE_EMAIL'] and RESEND_AVAILABLE:
    print(f"✅ Email notifications ENABLED via Resend - Emails will be sent from {EMAIL_CONFIG['SENDER_EMAIL']}")
else:
    EMAIL_CONFIG['ENABLE_EMAIL'] = False
    if not RESEND_AVAILABLE:
        print("⚠️ Email notifications DISABLED - Resend module not installed")
    elif not EMAIL_CONFIG['RESEND_API_KEY']:
        print("⚠️ Email notifications DISABLED - Configure RESEND_API_KEY in environment variables to enable")

def send_password_change_email(user_email, user_name):
    """Send email notification when password is changed using Resend API"""
    # Check if email is enabled
    if not EMAIL_CONFIG.get('ENABLE_EMAIL', False):
        print("Email notifications are disabled. Set ENABLE_EMAIL=True to enable.")
        return False
    
    # Check if Resend is available
    if not RESEND_AVAILABLE:
        print("⚠️ WARNING: Resend module not available! Please install the resend package.")
        return False
    
    # Validate email configuration
    if not EMAIL_CONFIG.get('RESEND_API_KEY'):
        print("⚠️ WARNING: RESEND_API_KEY not configured! Please set RESEND_API_KEY in environment variables.")
        return False
    
    if not user_email or not validate_email(user_email):
        print(f"Invalid recipient email: {user_email}")
        return False
    
    try:
        print(f"📧 Attempting to send password change notification to {user_email} via Resend...")
        
        # Create HTML email content - simplified to avoid spam filters
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; border-radius: 10px; padding: 30px;">
                <h2 style="color: #2563eb; margin-bottom: 20px;">Account Update Confirmation</h2>
                
                <p>Hello {user_name},</p>
                
                <p>Your EduChat Admin account credentials were updated recently.</p>
                
                <div style="background-color: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Details:</strong></p>
                    <p style="margin: 5px 0;">Account: {user_email}<br>
                    Time: {datetime.now(UTC).strftime('%B %d, %Y at %I:%M %p UTC')}</p>
                </div>
                
                <div style="background-color: #fff9c4; border-left: 4px solid #fbc02d; padding: 15px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>Important:</strong> If this was not you, please contact us immediately.</p>
                </div>
                
                <p>Thank you,<br>
                <strong>EduChat Team</strong></p>
                
                <hr style="border: none; border-top: 1px solid #dee2e6; margin: 30px 0;">
                <p style="color: #6c757d; font-size: 12px; text-align: center;">
                    Automated notification from EduChat Admin System
                </p>
            </div>
        </body>
        </html>
        """

        # Create plain text version for better deliverability
        text_content = f"""
Account Update Confirmation

Hello {user_name},

Your EduChat Admin account credentials were updated recently.

Details:
Account: {user_email}
Time: {datetime.now(UTC).strftime('%B %d, %Y at %I:%M %p UTC')}

Important: If this was not you, please contact us immediately.

Thank you,
EduChat Team
        """

        # Send email using Resend API
        try:
            params = {
                "from": f"{EMAIL_CONFIG['SENDER_NAME']} <{EMAIL_CONFIG['SENDER_EMAIL']}>",
                "to": [user_email],
                "subject": "Account Update Confirmation",  # Less spammy subject
                "html": html_content,
                "text": text_content.strip(),
            }
            
            email = resend.Emails.send(params)
            print(f"✓ Email sent successfully to {user_email} via Resend")
            print(f"✓ Resend email ID: {email.get('id', 'unknown')}")
            return True
            
        except Exception as e:
            print(f"❌ Resend API Error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    except Exception as e:
        print(f"❌ Error preparing email notification: {e}")
        import traceback
        traceback.print_exc()
        # Don't fail the password change if email fails
        return False

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

def create_default_sub_admins():
    """Create default sub-admin users for each office"""
    sub_admin_users = [
        {
            "email": "admissions@tcc.edu",
            "password": generate_password_hash("admissions123"),
            "name": "Admissions Office Admin",
            "role": "sub-admin",
            "office": "Admission Office",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "email": "registrar@tcc.edu",
            "password": generate_password_hash("registrar123"),
            "name": "Registrar Office Admin",
            "role": "sub-admin",
            "office": "Registrar's Office",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "email": "ict@tcc.edu",
            "password": generate_password_hash("ict123"),
            "name": "ICT Office Admin",
            "role": "sub-admin",
            "office": "ICT Office",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "email": "guidance@tcc.edu",
            "password": generate_password_hash("guidance123"),
            "name": "Guidance Office Admin",
            "role": "sub-admin",
            "office": "Guidance Office",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        },
        {
            "email": "osa@tcc.edu",
            "password": generate_password_hash("osa123"),
            "name": "OSA Office Admin",
            "role": "sub-admin",
            "office": "Office of Student Affairs",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
    ]
    
    for user_data in sub_admin_users:
        existing_user = users_collection.find_one({"email": user_data["email"]})
        if not existing_user:
            users_collection.insert_one(user_data)
            print(f"Default sub-admin user created: {user_data['name']}")


def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not JWT_AVAILABLE:
            return jsonify({'message': 'JWT authentication not available'}), 500
            
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
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    return True, "Password is valid"

def serialize_user(user):
    """Convert MongoDB user document to JSON serializable format"""
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)  # Remove password from response
        return user
    return None

# ===========================
# BOT SETTINGS API ROUTES
# ===========================

@app.route("/api/bot/settings", methods=["GET"])
def api_get_bot_settings():
    return get_bot_settings()


@app.route("/api/bot/settings/update", methods=["POST"])
def api_update_bot_settings():
    return update_bot_settings()


@app.route("/api/bot/settings/reset", methods=["POST"])
def api_reset_bot_settings():
    return reset_bot_settings()


@app.route('/api/bot/settings/upload_avatar', methods=['POST'])
def api_upload_bot_avatar():
    try:
        if 'avatar' not in request.files:
            return jsonify({"success": False, "message": "No file uploaded (avatar)."}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({"success": False, "message": "Empty filename."}), 400

        # Create upload directory under static if not exists
        upload_dir = os.path.join(current_app.root_path, 'static', 'images', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)

        # Sanitize filename
        safe_name = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
        # Ensure uniqueness
        timestamp = int(time.time())
        filename = f"{timestamp}_{safe_name}"
        save_path = os.path.join(upload_dir, filename)
        file.save(save_path)

        # Public URL
        public_url = f"/static/images/avatars/{filename}"
        return jsonify({"success": True, "url": public_url, "message": "Avatar uploaded successfully."})
    except Exception as e:
        print('Avatar upload error:', e)
        return jsonify({"success": False, "message": "Upload failed."}), 500

# ===========================
# AUTHENTICATION API ROUTES
# ===========================

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        if not JWT_AVAILABLE:
            return jsonify({
                'success': False,
                'message': 'JWT authentication not available'
            }), 500
            
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

        # Send email notification
        user_email = current_user.get('email', '')
        user_name = current_user.get('name', 'User')
        email_sent = False
        
        print(f"🔐 Password changed successfully for user: {user_email}")
        
        if user_email:
            # Send email notification
            try:
                email_sent = send_password_change_email(user_email, user_name)
                if email_sent:
                    print(f"✅ Email notification sent to {user_email}")
                else:
                    print(f"⚠️ Email notification failed for {user_email}")
            except Exception as email_error:
                # Log error but don't fail the password change
                print(f"❌ Exception sending email notification: {email_error}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️ No email address found for user, skipping email notification")

        # Return success with email status
        response_message = 'Password changed successfully'
        if email_sent:
            response_message += '. A confirmation email has been sent.'
        elif EMAIL_CONFIG.get('ENABLE_EMAIL', False):
            response_message += '. (Email notification could not be sent)'
        
        return jsonify({
            'success': True,
            'message': response_message,
            'email_sent': email_sent
        })

    except Exception as e:
        print(f"Change password error: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/auth/test-email', methods=['POST'])
@token_required
def test_email_notification(current_user):
    """Test endpoint to verify email configuration"""
    try:
        user_email = current_user.get('email', '')
        user_name = current_user.get('name', 'Test User')
        
        if not user_email:
            return jsonify({
                'success': False,
                'message': 'No email address found for current user'
            }), 400
        
        print(f"\n{'='*60}")
        print(f"TESTING EMAIL CONFIGURATION")
        print(f"{'='*60}")
        print(f"Email Service: Resend API")
        print(f"Sender Email: {EMAIL_CONFIG['SENDER_EMAIL']}")
        print(f"Email Enabled: {EMAIL_CONFIG.get('ENABLE_EMAIL', False)}")
        print(f"Recipient: {user_email}")
        print(f"{'='*60}\n")
        
        # Send test email
        result = send_password_change_email(user_email, user_name)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Test email sent successfully to {user_email}',
                'email_sent': True
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send test email. Check server logs for details.',
                'email_sent': False
            }), 500
    
    except Exception as e:
        print(f"Test email error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error testing email: {str(e)}'
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

        # Send email notification
        try:
            user_email = user.get('email', '')
            user_name = user.get('name', 'User')
            email_sent = send_password_change_email(user_email, user_name)
            if email_sent:
                print(f"✅ Email notification sent to {user_email}")
        except Exception as email_error:
            print(f"⚠️ Failed to send email notification: {email_error}")
            # Don't fail the password reset if email fails

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
def get_sub_admin_permissions(user_id):
    """Get permissions for a sub-admin user"""
    try:
        print(f"DEBUG: Getting permissions for user_id: {user_id}")
        
        # Get permissions from the sub_admin_permissions collection
        permissions_collection = db["sub_admin_permissions"]
        permissions_doc = permissions_collection.find_one({"sub_admin_id": str(user_id)})
        
        if permissions_doc:
            permissions = permissions_doc.get("permissions", {})
            print(f"DEBUG: Found permissions in DB: {permissions}")
            return permissions
        
        # If no permissions found, get default permissions based on office
        user = users_collection.find_one({"_id": ObjectId(user_id)})
        if user:
            office = user.get("office", "")
            print(f"DEBUG: User office: {office}")
            
            # Return default permissions based on office
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
            default_perms = default_permissions.get(office, {
                'dashboard': True,
                'conversations': False,
                'faq': False,
                'announcements': False,
                'usage': False,
                'feedback': False
            })
            print(f"DEBUG: Using default permissions: {default_perms}")
            return default_perms
        
        print("DEBUG: No user found, returning empty permissions")
        return {}
    except Exception as e:
        print(f"Error getting sub-admin permissions: {e}")
        import traceback
        traceback.print_exc()
        return {}

def require_sub_admin_permission(permission_name):
    """Decorator to require sub-admin authentication and specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                print(f"DEBUG: Checking permission '{permission_name}' for route {request.endpoint}")
                print(f"DEBUG: Session data: role={session.get('role')}, user_id={session.get('user_id')}")
                
                # Check if user is authenticated as sub-admin
                if not (session.get("role") == "sub-admin" and session.get("user_id")):
                    print("DEBUG: User not authenticated as sub-admin")
                    return redirect("/sub-index?expired=true")
                
                # ✅ Check for 24-hour session expiration
                login_time_str = session.get("login_time")
                if login_time_str:
                    login_time = datetime.fromisoformat(login_time_str)
                    time_elapsed = datetime.utcnow() - login_time
                    
                    # If more than 24 hours have passed, expire the session
                    if time_elapsed > timedelta(hours=24):
                        print("DEBUG: Session expired after 24 hours")
                        session.clear()
                        return redirect("/sub-index?expired=true")
                
                # Get user permissions
                user_id = session.get("user_id")
                permissions = get_sub_admin_permissions(user_id)
                
                print(f"DEBUG: User permissions: {permissions}")
                print(f"DEBUG: Required permission '{permission_name}': {permissions.get(permission_name, False)}")
                
                # Check if user has the required permission
                if not permissions.get(permission_name, False):
                    print(f"DEBUG: User {user_id} does not have permission for {permission_name}")
                    return render_template("access_denied.html", 
                                         permission=permission_name,
                                         user_permissions=permissions)
                
                print(f"DEBUG: Permission '{permission_name}' granted for user {user_id}")
                
                # Add permissions to session for template access
                session['user_permissions'] = permissions
                
                return f(*args, **kwargs)
                
            except Exception as e:
                print(f"ERROR in require_sub_admin_permission decorator: {e}")
                print(traceback.format_exc())
                return redirect("/sub-index")
        
        return decorated
    return decorator

def require_sub_admin_office(f):
    """Decorator to require sub-admin authentication and validate office access"""
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Check if user is authenticated as sub-admin
            if not (session.get("role") == "sub-admin" and session.get("office")):
                print("DEBUG: User not authenticated as sub-admin")
                return redirect("/sub-index?expired=true")
            
            # ✅ Check for 24-hour session expiration
            login_time_str = session.get("login_time")
            if login_time_str:
                login_time = datetime.fromisoformat(login_time_str)
                time_elapsed = datetime.utcnow() - login_time
                
                # If more than 24 hours have passed, expire the session
                if time_elapsed > timedelta(hours=24):
                    print("DEBUG: Session expired after 24 hours")
                    session.clear()
                    return redirect("/sub-index?expired=true")
            
            # Get office from URL parameters
            requested_office = request.args.get("office")
            session_office = session.get("office")
            
            print(f"DEBUG: Requested office: {requested_office}")
            print(f"DEBUG: Session office: {session_office}")
            
            # If office in URL doesn't match session office, redirect to correct office
            if requested_office and requested_office != session_office:
                print(f"DEBUG: Office mismatch, redirecting to {session_office}")
                # Get the current endpoint name
                current_endpoint = request.endpoint
                if current_endpoint:
                    # Convert endpoint back to URL path
                    page_path = current_endpoint.replace('_', '-')
                    redirect_url = f"/{page_path}?office={session_office}"
                else:
                    redirect_url = f"/Sub-dashboard?office={session_office}"
                
                print(f"DEBUG: Redirecting to: {redirect_url}")
                return redirect(redirect_url)
            
            return f(*args, **kwargs)
            
        except Exception as e:
            print(f"ERROR in require_sub_admin_office decorator: {e}")
            print(traceback.format_exc())
            return redirect("/sub-index")
    
    return decorated
def verify_password(stored_password, input_password):
    """Verify password against stored hash or plain text"""
    try:
        stored_str = str(stored_password)
        
        # If it looks like any kind of hash, try check_password_hash
        if '$' in stored_str or ':' in stored_str:
            return check_password_hash(stored_str, input_password)
        else:
            # Plain text fallback
            return stored_str == input_password
    except:
        return False

@app.route('/subadmin/login', methods=['POST'])
def subadmin_login():
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"success": False, "message": "No JSON payload received"}), 400

        office = (data.get("office") or "").strip()
        email = (data.get("email") or "").strip().lower()
        password = data.get("password") or ""

        if not email or not password or not office:
            return jsonify({"success": False, "message": "Missing office, email, or password"}), 400

        # 🔹 Find sub-admin
        user = sub_users.find_one({"email": email})
        if not user:
            return jsonify({"success": False, "message": "Email not found"}), 401

        stored_password = user.get("password", "")
        
        # 🔹 Use the verify_password function
        password_ok = verify_password(stored_password, password)

        if not password_ok:
            return jsonify({"success": False, "message": "Invalid password"}), 401
        
        # 🔹 Update last_login timestamp in database (after password verification)
        sub_users.update_one(
            {"_id": user["_id"]},
            {"$set": {"last_login": datetime.now()}}
        )

        # 🔹 Role check
        role_val = str(user.get("role", "")).strip().lower()
        if not ("sub" in role_val and "admin" in role_val):
            return jsonify({"success": False, "message": "Not a Sub-Admin account"}), 401

        # 🔹 Office check
        saved_office = str(user.get("office", "")).strip()
        if saved_office.lower() != office.lower():
            return jsonify({"success": False, "message": "Invalid office"}), 401

        # 🔹 Extract name from MongoDB document
        user_name = str(user.get("name", "")).strip()
        if not user_name:
            # Fallback to email prefix if name is not available
            user_name = email.split("@")[0].title()

        # 🔹 Create session with both office and name
        session["user_id"] = str(user["_id"])
        session["email"] = user["email"]
        session["role"] = "sub-admin"
        session["office"] = saved_office
        session["name"] = user_name  # ✅ Add name to session
        session["login_time"] = datetime.utcnow().isoformat()  # ✅ Add login timestamp for 24hr expiration

        return jsonify({
            "success": True, 
            "office": saved_office, 
            "name": user_name,  # ✅ Return name in response
            "message": "Login successful"
        })

    except Exception as e:
        current_app.logger.error("ERROR in /subadmin/login: %s", e)
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "message": "Server error during login"}), 500


@app.route('/admin/session', methods=['GET'])
def admin_session():
    """Check admin session status"""
    if "user_id" in session and session.get("role") == "admin":
        # Check for 24-hour session expiration
        login_time_str = session.get("login_time")
        if login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            time_elapsed = datetime.utcnow() - login_time
            
            # If more than 24 hours have passed, expire the session
            if time_elapsed > timedelta(hours=24):
                session.clear()
                return jsonify({
                    "authenticated": False,
                    "expired": True,
                    "message": "Session expired after 24 hours. Please login again."
                })
        
        return jsonify({
            "authenticated": True,
            "email": session.get("email"),
            "role": session.get("role"),
            "office": session.get("office"),
            "name": session.get("name")
        })
    return jsonify({"authenticated": False})

@app.route('/subadmin/session', methods=['GET'])
def subadmin_session():
    if "user_id" in session and session.get("role") == "sub-admin":
        # ✅ Check for 24-hour session expiration
        login_time_str = session.get("login_time")
        if login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            time_elapsed = datetime.utcnow() - login_time
            
            # If more than 24 hours have passed, expire the session
            if time_elapsed > timedelta(hours=24):
                session.clear()
                return jsonify({
                    "authenticated": False,
                    "expired": True,
                    "message": "Session expired after 24 hours. Please login again."
                })
        
        return jsonify({
            "authenticated": True,
            "email": session.get("email"),
            "role": session.get("role"),
            "office": session.get("office"),
            "name": session.get("name")  # ✅ Include name in session response
        })
    return jsonify({"authenticated": False})


@app.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout route"""
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})

@app.route('/subadmin/logout', methods=['POST'])
def subadmin_logout():
    session.clear()
    return jsonify({"success": True, "message": "Logged out"})
# ===========================
# EXISTING ROUTES (Updated with auth where needed)
# ===========================

@app.get("/")
def home():
    """Render the college website home page"""
    return render_template("home.html")

@app.get("/tcc")
def tcc_page():
    """Render the 'This is TCC' page"""
    return render_template("tcc.html")

@app.get("/academics")
def academics_page():
    """Render the Academics page"""
    return render_template("academics.html")

@app.get("/community")
def community_page():
    """Render the Community page"""
    return render_template("community.html")

@app.get("/admission")
def admission_page():
    """Render the Admission page"""
    return render_template("admission.html")

@app.get("/index")
def index_page():
    """Render the main index page"""
    return render_template("index.html")

@app.get("/sub-index")
def sub_index():
    """Render the Sub Admin login page"""
    return render_template("sub-index.html")


# ✅ IMPORTANT: user_contexts and office_tags are now imported from chat.py (single source of truth)
# This ensures reset_context works properly and context is shared across modules

def detect_office_from_message(msg):
    """
    Detect which office the user is asking about based on comprehensive keyword matching
    Returns office tag (e.g., 'admission_office') or None
    """
    msg_lower = msg.lower()
    
    # ✅ ADMISSION OFFICE - Enhanced patterns
    admission_keywords = [
        'admission', 'apply', 'applying', 'enroll', 'enrollment', 'application',
        'transferee', 'transferees', 'requirements', 'requirement', 'psa',
        "voter's certificate", 'form 137', 'form 138', 'deadline', 'period',
        'graduate programs', 'masteral', 'programs offered', 'courses available',
        'offered courses', 'available programs', 'how to apply', 'how to enroll',
        'incoming first-year', 'first year', 'freshmen'
    ]
    admission_score = sum(1 for keyword in admission_keywords if keyword in msg_lower)
    
    # ✅ REGISTRAR'S OFFICE - Enhanced patterns  
    registrar_keywords = [
        'registrar', 'transcript', 'tor', 'transcript of records', 'grades', 
        'academic records', 'documents', 'document', 'claiming', 'claim',
        'certificate', 'certification', 'certified copy', 'tuition fee',
        'tuition', 'free tuition', 'slots', 'available slots', 'entrance exam',
        'psychological test', 'student portal', 'form 137', 'good moral',
        'valid id', 'authorization letter', 'drop', 'graduation'
    ]
    registrar_score = sum(1 for keyword in registrar_keywords if keyword in msg_lower)
    
    # ✅ ICT OFFICE - Enhanced patterns
    ict_keywords = [
        'ict', 'e-hub', 'ehub', 'tcc ehub', 'tcc e-hub', 'password', 'username',
        'student id', 'login', 'login attempts', 'failed login', 'account locked',
        'deactivated account', 'recovery email', 'forgot password', 'password reset',
        'reset password', 'student portal', 'access', 'locked out', 'misu',
        'qr code', 'web browser', 'update button', 'my account'
    ]
    ict_score = sum(1 for keyword in ict_keywords if keyword in msg_lower)
    
    # ✅ GUIDANCE OFFICE - Enhanced patterns
    guidance_keywords = [
        'guidance', 'counseling', 'counselor', 'scholarship', 'career advice',
        'career guidance', 'personal counseling', 'academic counseling',
        'financial aid', 'mental health', 'psychological', 'stress',
        'study habits', 'time management', 'goal setting', 'resume',
        'interview preparation', 'job placement', 'internship', 'career assessment',
        'academic planning', 'course selection', 'career opportunities',
        'job search', 'graduate school preparation', 'personal problems',
        'peer counseling', 'academic difficulties'
    ]
    guidance_score = sum(1 for keyword in guidance_keywords if keyword in msg_lower)
    
    # ✅ OSA OFFICE - Enhanced patterns
    osa_keywords = [
        'osa', 'student affairs', 'office of student affairs', 'clubs', 
        'organizations', 'student activities', 'activities', 'discipline',
        'student government', 'extracurricular', 'sports', 'cultural events',
        'leadership programs', 'student council', 'campus events',
        'social activities', 'volunteer', 'community service', 'student handbook',
        'code of conduct', 'disciplinary', 'student rights', 'campus policies',
        'event planning', 'organization registration', 'club membership'
    ]
    osa_score = sum(1 for keyword in osa_keywords if keyword in msg_lower)
    
    # Find office with highest score (must have at least 1 match)
    scores = {
        'admission_office': admission_score,
        'registrar_office': registrar_score,
        'ict_office': ict_score,
        'guidance_office': guidance_score,
        'osa_office': osa_score
    }
    
    max_score = max(scores.values())
    if max_score > 0:
        # Return the office with highest score
        detected_office = max(scores, key=scores.get)
        print(f"🎯 Office detected: {detected_office} (score: {max_score})")
        return detected_office
    
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
        # ✅ Handle both dict and string formats for backward compatibility
        if isinstance(user_contexts[user], dict):
            # New format: dict with 'current_office' and 'pending_switch'
            current_office = user_contexts[user].get('current_office')
            if current_office:
                office = office_tags.get(current_office, current_office)
        else:
            # Old format: just a string with office tag
            office = office_tags.get(user_contexts[user], user_contexts[user])
    elif sender == "user":
        detected_tag = detect_office_from_message(message)
        if detected_tag:
            office = office_tags.get(detected_tag, detected_tag)
            # ✅ Store as dict to support pending_switch
            if user not in user_contexts:
                user_contexts[user] = {}
            if isinstance(user_contexts[user], dict):
                user_contexts[user]['current_office'] = detected_tag
            else:
                # Convert old string format to new dict format
                user_contexts[user] = {'current_office': detected_tag}
    if not office:
        office = "General"

    # Use UTC datetime for accurate timestamp
    timestamp = datetime.now(UTC)
    
    document = {
        "user": user,
        "sender": sender,
        "message": message,
        "office": office,
        "status": status,  # ✅ new field
        "timestamp": timestamp,  # UPDATED: Use datetime object instead of string
        "date": timestamp.isoformat()  # Keep ISO string for backward compatibility
    }
    
    try:
        conversations_collection.insert_one(document)
        print(f"Message saved (office={office}, status={status})")
    except Exception as e:
        print(f"Error saving message: {e}")
    
    return office
  # ✅ Return for reuse in predict()


def get_suggested_messages_from_settings():
    """
    Get suggested messages from bot settings in the database
    """
    try:
        # Get settings from MongoDB
        settings_doc = db["bot_settings"].find_one({}, {"_id": 0})
        
        if settings_doc and "suggested_messages" in settings_doc:
            suggested_messages = settings_doc["suggested_messages"]
            
            # Handle different formats of suggested_messages
            if isinstance(suggested_messages, list):
                # If it's a simple list of strings
                if suggested_messages and isinstance(suggested_messages[0], str):
                    return suggested_messages[:4]  # Limit to 4 suggestions
                # If it's a list of objects with categories
                elif suggested_messages and isinstance(suggested_messages[0], dict):
                    # Flatten all messages from all categories
                    all_messages = []
                    for category in suggested_messages:
                        if "messages" in category and isinstance(category["messages"], list):
                            all_messages.extend(category["messages"])
                    return all_messages[:4]  # Limit to 4 suggestions
        
        # Fallback to default suggestions if none configured
        return [
            "How can I help you?",
            "What services are available?",
            "Office contact information",
            "Office hours and location"
        ]
        
    except Exception as e:
        print(f"Error getting suggested messages from settings: {e}")
        # Return default suggestions on error
        return [
            "How can I help you?",
            "What services are available?",
            "Office contact information", 
            "Office hours and location"
        ]

@app.post("/predict")
def predict():
    start_time = time.time()
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"answer": "Invalid request data."}), 400
            
        text = data.get("message")
        user = data.get("user", "guest")
        user_language = data.get("language", "en")
        
        print(f"🚀 Processing request for user '{user}': '{text[:50]}...'")

        if not text or not text.strip():
            return jsonify({"answer": "Please type something."})
        
        # ✅ EARLY OFF-TOPIC DETECTION - Quick check before expensive operations
        # This prevents timeout by returning domain refusal message immediately for obviously off-topic questions
        text_lower = text.lower().strip()
        off_topic_keywords = [
            # Math and calculations
            'solve', 'calculate', 'what is 2+2', 'math problem', 'equation', 'formula',
            'algebra', 'calculus', 'geometry', 'trigonometry', 'derivative', 'integral',
            'square root', 'multiply', 'divide', 'percentage', 'fraction', 'decimal',
            # General knowledge (not TCC-specific)
            'what is the capital', 'history of', 'tell me about', 'who is the president',
            'what is the population', 'where is', 'when did', 'who invented', 'what happened in',
            'world war', 'ancient', 'civilization', 'country', 'city', 'continent',
            # Personal advice (not TCC-related)
            'should i break up', 'relationship advice', 'dating advice', 'personal problem',
            'how to get a girlfriend', 'how to get a boyfriend', 'marriage advice', 'divorce',
            'family problem', 'friend problem', 'social anxiety', 'loneliness', 'depression',
            # Health and Medical (not TCC health services)
            'how to lose weight', 'diet plan', 'exercise routine', 'workout', 'gym',
            'symptoms', 'diagnosis', 'medicine', 'prescription', 'doctor', 'hospital',
            'cure', 'treatment', 'disease', 'illness', 'pain', 'headache', 'fever',
            # Legal advice
            'legal advice', 'lawyer', 'lawsuit', 'court', 'legal case', 'contract',
            'divorce lawyer', 'criminal', 'arrest', 'lawsuit', 'legal document',
            # Financial advice (non-TCC)
            'how to invest', 'stock market', 'cryptocurrency', 'bitcoin', 'trading',
            'how to make money', 'side hustle', 'business idea', 'startup', 'entrepreneur',
            'loan', 'credit card', 'mortgage', 'insurance', 'retirement plan',
            # Technology help (not TCC systems)
            'how to use windows', 'install software', 'computer virus', 'phone problem',
            'how to hack', 'programming tutorial', 'coding help', 'python tutorial',
            'javascript tutorial', 'website development', 'app development', 'gaming pc',
            'iphone', 'android', 'macbook', 'laptop recommendation', 'best phone',
            # Entertainment
            'movie', 'netflix', 'youtube', 'spotify', 'music', 'song', 'artist',
            'celebrity', 'actor', 'actress', 'tv show', 'series', 'anime', 'manga',
            'video game', 'gaming', 'playstation', 'xbox', 'nintendo', 'steam',
            # Food and Recipes
            'recipe', 'cooking', 'how to cook', 'baking', 'restaurant', 'food',
            'cuisine', 'ingredients', 'how to make', 'dish', 'meal prep', 'diet',
            # Travel
            'travel', 'vacation', 'hotel', 'flight', 'ticket', 'tourist', 'destination',
            'visa', 'passport', 'airline', 'booking', 'resort', 'beach', 'mountain',
            # Sports
            'sports score', 'football', 'basketball', 'soccer', 'baseball', 'tennis',
            'olympics', 'championship', 'player', 'team', 'match', 'game result',
            # News and Current Events
            'news', 'breaking news', 'politics', 'election', 'government', 'president',
            'latest news', 'headlines', 'current events', 'world news', 'local news',
            # Weather
            'weather', 'forecast', 'temperature', 'rain', 'snow', 'hurricane', 'storm',
            'climate', 'season', 'sunny', 'cloudy', 'windy',
            # Shopping
            'where to buy', 'best price', 'shopping', 'amazon', 'online store',
            'product review', 'best product', 'cheap', 'discount', 'sale',
            # Social Media
            'instagram', 'facebook', 'twitter', 'tiktok', 'snapchat', 'social media',
            'how to post', 'followers', 'likes', 'viral', 'trending',
            # Other Educational Topics (not TCC)
            'how to learn', 'online course', 'tutorial', 'certification', 'skill',
            'language learning', 'how to speak', 'grammar', 'vocabulary',
            # Miscellaneous
            'joke', 'funny', 'meme', 'quote', 'inspirational', 'motivation',
            'horoscope', 'zodiac', 'fortune', 'prediction', 'astrology',
            'how to', 'tips for', 'tricks', 'life hack', 'productivity',
            'fashion', 'style', 'outfit', 'makeup', 'beauty', 'skincare',
            'pet', 'dog', 'cat', 'animal', 'pet care', 'veterinary',
        ]
        
        # TCC-related keywords that indicate the question IS on-topic
        tcc_keywords = [
            'tcc', 'tanauan city college', 'college', 'admission', 'enrollment', 'registrar',
            'transcript', 'tuition', 'scholarship', 'guidance', 'osa', 'ict', 'misu',
            'course', 'program', 'degree', 'student', 'faculty', 'campus', 'office',
            'application', 'requirements', 'deadline', 'semester', 'academic', 'enroll',
            'bachelor', 'bs', 'bsed', 'bscpe', 'entrepreneurship', 'accounting', 'public administration'
        ]
        
        # Check if question contains TCC-related keywords
        has_tcc_keywords = any(keyword in text_lower for keyword in tcc_keywords)
        
        # If no TCC keywords and has off-topic keywords, return domain refusal immediately
        if not has_tcc_keywords and any(keyword in text_lower for keyword in off_topic_keywords):
            print(f"🚫 Early off-topic detection: Returning domain refusal message immediately")
            from chat import DOMAIN_REFUSAL_MESSAGE
            return jsonify({
                "answer": DOMAIN_REFUSAL_MESSAGE,
                "office": "General",
                "status": "resolved",
                "detected_language": "en",
                "early_rejection": True
            })

        # Proceed without response caching
        cache_key = f"{user}:{text.lower().strip()}"

        # Store original message for later use
        original_message = text

        # Check if required modules are available
        try:
            from chat import (
                get_response,
                user_contexts,
                office_tags,
                detect_office_from_message,
                get_openai_fallback
            )
        except ImportError as e:
            print(f"[ERROR] Chat module import error: {e}")
            return jsonify({
                "answer": "Chatbot is temporarily unavailable. Please try again later.",
                "error": "Module import failed"
            }), 500
        
        # Check if model is available
        try:
            import torch
            import os
            if not os.path.exists("data.pth"):
                print("[WARNING] Model file not found, using OpenAI fallback")
                ai_answer = get_openai_fallback(text) or "Hello! I'm TCC Assistant. How can I help you today?"
                return jsonify({
                    "answer": ai_answer,
                    "office": "General",
                    "status": "resolved",
                    "model_available": False
                })
        except ImportError:
            print("[WARNING] PyTorch not available, using OpenAI fallback")
            ai_answer = get_openai_fallback(text) or "Hello! I'm TCC Assistant. How can I help you today?"
            return jsonify({
                "answer": ai_answer,
                "office": "General", 
                "status": "resolved",
                "model_available": False
            })

        detected_language = "en"
        
        # ✅ Run translation even on Railway; set DISABLE_TRANSLATION=true to skip
        translation_start = time.time()
        if os.getenv('DISABLE_TRANSLATION', '').lower() != 'true':
            try:
                filipino_keywords = [
                    'ako', 'ikaw', 'siya', 'kami', 'tayo', 'kayo', 'sila',
                    'ang', 'ng', 'mga', 'sa', 'na', 'ay', 'po', 'opo',
                    'magandang', 'salamat', 'paano', 'ano', 'saan', 'kailan',
                    'kumusta', 'mabuti', 'hindi', 'oo', 'wala', 'mayroon',
                    'naman', 'lang', 'din', 'rin', 'ba', 'kasi', 'pero',
                    'gusto', 'kailangan', 'pwede', 'paki'
                ]
                text_lower = text.lower()
                has_filipino = any(word in text_lower.split() for word in filipino_keywords)
                if has_filipino:
                    detected_language = 'tl'
                    print(f"🌐 Detected Filipino keywords in message")
                else:
                    detected_language = detect(text)
                    print(f"🌐 Auto-detected language: {detected_language}")
                    ALLOWED_LANGUAGES = ['en', 'tl', 'fil']
                    if detected_language not in ALLOWED_LANGUAGES:
                        print(f"⚠️ Language '{detected_language}' not in supported list. Treating as English.")
                        detected_language = 'en'
                    elif detected_language == 'fil':
                        detected_language = 'tl'
                if detected_language == 'tl':
                    translated = GoogleTranslator(source='tl', target='en').translate(text)
                    print(f"📝 Translated Filipino to English: '{original_message}' → '{translated}'")
                    text = translated
                else:
                    print(f"✅ Message in English: {text}")
            except LanguageNotSupportedException as lang_error:
                print(f"⚠️ Language not supported: {lang_error}, defaulting to English")
                detected_language = "en"
            except Exception as translate_error:
                print(f"⚠️ Translation detection error: {translate_error}")
                detected_language = "en"
        else:
            print("🛑 Translation disabled via DISABLE_TRANSLATION env var")
        
        translation_time = time.time() - translation_start
        print(f"⏱️ Translation processing took {translation_time:.3f}s")
        
        print(f"User {user} asked: {text}")

        # ✅ CHECK FOR PENDING OFFICE SWITCH CONFIRMATION
        pending_switch_office = None
        if user in user_contexts:
            # ✅ Handle both dict and string formats
            if isinstance(user_contexts[user], dict):
                pending_switch_office = user_contexts[user].get('pending_switch')
            else:
                # Old format (string) doesn't have pending_switch
                pending_switch_office = None
        
        if pending_switch_office:
            print(f"🔍 Found pending office switch for user '{user}': {pending_switch_office}")
        
        # Check if user is confirming the office switch
        confirmation_keywords = ['yes', 'yeah', 'sure', 'okay', 'ok', 'yep', 'yup', 'please', 'switch', 'connect', 'go ahead', 'proceed']
        confirmation_keywords_filipino = ['oo', 'sige', 'okay', 'opo', 'ge']
        all_confirmation_keywords = confirmation_keywords + confirmation_keywords_filipino
        
        text_lower = text.lower().strip()
        is_confirming = any(keyword == text_lower or text_lower.startswith(keyword + ' ') for keyword in all_confirmation_keywords)
        
        if is_confirming:
            print(f"✅ User confirmation detected: '{text_lower}'")
        
        if pending_switch_office and is_confirming:
            # ✅ AUTO-SWITCH: User confirmed the office switch
            from chat import set_user_current_office
            set_user_current_office(user, pending_switch_office)
            
            # Clear pending switch and update current office
            if isinstance(user_contexts[user], dict):
                user_contexts[user].pop('pending_switch', None)
                user_contexts[user]['current_office'] = pending_switch_office
            
            office_name = office_tags.get(pending_switch_office, pending_switch_office)
            switch_confirmation = f"Great! I've switched to help you with {office_name} information. How can I assist you?"
            
            # Translate confirmation if needed
            if detected_language == 'tl':
                try:
                    switch_confirmation = GoogleTranslator(source='en', target='tl').translate(switch_confirmation)
                except:
                    pass  # Keep English if translation fails
            
            print(f"✅ Office switch confirmed: {office_name} for user '{user}'")
            
            # Save the confirmation exchange
            save_message(user=user, sender="user", message=original_message, detected_office=pending_switch_office)
            save_message(user=user, sender="bot", message=switch_confirmation, detected_office=pending_switch_office)
            
            return jsonify({
                "answer": switch_confirmation,
                "office": office_name,
                "status": "resolved",
                "detected_language": detected_language,
                "office_switched": True,
                "new_office": office_name,
                "new_office_tag": pending_switch_office
            })

        # ✅ Detect office from the message FIRST (using improved detection)
        detected_office_tag = detect_office_from_message(text)
        detected_office = office_tags.get(detected_office_tag, "General") if detected_office_tag else "General"
        print(f"🎯 Detected office: {detected_office}")

        # ✅ OFFICE CONTEXT SWITCHING PROTECTION
        # Check if user is trying to switch to a different office without resetting
        current_office_tag = None
        if user in user_contexts:
            if isinstance(user_contexts[user], dict):
                current_office_tag = user_contexts[user].get('current_office')
            else:
                # Old format: string is the office tag
                current_office_tag = user_contexts[user] if isinstance(user_contexts[user], str) else None
        
        # Debug logging
        print(f"🔍 Context Switch Check:")
        print(f"   User: {user}")
        print(f"   Current office in context: {current_office_tag}")
        print(f"   Detected office from message: {detected_office_tag}")
        print(f"   User contexts: {user_contexts.get(user, 'Not set')}")
        
        # If user has an active office context and is trying to switch to a different office
        if current_office_tag and detected_office_tag and current_office_tag != detected_office_tag:
            current_office_name = office_tags.get(current_office_tag, current_office_tag)
            new_office_name = office_tags.get(detected_office_tag, detected_office_tag)
            
            print(f"⚠️ Office context switch detected: {current_office_name} → {new_office_name}")
            
            # Create warning message
            warning_message = (
                f"⚠️ **Context Switch Detected**\n\n"
                f"You're currently in the **{current_office_name}** context. "
                f"I noticed you're now asking about the **{new_office_name}**.\n\n"
                f"To ensure clear and accurate responses, please **reset the {current_office_name} context** first before switching to the {new_office_name}.\n\n"
                f"💡 **How to reset:**\n"
                f"• Click the **'Reset Context'** button at the top of the chat\n\n"
                f"This helps me provide you with the most relevant information for each office! 😊"
            )
            
            # Translate warning if user's language is Filipino
            if detected_language == 'tl':
                try:
                    warning_message = GoogleTranslator(source='en', target='tl').translate(warning_message)
                except Exception as e:
                    print(f"⚠️ Warning translation failed: {e}")
                    # Keep English if translation fails
            
            # Save the exchange
            save_message(user=user, sender="user", message=original_message, detected_office=current_office_tag)
            save_message(user=user, sender="bot", message=warning_message, detected_office=current_office_tag, status="escalated")
            
            return jsonify({
                "answer": warning_message,
                "office": current_office_name,
                "status": "escalated",
                "detected_language": detected_language,
                "current_office": current_office_name,
                "current_office_tag": current_office_tag,
                "attempted_office": new_office_name,
                "attempted_office_tag": detected_office_tag,
                "requires_reset": True
            })

        # Search FAQs first for relevant answers
        faq_start = time.time()
        faq_response = None
        try:
            faq_search_result = search_faqs(text, top_k=3)
            if faq_search_result['success'] and faq_search_result['results']:
                # Check if any FAQ has high similarity score (above 0.8)
                best_match = faq_search_result['results'][0]
                if best_match['score'] > 0.8:
                    faq_response = best_match['answer']
                    print(f"FAQ match found with score: {best_match['score']}")
        except Exception as e:
            print(f"Error searching FAQs: {e}")
        
        faq_time = time.time() - faq_start
        print(f"⏱️ FAQ search took {faq_time:.3f}s")

        # Get chatbot response (in English)
        # Note: get_response() now includes enhanced website content search with improved
        # scoring, query expansion, and better context aggregation for more accurate predictions
        response_start = time.time()
        if faq_response:
            response = faq_response
            print("Using FAQ response")
        else:
            response = get_response(text, user_id=user, save_messages=False)
            print("Using neural network response with enhanced website content search")
        
        response_time = time.time() - response_start
        total_time = time.time() - start_time
        
        # Warn if response is taking too long
        if total_time > 20:
            print(f"⚠️ Slow response: {total_time:.2f}s (response: {response_time:.3f}s)")
        else:
            print(f"⏱️ Response generation took {response_time:.3f}s (total: {total_time:.2f}s)")

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
            "would you like me to connect you",     # NEW
            "Context Switch Detected",
            "Click the **'Reset Context'** button at the top of the chat",
            "⚠️ **Context Switch Detected**",  # Enhanced pattern for your specific message
            "reset context",  # Additional pattern for context reset
            "reset the",  # Pattern for "reset the Admissions Office context"
            "switching to the",  # Pattern for "switching to the Registrar's Office"
            "office context",  # Pattern for office context messages
            "context switch",  # Additional pattern
            "reset context'",  # Pattern with apostrophe
            "type 'reset context'",  # Pattern for "type 'reset context'"
            "clear the current office context",  # Pattern for "clear the current office context"
            "ensure clear and accurate responses"  # Pattern from your message
        ]

        # Detect resolved/unresolved/escalated status
        # First check for escalation patterns (highest priority)
        is_escalated = False
        if response:
            response_lower = response.lower()
            for pattern in escalation_patterns:
                if pattern.lower() in response_lower:
                    is_escalated = True
                    print(f"🚨 ESCALATION DETECTED: Pattern '{pattern}' found in response")
                    break
        
        if is_escalated:
            status = "escalated"
            print(f"✅ STATUS SET TO ESCALATED for response: {response[:100]}...")
        elif response and any(p in response.lower() for p in unresolved_patterns):
            # Try OpenAI fallback for unresolved responses (with timeout)
            try:
                ai_answer = get_openai_fallback(text)
                if ai_answer:
                    response = ai_answer
                    status = "resolved"
                    print("🤝 OpenAI fallback resolved the response")
                else:
                    status = "unresolved"
                    print(f"❌ STATUS SET TO UNRESOLVED for response: {response[:100]}...")
            except Exception as e:
                print(f"⚠️ OpenAI fallback failed: {e}, keeping original response")
                status = "unresolved"
        else:
            status = "resolved"
            print(f"✅ STATUS SET TO RESOLVED for response: {response[:100]}...")
        
        print(f"🎯 FINAL STATUS: {status}")

        # ✅ AUTO-SWITCH: Detect office switch suggestions and extract suggested office
        suggested_office = None
        suggested_office_tag = None
        if "i think you might be asking about" in response.lower() or "would you like me to connect you" in response.lower():
            # Extract office name from response
            for office_tag, office_name in office_tags.items():
                if office_name.lower() in response.lower():
                    suggested_office = office_name
                    suggested_office_tag = office_tag
                    print(f"🔄 Office switch suggested: {office_name} (tag: {office_tag})")
                    break

        # ✅ Translate response back to user's language (English or Filipino only)
        response_translation_start = time.time()
        translated_response = response
        try:
            if detected_language == 'tl':
                # Only translate back to Filipino if user's language was Filipino
                translated_response = GoogleTranslator(source='en', target='tl').translate(response)
                print(f"🌐 Translated response back to Filipino: '{response}' → '{translated_response}'")
            else:
                print(f"✅ Response kept in English")
        except LanguageNotSupportedException as lang_error:
            print(f"⚠️ Language not supported for response: {lang_error}")
            translated_response = response
        except Exception as translate_error:
            print(f"⚠️ Translation error for response: {translate_error}")
            # Use English response if translation fails
            translated_response = response
        
        response_translation_time = time.time() - response_translation_start
        print(f"⏱️ Response translation took {response_translation_time:.3f}s")

        # ✅ Save user query (original message in user's language) with detected office
        save_message(
            user=user,
            sender="user",
            message=original_message,
            detected_office=detected_office_tag  # Use the tag, not the display name
        )

        # ✅ Save bot response (translated response in user's language) with resolution status and office
        save_message(
            user=user,
            sender="bot",
            message=translated_response,
            detected_office=detected_office_tag,  # Use the tag, not the display name
            status=status
        )

        # ✅ STORE OFFICE CONTEXT: Update user_contexts with the detected office
        if detected_office_tag:
            if user not in user_contexts:
                user_contexts[user] = {}
            elif not isinstance(user_contexts[user], dict):
                # Convert old string format to new dict format
                old_office = user_contexts[user]
                user_contexts[user] = {'current_office': old_office}
            
            # Store the current office context
            user_contexts[user]['current_office'] = detected_office_tag
            print(f"✅ Stored office context for user '{user}': {detected_office} (tag: {detected_office_tag})")

        # Get suggested messages from bot settings
        suggested_messages = get_suggested_messages_from_settings()
        
        # ✅ Store suggested office in session for next message
        if suggested_office_tag:
            # Store pending office switch in user_contexts
            if user not in user_contexts:
                user_contexts[user] = {}
            elif not isinstance(user_contexts[user], dict):
                # Convert old string format to dict
                old_office = user_contexts[user]
                user_contexts[user] = {'current_office': old_office}
            
            user_contexts[user]['pending_switch'] = suggested_office_tag
            print(f"📌 Stored pending office switch for user '{user}': {suggested_office} (tag: {suggested_office_tag})")
        
        # Calculate total processing time
        total_time = time.time() - start_time
        print(f"⚡ Total processing time: {total_time:.3f}s")
        
        # Prepare response data
        response_data = {
            "answer": translated_response,
            "original_answer": response,  # English version for debugging
            "office": detected_office,  # Return the display name for frontend
            "status": status,
            "detected_language": detected_language,
            "original_message": original_message,
            "translated_message": text if detected_language != 'en' else None,
            "context_in_memory": user_contexts.get(user),
            "vector_enabled": vector_store.index is not None,
            "vector_stats": vector_store.get_stats(),
            "suggested_messages": suggested_messages,
            "response_time": round(total_time * 1000),  # Convert to milliseconds
            "performance_metrics": {
                "translation_time": round(translation_time * 1000),
                "faq_search_time": round(faq_time * 1000),
                "response_generation_time": round(response_time * 1000),
                "response_translation_time": round(response_translation_time * 1000),
                "total_time": round(total_time * 1000)
            },
            "suggested_office": suggested_office,  # ✅ Office name for display
            "suggested_office_tag": suggested_office_tag  # ✅ Office tag for switching
        }
        
        # Do not cache responses; return directly
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in predict: {e}")
        traceback.print_exc()
        return jsonify({
            "answer": "Sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500


# ===========================
# TRANSLATION CHATBOT ROUTES
# ===========================

@app.route("/chat", methods=["POST"])
def chat():
    """
    Simple rules-based chatbot endpoint for translation system.
    Receives message in English (already translated by frontend) and returns response.
    Now saves conversations to MongoDB with status tracking.
    """
    try:
        data = request.get_json()
        user_message = data.get("message", "")
        original_message = data.get("original_message", user_message)  # Original user message (before translation)
        user = data.get("user", "guest") # Support both user_id and user
        
        if not user_message or not user_message.strip():
            return jsonify({"response": "Please type something."})
        
        # Get response from rules-based chatbot (in English)
        # Returns dict with response, status, and office
        chatbot_result = get_chatbot_response(user_message)
        
        # Extract response details
        response_text = chatbot_result.get('response', '')
        status = chatbot_result.get('status', 'resolved')
        office = chatbot_result.get('office', 'General')
        
        # Add Pinecone vector search results if available
        pinecone_results = []
        if pinecone_available:
            try:
                # Search for similar content using Pinecone
                search_results = vs.search_similar(user_message, top_k=3)
                pinecone_results = search_results
                print(f"🔍 Pinecone search found {len(search_results)} results for: {user_message}")
            except Exception as e:
                print(f"⚠️ Pinecone search failed: {e}")
                pinecone_results = []
        
        # Save original user message to MongoDB (in user's language) with status
        save_message(
            user=user,
            sender="user",
            message=original_message,
            detected_office=office,
            status=status
        )
        
        # Note: Frontend will translate the response back to user's language
        # The translated version will be saved by frontend via /save_bot_message
        
        return jsonify({
            "response": response_text,
            "user": user,
            "status": status,
            "office": office,
            "pinecone_available": pinecone_available,
            "pinecone_results": pinecone_results,
            "pinecone_index": PINECONE_INDEX_NAME if pinecone_available else None
        })
    
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "response": "Sorry, I encountered an error. Please try again.",
            "status": "unresolved"
        }), 500


@app.route("/translate", methods=["POST"])
def translate():
    """
    Optional backend translation endpoint using Google Translate API.
    Note: The frontend handles translation directly, but this can be used as backup.
    """
    try:
        data = request.get_json()
        text = data.get("text", "")
        target_lang = data.get("target", "en")
        
        if not text:
            return jsonify({"translated": ""})
        
        # Use Google Translate API (free, no key needed)
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={text}"
        result = requests.get(url).json()
        translated = result[0][0][0]
        
        return jsonify({"translated": translated})
    
    except Exception as e:
        print(f"Error in translate endpoint: {e}")
        return jsonify({
            "translated": text,  # Return original text on error
            "error": str(e)
        }), 500


@app.route("/guarded-chat", methods=["POST"])
def guarded_chat():
    """
    Lightweight endpoint to test the TCC domain-guarded GPT workflow.
    """
    payload = request.get_json(silent=True) or {}
    user_message = (payload.get("message") or "").strip()
    user_id = (payload.get("user") or payload.get("user_id") or "guest").strip() or "guest"

    if not user_message:
        return jsonify({"success": False, "message": "A message is required."}), 400

    response_text = get_tcc_guarded_response(user_message, user_id=user_id)
    refused = response_text.strip().startswith(DOMAIN_REFUSAL_MESSAGE)

    print(f"[GuardedChat] user={user_id} | refused={refused} | message_preview={user_message[:80]}")

    return jsonify(
        {
            "success": True,
            "response": response_text,
            "refused": refused,
        }
    )


@app.route("/save_bot_message", methods=["POST"])
def save_bot_message():
    """
    Save bot response message to MongoDB with status tracking.
    Called by frontend after translation is complete.
    """
    try:
        data = request.get_json()
        user = data.get("user", "guest")  # Support both user_id and user
        message = data.get("message", "")
        status = data.get("status", "resolved")
        office = data.get("office", "General")
        
        if message:
            # Save bot message to MongoDB with status
            save_message(
                user=user,
                sender="bot",
                message=message,
                detected_office=office,
                status=status
            )
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "No message provided"}), 400
    
    except Exception as e:
        print(f"Error saving bot message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


cleared_users = set()

@app.post("/clear_history")
def clear_history():
    """Clear user's chat history from frontend display only (keeps MongoDB data for records)"""
    data = request.get_json()
    user = data.get("user") or "guest"
    clear_mongodb = data.get("clear_mongodb", False)  # ✅ Changed to False - keep MongoDB data by default

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

        # ✅ Updated message to reflect MongoDB data is preserved
        if clear_mongodb:
            message = f"Chat history cleared from display and database"
        else:
            message = f"Chat history cleared from display (database records preserved)"

        return jsonify({
            "status": "success",
            "message": message,
            "details": {
                "display_cleared": memory_count,
                "mongodb_cleared": mongo_deleted,
                "mongodb_preserved": not clear_mongodb,
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
# Note: user_contexts is managed by chat.py module

@app.post("/reset_context")
def reset_context():
    """
    Reset user's conversation context (optionally per office)
    Clears the shared user_contexts dictionary from chat.py
    """
    data = request.get_json()
    user = data.get("user", "guest")
    office = data.get("office", None)  # Optional office parameter (office tag like 'admission_office')
    
    try:
        print(f"🔄 Reset request - User: {user}, Office: {office}")
        print(f"🔍 Context before reset: {user_contexts.get(user, 'Not set')}")
        
        # ✅ Reset using the chat.py function (which modifies the shared user_contexts)
        reset_user_context(user, office)
        
        print(f"🔍 Context after reset: {user_contexts.get(user, 'Not set')}")
        
        if office:
            office_name = office_tags.get(office, office)
            status_msg = f"Context reset successfully for {office_name}"
            print(f"✅ Context reset for user '{user}' - Office: {office_name}")
        else:
            status_msg = "All contexts reset successfully"
            print(f"✅ All contexts reset for user '{user}'")
            
        return jsonify({
            "status": "success",
            "message": status_msg,
            "user": user,
            "office": office,
            "context_cleared": True  # ✅ frontend can use this flag
        })
    except Exception as e:
        print(f"❌ Error resetting context: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500



    




@app.get("/announcements")
def get_announcements():
    """Get all active announcements from MongoDB only (Pinecone for search)"""
    try:
        # Get announcements from MongoDB only
        announcements = get_active_announcements()
        
        # Format announcements for frontend display
        formatted_announcements = []
        for ann in announcements:
            formatted_announcements.append({
                "id": ann.get("id", ""),
                "title": ann.get("title", ""),
                "message": ann.get("message", ""),
                "date": ann.get("date", ""),
                "priority": ann.get("priority", "medium"),
                "category": ann.get("category", "general"),
                "office": ann.get("office", ann.get("category", "General")),
                "source": ann.get("source", "mongodb"),
                "active": ann.get("active", True),
                "created_by": ann.get("created_by", "")
            })
        
        print(f"API: Returning {len(formatted_announcements)} announcements from MongoDB")
        return jsonify({
            "announcements": formatted_announcements, 
            "count": len(formatted_announcements),
            "source": "mongodb_only"
        })
    except Exception as e:
        print(f"Error getting announcements: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "announcements": [], 
            "count": 0,
            "error": str(e)
        }), 500

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
        # Get Pinecone index stats if available
        pinecone_stats = None
        if pinecone_available and pinecone_index:
            try:
                pinecone_stats = pinecone_index.describe_index_stats()
            except Exception as e:
                pinecone_stats = {"error": str(e)}
        
        return jsonify({
            "status": "healthy",
            "pinecone_available": pinecone_available,
            "pinecone_index": PINECONE_INDEX_NAME if pinecone_available else None,
            "pinecone_region": PINECONE_ENV if pinecone_available else None,
            "pinecone_stats": pinecone_stats,
            "vector_enabled": vector_store.index is not None,
            "database_connected": conversations_collection is not None,
            "vector_stats": vector_store.get_stats()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.route('/api/pinecone/status', methods=['GET'])
def pinecone_status():
    """Get Pinecone connection status and statistics"""
    try:
        if not pinecone_available:
            return jsonify({
                "status": "unavailable",
                "message": "Pinecone not configured or failed to initialize",
                "api_key_set": bool(PINECONE_API_KEY),
                "index_name": PINECONE_INDEX_NAME,
                "region": PINECONE_ENV
            })
        
        # Get index statistics
        stats = pinecone_index.describe_index_stats()
        
        return jsonify({
            "status": "available",
            "index_name": PINECONE_INDEX_NAME,
            "region": PINECONE_ENV,
            "stats": {
                "total_vector_count": stats.get('total_vector_count', 0),
                "dimension": stats.get('dimension', 384),
                "index_fullness": stats.get('index_fullness', 0.0)
            },
            "environment": {
                "api_key_set": bool(PINECONE_API_KEY),
                "index_name": PINECONE_INDEX_NAME,
                "region": PINECONE_ENV
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "api_key_set": bool(PINECONE_API_KEY),
            "index_name": PINECONE_INDEX_NAME,
            "region": PINECONE_ENV
        }), 500

@app.route('/api/pinecone/search', methods=['POST'])
def pinecone_search():
    """Search using Pinecone vector store"""
    try:
        if not pinecone_available:
            return jsonify({
                "error": "Pinecone not available",
                "message": "Vector search is not configured or failed to initialize"
            }), 503
        
        data = request.get_json()
        query = data.get('query', '')
        top_k = data.get('top_k', 5)
        
        if not query.strip():
            return jsonify({"error": "Query is required"}), 400
        
        # Use VectorStore for search
        results = vs.search_similar(query, top_k=top_k)
        
        return jsonify({
            "query": query,
            "results": results,
            "total_results": len(results),
            "pinecone_index": PINECONE_INDEX_NAME,
            "region": PINECONE_ENV
        })
        
    except Exception as e:
        print(f"Pinecone search error: {e}")
        return jsonify({
            "error": str(e),
            "message": "Search failed"
        }), 500

@app.route('/api/pinecone/add', methods=['POST'])
def pinecone_add_vector():
    """Add a vector to Pinecone index"""
    try:
        if not pinecone_available:
            return jsonify({
                "error": "Pinecone not available",
                "message": "Vector store is not configured or failed to initialize"
            }), 503
        
        data = request.get_json()
        text = data.get('text', '')
        metadata = data.get('metadata', {})
        vector_id = data.get('id', None)
        
        if not text.strip():
            return jsonify({"error": "Text is required"}), 400
        
        # Add vector using VectorStore
        result = vs.add_vector(text, metadata=metadata, vector_id=vector_id)
        
        return jsonify({
            "success": True,
            "vector_id": result.get('id'),
            "text": text,
            "metadata": metadata
        })
        
    except Exception as e:
        print(f"Pinecone add vector error: {e}")
        return jsonify({
            "error": str(e),
            "message": "Failed to add vector"
        }), 500

@app.route('/api/auth/check', methods=['GET'])
def check_auth_status():
    """Check if user is authenticated (for frontend use)"""
    try:
        if not JWT_AVAILABLE:
            return jsonify({'authenticated': False, 'message': 'JWT authentication not available'}), 500
            
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'authenticated': False, 'message': 'No token provided'}), 401
        
        try:
            token = auth_header.split(" ")[1]  # Bearer <token>
        except IndexError:
            return jsonify({'authenticated': False, 'message': 'Invalid token format'}), 401

        try:
            # Decode and verify token
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user_id = data['user_id']
            
            # Get user from database
            user = users_collection.find_one({"_id": ObjectId(user_id), "is_active": True})
            
            if not user:
                return jsonify({'authenticated': False, 'message': 'User not found'}), 401
            
            if user.get('role') != 'admin':
                return jsonify({'authenticated': False, 'message': 'Admin access required'}), 403
                
            return jsonify({
                'authenticated': True,
                'user': serialize_user(user),
                'message': 'Authentication valid'
            })
            
        except jwt.ExpiredSignatureError:
            return jsonify({'authenticated': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'authenticated': False, 'message': 'Invalid token'}), 401
            
    except Exception as e:
        print(f"Auth check error: {e}")
        return jsonify({'authenticated': False, 'message': 'Authentication error'}), 500
@app.get("/admin")
def admin_panel():
    """Admin panel for managing announcements and vector database"""
    return render_template("dashboard.html")

@app.get("/admin/index")
def admin_index():
    """Alternative admin index route"""
    return render_template("index.html")

@app.get("/dashboard")
def dashboard():
    """Dashboard route with authentication check"""
    # Check if there's a valid admin session
    # This is a simple check - for production you might want more robust session management
    
    # For now, we'll let the frontend handle authentication checks via JavaScript
    # The frontend will redirect to login if no valid token is found
    return render_template("dashboard.html", active_page="dashboard")

@app.get("/admin/dashboard")
def admin_dashboard():
    """Admin dashboard for EduChat system analytics and management"""
    return render_template("dashboard.html", active_page="dashboard")

@app.get("/Super-dashboard")
def super_dashboard():
    """Super Admin dashboard route"""
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
@require_sub_admin_permission("dashboard")
def sub_admin_dashboard():
    """Sub-Admin dashboard for EduChat system analytics and management"""
    return render_template("Sub-dashboard.html")

@app.route("/Sub-dashboard")
@require_sub_admin_permission("dashboard")
def sub_dashboard():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-dashboard for {name} from {office}")
        
        return render_template(
            "Sub-dashboard.html",
            active_page="sub_dashboard",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_dashboard: {e}")
        print(traceback.format_exc())
        return f"Error loading dashboard: {str(e)}", 500

@app.get("/Sub-admin/Sub-conversations")
@require_sub_admin_permission("conversations")
def sub_admin_conversations():
    """Sub-Admin conversations page"""
    return render_template("Sub-conversations.html")

@app.route("/Sub-conversations")
@require_sub_admin_permission("conversations")
def sub_conversations():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-conversations for {name} from {office}")
        
        return render_template(
            "Sub-conversations.html", 
            active_page="sub_conversations",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_conversations: {e}")
        print(traceback.format_exc())
        return f"Error loading conversations: {str(e)}", 500

@app.get("/Sub-admin/Sub-faq")
@require_sub_admin_permission("faq")
def sub_admin_faq():
    """Sub-Admin faq page"""
    return render_template("Sub-faq.html")

@app.route("/Sub-faq")
@require_sub_admin_permission("faq")
def sub_faq():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-faq for {name} from {office}")
        
        return render_template(
            "Sub-faq.html", 
            active_page="sub_faq",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_faq: {e}")
        print(traceback.format_exc())
        return f"Error loading FAQ: {str(e)}", 500

@app.get("/Sub-admin/Sub-announcements")
@require_sub_admin_permission("announcements")
def sub_admin_announcements():
    """Sub-Admin announcements page"""
    return render_template("Sub-announcements.html")

@app.route("/Sub-announcements")
@require_sub_admin_permission("announcements")
def sub_announcements():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-announcements for {name} from {office}")
        
        return render_template(
            "Sub-announcements.html", 
            active_page="sub_announcements",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_announcements: {e}")
        print(traceback.format_exc())
        return f"Error loading announcements: {str(e)}", 500

@app.get("/Sub-admin/Sub-usage_stats")
@require_sub_admin_permission("usage")
def sub_admin_usage_stats():
    """Sub-Admin usage_stats page"""
    return render_template("Sub-usage.html")

@app.route("/Sub-usage_stats")
@require_sub_admin_permission("usage")
def sub_usage_stats():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-usage_stats for {name} from {office}")
        
        return render_template(
            "Sub-usage.html", 
            active_page="sub_usage_stats",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_usage_stats: {e}")
        print(traceback.format_exc())
        return f"Error loading usage stats: {str(e)}", 500


@app.get("/Sub-admin/Sub-feedback")
@require_sub_admin_permission("feedback")
def sub_admin_feedback():
    """Sub-Admin feedback page"""
    return render_template("Sub-feedback.html")

@app.route("/Sub-feedback")
@require_sub_admin_permission("feedback")
def sub_feedback():
    try:
        office = session.get("office", "Sub Admin")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Rendering Sub-feedback for {name} from {office}")
        
        return render_template(
            "Sub-feedback.html", 
            active_page="sub_feedback",
            office=office,
            name=name
        )
    except Exception as e:
        print(f"ERROR in sub_feedback: {e}")
        print(traceback.format_exc())
        return f"Error loading feedback: {str(e)}", 500
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
    # Define specific offices to display
    specific_offices = [
        "Admission Office",
        "Registrar's Office",
        "ICT Office",
        "Guidance Office",
        "Office of the Student Affairs (OSA)",
        "General"
    ]
    
    # Get all conversations grouped by office
    pipeline = [
        {"$group": {"_id": "$office", "count": {"$sum": 1}}}
    ]
    results = list(conversations.aggregate(pipeline))
    
    # Create a dictionary for easy lookup with all database values
    office_counts = {}
    for r in results:
        if r["_id"]:
            office_counts[r["_id"]] = r["count"]
    
    print(f"DEBUG: Raw office counts from database: {office_counts}")
    
    # Build the response with only specific offices
    labels = []
    data = []
    
    for office in specific_offices:
        labels.append(office)
        # Get count for this office, checking both exact match and variants
        count = office_counts.get(office, 0)
        
        # Handle OSA office name variants
        if office == "Office of the Student Affairs (OSA)" and count == 0:
            # Check for alternate naming
            count = office_counts.get("Office of Student Affairs", 0)
        
        data.append(count)
    
    print(f"Department Distribution - Labels: {labels}, Data: {data}")

    return jsonify({"labels": labels, "data": data})

# Sub-admin specific API endpoints
@app.route("/api/sub-admin/stats")
def get_sub_admin_stats_session():
    """Get statistics for sub-admin dashboard using Flask session"""
    try:
        # Check if user is authenticated as sub-admin
        if not (session.get("role") == "sub-admin" and session.get("office")):
            print("DEBUG: Stats API - Sub-admin authentication required")
            return jsonify({'success': False, 'message': 'Sub-admin authentication required'}), 401
        
        office = session.get("office")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: Stats API - Loading stats for {office}")
        
        # Get office-specific statistics from conversations collection
        # Filter by office field in conversation documents
        office_conversations = conversations_collection.count_documents({"office": office})
        office_users_list = conversations_collection.distinct("user", {"office": office})
        office_users = len(office_users_list)
        
        # Calculate resolution metrics
        resolved_queries = conversations_collection.count_documents({
            "office": office, 
            "status": "resolved"
        })
        escalated_issues = conversations_collection.count_documents({
            "office": office, 
            "status": "escalated"
        })
        
        # Get last login from sub_users collection
        last_login = None
        try:
            sub_user = sub_users.find_one({"name": name, "office": office})
            if sub_user and 'last_login' in sub_user:
                last_login = sub_user['last_login']
                print(f"DEBUG: Found last_login for {name}: {last_login}")
            else:
                print(f"DEBUG: No last_login found for {name} in {office}")
        except Exception as e:
            print(f"ERROR fetching last_login: {e}")
        
        stats = {
            "office": office,
            "name": name,
            "office_conversations": office_conversations,
            "office_users": office_users,
            "office_resolved_queries": resolved_queries,
            "office_escalated_issues": escalated_issues,
            "last_login": last_login.isoformat() if last_login else None
        }
        
        print(f"DEBUG: Stats API - Returning stats: {stats}")
        return jsonify({"success": True, "stats": stats})
    
    except Exception as e:
        print(f"ERROR in get_sub_admin_stats_session API: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/sub-admin/office-data")
def get_office_data():
    """Get office-specific data for Sub-Admin (with session validation)"""
    try:
        # Check if user is authenticated as sub-admin
        if not (session.get("role") == "sub-admin" and session.get("office")):
            print("DEBUG: API - Sub-admin authentication required")
            return jsonify({'success': False, 'message': 'Sub-admin authentication required'}), 401
        
        office = session.get("office")
        name = session.get("name", "Sub Admin")
        
        print(f"DEBUG: API - Loading office data for {office}")
        
        # Get office-specific statistics
        office_conversations = conversations_collection.count_documents({"office": office})
        office_users_list = conversations_collection.distinct("user", {"office": office})
        office_users = len(office_users_list)
        
        print(f"DEBUG: API - Found {office_conversations} conversations, {office_users} users")
        
        # Calculate office-specific metrics
        resolved_queries = conversations_collection.count_documents({
            "office": office, 
            "status": "resolved"
        })
        escalated_issues = conversations_collection.count_documents({
            "office": office, 
            "status": "escalated"
        })
        unresolved_queries = conversations_collection.count_documents({
            "office": office, 
            "status": "unresolved"
        })
        
        # Get recent office conversations
        recent_conversations = list(conversations_collection.find(
            {"office": office}
        ).sort("date", -1).limit(10))
        
        # Convert ObjectId to string for JSON serialization
        for conv in recent_conversations:
            if '_id' in conv:
                conv['_id'] = str(conv['_id'])
        
        office_data = {
            "office": office,
            "name": name,
            "stats": {
                "office_conversations": office_conversations,
                "office_users": office_users,
                "office_resolved_queries": resolved_queries,
                "office_escalated_issues": escalated_issues,
                "office_unresolved_queries": unresolved_queries
            },
            "recent_conversations": recent_conversations,
            "allowed_offices": [office]  # Only their own office
        }
        
        print(f"DEBUG: API - Returning office data: {office_data['stats']}")
        return jsonify({"success": True, "data": office_data})
    
    except Exception as e:
        print(f"ERROR in get_office_data API: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/sub-admin/conversations")
def get_office_conversations():
    """Get conversations for specific office only"""
    try:
        # Check authentication
        if not (session.get("role") == "sub-admin" and session.get("office")):
            return jsonify({'success': False, 'message': 'Sub-admin authentication required'}), 401
        
        office = session.get("office")
        
        print(f"DEBUG: API - Loading conversations for {office}")
        
        # Get only conversations for this office
        conversations = list(conversations_collection.find(
            {"office": office}
        ).sort("date", -1).limit(100))
        
        # Convert ObjectId to string for JSON serialization
        for conv in conversations:
            if '_id' in conv:
                conv['_id'] = str(conv['_id'])
        
        print(f"DEBUG: API - Found {len(conversations)} conversations for {office}")
        return jsonify({"success": True, "conversations": conversations, "office": office})
    
    except Exception as e:
        print(f"ERROR in get_office_conversations API: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
@app.route("/api/sub-admin/feedback")
def get_office_feedback():
    """Get feedback for specific office only"""
    try:
        # Check authentication
        if not (session.get("role") == "sub-admin" and session.get("office")):
            return jsonify({'success': False, 'message': 'Sub-admin authentication required'}), 401
        
        office = session.get("office")
        
        print(f"DEBUG: API - Loading feedback for {office}")
        
        # Get office-specific feedback (you'll need to add office field to feedback collection)
        # For now, we'll filter conversations that might contain feedback
        feedback_conversations = list(conversations_collection.find({
            "office": office,
            "$or": [
                {"message": {"$regex": "feedback|rating|review", "$options": "i"}},
                {"sender": "user", "message": {"$regex": "thank|good|bad|poor|excellent", "$options": "i"}}
            ]
        }).sort("date", -1).limit(50))
        
        # Convert ObjectId to string for JSON serialization
        for conv in feedback_conversations:
            if '_id' in conv:
                conv['_id'] = str(conv['_id'])
        
        print(f"DEBUG: API - Found {len(feedback_conversations)} feedback items for {office}")
        return jsonify({"success": True, "feedback": feedback_conversations, "office": office})
    
    except Exception as e:
        print(f"ERROR in get_office_feedback API: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500
@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback submission from chatbot"""
    try:
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '')
        user_id = data.get('user_id', 'guest')
        session_id = data.get('session_id')
        
        # Validate required fields
        if not rating:
            return jsonify({
                'success': False,
                'message': 'Rating is required'
            }), 400
        
        # Save feedback using the feedback module
        result = save_feedback(
            rating=rating,
            comment=comment,
            user_id=user_id,
            session_id=session_id
        )
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Thank you for your feedback!'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': result['message']
            }), 400
            
    except Exception as e:
        print(f"Error processing feedback: {e}")
        return jsonify({
            'success': False,
            'message': 'Something went wrong, please try again.'
        }), 500

@app.route('/api/feedback/stats', methods=['GET'])
@token_required
def get_feedback_statistics(current_user):
    """Get feedback statistics for admin dashboard"""
    try:
        stats = get_feedback_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        print(f"Error getting feedback stats: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving feedback statistics'
        }), 500

@app.route('/api/feedback/recent', methods=['GET'])
@token_required
def get_recent_feedback_data(current_user):
    """Get recent feedback for admin dashboard"""
    try:
        limit = request.args.get('limit', 20, type=int)
        feedback = get_recent_feedback(limit)
        return jsonify({
            'success': True,
            'feedback': feedback
        })
    except Exception as e:
        print(f"Error getting recent feedback: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving recent feedback'
        }), 500

@app.route('/api/admin/feedback', methods=['GET'])
@token_required
def get_admin_feedback_analytics(current_user):
    """Get comprehensive feedback analytics for admin dashboard"""
    try:
        analytics = get_feedback_analytics()
        return jsonify(analytics)
    except Exception as e:
        print(f"Error getting feedback analytics: {e}")
        return jsonify({
            'success': False,
            'message': 'Error retrieving feedback analytics'
        }), 500

@app.route('/api/test/feedback', methods=['GET'])
def test_feedback_route():
    """Test route to verify server is working"""
    return jsonify({
        'success': True,
        'message': 'Test route working',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route("/search", methods=["POST"])
def search_vectors():
    data = request.json
    query = data.get("query", "")
    results = vs.search_similar(query, top_k=5)
    return jsonify(results)

# ===========================
# FAQ API ROUTES
# ===========================

@app.route('/api/faqs', methods=['GET'])
@token_required
def get_faqs_route(current_user):
    """Get all FAQs or filter by office"""
    try:
        office = request.args.get('office')
        result = get_faqs(office)
        return jsonify(result)
    except Exception as e:
        print(f"Error in get_faqs_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'faqs': []
        }), 500

@app.route('/api/faqs', methods=['POST'])
@token_required
@admin_required
def add_faq_route(current_user):
    """Add a new FAQ"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        result = add_faq(data)
        if result['success']:
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in add_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/faqs/<faq_id>', methods=['GET'])
@token_required
def get_faq_route(current_user, faq_id):
    """Get a specific FAQ by ID"""
    try:
        result = get_faq_by_id(faq_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"Error in get_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/faqs/<faq_id>', methods=['PUT'])
@token_required
@admin_required
def update_faq_route(current_user, faq_id):
    """Update an existing FAQ"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        # Pass the current user for version tracking
        edited_by = current_user.get('username', 'admin')
        result = update_faq(faq_id, data, edited_by)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in update_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/faqs/<faq_id>', methods=['DELETE'])
@token_required
@admin_required
def delete_faq_route(current_user, faq_id):
    """Delete an FAQ"""
    try:
        result = delete_faq(faq_id)
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 404
            
    except Exception as e:
        print(f"Error in delete_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@app.route('/api/faqs/search', methods=['POST'])
@token_required
def search_faqs_route(current_user):
    """Search FAQs using vector similarity"""
    try:
        data = request.get_json()
        if not data or not data.get('query'):
            return jsonify({
                'success': False,
                'message': 'Query is required'
            }), 400
        
        query = data.get('query')
        office = data.get('office')
        top_k = data.get('top_k', 5)
        
        result = search_faqs(query, office, top_k)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in search_faqs_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'results': []
        }), 500

@app.route('/api/faqs/<faq_id>/versions', methods=['GET'])
@token_required
@admin_required
def get_faq_versions_route(current_user, faq_id):
    """Get version history for a specific FAQ"""
    try:
        result = get_faq_versions(faq_id)
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_faq_versions_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error',
            'versions': []
        }), 500

@app.route('/api/faqs/<faq_id>/rollback/<int:version_number>', methods=['POST'])
@token_required
@admin_required
def rollback_faq_route(current_user, faq_id, version_number):
    """Rollback FAQ to a previous version"""
    try:
        admin_user = current_user.get('username', 'admin')
        result = rollback_faq(faq_id, version_number, admin_user)
        
        if result['success']:
            return jsonify(result)
        else:
            return jsonify(result), 400
            
    except Exception as e:
        print(f"Error in rollback_faq_route: {e}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500
# Notification API Endpoint for Admin
@app.route('/api/admin/notifications', methods=['GET'])
@token_required
@admin_required
def get_admin_notifications(current_user):
    """Aggregate notifications from all admin content areas"""
    try:
        from datetime import datetime, timedelta
        
        notifications = []
        total_count = 0
        
        # Get current time for "recent" checks (last 24 hours)
        recent_time = datetime.now() - timedelta(hours=24)
        
        # 1. NEW FEEDBACK - Check for unread or recent feedback
        try:
            feedback_collection = db['feedback']
            new_feedback_count = feedback_collection.count_documents({
                'created_at': {'$gte': recent_time}
            })
            
            if new_feedback_count > 0:
                recent_feedback = list(feedback_collection.find({
                    'created_at': {'$gte': recent_time}
                }).sort('created_at', -1).limit(3))
                
                for fb in recent_feedback:
                    comment = fb.get('comment') or 'No comment'
                    comment_preview = comment[:50] + '...' if len(comment) > 50 else comment
                    notifications.append({
                        'id': str(fb.get('_id', '')),
                        'type': 'feedback',
                        'title': f"New {fb.get('rating', 5)}-star feedback",
                        'message': comment_preview,
                        'time': fb.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-heart',
                        'color': 'success' if fb.get('rating', 0) >= 4 else 'warning',
                        'link': '/feedback'
                    })
                total_count += new_feedback_count
        except Exception as e:
            print(f"Error fetching feedback notifications: {e}")
        
        # 2. UNRESOLVED CONVERSATIONS - Recent conversations needing attention
        try:
            unresolved_count = conversations_collection.count_documents({
                'status': {'$in': ['unresolved', 'escalated']},
                'timestamp': {'$gte': recent_time}
            })
            
            if unresolved_count > 0:
                recent_unresolved = list(conversations_collection.find({
                    'status': {'$in': ['unresolved', 'escalated']}
                }).sort('timestamp', -1).limit(3))
                
                for conv in recent_unresolved:
                    notifications.append({
                        'id': str(conv.get('_id', '')),
                        'type': 'conversation',
                        'title': f"{conv.get('status', 'Unresolved').capitalize()} conversation",
                        'message': f"User: {conv.get('user', 'Unknown')} - Office: {conv.get('office', 'General')}",
                        'time': conv.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-comments',
                        'color': 'danger' if conv.get('status') == 'escalated' else 'warning',
                        'link': '/conversations'
                    })
                total_count += unresolved_count
        except Exception as e:
            print(f"Error fetching conversation notifications: {e}")
        
        # 3. NEW USERS - Recently created sub-admin accounts
        try:
            new_users_count = sub_users.count_documents({
                'created_at': {'$gte': recent_time}
            })
            
            if new_users_count > 0:
                recent_users = list(sub_users.find({
                    'created_at': {'$gte': recent_time}
                }).sort('created_at', -1).limit(3))
                
                for user in recent_users:
                    notifications.append({
                        'id': str(user.get('_id', '')),
                        'type': 'user',
                        'title': 'New sub-admin created',
                        'message': f"{user.get('name', 'Unknown')} - {user.get('office', 'No office')}",
                        'time': user.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-user-plus',
                        'color': 'info',
                        'link': '/users'
                    })
                total_count += new_users_count
        except Exception as e:
            print(f"Error fetching user notifications: {e}")
        
        # 4. FAQ UPDATES - Recently added or modified FAQs
        try:
            faqs_collection = db['faqs']
            new_faqs_count = faqs_collection.count_documents({
                'created_at': {'$gte': recent_time}
            })
            
            if new_faqs_count > 0:
                recent_faqs = list(faqs_collection.find({
                    'created_at': {'$gte': recent_time}
                }).sort('created_at', -1).limit(2))
                
                for faq in recent_faqs:
                    question = faq.get('question') or 'No question'
                    question_preview = question[:50] + '...' if len(question) > 50 else question
                    notifications.append({
                        'id': str(faq.get('_id', '')),
                        'type': 'faq',
                        'title': 'New FAQ added',
                        'message': question_preview,
                        'time': faq.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-question-circle',
                        'color': 'primary',
                        'link': '/faq'
                    })
                total_count += new_faqs_count
        except Exception as e:
            print(f"Error fetching FAQ notifications: {e}")
        
        # 5. HIGH USAGE ALERT - Check if usage spike in last hour
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_conversations_count = conversations_collection.count_documents({
                'timestamp': {'$gte': one_hour_ago}
            })
            
            # If more than 50 conversations in last hour, show alert
            if recent_conversations_count > 50:
                notifications.append({
                    'id': 'usage_spike',
                    'type': 'alert',
                    'title': 'High usage detected',
                    'message': f'{recent_conversations_count} conversations in the last hour',
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'icon': 'fa-chart-line',
                    'color': 'warning',
                    'link': '/usage'
                })
                total_count += 1
        except Exception as e:
            print(f"Error checking usage spike: {e}")
        
        # Sort notifications by time (most recent first)
        notifications.sort(key=lambda x: x['time'], reverse=True)
        
        # Limit to top 10 notifications
        notifications = notifications[:10]
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total_count': total_count,
            'unread_count': total_count  # All are considered unread for now
        })
        
    except Exception as e:
        print(f"Error fetching admin notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error fetching notifications',
            'notifications': [],
            'total_count': 0,
            'unread_count': 0
        }), 500

# Notification API Endpoint for Sub-Admin
@app.route('/api/sub-admin/notifications', methods=['GET'])
def get_sub_admin_notifications():
    """Aggregate notifications from all sub-admin content areas"""
    try:
        # Check if user is authenticated as sub-admin
        if not (session.get("role") == "sub-admin" and session.get("office")):
            return jsonify({
                'success': False,
                'message': 'Sub-admin authentication required',
                'notifications': [],
                'total_count': 0,
                'unread_count': 0
            }), 401
        
        from datetime import datetime, timedelta
        
        office = session.get("office")
        notifications = []
        total_count = 0
        
        # Get current time for "recent" checks (last 24 hours)
        recent_time = datetime.now() - timedelta(hours=24)
        
        # 1. NEW FEEDBACK - Office-specific feedback
        try:
            feedback_collection = db['feedback']
            new_feedback_count = feedback_collection.count_documents({
                'office': office,
                'created_at': {'$gte': recent_time}
            })
            
            if new_feedback_count > 0:
                recent_feedback = list(feedback_collection.find({
                    'office': office,
                    'created_at': {'$gte': recent_time}
                }).sort('created_at', -1).limit(3))
                
                for fb in recent_feedback:
                    comment = fb.get('comment') or 'No comment'
                    comment_preview = comment[:50] + '...' if len(comment) > 50 else comment
                    notifications.append({
                        'id': str(fb.get('_id', '')),
                        'type': 'feedback',
                        'title': f"New {fb.get('rating', 5)}-star feedback",
                        'message': comment_preview,
                        'time': fb.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-heart',
                        'color': 'success' if fb.get('rating', 0) >= 4 else 'warning',
                        'link': f'/Sub-feedback?office={office}'
                    })
                total_count += new_feedback_count
        except Exception as e:
            print(f"Error fetching feedback notifications: {e}")
        
        # 2. UNRESOLVED CONVERSATIONS - Office-specific
        try:
            unresolved_count = conversations_collection.count_documents({
                'office': office,
                'status': {'$in': ['unresolved', 'escalated']},
                'timestamp': {'$gte': recent_time}
            })
            
            if unresolved_count > 0:
                recent_unresolved = list(conversations_collection.find({
                    'office': office,
                    'status': {'$in': ['unresolved', 'escalated']}
                }).sort('timestamp', -1).limit(3))
                
                for conv in recent_unresolved:
                    notifications.append({
                        'id': str(conv.get('_id', '')),
                        'type': 'conversation',
                        'title': f"{conv.get('status', 'Unresolved').capitalize()} conversation",
                        'message': f"User: {conv.get('user', 'Unknown')}",
                        'time': conv.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-comments',
                        'color': 'danger' if conv.get('status') == 'escalated' else 'warning',
                        'link': f'/Sub-conversations?office={office}'
                    })
                total_count += unresolved_count
        except Exception as e:
            print(f"Error fetching conversation notifications: {e}")
        
        # 3. NEW FAQs - Office-specific
        try:
            faqs_collection = db['faqs']
            new_faqs_count = faqs_collection.count_documents({
                'office': office,
                'created_at': {'$gte': recent_time}
            })
            
            if new_faqs_count > 0:
                recent_faqs = list(faqs_collection.find({
                    'office': office,
                    'created_at': {'$gte': recent_time}
                }).sort('created_at', -1).limit(2))
                
                for faq in recent_faqs:
                    question = faq.get('question') or 'No question'
                    question_preview = question[:50] + '...' if len(question) > 50 else question
                    notifications.append({
                        'id': str(faq.get('_id', '')),
                        'type': 'faq',
                        'title': 'New FAQ added',
                        'message': question_preview,
                        'time': faq.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-question-circle',
                        'color': 'primary',
                        'link': f'/Sub-faq?office={office}'
                    })
                total_count += new_faqs_count
        except Exception as e:
            print(f"Error fetching FAQ notifications: {e}")
        
        # 4. NEW ANNOUNCEMENTS - Office-specific
        try:
            announcements_collection = db['announcements']
            new_announcements_count = announcements_collection.count_documents({
                'office': office,
                'created_at': {'$gte': recent_time},
                'is_active': True
            })
            
            if new_announcements_count > 0:
                recent_announcements = list(announcements_collection.find({
                    'office': office,
                    'created_at': {'$gte': recent_time},
                    'is_active': True
                }).sort('created_at', -1).limit(2))
                
                for announcement in recent_announcements:
                    title = announcement.get('title') or 'New announcement'
                    title_preview = title[:50] + '...' if len(title) > 50 else title
                    notifications.append({
                        'id': str(announcement.get('_id', '')),
                        'type': 'announcement',
                        'title': 'New announcement',
                        'message': title_preview,
                        'time': announcement.get('created_at', datetime.now()).strftime('%Y-%m-%d %H:%M'),
                        'icon': 'fa-bullhorn',
                        'color': 'info',
                        'link': f'/Sub-announcements?office={office}'
                    })
                total_count += new_announcements_count
        except Exception as e:
            print(f"Error fetching announcement notifications: {e}")
        
        # 5. HIGH USAGE ALERT - Office-specific
        try:
            one_hour_ago = datetime.now() - timedelta(hours=1)
            recent_conversations_count = conversations_collection.count_documents({
                'office': office,
                'timestamp': {'$gte': one_hour_ago}
            })
            
            # If more than 30 conversations in last hour for this office
            if recent_conversations_count > 30:
                notifications.append({
                    'id': 'usage_spike',
                    'type': 'alert',
                    'title': 'High usage detected',
                    'message': f'{recent_conversations_count} conversations in the last hour',
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'icon': 'fa-chart-line',
                    'color': 'warning',
                    'link': f'/Sub-usage?office={office}'
                })
                total_count += 1
        except Exception as e:
            print(f"Error checking usage spike: {e}")
        
        # Sort notifications by time (most recent first)
        notifications.sort(key=lambda x: x['time'], reverse=True)
        
        # Limit to top 10 notifications
        notifications = notifications[:10]
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total_count': total_count,
            'unread_count': total_count  # All are considered unread for now
        })
        
    except Exception as e:
        print(f"Error fetching sub-admin notifications: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': 'Error fetching notifications',
            'notifications': [],
            'total_count': 0,
            'unread_count': 0
        }), 500

# Add some debugging information on startup
def startup_info():
    print("=== TCC Assistant Starting ===")
    print(f"Vector Store Status: {vector_store.get_stats()}")
    print(f"Pinecone Available: {vector_store.index is not None}")
    print("===============================")

if __name__ == "__main__":
    # Create default admin user on startup
    create_default_admin()
    
    # Create default sub-admin users on startup
    create_default_sub_admins()
    
    # Print startup information
    startup_info()
    
    if not vector_store.index:
        print("\n⚠️  WARNING: Pinecone not available!")
        print("To enable vector search:")
        print("1. Set PINECONE_API_KEY environment variable")
        print("2. Run: export PINECONE_API_KEY='your-api-key'")
        print("3. Install required packages: pip install pinecone-client sentence-transformers")
    
    # Email configuration status
    print("\n" + "="*60)
    print("📧 EMAIL NOTIFICATION STATUS")
    print("="*60)
    if EMAIL_CONFIG.get('ENABLE_EMAIL', False):
        print(f"✅ Status: ENABLED")
        print(f"📤 Sender: {EMAIL_CONFIG['SENDER_EMAIL']}")
        print(f"🔗 Service: Resend API")
        print(f"🔑 API Key configured: {'Yes' if EMAIL_CONFIG.get('RESEND_API_KEY') else 'No'}")
        print("\n✅ Password change emails will be sent automatically!")
    else:
        print(f"⚠️  Status: DISABLED")
        print(f"\n📝 To enable email notifications:")
        print(f"   1. Go to: https://resend.com/signup")
        print(f"   2. Create an account and get your API key")
        print(f"   3. Set RESEND_API_KEY environment variable")
        print(f"   4. Set SENDER_EMAIL to a verified email in Resend")
        print(f"   5. Set ENABLE_EMAIL=True environment variable")
        print(f"   6. Restart the app")
    print("="*60)
    
    print("\n=========================================\n")
    
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)