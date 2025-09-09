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
from nltk_utils import bag_of_words, tokenize, clean_text
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime, UTC
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
    print("MongoDB database and collection initialized")
else:
    print("Failed to connect to MongoDB. Running in offline mode.")
    db = None
    conversations = None

# Load intents
with open("intents.json", "r") as f:
    intents = json.load(f)

# Initialize Vector Store
vector_store = VectorStore()

# Load announcements and store in vector database
def load_announcements():
    try:
        with open("announcements.json", "r") as f:
            announcements_data = json.load(f)
            announcements = announcements_data["announcements"]
            
            # Store announcements in vector database
            vector_store.store_announcements(announcements)
            
            return announcements
    except FileNotFoundError:
        print("announcements.json not found. Creating default announcements...")
        create_default_announcements()
        return load_announcements()

def create_default_announcements():
    default_announcements = {
        "announcements": [
            {
                "id": 1,
                "title": "College Orientation 2025",
                "date": "2025-08-20",
                "priority": "high",
                "message": "Welcome to all freshmen! The college orientation will be held at the Main Auditorium on August 20, 2025, starting at 9:00 AM. Attendance is mandatory.",
                "category": "academic",
                "active": True
            }
        ]
    }
    with open("announcements.json", "w") as f:
        json.dump(default_announcements, f, indent=2)

# Load trained model
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
    print("Neural network and vector store loaded successfully")
    
except FileNotFoundError:
    print("Neural network model not found. Run train.py first.")
    model = None
    hybrid_model = None

# Store conversation contexts for each user
user_contexts = {}

# Office mapping for context switching
office_tags = {
    'admission_office': 'Admission Office',
    'registrar_office': "Registrar's Office",
    'ict_office': 'ICT Office',
    'guidance_office': 'Guidance Office',
    'osa_office': 'Office of Student Affairs'
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
    elif 'osa' in msg_lower or 'student affairs' in msg_lower or 'clubs' in msg_lower or 'activities' in msg_lower:
        return 'osa_office'
    
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
    elif user_id in user_contexts:
        office = office_tags.get(user_contexts[user_id])
    
    # If still no office, try to detect from message content
    elif sender == "user":
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
            # Create document with office field
            document = {
                "user_id": user_id,
                "sender": sender,
                "message": message,
                "office": office,
                "timestamp": datetime.now(UTC)
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

def clear_chat_history(user_id):
    """Clear all chat history for a specific user"""
    global conversations
    
    if conversations is None:
        print("MongoDB not available. Cannot clear chat history.")
        return 0
    
    try:
        result = conversations.delete_many({"user_id": user_id})
        return result.deleted_count
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return 0

def get_active_announcements():
    """Get all active announcements sorted by priority and date"""
    announcements = load_announcements()
    active_announcements = [ann for ann in announcements if ann.get("active", True)]
    
    # Sort by priority (high, medium, low) then by date (newest first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    active_announcements.sort(
        key=lambda x: (priority_order.get(x.get("priority", "medium"), 1), x.get("date", ""))
    )
    
    return active_announcements

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
    """Search announcements using vector similarity"""
    vector_results = vector_store.search_announcements(query, top_k=3)
    
    if not vector_results:
        return format_announcements_response()
    
    response = "Relevant Announcements:\n\n"
    
    for result in vector_results:
        metadata = result['metadata']
        priority_emoji = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}
        priority = priority_emoji.get(metadata.get("priority", "medium"), "[INFO]")
        
        response += f"{priority} {metadata['title']} (Relevance: {result['score']:.2f})\n"
        response += f"Date: {metadata['date']}\n"
        response += f"{result['text']}\n\n"
    
    return response

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

def get_response(msg, user_id="guest"):
    # Clean the message
    cleaned_msg = clean_text(msg)
    sentence = tokenize(cleaned_msg)
    
    # Detect office from message for context
    detected_office = detect_office_from_message(msg)
    
    # Save user message with office context
    save_message(user_id, "user", msg, detected_office)

    # Check if user is asking to switch context or confirming switch
    msg_lower = msg.lower()
    if any(word in msg_lower for word in ['yes', 'switch', 'connect', 'change']):
        # User wants to switch context
        requested_office = detect_office_from_message(msg)
        if requested_office:
            user_contexts[user_id] = requested_office
            bot_response = f"Great! I've switched to help you with {office_tags[requested_office]} information. How can I assist you?"
            save_message(user_id, "bot", bot_response, requested_office)
            return bot_response

    # Detect which office the user is asking about
    requested_office = detect_office_from_message(msg)
    
    # Check if user has an active context
    current_context = user_contexts.get(user_id)
    
    # If user is asking about a different office than current context
    if current_context and requested_office and requested_office != current_context:
        bot_response = get_context_switch_response(current_context, requested_office, user_id)
        save_message(user_id, "bot", bot_response, current_context)
        return bot_response
    
    # Use hybrid model for prediction
    if hybrid_model and all_words:
        # Prepare input for neural network
        X = bag_of_words(sentence, all_words)
        X = torch.from_numpy(X).unsqueeze(0)
        
        # Get hybrid prediction
        hybrid_result = hybrid_model.get_hybrid_response(cleaned_msg, X)
        
        tag = hybrid_result['final_tag']
        confidence = hybrid_result['confidence']
        
        print(f"Hybrid prediction: tag={tag}, confidence={confidence:.3f}, method={hybrid_result['response_source']}")
        
        # High confidence threshold for proceeding
        if confidence > 0.7 and tag:
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
                            user_contexts[user_id] = tag
                        
                        # Reset context for greetings, thanks, goodbye
                        if tag in ['greeting', 'thanks', 'goodbye', 'fallback']:
                            user_contexts.pop(user_id, None)
                        
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
    
    # Fallback to vector search only
    if vector_store.index:
        vector_results = vector_store.search_similar(cleaned_msg, top_k=3, score_threshold=0.6)
        
        if vector_results:
            best_match = vector_results[0]
            tag = best_match['metadata'].get('tag')
            
            if tag:
                for intent in intents["intents"]:
                    if intent["tag"] == tag:
                        if tag in office_tags:
                            user_contexts[user_id] = tag
                        
                        bot_response = random.choice(intent["responses"])
                        office_context = tag if tag in office_tags else None
                        save_message(user_id, "bot", bot_response, office_context)
                        return bot_response
    
    # Final fallback
    if current_context:
        office_name = office_tags[current_context]
        bot_response = f"I'm currently helping you with {office_name} information. Could you rephrase your question about this office, or would you like to switch to a different topic?"
        save_message(user_id, "bot", bot_response, current_context)
    else:
        bot_response = "I'm not sure how to respond to that. Please try one of the suggested topics or rephrase your question."
        save_message(user_id, "bot", bot_response, None)
    
    return bot_response

def reset_user_context(user_id):
    """Reset user's conversation context"""
    user_contexts.pop(user_id, None)

def get_announcement_by_id(announcement_id):
    """Get a specific announcement by ID"""
    announcements = load_announcements()
    for ann in announcements:
        if ann["id"] == announcement_id:
            return ann
    return None

def add_announcement(title, date, message, priority="medium", category="general"):
    """Add a new announcement"""
    announcements = load_announcements()
    new_id = max([ann["id"] for ann in announcements], default=0) + 1
    
    new_announcement = {
        "id": new_id,
        "title": title,
        "date": date,
        "priority": priority,
        "message": message,
        "category": category,
        "active": True
    }
    
    announcements.append(new_announcement)
    
    # Save to file
    announcements_data = {"announcements": announcements}
    with open("announcements.json", "w") as f:
        json.dump(announcements_data, f, indent=2)
    
    # Store in vector database
    vector_store.store_announcements([new_announcement])
    
    return new_announcement

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

if __name__ == "__main__":
    print("Enhanced Chatbot with Vector Search is running! Type 'quit' to exit.\n")
    
    # Display connection status
    if check_mongodb_connection():
        print("MongoDB connection is healthy")
    else:
        print("MongoDB connection issues detected - running in limited mode")
    
    print()
    user_id = "guest"

    while True:
        user_message = input("You: ")
        if user_message.lower() == "quit":
            print("Bot: Goodbye!")
            break

        bot_reply = get_response(user_message, user_id)
        print(f"Bot: {bot_reply}")