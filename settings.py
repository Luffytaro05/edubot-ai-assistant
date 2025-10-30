from flask import jsonify, request
from pymongo import MongoClient

# Use the same cluster/db naming convention as app.py
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
settings_collection = db["bot_settings"]


def get_default_settings():
    return {
        "bot_name": "TCC Assistant",
        "bot_avatar": "/static/images/bot-icon.png",
        "welcome_message": "Hello! How can I assist you today?",
        "office_specific_messages": {},
        "suggested_messages": [],
        # Increase default timeout to better accommodate cold starts on Railway
        "response_timeout": 90,
        "show_typing_indicator": True,
        "show_suggested_questions": True,
        "tone_of_voice": "Professional",
        "custom_greetings": "",
        "primary_color": "#3B82F6",
        "confidence_threshold": 0.7,
    }


def get_settings():
    settings = settings_collection.find_one({}, {"_id": 0})
    if not settings:
        settings = get_default_settings()
    return jsonify(settings)


def update_settings(data=None):
    payload = data if data is not None else request.json or {}
    if not isinstance(payload, dict):
        return jsonify({"success": False, "message": "Invalid payload."}), 400

    # Coerce and sanitize fields
    sanitized = {}
    if "bot_name" in payload:
        sanitized["bot_name"] = str(payload.get("bot_name") or "").strip()
    if "bot_avatar" in payload:
        sanitized["bot_avatar"] = str(payload.get("bot_avatar") or "").strip()
    if "welcome_message" in payload:
        sanitized["welcome_message"] = str(payload.get("welcome_message") or "")
    if "office_specific_messages" in payload and isinstance(payload.get("office_specific_messages"), dict):
        sanitized["office_specific_messages"] = payload.get("office_specific_messages")
    if "suggested_messages" in payload and isinstance(payload.get("suggested_messages"), list):
        sanitized["suggested_messages"] = payload.get("suggested_messages")
    if "response_timeout" in payload:
        try:
            sanitized["response_timeout"] = int(payload.get("response_timeout"))
        except Exception:
            pass
    if "show_typing_indicator" in payload:
        sanitized["show_typing_indicator"] = bool(payload.get("show_typing_indicator"))
    if "show_suggested_questions" in payload:
        sanitized["show_suggested_questions"] = bool(payload.get("show_suggested_questions"))
    if "tone_of_voice" in payload:
        sanitized["tone_of_voice"] = str(payload.get("tone_of_voice") or "").strip()
    if "custom_greetings" in payload:
        sanitized["custom_greetings"] = str(payload.get("custom_greetings") or "")
    if "primary_color" in payload:
        sanitized["primary_color"] = str(payload.get("primary_color") or "").strip()
    if "confidence_threshold" in payload:
        try:
            # Accept either 0-1 float or 0-100 number
            ct = float(payload.get("confidence_threshold"))
            if ct > 1:
                ct = ct / 100.0
            sanitized["confidence_threshold"] = max(0.0, min(1.0, ct))
        except Exception:
            pass

    if not sanitized:
        return jsonify({"success": False, "message": "No valid fields to update."}), 400

    settings_collection.update_one({}, {"$set": sanitized}, upsert=True)
    return jsonify({"success": True, "message": "Settings updated successfully."})


def reset_settings():
    default = get_default_settings()
    settings_collection.replace_one({}, default, upsert=True)
    return jsonify({"success": True, "message": "Settings reset to default."})


