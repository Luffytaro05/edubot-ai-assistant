from flask import Flask, jsonify, Blueprint, request
from pymongo import MongoClient
from datetime import datetime, timedelta

# Blueprint for dashboard routes
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations = db["conversations"]
sub_users = db["sub_users"]
faqs_collection = db["faqs"]

# -------------------------------
# KPIs
# -------------------------------
@dashboard_bp.route("/kpis", methods=["GET"])
def get_kpis():
    try:
        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        date_filter = {}
        if start_param:
            try:
                # Expect YYYY-MM-DD; treat as UTC day start
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
                date_filter.setdefault("$gte", start_dt.isoformat())
            except Exception:
                pass
        if end_param:
            try:
                # Inclusive end: next day start (UTC)
                end_dt = datetime.strptime(end_param, "%Y-%m-%d")
                date_filter.setdefault("$lt", (end_dt + timedelta(days=1)).isoformat())
            except Exception:
                pass

        match_stage = {"date": date_filter} if date_filter else {}

        # Unique users
        unique_users = len(conversations.distinct("user", filter=match_stage if match_stage else None))

        # Total conversations
        total_conversations = conversations.count_documents(match_stage if match_stage else {})

        # Resolution breakdown
        status_base = match_stage.copy() if match_stage else {}
        resolved_queries = conversations.count_documents({**status_base, "status": "resolved"})
        unresolved_queries = conversations.count_documents({**status_base, "status": "unresolved"})
        escalated_issues = conversations.count_documents({**status_base, "status": "escalated"})

        # Success rate (resolved / total)
        success_rate = (
            round((resolved_queries / total_conversations) * 100, 2)
            if total_conversations > 0 else 0
        )

        return jsonify({
            "uniqueUsers": unique_users,
            "totalConversations": total_conversations,
            "resolvedQueries": resolved_queries,
            "unresolvedQueries": unresolved_queries,
            "escalatedIssues": escalated_issues,
            "successRate": success_rate
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# -------------------------------
# Usage Trends
# -------------------------------
@dashboard_bp.route("/usage/<period>", methods=["GET"])
def get_usage(period):
    try:
        # Use UTC consistently for time buckets
        now = datetime.utcnow()
        labels, data = [], []
        
        print(f"Fetching usage data for period: {period}")

        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        date_filter = {}
        if start_param:
            try:
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
                date_filter.setdefault("$gte", start_dt.isoformat())
            except Exception:
                pass
        if end_param:
            try:
                end_dt = datetime.strptime(end_param, "%Y-%m-%d")
                date_filter.setdefault("$lt", (end_dt + timedelta(days=1)).isoformat())
            except Exception:
                pass

        if period == "hourly":
            # Past 24 hours
            start_time = now - timedelta(hours=23)
            pipeline = [
                {"$match": {"date": {**({"$gte": start_time.isoformat()} if not date_filter.get("$gte") else {}), **date_filter}}},
                {"$group": {
                    "_id": {"$substr": ["$date", 0, 13]},  # "YYYY-MM-DDTHH"
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            results = list(conversations.aggregate(pipeline))
            labels = [f"{i}:00" for i in range(24)]
            counts = {r["_id"][-2:]: r["count"] for r in results}
            data = [counts.get(f"{i:02}", 0) for i in range(24)]

        elif period == "daily":
            # Past 7 days
            start_time = now - timedelta(days=6)
            pipeline = [
                {"$match": {"date": {**({"$gte": start_time.isoformat()} if not date_filter.get("$gte") else {}), **date_filter}}},
                {"$group": {
                    "_id": {"$substr": ["$date", 0, 10]},  # "YYYY-MM-DD"
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            results = list(conversations.aggregate(pipeline))
            labels = [(now - timedelta(days=i)).strftime("%a") for i in range(6, -1, -1)]
            counts = {r["_id"]: r["count"] for r in results}
            data = [counts.get((now - timedelta(days=i)).strftime("%Y-%m-%d"), 0) for i in range(6, -1, -1)]

        elif period == "weekly":
            # Past 4 weeks
            labels = []
            data = []
            
            for i in range(3, -1, -1):  # 3 weeks ago to current week
                week_start = now - timedelta(weeks=i+1)
                week_end = now - timedelta(weeks=i)
                
                # Create readable label
                if i == 0:
                    label = "This Week"
                elif i == 1:
                    label = "Last Week"
                else:
                    label = f"{i+1} Weeks Ago"
                
                # Count conversations for this week
                date_bounds = {
                    "$gte": week_start.isoformat(),
                    "$lt": week_end.isoformat()
                }
                if date_filter.get("$gte") and date_filter["$gte"] > date_bounds["$gte"]:
                    date_bounds["$gte"] = date_filter["$gte"]
                if date_filter.get("$lt") and date_filter["$lt"] < date_bounds["$lt"]:
                    date_bounds["$lt"] = date_filter["$lt"]
                count = conversations.count_documents({"date": date_bounds})
                
                labels.append(label)
                data.append(count)
            
            print(f"Weekly data - Labels: {labels}, Data: {data}")

        return jsonify({"labels": labels, "data": data})

    except Exception as e:
        print(f"Error in get_usage endpoint for period '{period}': {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e), "labels": [], "data": []}), 500


# -------------------------------
# Department Distribution
# -------------------------------
@dashboard_bp.route("/departments", methods=["GET"])
def get_departments():
    try:
        # Optional date range filtering
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        date_filter = {}
        if start_param:
            try:
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
                date_filter.setdefault("$gte", start_dt.isoformat())
            except Exception:
                pass
        if end_param:
            try:
                end_dt = datetime.strptime(end_param, "%Y-%m-%d")
                date_filter.setdefault("$lt", (end_dt + timedelta(days=1)).isoformat())
            except Exception:
                pass
        # Define specific offices to display
        specific_offices = [
            "Admissions Office",
            "Registrar's Office",
            "ICT Office",
            "Guidance Office",
            "Office of the Student Affairs (OSA)",
            "General"
        ]
        
        # Get all conversations grouped by office
        pipeline = []
        if date_filter:
            pipeline.append({"$match": {"date": date_filter}})
        pipeline.append({"$group": {"_id": "$office", "count": {"$sum": 1}}})
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

    except Exception as e:
        return jsonify({"error": str(e), "labels": [], "data": []}), 500


# -------------------------------
# Recent Users (from user accounts)
# -------------------------------
@dashboard_bp.route("/recent-users", methods=["GET"])
def get_recent_users():
    try:
        # Optional date range filtering for last_login or createdAt
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        
        # Build date bounds for filtering
        start_dt = None
        end_dt = None
        if start_param:
            try:
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
            except Exception as e:
                print(f"Error parsing start_date: {e}")
        if end_param:
            try:
                end_dt = datetime.strptime(end_param, "%Y-%m-%d") + timedelta(days=1)
            except Exception as e:
                print(f"Error parsing end_date: {e}")

        # Get recent user accounts sorted by last_login
        # Find users who have logged in recently
        base_filter = {"last_login": {"$ne": None}}
        
        # Add date filtering if provided
        if start_dt or end_dt:
            date_conditions = []
            
            # Build date range for last_login
            login_condition = {}
            if start_dt:
                login_condition["$gte"] = start_dt
            if end_dt:
                login_condition["$lt"] = end_dt
            
            if login_condition:
                date_conditions.append({"last_login": login_condition})
            
            # Build date range for createdAt
            created_condition = {}
            if start_dt:
                created_condition["$gte"] = start_dt
            if end_dt:
                created_condition["$lt"] = end_dt
            
            if created_condition:
                date_conditions.append({"createdAt": created_condition})
            
            # Combine: must have last_login AND (last_login in range OR createdAt in range)
            if date_conditions:
                base_filter = {
                    "$and": [
                        {"last_login": {"$ne": None}},
                        {"$or": date_conditions}
                    ]
                }
        
        recent_users = list(sub_users.find(
            base_filter,
            {"password": 0}  # Exclude password field
        ).sort("last_login", -1).limit(10))
        
        # If no users with login history, get most recent created users
        if not recent_users:
            # Fallback: get by creation date
            createdAt_filter = {}
            if start_dt or end_dt:
                # Build date range for createdAt
                created_range = {}
                if start_dt:
                    created_range["$gte"] = start_dt
                if end_dt:
                    created_range["$lt"] = end_dt
                if created_range:
                    createdAt_filter["createdAt"] = created_range
            
            recent_users = list(sub_users.find(
                createdAt_filter,
                {"password": 0}
            ).sort("createdAt", -1).limit(10))
        
        # Format the response
        formatted_users = []
        for user in recent_users:
            # Format last_login
            last_login = user.get("last_login", "Never")
            if last_login and last_login != "Never":
                try:
                    # Try to format if it's a datetime object or ISO string
                    if isinstance(last_login, str):
                        dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    else:
                        dt = last_login
                    last_login = dt.strftime("%b %d, %Y %I:%M %p")
                except:
                    last_login = str(last_login)
            
            formatted_users.append({
                "id": str(user["_id"]),
                "name": user.get("name", "Unknown"),
                "email": user.get("email", ""),
                "office": user.get("office", "Unknown Office"),
                "role": user.get("role", "User"),
                "status": user.get("status", "Active"),
                "last_login": last_login
            })
        
        return jsonify({
            "success": True,
            "users": formatted_users
        })
        
    except Exception as e:
        print(f"Error fetching recent users: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e),
            "users": []
        }), 500


# -------------------------------
# Recent FAQ Activity (Office Activity)
# -------------------------------
@dashboard_bp.route("/faq-activity", methods=["GET"])
def get_faq_activity():
    try:
        # Optional date range; default to last 7 days
        start_param = request.args.get('start_date')
        end_param = request.args.get('end_date')
        if start_param:
            try:
                start_dt = datetime.strptime(start_param, "%Y-%m-%d")
            except Exception:
                start_dt = None
        else:
            start_dt = datetime.utcnow() - timedelta(days=7)

        end_dt = None
        if end_param:
            try:
                end_dt = datetime.strptime(end_param, "%Y-%m-%d") + timedelta(days=1)
            except Exception:
                end_dt = None

        # Get recently updated FAQs
        faq_filter = {}
        if start_dt or end_dt:
            bounds = {}
            if start_dt:
                bounds["$gte"] = start_dt
            if end_dt:
                bounds["$lt"] = end_dt
            faq_filter["updated_at"] = bounds
        else:
            faq_filter["updated_at"] = {"$gte": start_dt}

        recent_faqs = list(faqs_collection.find(faq_filter).sort("updated_at", -1).limit(10))
        
        # If no recent updates, get recently created FAQs
        if not recent_faqs:
            if start_dt or end_dt:
                created_bounds = {}
                if start_dt:
                    created_bounds["$gte"] = start_dt
                if end_dt:
                    created_bounds["$lt"] = end_dt
                recent_faqs = list(faqs_collection.find({"created_at": created_bounds}).sort("created_at", -1).limit(10))
            else:
                recent_faqs = list(faqs_collection.find().sort("created_at", -1).limit(10))
        
        # Group by office and count
        office_activity = {}
        for faq in recent_faqs:
            office = faq.get('office', 'Unknown Office')
            if office not in office_activity:
                office_activity[office] = {
                    'office': office,
                    'count': 0,
                    'last_update': faq.get('updated_at', faq.get('created_at'))
                }
            office_activity[office]['count'] += 1
        
        # Convert to list and sort by last update
        activity_list = list(office_activity.values())
        activity_list.sort(key=lambda x: x['last_update'], reverse=True)
        
        # Format the response
        formatted_activity = []
        for activity in activity_list[:5]:  # Top 5 offices
            # Calculate time ago
            last_update = activity['last_update']
            if isinstance(last_update, str):
                last_update = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
            
            time_diff = datetime.utcnow() - last_update
            if time_diff.days > 0:
                time_ago = f"{time_diff.days} day{'s' if time_diff.days > 1 else ''} ago"
            elif time_diff.seconds >= 3600:
                hours = time_diff.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif time_diff.seconds >= 60:
                minutes = time_diff.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_ago = "Just now"
            
            # Determine action description
            if activity['count'] == 1:
                description = "Updated 1 FAQ entry"
            else:
                description = f"Updated {activity['count']} FAQ entries"
            
            formatted_activity.append({
                'office': activity['office'],
                'description': description,
                'time_ago': time_ago,
                'count': activity['count']
            })
        
        return jsonify({
            'success': True,
            'activity': formatted_activity
        })
        
    except Exception as e:
        print(f"Error fetching FAQ activity: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'activity': []
        }), 500


# -------------------------------
# Register Blueprint in main app
# -------------------------------
def init_app(app: Flask):
    app.register_blueprint(dashboard_bp)
