from flask import Flask, jsonify, Blueprint
from pymongo import MongoClient
from datetime import datetime, timedelta

# Blueprint for dashboard routes
dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations = db["conversations"]

# -------------------------------
# KPIs
# -------------------------------
@dashboard_bp.route("/kpis", methods=["GET"])
def get_kpis():
    try:
        # Unique users
        unique_users = len(conversations.distinct("user"))

        # Total conversations
        total_conversations = conversations.count_documents({})

        # Resolution breakdown
        resolved_queries = conversations.count_documents({"status": "resolved"})
        unresolved_queries = conversations.count_documents({"status": "unresolved"})
        escalated_issues = conversations.count_documents({"status": "escalated"})

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
        now = datetime.utcnow()
        labels, data = [], []

        if period == "hourly":
            # Past 24 hours
            start_time = now - timedelta(hours=23)
            pipeline = [
                {"$match": {"date": {"$gte": start_time.isoformat()}}},
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
                {"$match": {"date": {"$gte": start_time.isoformat()}}},
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
            start_time = now - timedelta(weeks=3)
            pipeline = [
                {"$match": {"date": {"$gte": start_time.isoformat()}}},
                {"$group": {
                    "_id": {"$isoWeek": {"date": {"$toDate": "$date"}}},
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id": 1}}
            ]
            results = list(conversations.aggregate(pipeline))
            labels = [f"Week {i}" for i in range(1, 5)]
            counts = {str(r["_id"]): r["count"] for r in results}
            data = [counts.get(str(i), 0) for i in range(1, 5)]

        return jsonify({"labels": labels, "data": data})

    except Exception as e:
        return jsonify({"error": str(e), "labels": [], "data": []}), 500


# -------------------------------
# Department Distribution
# -------------------------------
@dashboard_bp.route("/departments", methods=["GET"])
def get_departments():
    try:
        pipeline = [
            {"$group": {"_id": "$detected_office", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        results = list(conversations.aggregate(pipeline))

        labels = [r["_id"] if r["_id"] else "Unknown" for r in results]
        data = [r["count"] for r in results]

        return jsonify({"labels": labels, "data": data})

    except Exception as e:
        return jsonify({"error": str(e), "labels": [], "data": []}), 500


# -------------------------------
# Register Blueprint in main app
# -------------------------------
def init_app(app: Flask):
    app.register_blueprint(dashboard_bp)
