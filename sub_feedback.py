"""
sub_feedback.py
Flask Blueprint for Sub-Admin Feedback Analytics
Provides global feedback statistics and recent reviews across all offices
"""

from flask import Blueprint, jsonify, session, request
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import traceback

sub_feedback_bp = Blueprint("sub_feedback", __name__)

# MongoDB setup
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
feedback_collection = db["feedback"]

def get_current_subadmin():
    """Get logged-in sub-admin from Flask session"""
    if session.get("role") == "sub-admin" and session.get("office"):
        return {
            "office": session.get("office"),
            "name": session.get("name", "Sub Admin"),
            "email": session.get("email")
        }
    return None

def determine_sentiment(rating, comment=None):
    """
    Determine sentiment based on rating and optional comment analysis
    
    Args:
        rating (int): Rating from 1-5
        comment (str, optional): Feedback comment
    
    Returns:
        str: 'positive', 'neutral', or 'negative'
    """
    if rating >= 4:
        return "positive"
    elif rating == 3:
        return "neutral"
    else:
        return "negative"

def serialize_feedback(feedback_doc):
    """Convert MongoDB document to JSON-serializable dict"""
    if feedback_doc:
        feedback_doc['_id'] = str(feedback_doc['_id'])
        if 'timestamp' in feedback_doc and isinstance(feedback_doc['timestamp'], datetime):
            feedback_doc['timestamp'] = feedback_doc['timestamp'].isoformat()
        if 'created_at' in feedback_doc and isinstance(feedback_doc['created_at'], datetime):
            feedback_doc['created_at'] = feedback_doc['created_at'].isoformat()
        
        # Add sentiment if not present
        if 'sentiment' not in feedback_doc:
            feedback_doc['sentiment'] = determine_sentiment(
                feedback_doc.get('rating', 3),
                feedback_doc.get('comment')
            )
    return feedback_doc

@sub_feedback_bp.route("/api/sub-admin/feedback/stats", methods=["GET"])
def get_feedback_stats():
    """Return aggregated feedback KPIs (global across all offices)"""
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        # Get time filter if provided
        time_filter = request.args.get("time_filter", None)
        time_value = request.args.get("time_value", None)
        
        # Build query based on time filter
        query = {}
        if time_filter and time_value:
            try:
                time_value = int(time_value)
                end_date = datetime.utcnow()
                
                if time_filter == "hours":
                    start_date = end_date - timedelta(hours=time_value)
                elif time_filter == "days":
                    start_date = end_date - timedelta(days=time_value)
                elif time_filter == "weeks":
                    start_date = end_date - timedelta(weeks=time_value)
                else:
                    start_date = None
                
                if start_date:
                    query["timestamp"] = {"$gte": start_date, "$lte": end_date}
            except ValueError:
                pass

        # Total Reviews
        total_reviews = feedback_collection.count_documents(query)

        # Average Rating
        pipeline = [
            {"$match": query},
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        avg_result = list(feedback_collection.aggregate(pipeline))
        average_rating = round(avg_result[0]["avg_rating"], 2) if avg_result and avg_result[0]["avg_rating"] else 0.0

        # Positive, Negative, Neutral Counts
        positive_count = feedback_collection.count_documents({**query, "rating": {"$gte": 4}})
        negative_count = feedback_collection.count_documents({**query, "rating": {"$lte": 2}})
        neutral_count = feedback_collection.count_documents({**query, "rating": 3})

        # Calculate percentages
        if total_reviews > 0:
            positive_percentage = round((positive_count / total_reviews) * 100, 1)
            negative_percentage = round((negative_count / total_reviews) * 100, 1)
            neutral_percentage = round((neutral_count / total_reviews) * 100, 1)
        else:
            positive_percentage = 0.0
            negative_percentage = 0.0
            neutral_percentage = 0.0

        # Rating Distribution
        rating_distribution = {}
        for i in range(1, 6):
            count = feedback_collection.count_documents({**query, "rating": i})
            rating_distribution[f"{i}_star"] = count

        return jsonify({
            "success": True,
            "data": {
                "average_rating": average_rating,
                "total_reviews": total_reviews,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "positive_percentage": positive_percentage,
                "negative_percentage": negative_percentage,
                "neutral_percentage": neutral_percentage,
                "rating_distribution": rating_distribution
            }
        }), 200

    except Exception as e:
        print(f"ERROR in get_feedback_stats: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500

@sub_feedback_bp.route("/api/sub-admin/feedback/recent", methods=["GET"])
def get_recent_feedback():
    """Return recent feedback (last 10-20 reviews globally)"""
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        # Get query parameters
        limit = min(int(request.args.get("limit", 20)), 50)
        rating_filter = request.args.get("rating", None)
        time_filter = request.args.get("time_filter", None)
        time_value = request.args.get("time_value", None)
        search_query = request.args.get("search", None)

        # Build query
        query = {}
        
        if rating_filter:
            try:
                rating_filter = int(rating_filter)
                if 1 <= rating_filter <= 5:
                    query["rating"] = rating_filter
            except ValueError:
                pass

        if time_filter and time_value:
            try:
                time_value = int(time_value)
                end_date = datetime.utcnow()
                
                if time_filter == "hours":
                    start_date = end_date - timedelta(hours=time_value)
                elif time_filter == "days":
                    start_date = end_date - timedelta(days=time_value)
                elif time_filter == "weeks":
                    start_date = end_date - timedelta(weeks=time_value)
                else:
                    start_date = None
                
                if start_date:
                    query["timestamp"] = {"$gte": start_date, "$lte": end_date}
            except ValueError:
                pass

        if search_query:
            query["comment"] = {"$regex": search_query, "$options": "i"}

        # Fetch feedback
        feedback_list = list(
            feedback_collection.find(query)
            .sort("timestamp", -1)
            .limit(limit)
        )

        # Serialize feedback documents
        serialized_feedback = [serialize_feedback(fb) for fb in feedback_list]

        return jsonify({
            "success": True,
            "data": serialized_feedback,
            "count": len(serialized_feedback)
        }), 200

    except Exception as e:
        print(f"ERROR in get_recent_feedback: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "message": f"Error: {str(e)}"}), 500
