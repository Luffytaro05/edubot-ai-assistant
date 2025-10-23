"""
sub_usage.py
Flask Blueprint for Sub Admin Usage Statistics
Calculates and returns office-specific usage metrics
"""

from flask import Blueprint, jsonify, session, request
from pymongo import MongoClient
from datetime import datetime, timedelta
from collections import Counter
import traceback

sub_usage_bp = Blueprint("sub_usage", __name__)

# MongoDB setup
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations_col = db["conversations"]
sub_users_col = db["sub_users"]

def get_current_subadmin():
    """Get logged-in sub-admin from Flask session"""
    if session.get("role") == "sub-admin" and session.get("office"):
        return {
            "office": session.get("office"),
            "name": session.get("name", "Sub Admin"),
            "email": session.get("email")
        }
    return None

def format_duration(seconds):
    """Format duration in seconds to human-readable format"""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

def classify_time_of_day(hour):
    """Classify hour into time period"""
    if 6 <= hour < 12:
        return "Morning"
    elif 12 <= hour < 17:
        return "Afternoon"
    elif 17 <= hour < 21:
        return "Evening"
    else:
        return "Night"

@sub_usage_bp.route("/api/sub-admin/usage/overview", methods=["GET"])
def get_usage_overview():
    """
    Return comprehensive usage statistics for the logged-in sub-admin's office
    Includes: Total Sessions, Avg Duration, Response Rate, Success Rate
    """
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        
        # Check for single date filter
        filter_date_param = request.args.get('filter_date')
        
        if filter_date_param:
            # Single date filter - filter for that specific day
            try:
                filter_dt = datetime.strptime(filter_date_param, "%Y-%m-%d")
                start_date = filter_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
            except Exception:
                # Fallback to default range
                days = int(request.args.get("days", 30))
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=days)
        else:
            # Get date range (default: last 30 days)
            days = int(request.args.get("days", 30))
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

        # Query for all conversations in this office with date filter
        date_query = {
            "$or": [
                {"timestamp": {"$exists": True, "$gte": start_date, "$lt": end_date}},
                {"date": {"$exists": True, "$gte": start_date.isoformat(), "$lt": end_date.isoformat()}}
            ]
        }
        
        all_conversations = list(conversations_col.find({
            "office": office,
            **date_query
        }))

        # ==========================================
        # 1. Total Sessions Calculation
        # ==========================================
        # Group conversations by user to count unique sessions
        user_sessions = {}
        for conv in all_conversations:
            user = conv.get("user", "Anonymous")
            if user not in user_sessions:
                user_sessions[user] = []
            user_sessions[user].append(conv)
        
        total_sessions = len(user_sessions)

        # ==========================================
        # 2. Average Session Duration
        # ==========================================
        total_duration_seconds = 0
        sessions_with_duration = 0
        
        for user, convs in user_sessions.items():
            # Sort conversations by timestamp
            sorted_convs = sorted(convs, key=lambda x: x.get("date", datetime.min))
            
            if len(sorted_convs) >= 2:
                # Calculate duration from first to last message
                first_time = sorted_convs[0].get("date")
                last_time = sorted_convs[-1].get("date")
                
                if first_time and last_time:
                    if isinstance(first_time, str):
                        first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
                    if isinstance(last_time, str):
                        last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))
                    
                    duration = (last_time - first_time).total_seconds()
                    if duration > 0:
                        total_duration_seconds += duration
                        sessions_with_duration += 1
            elif conv.get("duration"):
                # Use pre-calculated duration if available
                total_duration_seconds += conv.get("duration", 0)
                sessions_with_duration += 1
        
        avg_session_duration_seconds = (
            total_duration_seconds / sessions_with_duration 
            if sessions_with_duration > 0 
            else 0
        )
        avg_duration_formatted = format_duration(avg_session_duration_seconds)

        # ==========================================
        # 3. Response Rate Calculation
        # ==========================================
        # Count user messages and bot responses
        user_messages = [c for c in all_conversations if c.get("sender") == "user"]
        bot_messages = [c for c in all_conversations if c.get("sender") == "bot"]
        
        total_user_messages = len(user_messages)
        total_bot_responses = len(bot_messages)
        
        # Response Rate = (Bot Responses / User Messages) × 100
        response_rate = (
            (total_bot_responses / total_user_messages * 100) 
            if total_user_messages > 0 
            else 0
        )

        # ==========================================
        # 4. Success Rate Calculation
        # ==========================================
        # Count resolved vs total conversations (with date filter)
        resolved_conversations = conversations_col.count_documents({
            "office": office,
            "status": "resolved",
            **date_query
        })
        
        escalated_conversations = conversations_col.count_documents({
            "office": office,
            "status": "escalated",
            **date_query
        })
        
        total_with_status = resolved_conversations + escalated_conversations
        
        # Success Rate = (Resolved / Total with Status) × 100
        success_rate = (
            (resolved_conversations / total_with_status * 100) 
            if total_with_status > 0 
            else 0
        )

        # Prepare response data
        overview = {
            "totalSessions": total_sessions,
            "avgSessionDuration": avg_duration_formatted,
            "avgSessionDurationSeconds": round(avg_session_duration_seconds, 2),
            "responseRate": round(response_rate, 1),
            "successRate": round(success_rate, 1),
            "totalUserMessages": total_user_messages,
            "totalBotResponses": total_bot_responses,
            "resolvedQueries": resolved_conversations,
            "escalatedQueries": escalated_conversations,
            "office": office
        }

        return jsonify({"success": True, "data": overview})

    except Exception as e:
        print(f"ERROR in /api/sub-admin/usage/overview: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@sub_usage_bp.route("/api/sub-admin/usage/time-of-day", methods=["GET"])
def get_usage_by_time():
    """
    Return usage statistics grouped by time of day
    Categories: Morning (6-12), Afternoon (12-17), Evening (17-21), Night (21-6)
    """
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        
        # Check for single date filter
        filter_date_param = request.args.get('filter_date')
        
        # Build date filter
        date_filter = {"$exists": True}
        if filter_date_param:
            try:
                filter_dt = datetime.strptime(filter_date_param, "%Y-%m-%d")
                start_date = filter_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
                date_filter = {
                    "$gte": start_date.isoformat(),
                    "$lt": end_date.isoformat()
                }
            except Exception:
                date_filter = {"$exists": True}
        
        # Get all conversations with timestamps
        conversations = list(conversations_col.find({
            "office": office,
            "date": date_filter
        }))

        # Count conversations by time period
        time_periods = Counter()
        
        for conv in conversations:
            date = conv.get("date")
            if date:
                if isinstance(date, str):
                    try:
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))
                    except:
                        continue
                
                hour = date.hour
                period = classify_time_of_day(hour)
                time_periods[period] += 1

        # Ensure all periods are represented
        all_periods = ["Morning", "Afternoon", "Evening", "Night"]
        time_data = {
            "labels": all_periods,
            "counts": [time_periods.get(period, 0) for period in all_periods],
            "office": office
        }

        return jsonify({"success": True, "data": time_data})

    except Exception as e:
        print(f"ERROR in /api/sub-admin/usage/time-of-day: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@sub_usage_bp.route("/api/sub-admin/usage/top-categories", methods=["GET"])
def get_top_categories():
    """
    Return top query categories/intents from conversations
    """
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        limit = int(request.args.get("limit", 10))
        
        # Check for single date filter
        filter_date_param = request.args.get('filter_date')
        
        # Build query
        query_filter = {
            "office": office,
            "category": {"$exists": True}
        }
        
        if filter_date_param:
            try:
                filter_dt = datetime.strptime(filter_date_param, "%Y-%m-%d")
                start_date = filter_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = start_date + timedelta(days=1)
                query_filter["$or"] = [
                    {"timestamp": {"$exists": True, "$gte": start_date, "$lt": end_date}},
                    {"date": {"$exists": True, "$gte": start_date.isoformat(), "$lt": end_date.isoformat()}}
                ]
            except Exception:
                pass  # Skip date filter if parsing fails
        
        # Get all conversations with category field
        conversations = list(conversations_col.find(query_filter))

        # Count categories
        category_counter = Counter()
        for conv in conversations:
            category = conv.get("category", "General")
            if category:
                category_counter[category] += 1

        # Get top N categories
        top_categories = category_counter.most_common(limit)
        
        # Format data for frontend
        categories_data = {
            "categories": [
                {
                    "name": category,
                    "count": count,
                    "percentage": round((count / len(conversations) * 100) if len(conversations) > 0 else 0, 1)
                }
                for category, count in top_categories
            ],
            "totalConversations": len(conversations),
            "office": office
        }

        return jsonify({"success": True, "data": categories_data})

    except Exception as e:
        print(f"ERROR in /api/sub-admin/usage/top-categories: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@sub_usage_bp.route("/api/sub-admin/usage/export", methods=["GET"])
def export_usage_stats():
    """
    Export usage statistics as CSV
    """
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        
        # Get all statistics
        # Note: In a real implementation, you'd make internal calls or refactor
        # For now, return a CSV structure
        
        csv_data = f"""Office,Metric,Value
{office},Total Sessions,{conversations_col.count_documents({"office": office})}
{office},User Messages,{conversations_col.count_documents({"office": office, "sender": "user"})}
{office},Bot Responses,{conversations_col.count_documents({"office": office, "sender": "bot"})}
{office},Resolved Queries,{conversations_col.count_documents({"office": office, "status": "resolved"})}
{office},Escalated Queries,{conversations_col.count_documents({"office": office, "status": "escalated"})}
"""

        return jsonify({"success": True, "data": csv_data, "filename": f"{office.replace(' ', '_')}_usage_stats.csv"})

    except Exception as e:
        print(f"ERROR in /api/sub-admin/usage/export: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500

