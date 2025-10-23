from flask import Blueprint, jsonify, session, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import traceback

sub_dashboard_bp = Blueprint("sub_dashboard", __name__)

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

@sub_dashboard_bp.route("/api/sub-admin/stats", methods=["GET"])
def get_stats():
    """Return dashboard stats for the logged-in sub-admin's office"""
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")

        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        date_filter = {}
        if start_param:
            try:
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
                date_filter["$gte"] = start_dt.isoformat()
            except Exception:
                pass
        if end_param:
            try:
                end_dt = datetime.strptime(end_param, "%Y-%m-%d")
                date_filter["$lt"] = (end_dt + timedelta(days=1)).isoformat()
            except Exception:
                pass

        # Base filter with office
        base_filter = {"office": office}
        if date_filter:
            base_filter["date"] = date_filter

        # Count unique users who interacted with this office
        unique_users = len(conversations_col.distinct("user", filter=base_filter))

        # Total conversations for this office
        total_conversations = conversations_col.count_documents(base_filter)

        # Resolved queries
        resolved_queries = conversations_col.count_documents({
            **base_filter,
            "status": "resolved"
        })

        # Escalated queries
        escalated_queries = conversations_col.count_documents({
            **base_filter,
            "status": "escalated"
        })

        stats = {
            "office": office,
            "name": sub_admin.get("name"),
            "office_users": unique_users,
            "office_conversations": total_conversations,
            "office_resolved_queries": resolved_queries,
            "office_escalated_issues": escalated_queries,
        }

        return jsonify({"success": True, "stats": stats})

    except Exception as e:
        print(f"ERROR in /api/sub-admin/stats: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@sub_dashboard_bp.route("/api/sub-admin/weekly-usage", methods=["GET"])
def weekly_usage():
    """Return daily chatbot usage for the last 7 days (per office)"""
    try:
        # Debug: Print session data
        print(f"DEBUG: Session data: {dict(session)}")
        
        sub_admin = get_current_subadmin()
        if not sub_admin:
            print("DEBUG: Not authenticated - session invalid")
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        print(f"DEBUG: Loading weekly usage for office: {office}")
        
        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        
        if start_param and end_param:
            try:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.strptime(end_param, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                print(f"DEBUG: Using custom date range: {start_date} to {end_date}")
            except Exception as e:
                print(f"DEBUG: Error parsing dates, using default: {e}")
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = today - timedelta(days=6)
                end_date = today
        else:
            # Calculate date range (last 7 days)
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=6)
            end_date = today

        # First, check if any documents exist for this office
        total_docs = conversations_col.count_documents({"office": office})
        print(f"DEBUG: Total documents for {office}: {total_docs}")
        
        # Check documents with timestamp field
        docs_with_timestamp = conversations_col.count_documents({
            "office": office,
            "timestamp": {"$exists": True}
        })
        print(f"DEBUG: Documents with timestamp: {docs_with_timestamp}")

        # MongoDB aggregation pipeline
        pipeline = [
            {
                "$match": {
                    "office": office,
                    "sender": "user",  # Only count user queries, not bot responses
                    "$or": [
                        {"timestamp": {"$exists": True, "$gte": start_date, "$lte": end_date + timedelta(days=1)}},
                        {"date": {"$exists": True, "$gte": start_date.isoformat(), "$lt": (end_date + timedelta(days=1)).isoformat()}}
                    ]
                }
            },
            {
                "$addFields": {
                    "parsedDate": {
                        "$cond": [
                            {"$ifNull": ["$timestamp", False]},
                            "$timestamp",
                            {"$dateFromString": {"dateString": "$date"}}
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$parsedDate"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        try:
            results = list(conversations_col.aggregate(pipeline))
            print(f"DEBUG: Aggregation returned {len(results)} results: {results}")
        except Exception as agg_error:
            print(f"ERROR: Aggregation failed: {agg_error}")
            print(traceback.format_exc())
            
            # Fallback: Return empty data if aggregation fails
            usage_data = []
            days_diff = (end_date - start_date).days + 1
            for i in range(days_diff):
                current_day = start_date + timedelta(days=i)
                date_label = current_day.strftime("%b %d")
                usage_data.append({"date": date_label, "count": 0})
            
            return jsonify({
                "success": True,
                "usage": usage_data,
                "office": office,
                "note": "Using fallback data due to aggregation error"
            })

        # Create a complete date range (dynamic based on filter)
        usage_data = []
        usage_dict = {item["_id"]: item["count"] for item in results}

        # Calculate the number of days in the range
        days_diff = (end_date - start_date).days + 1
        
        for i in range(days_diff):
            current_day = start_date + timedelta(days=i)
            date_key = current_day.strftime("%Y-%m-%d")
            date_label = current_day.strftime("%b %d")  # e.g., "Sep 24"
            
            usage_data.append({
                "date": date_label,
                "count": usage_dict.get(date_key, 0)
            })

        return jsonify({
            "success": True,
            "usage": usage_data,
            "office": office
        })

    except Exception as e:
        print(f"ERROR in /api/sub-admin/weekly-usage: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500


@sub_dashboard_bp.route("/api/sub-admin/office-info", methods=["GET"])
def get_office_info():
    """Get current office information"""
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        return jsonify({
            "success": True,
            "office": sub_admin.get("office"),
            "name": sub_admin.get("name"),
            "email": sub_admin.get("email")
        })

    except Exception as e:
        print(f"ERROR in /api/sub-admin/office-info: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@sub_dashboard_bp.route("/api/sub-admin/export", methods=["GET"])
def export_dashboard():
    """Export sub-admin dashboard data as CSV"""
    try:
        sub_admin = get_current_subadmin()
        if not sub_admin:
            return jsonify({"success": False, "message": "Not authenticated"}), 401

        office = sub_admin.get("office")
        name = sub_admin.get("name", "Sub Admin")

        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        
        if start_param and end_param:
            try:
                start_date = datetime.strptime(start_param, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = datetime.strptime(end_param, "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                date_range_label = f"{start_param} to {end_param}"
            except Exception:
                today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                start_date = today - timedelta(days=6)
                end_date = today
                date_range_label = "Last 7 days"
        else:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            start_date = today - timedelta(days=6)
            end_date = today
            date_range_label = "Last 7 days"

        # Build date filter
        date_filter = {}
        date_filter["$gte"] = start_date.isoformat()
        date_filter["$lt"] = (end_date + timedelta(days=1)).isoformat()

        base_filter = {"office": office, "date": date_filter}

        # Gather all stats
        unique_users = len(conversations_col.distinct("user", filter=base_filter))
        total_conversations = conversations_col.count_documents(base_filter)
        resolved_queries = conversations_col.count_documents({**base_filter, "status": "resolved"})
        escalated_queries = conversations_col.count_documents({**base_filter, "status": "escalated"})
        
        # Calculate success rate
        success_rate = round((resolved_queries / total_conversations * 100), 2) if total_conversations > 0 else 0

        # Get daily usage data
        pipeline = [
            {
                "$match": {
                    "office": office,
                    "sender": "user",
                    "$or": [
                        {"timestamp": {"$exists": True, "$gte": start_date, "$lte": end_date + timedelta(days=1)}},
                        {"date": {"$exists": True, "$gte": start_date.isoformat(), "$lt": (end_date + timedelta(days=1)).isoformat()}}
                    ]
                }
            },
            {
                "$addFields": {
                    "parsedDate": {
                        "$cond": [
                            {"$ifNull": ["$timestamp", False]},
                            "$timestamp",
                            {"$dateFromString": {"dateString": "$date"}}
                        ]
                    }
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$parsedDate"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]

        daily_results = list(conversations_col.aggregate(pipeline))
        usage_dict = {item["_id"]: item["count"] for item in daily_results}

        # Build CSV content
        csv_lines = []
        csv_lines.append(f"Sub-Admin Dashboard Export - {office}")
        csv_lines.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        csv_lines.append(f"Sub-Admin: {name}")
        csv_lines.append(f"Date Range: {date_range_label}")
        csv_lines.append("")
        
        # KPI Summary
        csv_lines.append("KEY PERFORMANCE INDICATORS")
        csv_lines.append("Metric,Value")
        csv_lines.append(f"Total Users,{unique_users}")
        csv_lines.append(f"Total Conversations,{total_conversations}")
        csv_lines.append(f"Resolved Queries,{resolved_queries}")
        csv_lines.append(f"Escalated Queries,{escalated_queries}")
        csv_lines.append(f"Success Rate,{success_rate}%")
        csv_lines.append("")
        
        # Daily Usage
        csv_lines.append("DAILY USAGE")
        csv_lines.append("Date,Queries")
        
        days_diff = (end_date - start_date).days + 1
        for i in range(days_diff):
            current_day = start_date + timedelta(days=i)
            date_key = current_day.strftime("%Y-%m-%d")
            date_label = current_day.strftime("%b %d, %Y")
            count = usage_dict.get(date_key, 0)
            csv_lines.append(f"{date_label},{count}")
        
        csv_lines.append("")
        csv_lines.append("End of Report")

        csv_content = "\n".join(csv_lines)
        filename = f"sub-dashboard-{office.replace(' ', '-').lower()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.csv"

        return jsonify({
            "success": True,
            "csv": csv_content,
            "filename": filename
        })

    except Exception as e:
        print(f"ERROR in /api/sub-admin/export: {e}")
        print(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)}), 500