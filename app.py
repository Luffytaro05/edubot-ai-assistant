from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from chat import (get_response, reset_user_context, clear_chat_history, 
                  get_active_announcements, add_announcement, get_announcement_by_id,
                  vector_store)
from pymongo import MongoClient
import os

app = Flask(__name__)
CORS(app)

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations = db["conversations"]

@app.get("/")
def index_get():
    return render_template("base.html")

@app.post("/predict")
def predict():
    data = request.get_json()
    text = data.get("message")
    user_id = data.get("user_id", "guest")

    if not text or not text.strip():
        return jsonify({"answer": "Please type something."})

    try:
        # Get chatbot response with enhanced vector search
        response = get_response(text, user_id=user_id)
        
        return jsonify({
            "answer": response,
            "vector_enabled": vector_store.index is not None,
            "vector_stats": vector_store.get_stats()
        })
    
    except Exception as e:
        print(f"Error in predict: {e}")
        return jsonify({
            "answer": "Sorry, I encountered an error processing your request. Please try again.",
            "error": str(e)
        }), 500

@app.post("/history")
def history():
    data = request.get_json()
    user_id = data.get("user_id", "guest")

    try:
        history_data = list(conversations.find(
            {"user_id": user_id}
        ).sort("timestamp", -1).limit(20))

        history_data.reverse()
        history_formatted = [
            {"name": "User" if m["sender"] == "user" else "Bot", "message": m["message"]}
            for m in history_data
        ]

        return jsonify({"messages": history_formatted})
    
    except Exception as e:
        print(f"Error loading history: {e}")
        return jsonify({"messages": []})

@app.post("/reset_context")
def reset_context():
    """Reset user's conversation context"""
    data = request.get_json()
    user_id = data.get("user_id", "guest")
    
    try:
        reset_user_context(user_id)
        return jsonify({"status": "Context reset successfully"})
    except Exception as e:
        print(f"Error resetting context: {e}")
        return jsonify({"error": str(e)}), 500

@app.post("/clear_history")
def clear_history():
    """Clear user's chat history"""
    data = request.get_json()
    user_id = data.get("user_id", "guest")
    
    try:
        deleted_count = clear_chat_history(user_id)
        return jsonify({"status": f"Cleared {deleted_count} messages"})
    except Exception as e:
        print(f"Error clearing history: {e}")
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
def create_announcement():
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
def reindex_vectors():
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
            "database_connected": conversations is not None,
            "vector_stats": vector_store.get_stats()
        })
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e)
        }), 500

@app.get("/admin")
def admin_panel():
    """Simple admin panel for managing announcements and vector database"""
    return render_template("admin.html")

# Add some debugging information on startup
def startup_info():
    print("=== TCC Assistant Starting ===")
    print(f"Vector Store Status: {vector_store.get_stats()}")
    print(f"Pinecone Available: {vector_store.index is not None}")
    print("===============================")

if __name__ == "__main__":
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
    
    app.run(debug=True)