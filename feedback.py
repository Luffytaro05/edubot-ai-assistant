# feedback.py

from pymongo import MongoClient
from datetime import datetime
from textblob import TextBlob

class FeedbackSystem:
    def __init__(self, mongo_uri="mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/", db_name="chatbot_db"):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]
        self.collection = self.db['feedbacks']

    def analyze_sentiment(self, feedback_text):
        blob = TextBlob(feedback_text)
        polarity = blob.sentiment.polarity

        appreciation_keywords = ['thank', 'thanks', 'appreciate', 'great', 'excellent', 'love', 'awesome', 'helpful', 'satisfied']
        for word in appreciation_keywords:
            if word in feedback_text.lower():
                polarity += 0.1

        polarity = max(min(polarity, 1.0), -1.0)

        if polarity > 0.6:
            return 5
        elif polarity > 0.2:
            return 4
        elif polarity >= -0.2:
            return 3
        elif polarity >= -0.6:
            return 2
        else:
            return 1

    def add_feedback(self, feedback_text):
        star_rating = self.analyze_sentiment(feedback_text)
        feedback_entry = {
            "feedback": feedback_text,
            "star_rating": star_rating,
            "created_at": datetime.utcnow()
        }
        result = self.collection.insert_one(feedback_entry)
        return result.inserted_id, star_rating

    def get_all_feedbacks(self):
        return list(self.collection.find().sort("created_at", -1))
