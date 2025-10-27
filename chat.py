#(chat.py):
import random
import json
import torch
import os
import ssl
import sys
import pymongo
from dotenv import load_dotenv
from model import NeuralNet, HybridChatModel
from vector_store import VectorStore
from nltk_utils import bag_of_words, tokenize, clean_text, enhanced_bag_of_words, fuzzy_match, expand_synonyms
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime, UTC, date
import certifi
import time

# Load environment variables
load_dotenv()

# Print diagnostic information
print("System Information:")
print(f"Python version: {sys.version}")
print(f"PyMongo version: {pymongo.__version__}")
print(f"SSL version: {ssl.OPENSSL_VERSION}")
print(f"Certifi version: {certifi.__version__}")
print()

# MongoDB Announcements Collections
sub_announcements_collection = None
admin_announcements_collection = None

# MongoDB connection with improved error handling and SSL settings
def create_mongo_connection():
    """Create MongoDB connection with multiple fallback strategies"""
    
    # Base connection string without parameters
    base_connection = "mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/"
    
    # Strategy 1: Simple connection with just TLS disabled for testing
    try:
        print("Attempting MongoDB connection (Method 1: TLS disabled - testing only)...")
        # Note: This is for testing only - not recommended for production
        client = MongoClient(
            base_connection + "?ssl=false&retryWrites=true&w=majority",
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 1")
        return client
    except Exception as e:
        print(f"Method 1 failed: {e}")
    
    # Strategy 2: Use TLS with certificate verification disabled
    try:
        print("Attempting MongoDB connection (Method 2: TLS with no cert verification)...")
        client = MongoClient(
            base_connection,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            retryWrites=True
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 2")
        return client
    except Exception as e:
        print(f"Method 2 failed: {e}")
    
    # Strategy 3: Use older SSL parameter instead of TLS
    try:
        print("Attempting MongoDB connection (Method 3: Legacy SSL parameters)...")
        client = MongoClient(
            base_connection,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_match_hostname=False,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            retryWrites=True
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 3")
        return client
    except Exception as e:
        print(f"Method 3 failed: {e}")
    
    # Strategy 4: Try with explicit SSL context using ssl_ca_certs parameter
    try:
        print("Attempting MongoDB connection (Method 4: SSL with CA certs)...")
        client = MongoClient(
            base_connection,
            ssl=True,
            ssl_ca_certs=certifi.where(),
            ssl_cert_reqs=ssl.CERT_REQUIRED,
            ssl_match_hostname=True,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            retryWrites=True
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 4")
        return client
    except Exception as e:
        print(f"Method 4 failed: {e}")
    
    # Strategy 5: Try using direct connection string with parameters
    try:
        print("Attempting MongoDB connection (Method 5: Connection string parameters)...")
        connection_string = base_connection + "?retryWrites=true&w=majority&ssl=true&ssl_cert_reqs=CERT_NONE"
        client = MongoClient(
            connection_string,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 5")
        return client
    except Exception as e:
        print(f"Method 5 failed: {e}")
    
    # Strategy 6: Try with Python OpenSSL instead of system SSL
    try:
        print("Attempting MongoDB connection (Method 6: Force SSL version)...")
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
        ssl_context.maximum_version = ssl.TLSVersion.TLSv1_3
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        client = MongoClient(
            base_connection,
            ssl=True,
            ssl_cert_reqs=ssl.CERT_NONE,
            ssl_match_hostname=False,
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            retryWrites=True
        )
        # Test the connection
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 6")
        return client
    except Exception as e:
        print(f"Method 6 failed: {e}")
    
    # Strategy 7: Last resort - try with minimal settings
    try:
        print("Attempting MongoDB connection (Method 7: Minimal settings)...")
        client = MongoClient(base_connection)
        # Test the connection with longer timeout
        client.admin.command('ping')
        print("MongoDB connected successfully using Method 7")
        return client
    except Exception as e:
        print(f"Method 7 failed: {e}")
    
    print("All connection methods failed!")
    print("Possible solutions:")
    print("   1. Check your internet connection")
    print("   2. Verify MongoDB Atlas cluster is running")
    print("   3. Check Network Access settings in MongoDB Atlas")
    print("   4. Update Python and pymongo: pip install --upgrade pymongo")
    print("   5. Try connecting from a different network")
    print("   6. Contact your system administrator about SSL/TLS settings")
    
    return None

# Initialize MongoDB connection
print("Initializing MongoDB connection...")
mongo_client = create_mongo_connection()

if mongo_client:
    db = mongo_client["chatbot_db"]
    conversations = db["conversations"]
    sub_announcements_collection = db["sub_announcements"]
    admin_announcements_collection = db["admin_announcements"]
    print("MongoDB database and collections initialized")
else:
    print("Failed to connect to MongoDB. Running in offline mode.")
    db = None
    conversations = None
    sub_announcements_collection = None
    admin_announcements_collection = None

# Load intents
with open("intents.json", "r") as f:
    intents = json.load(f)

# Initialize Vector Store
vector_store = VectorStore()

# Note: Announcements are now stored exclusively in MongoDB and Pinecone
# No JSON file fallback - all announcements come from database

# Load trained model with Railway fallback
FILE = "data.pth"
try:
    data = torch.load(FILE)

    input_size = data["input_size"]
    hidden_size = data["hidden_size"]
    output_size = data["output_size"]
    all_words = data["all_words"]
    tags = data["tags"]
    model_state = data["model_state"]

    model = NeuralNet(input_size, hidden_size, output_size)
    model.load_state_dict(model_state)
    model.eval()
    
    # Initialize hybrid model
    hybrid_model = HybridChatModel(model, vector_store, tags)
    print("[OK] Neural network and vector store loaded successfully")
    
except FileNotFoundError:
    print("[WARNING] Neural network model not found. Using fallback mode.")
    model = None
    hybrid_model = None
    # Create minimal fallback data
    all_words = ["hello", "help", "thanks", "goodbye"] * 25
    tags = ["greeting", "help", "thanks", "goodbye"]
except Exception as e:
    print(f"[ERROR] Error loading model: {e}. Using fallback mode.")
    model = None
    hybrid_model = None
    all_words = ["hello", "help", "thanks", "goodbye"] * 25
    tags = ["greeting", "help", "thanks", "goodbye"]

# Store conversation contexts for each user per office
# Structure: user_contexts[user_id] = {
#     "current_office": "admission_office",  # Currently active office
#     "offices": {
#         "admission_office": {...},  # Office-specific context data
#         "registrar_office": {...},
#         ...
#     }
# }
user_contexts = {}

# Office mapping for context switching
office_tags = {
    'admission_office': 'Admissions Office',
    'registrar_office': "Registrar's Office",
    'ict_office': 'ICT Office',
    'guidance_office': 'Guidance Office',
    'osa_office': 'Office of the Student Affairs (OSA)'
}

def get_user_current_office(user_id):
    """Get the current office context for a user"""
    if user_id not in user_contexts:
        return None
    return user_contexts[user_id].get("current_office")

def set_user_current_office(user_id, office_tag):
    """Set the current office context for a user"""
    if user_id not in user_contexts:
        user_contexts[user_id] = {"current_office": None, "offices": {}}
    user_contexts[user_id]["current_office"] = office_tag
    # Initialize office context if not exists
    if office_tag and office_tag not in user_contexts[user_id]["offices"]:
        user_contexts[user_id]["offices"][office_tag] = {"messages": [], "last_intent": None}

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
        'valid id', 'authorization letter', 'graduation'
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

def save_message(user_id, sender, message, detected_office=None):
    """Save message to MongoDB with error handling and office detection"""
    global mongo_client, db, conversations
    
    if conversations is None:
        print("MongoDB not available. Message not saved to database.")
        return False
    
    # Determine office based on context or detection
    office = None
    
    # First check if office was explicitly provided
    if detected_office:
        office = office_tags.get(detected_office, detected_office)
    
    # If no office provided, check user context
    else:
        current_office = get_user_current_office(user_id)
        if current_office:
            office = office_tags.get(current_office)
    
    # If still no office, try to detect from message content
    if not office and sender == "user":
        detected_tag = detect_office_from_message(message)
        if detected_tag:
            office = office_tags.get(detected_tag)
    
    # Default to General if no office detected
    if not office:
        office = "General"
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Create document with office field and date instead of timestamp
            document = {
                "user": user,
                "sender": sender,
                "message": message,
                "office": office,
                "date": date.today().isoformat()  # Convert date to ISO string format
            }
            
            conversations.insert_one(document)
            return True
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            retry_count += 1
            print(f"MongoDB connection error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                print("Retrying in 2 seconds...")
                time.sleep(2)
                
                # Try to reconnect
                mongo_client = create_mongo_connection()
                if mongo_client:
                    db = mongo_client["chatbot_db"]
                    conversations = db["conversations"]
                else:
                    break
            else:
                print("Failed to save message after all retries")
                return False
                
        except Exception as e:
            print(f"Unexpected error saving message: {e}")
            return False
    
    return False

def clear_chat_history(user):
    """Clear all chat history for a specific user"""
    global conversations
    
    if conversations is None:
        print("MongoDB not available. Cannot clear chat history.")
        return 0
    
    try:
        result = conversations.delete_many({"user": user})
        return result.deleted_count
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return 0

def get_active_announcements():
    """Get all active announcements from MongoDB only, sorted by priority and date"""
    all_announcements = []
    
    # Get announcements from MongoDB collections only
    try:
        if sub_announcements_collection is not None:
            # Fetch sub-admin announcements
            sub_announcements = list(sub_announcements_collection.find({"status": "active"}))
            for ann in sub_announcements:
                # Convert MongoDB format to consistent format
                all_announcements.append({
                    "id": str(ann.get("_id")),
                    "title": ann.get("title", ""),
                    "message": ann.get("description", ""),
                    "date": ann.get("start_date", ""),
                    "priority": ann.get("priority", "medium"),
                    "category": ann.get("office", "general"),
                    "office": ann.get("office", "General"),
                    "active": True,
                    "source": "mongodb",
                    "created_by": ann.get("created_by", "")
                })
        
        if admin_announcements_collection is not None:
            # Fetch admin announcements
            admin_announcements = list(admin_announcements_collection.find({"status": "active"}))
            for ann in admin_announcements:
                all_announcements.append({
                    "id": str(ann.get("_id")),
                    "title": ann.get("title", ""),
                    "message": ann.get("description", ""),
                    "date": ann.get("start_date", ""),
                    "priority": ann.get("priority", "medium"),
                    "category": ann.get("office", "general"),
                    "office": ann.get("office", "General"),
                    "active": True,
                    "source": "mongodb",
                    "created_by": ann.get("created_by", "")
                })
    except Exception as e:
        print(f"Error fetching announcements from MongoDB: {e}")
        import traceback
        traceback.print_exc()
    
    # Sort by priority (high, medium, low) then by date (newest first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_announcements.sort(
        key=lambda x: (priority_order.get(x.get("priority", "medium"), 1), x.get("date", "")),
        reverse=True  # Newest first
    )
    
    print(f"Loaded {len(all_announcements)} active announcements from MongoDB")
    return all_announcements

def format_announcements_response():
    """Format announcements for chatbot response"""
    announcements = get_active_announcements()
    
    if not announcements:
        return "There are no active announcements at this time."
    
    response = "Latest College Announcements:\n\n"
    
    for i, ann in enumerate(announcements[:3], 1):  # Show top 3 announcements
        priority_emoji = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}
        priority = priority_emoji.get(ann.get("priority", "medium"), "[INFO]")
        
        response += f"{priority} {ann['title']}\n"
        response += f"Date: {ann['date']}\n"
        response += f"{ann['message']}\n\n"
    
    if len(announcements) > 3:
        response += f"And {len(announcements) - 3} more announcements available..."
    
    return response

def search_announcements_with_vector(query):
    """Search announcements using vector similarity from Pinecone with enhanced formatting"""
    # Search in Pinecone for announcements
    try:
        vector_results = vector_store.search_similar(
            query, 
            top_k=5,  # Increased from 3 to show more results
            filter_dict={
                "$or": [
                    {"type": {"$eq": "announcement"}},
                    {"intent_type": {"$eq": "announcement"}}
                ]
            },
            score_threshold=0.5  # Lowered threshold to catch more relevant results
        )
        
        if not vector_results:
            # Fallback to traditional search
            return format_announcements_response()
        
        # Enhanced header with decorative line
        response = "╔═══════════════════════════════════════╗\n"
        response += "║     📢 COLLEGE ANNOUNCEMENTS 📢      ║\n"
        response += "╚═══════════════════════════════════════╝\n\n"
        response += f"Found {len(vector_results)} relevant announcement(s) for your query.\n\n"
        
        for idx, result in enumerate(vector_results, 1):
            metadata = result['metadata']
            
            # Priority styling with emojis
            priority_emoji = {
                "high": "🔴 [HIGH PRIORITY]", 
                "medium": "🟡 [MEDIUM PRIORITY]", 
                "low": "🟢 [LOW PRIORITY]"
            }
            priority = priority_emoji.get(metadata.get("priority", "medium").lower(), "ℹ️ [INFO]")
            
            # Extract metadata
            title = metadata.get('title', metadata.get('text', 'Untitled')).strip()
            description = metadata.get('description', metadata.get('text', 'No description available')).strip()
            office = metadata.get('office', metadata.get('category', 'General'))
            start_date = metadata.get('start_date', metadata.get('date', 'N/A'))
            created_by = metadata.get('created_by', '')
            
            # Format each announcement with enhanced styling
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"📌 ANNOUNCEMENT #{idx}\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            response += f"{priority}\n"
            response += f"📋 Title: {title}\n\n"
            
            response += f"📍 Office: {office}\n"
            response += f"📅 Date: {start_date}\n"
            
            if created_by:
                response += f"👤 Posted by: {created_by}\n"
            
            response += f"🎯 Relevance: {result['score']:.0%}\n\n"
            
            # Format description with better readability
            response += f"📝 Details:\n"
            # Truncate long descriptions
            if len(description) > 300:
                description = description[:297] + "..."
            response += f"{description}\n\n"
        
        # Footer with helpful tip
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += "💡 Tip: Click the 📢 button in the chat header to view all announcements!\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return response
        
    except Exception as e:
        print(f"Error searching announcements with vector: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to traditional format
        return format_announcements_response()

def get_context_switch_response(current_context, requested_office, user_id):
    """Generate context switch response"""
    office_name = office_tags.get(requested_office, "that office")
    current_office_name = office_tags.get(current_context, "the current topic")
    
    response = f"I think you might be asking about the {office_name}. Right now, I can only assist you with {current_office_name} concerns. Would you like me to connect you to the {office_name} information instead?"
    
    return response

def get_vector_enhanced_response(msg, predicted_tag, confidence):
    """Get enhanced response using vector search"""
    # Search for similar patterns
    vector_results = vector_store.search_similar(msg, top_k=3)
    
    if not vector_results:
        return None
    
    # Check if vector search provides better results
    best_vector_match = vector_results[0]
    
    # If vector search has high confidence and different tag, consider it
    if best_vector_match['score'] > 0.8 and best_vector_match['score'] > confidence:
        vector_tag = best_vector_match['metadata'].get('tag')
        if vector_tag and vector_tag != predicted_tag:
            # Use vector search result
            for intent in intents["intents"]:
                if intent["tag"] == vector_tag:
                    return {
                        'tag': vector_tag,
                        'responses': intent['responses'],
                        'method': 'vector_search',
                        'confidence': best_vector_match['score']
                    }
    
    return None

def search_faq_database(query, office=None):
    """
    Search FAQ database in Pinecone
    Returns the FAQ answer if a match is found, otherwise None
    """
    if not vector_store or not vector_store.index:
        return None
    
    try:
        # Generate query embedding
        query_embedding = vector_store.embedding_model.encode(query)
        
        # Build filter for FAQs
        filter_dict = {
            'type': {'$eq': 'faq'},
            'status': {'$eq': 'published'}
        }
        
        if office:
            filter_dict['office'] = {'$eq': office}
        
        # Search in Pinecone
        results = vector_store.index.query(
            vector=query_embedding.tolist(),
            top_k=3,
            filter=filter_dict,
            include_metadata=True
        )
        
        # Return best match if score is good enough
        if results.matches and len(results.matches) > 0:
            best = results.matches[0]
            if best.score >= 0.70:  # 70% similarity threshold
                print(f"✅ FAQ found: {best.metadata.get('question', 'N/A')} (score: {best.score:.3f})")
                return best.metadata.get('answer', None)
        
        return None
    except Exception as e:
        print(f"FAQ search error: {e}")
        return None

def get_fallback_response(msg, user_id="guest"):
    """Simple fallback response when model is not available"""
    msg_lower = msg.lower()
    
    # Simple keyword matching
    if any(word in msg_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "Hello! Welcome to TCC Assistant. How can I help you today?"
    elif any(word in msg_lower for word in ["help", "assist", "support"]):
        return "I'm here to help! You can ask me about admissions, registrar services, ICT support, guidance, or student affairs."
    elif any(word in msg_lower for word in ["admission", "apply", "enroll"]):
        return "For admission inquiries, please contact the Admissions Office. They can help with requirements and application procedures."
    elif any(word in msg_lower for word in ["registrar", "transcript", "grades"]):
        return "The Registrar's Office handles academic records and transcripts. Please visit them for document requests."
    elif any(word in msg_lower for word in ["ict", "password", "login", "portal"]):
        return "For ICT support and password issues, please contact the ICT Office. They can help with student portal access."
    elif any(word in msg_lower for word in ["guidance", "counseling", "scholarship"]):
        return "The Guidance Office provides counseling services and scholarship information. Visit them for career guidance."
    elif any(word in msg_lower for word in ["osa", "student affairs", "clubs", "activities"]):
        return "The Office of Student Affairs manages student activities and clubs. Contact them for organization information."
    elif any(word in msg_lower for word in ["thank", "thanks", "salamat"]):
        return "You're welcome! Feel free to ask if you need more help."
    elif any(word in msg_lower for word in ["bye", "goodbye", "see you"]):
        return "Goodbye! Have a great day!"
    else:
        return "I'm TCC Assistant! I can help you with information about admissions, registrar services, ICT support, guidance, and student affairs. What would you like to know?"

def get_response(msg, user_id="guest"):
    # Check if model is available, use fallback if not
    if model is None or hybrid_model is None:
        print("⚠️ Using fallback response (model not available)")
        return get_fallback_response(msg, user_id)
    
    # Enhanced text preprocessing with error handling
    try:
        cleaned_msg = clean_text(msg)
        sentence = tokenize(cleaned_msg)
        
        # Expand with synonyms for better matching
        expanded_msg = expand_synonyms(cleaned_msg)
        expanded_sentence = tokenize(expanded_msg)
    except Exception as e:
        print(f"⚠️ Text preprocessing failed: {e}, using fallback")
        # Use simple fallback tokenization
        cleaned_msg = msg.lower().strip()
        sentence = cleaned_msg.split()
        expanded_msg = cleaned_msg
        expanded_sentence = sentence
    
    # Detect office from message for context
    detected_office = detect_office_from_message(msg)
    
    # Save user message with office context
    save_message(user_id, "user", msg, detected_office)
    
    # If office is detected, prioritize office-specific responses
    if detected_office:
        # Check if we have current context and it matches detected office
        current_context = get_user_current_office(user_id)
        if not current_context or current_context != detected_office:
            set_user_current_office(user_id, detected_office)

    # Check if user is asking to switch context or confirming switch
    msg_lower = msg.lower()
    if any(word in msg_lower for word in ['yes', 'switch', 'connect', 'change']):
        # User wants to switch context
        requested_office = detect_office_from_message(msg)
        if requested_office:
            set_user_current_office(user_id, requested_office)
            bot_response = f"Great! I've switched to help you with {office_tags[requested_office]} information. How can I assist you?"
            save_message(user_id, "bot", bot_response, requested_office)
            return bot_response

    # Detect which office the user is asking about
    requested_office = detect_office_from_message(msg)
    
    # Check if user has an active context
    current_context = get_user_current_office(user_id)
    
    # If user is asking about a different office than current context
    if current_context and requested_office and requested_office != current_context:
        bot_response = get_context_switch_response(current_context, requested_office, user_id)
        save_message(user_id, "bot", bot_response, current_context)
        return bot_response
    
    # ============= SEARCH FAQ DATABASE =============
    # Map office tags to office names
    office_name_map = {
        'registrar_office': "Registrar's Office",
        'admission_office': "Admission Office",
        'guidance_office': "Guidance Office",
        'ict_office': "ICT Office",
        'osa_office': "Office of the Student Affairs (OSA)"
    }
    
    # Try FAQ search with detected office first
    faq_answer = None
    if detected_office and detected_office in office_name_map:
        faq_answer = search_faq_database(cleaned_msg, office=office_name_map[detected_office])
    
    # Try FAQ search with current context office
    if not faq_answer and current_context and current_context in office_name_map:
        faq_answer = search_faq_database(cleaned_msg, office=office_name_map[current_context])
    
    # Try general FAQ search (all offices)
    if not faq_answer:
        faq_answer = search_faq_database(cleaned_msg, office=None)
    
    # If FAQ found, return it
    if faq_answer:
        office_context = detected_office if detected_office else current_context
        save_message(user_id, "bot", faq_answer, office_context)
        return faq_answer
    # ============= END FAQ SEARCH =============
    
    # Use hybrid model for prediction with enhanced features
    if hybrid_model and all_words:
        # Prepare input for neural network with enhanced bag of words
        X = enhanced_bag_of_words(expanded_sentence, all_words)
        X = torch.from_numpy(X).unsqueeze(0)
        
        # Get current context for better prediction
        current_context = get_user_current_office(user_id)
        
        # Get hybrid prediction with context
        hybrid_result = hybrid_model.get_hybrid_response(cleaned_msg, X, current_context)
        
        tag = hybrid_result['final_tag']
        confidence = hybrid_result['confidence']
        
        print(f"Hybrid prediction: tag={tag}, confidence={confidence:.3f}, method={hybrid_result['response_source']}")
        
        # High confidence threshold for proceeding
        if confidence > 0.7 and tag:
            # PRIORITY 1: If office is detected from message, prioritize office-specific responses
            if detected_office:
                for intent in intents["intents"]:
                    if intent["tag"] == detected_office:
                        # Use office-specific responses based on detected office
                        bot_response = random.choice(intent["responses"])
                        save_message(user_id, "bot", bot_response, detected_office)
                        return bot_response
            
            # PRIORITY 2: Handle the predicted tag normally
            for intent in intents["intents"]:
                if tag == intent["tag"]:
                    # Handle announcements with vector search
                    if tag == "announcements":
                        # Use vector search for more relevant announcements
                        if vector_store.index:
                            bot_response = search_announcements_with_vector(cleaned_msg)
                        else:
                            bot_response = format_announcements_response()
                        save_message(user_id, "bot", bot_response, None)  # Announcements are general
                    else:
                        # Set user context based on the detected office
                        if tag in office_tags:
                            set_user_current_office(user_id, tag)
                        
                        # ✅ ONLY reset context on goodbye (not greeting/thanks as they can happen mid-conversation)
                        if tag in ['goodbye']:
                            reset_user_context(user_id)
                            print(f"🔄 Context reset for user '{user_id}' due to goodbye intent")
                        
                        # Choose response - prioritize vector search if available
                        if hybrid_result['vector_results'] and hybrid_result['response_source'] == 'vector_search':
                            # Use similar response from vector database
                            similar_responses = hybrid_result['vector_results']
                            if similar_responses:
                                best_match = similar_responses[0]
                                if best_match['metadata'].get('intent_type') == 'response':
                                    bot_response = best_match['text']
                                else:
                                    bot_response = random.choice(intent["responses"])
                            else:
                                bot_response = random.choice(intent["responses"])
                        else:
                            bot_response = random.choice(intent["responses"])
                        
                        # Save bot response with appropriate office context
                        office_context = tag if tag in office_tags else None
                        save_message(user_id, "bot", bot_response, office_context)
                    
                    return bot_response
    
    # Fallback to vector search only (but still prioritize detected office)
    if detected_office:
        # If we detected an office but hybrid model didn't work, use office-specific responses
        for intent in intents["intents"]:
            if intent["tag"] == detected_office:
                bot_response = random.choice(intent["responses"])
                save_message(user_id, "bot", bot_response, detected_office)
                return bot_response
    
    # If no office detected, fall back to vector search
    if vector_store.index:
        vector_results = vector_store.search_similar(cleaned_msg, top_k=3, score_threshold=0.6)
        
        if vector_results:
            best_match = vector_results[0]
            tag = best_match['metadata'].get('tag')
            
            if tag:
                for intent in intents["intents"]:
                    if intent["tag"] == tag:
                        if tag in office_tags:
                            set_user_current_office(user_id, tag)
                        
                        bot_response = random.choice(intent["responses"])
                        office_context = tag if tag in office_tags else None
                        save_message(user_id, "bot", bot_response, office_context)
                        return bot_response
    
    # Last resort: Try FAQ search with lower threshold
    try:
        query_embedding = vector_store.embedding_model.encode(cleaned_msg)
        results = vector_store.index.query(
            vector=query_embedding.tolist(),
            top_k=3,
            filter={'type': {'$eq': 'faq'}, 'status': {'$eq': 'published'}},
            include_metadata=True
        )
        if results.matches and len(results.matches) > 0:
            best = results.matches[0]
            if best.score >= 0.60:  # Lower threshold for last resort
                print(f"✅ Last resort FAQ found: {best.metadata.get('question', 'N/A')} (score: {best.score:.3f})")
                faq_answer = best.metadata.get('answer', None)
                if faq_answer:
                    office_context = None
                    for tag, name in office_name_map.items():
                        if name == best.metadata.get('office'):
                            office_context = tag
                            break
                    save_message(user_id, "bot", faq_answer, office_context)
                    return faq_answer
    except Exception as e:
        print(f"Last resort FAQ search error: {e}")
    
    # Enhanced fallback with fuzzy matching
    if current_context:
        office_name = office_tags[current_context]
        
        # Try fuzzy matching with current context patterns
        context_patterns = []
        for intent in intents["intents"]:
            if intent["tag"] == current_context:
                context_patterns.extend(intent["patterns"])
                break
        
        if context_patterns:
            fuzzy_matches = fuzzy_match(cleaned_msg, context_patterns, threshold=0.4)
            if fuzzy_matches:
                best_match = fuzzy_matches[0]
                print(f"Fuzzy match found: {best_match[0]} (similarity: {best_match[1]:.3f})")
                bot_response = f"I think you're asking about something related to {office_name}. Could you provide more details about: {best_match[0]}?"
                save_message(user_id, "bot", bot_response, current_context)
                return bot_response
        
        bot_response = f"I'm currently helping you with {office_name} information. Could you rephrase your question about this office, or would you like to switch to a different topic?"
        save_message(user_id, "bot", bot_response, current_context)
    else:
        # Try fuzzy matching across all patterns
        all_patterns = []
        for intent in intents["intents"]:
            all_patterns.extend(intent["patterns"])
        
        fuzzy_matches = fuzzy_match(cleaned_msg, all_patterns, threshold=0.3)
        if fuzzy_matches:
            best_match = fuzzy_matches[0]
            print(f"Global fuzzy match found: {best_match[0]} (similarity: {best_match[1]:.3f})")
            bot_response = f"I think you might be asking about: {best_match[0]}. Could you provide more details?"
            save_message(user_id, "bot", bot_response, None)
            return bot_response
        
        bot_response = "I'm not sure how to respond to that. Please try one of the suggested topics or rephrase your question."
        save_message(user_id, "bot", bot_response, None)
    
    return bot_response

def reset_user_context(user_id, office=None):
    """
    Reset user's conversation context
    
    Args:
        user_id: The user identifier
        office: Optional office tag (e.g., 'admission_office'). 
                If provided, only resets that office's context.
                If None, resets all contexts for the user.
    """
    if user_id not in user_contexts:
        print(f"🔄 No context found for user '{user_id}' - nothing to reset")
        return
    
    # Get current context info for logging
    current_context = user_contexts[user_id]
    print(f"🔍 Context before reset: {current_context}")
    
    if office:
        # ✅ Reset only the specified office's context
        if isinstance(user_contexts[user_id], dict):
            # Check if this is the current office
            current_office = user_contexts[user_id].get("current_office")
            if current_office == office:
                # Clear the current office
                user_contexts[user_id]["current_office"] = None
                print(f"✅ Reset context for user '{user_id}' - Office: {office_tags.get(office, office)} (cleared current office)")
            else:
                print(f"⚠️ Office '{office}' is not the current office (current: {current_office})")
            
            # Also clear from offices dict if it exists
            if "offices" in user_contexts[user_id] and office in user_contexts[user_id]["offices"]:
                user_contexts[user_id]["offices"][office] = {"messages": [], "last_intent": None}
                print(f"✅ Cleared office data for: {office_tags.get(office, office)}")
        else:
            # Old format: string - just clear it if it matches
            if user_contexts[user_id] == office:
                user_contexts.pop(user_id, None)
                print(f"✅ Reset context for user '{user_id}' - Office: {office_tags.get(office, office)}")
    else:
        # ✅ Reset ALL contexts for the user
        if isinstance(user_contexts[user_id], dict):
            current_office = user_contexts[user_id].get("current_office")
            office_count = len(user_contexts[user_id].get("offices", {}))
            user_contexts.pop(user_id, None)
            print(f"✅ Reset ALL contexts for user '{user_id}' (cleared {office_count} office contexts, last office: {current_office})")
        else:
            # Old format
            user_contexts.pop(user_id, None)
            print(f"✅ Reset context for user '{user_id}'")
    
    print(f"🔍 Context after reset: {user_contexts.get(user_id, 'Removed from dictionary')}")

def get_announcement_by_id(announcement_id):
    """Get a specific announcement by ID from MongoDB"""
    try:
        from bson import ObjectId
        if admin_announcements_collection is not None:
            announcement = admin_announcements_collection.find_one({"_id": ObjectId(announcement_id)})
            if announcement:
                return {
                    "id": str(announcement["_id"]),
                    "title": announcement.get("title", ""),
                    "message": announcement.get("description", ""),
                    "date": announcement.get("start_date", ""),
                    "priority": announcement.get("priority", "medium"),
                    "category": announcement.get("office", "general"),
                    "active": announcement.get("status") == "active"
                }
    except Exception as e:
        print(f"Error getting announcement by ID: {e}")
    return None

def add_announcement(title, date, message, priority="medium", category="general"):
    """Add a new announcement to MongoDB and Pinecone"""
    try:
        from bson import ObjectId
        
        # Create announcement document for MongoDB
        announcement_doc = {
            "title": title,
            "description": message,
            "start_date": date,
            "end_date": date,  # Same as start date if not specified
            "priority": priority.lower(),
            "status": "active",
            "office": category,
            "created_by": "System",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": "system"
        }
        
        # Save to MongoDB admin_announcements collection
        if admin_announcements_collection is not None:
            result = admin_announcements_collection.insert_one(announcement_doc)
            announcement_id = str(result.inserted_id)
            
            # Create embedding text for Pinecone
            embed_text = f"Title: {title}\nDescription: {message}\nOffice: {category}\nPriority: {priority}\nDate: {date}"
            
            # Store in Pinecone with metadata
            metadata = {
                "type": "announcement",
                "intent_type": "announcement",
                "announcement_id": announcement_id,
                "title": title,
                "description": message,
                "office": category,
                "priority": priority.lower(),
                "start_date": date,
                "end_date": date,
                "status": "active",
                "tag": "announcements"
            }
            
            vector_id = vector_store.store_text(embed_text, metadata)
            
            # Update MongoDB document with vector_id
            admin_announcements_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"vector_id": vector_id}}
            )
            
            print(f"Announcement added to MongoDB (ID: {announcement_id}) and Pinecone (Vector ID: {vector_id})")
            
            return {
                "id": announcement_id,
                "title": title,
                "date": date,
                "priority": priority,
                "message": message,
                "category": category,
                "active": True
            }
    except Exception as e:
        print(f"Error adding announcement: {e}")
        import traceback
        traceback.print_exc()
    
    return None

# Health check function
def check_mongodb_connection():
    """Check MongoDB connection status"""
    if mongo_client is None:
        return False
    
    try:
        mongo_client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB health check failed: {e}")
        return False

def get_chatbot_response(message):
    """
    Simple rules-based chatbot for TCC Assistant.
    Returns appropriate responses based on keyword matching.
    This function provides basic responses without AI/NLP.
    
    Returns:
        dict: {
            'response': str - The chatbot response text
            'status': str - 'resolved', 'unresolved', or 'escalated'
            'office': str - Detected office or 'General'
        }
    """
    message_lower = message.lower()
    office = "General"
    status = "resolved"
    response = ""

    # TCC E-Hub / Portal
    if "tcc e-hub" in message_lower or "ehub" in message_lower or "e-hub" in message_lower:
        response = "You can access TCC E-Hub by searching 'TCC eHub' or scanning the QR code provided in your student guide."
        office = "ICT Office"
        status = "resolved"
    
    # Username queries
    elif "username" in message_lower and ("what" in message_lower or "default" in message_lower):
        response = "Your default username is your Student ID number (e.g., TCC-0000-0000)."
        office = "ICT Office"
        status = "resolved"
    
    # Password queries
    elif "password" in message_lower and not "reset" in message_lower:
        response = "Your password is provided by your department or ICT office upon enrollment."
        office = "ICT Office"
        status = "resolved"
    
    # Password reset
    elif "password" in message_lower and "reset" in message_lower:
        response = "To reset your password, visit the ICT Office at the IT Building, Room 101, or contact them during office hours (8:00 AM - 5:00 PM, Monday to Friday)."
        office = "ICT Office"
        status = "escalated"  # Requires office visit
    
    # Registrar's Office
    elif "registrar" in message_lower:
        response = "The Registrar's Office handles student records and enrollment. Visit the 2nd floor of the Admin Building during office hours (8:00 AM - 5:00 PM, Monday to Friday)."
        office = "Registrar's Office"
        status = "resolved"
    
    # Office hours
    elif "office hours" in message_lower or "open" in message_lower:
        response = "TCC offices are open from 8:00 AM to 5:00 PM, Monday to Friday."
        status = "resolved"
    
    # Admission
    elif "admission" in message_lower or "apply" in message_lower or "enroll" in message_lower:
        response = "For admission and enrollment inquiries, please visit the Admission Office or contact them during office hours. Requirements and application forms are available at the main building."
        office = "Admission Office"
        status = "escalated"  # Requires office visit
    
    # ICT / Technical Support
    elif "ict" in message_lower or "wifi" in message_lower or "internet" in message_lower:
        response = "The ICT Office handles technical support, WiFi issues, and student portal problems. They're located at the IT Building, Room 101."
        office = "ICT Office"
        status = "resolved"
    
    # Guidance Office
    elif "guidance" in message_lower or "counseling" in message_lower or "scholarship" in message_lower:
        response = "The Guidance Office offers counseling services, scholarship information, and career guidance. Visit them at the Main Building, Room 210."
        office = "Guidance Office"
        status = "resolved"
    
    # Student Affairs / OSA
    elif "osa" in message_lower or "student affairs" in message_lower or "clubs" in message_lower or "activities" in message_lower:
        response = "The Office of Student Affairs (OSA) manages student activities, clubs, and organizations. They're at the Student Center, Room 305."
        office = "Office of Student Affairs"
        status = "resolved"
    
    # Greetings
    elif any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        response = "Hello! Welcome to TCC Assistant. How can I help you today?"
        status = "resolved"
    
    # Thank you
    elif "thank" in message_lower or "salamat" in message_lower:
        response = "You're welcome! Have a great day!"
        status = "resolved"
    
    # Goodbye
    elif "bye" in message_lower or "goodbye" in message_lower:
        response = "Goodbye! Feel free to chat with me again anytime."
        status = "resolved"
    
    # Default fallback
    else:
        response = "I'm sorry, I don't have information about that yet. Please try asking about: TCC E-Hub, student portal, office hours, admissions, registrar, ICT support, guidance services, or student affairs."
        status = "unresolved"
    
    return {
        'response': response,
        'status': status,
        'office': office
    }


if __name__ == "__main__":
    print("Enhanced Chatbot with Vector Search is running! Type 'quit' to exit.\n")
    
    # Display connection status
    if check_mongodb_connection():
        print("MongoDB connection is healthy")
    else:
        print("MongoDB connection issues detected - running in limited mode")
    
    print()
    user = "guest"

    while True:
        user_message = input("You: ")
        if user_message.lower() == "quit":
            print("Bot: Goodbye!")
            break

        bot_reply = get_response(user_message, user)
        print(f"Bot: {bot_reply}")