import json
import os
from datetime import datetime
from pymongo import MongoClient
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

# Download VADER lexicon for sentiment analysis
try:
    nltk.download('vader_lexicon', quiet=True)
except:
    pass

# Initialize VADER sentiment analyzer
try:
    sia = SentimentIntensityAnalyzer()
except LookupError:
    nltk.download('vader_lexicon', quiet=True)
    sia = SentimentIntensityAnalyzer()

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
feedback_collection = db["feedback"]

def analyze_sentiment(rating, comment=None):
    """
    Analyze sentiment based on rating and optional comment text using VADER sentiment analysis
    
    Args:
        rating (int): Star rating from 1-5
        comment (str, optional): User's text feedback
    
    Returns:
        str: Sentiment classification ('positive', 'neutral', 'negative')
        dict: Sentiment scores (compound, positive, negative, neutral)
    """
    # Basic sentiment determination based on rating
    if rating >= 4:
        sentiment = "positive"
    elif rating == 3:
        sentiment = "neutral"
    else:
        sentiment = "negative"
    
    # Initialize sentiment scores
    sentiment_scores = {
        'compound': 0.0,
        'pos': 0.0,
        'neu': 0.0,
        'neg': 0.0
    }
    
    # If comment is provided, use VADER for sophisticated text analysis
    if comment and comment.strip():
        try:
            # Get VADER sentiment scores
            scores = sia.polarity_scores(comment)
            sentiment_scores = scores
            
            # VADER compound score ranges from -1 (most negative) to +1 (most positive)
            # Compound score thresholds:
            # positive: >= 0.05
            # neutral: between -0.05 and 0.05
            # negative: <= -0.05
            compound_score = scores['compound']
            
            # Determine sentiment from comment
            if compound_score >= 0.05:
                comment_sentiment = "positive"
            elif compound_score <= -0.05:
                comment_sentiment = "negative"
            else:
                comment_sentiment = "neutral"
            
            # If comment sentiment is strong (compound > 0.5 or < -0.5), 
            # it can override the rating-based sentiment
            if abs(compound_score) > 0.5:
                sentiment = comment_sentiment
            # For moderate sentiment, use a weighted approach
            elif abs(compound_score) > 0.2:
                # If comment sentiment differs significantly from rating sentiment
                if comment_sentiment != sentiment:
                    # Use comment sentiment if it's strong enough
                    if abs(compound_score) > 0.3:
                        sentiment = comment_sentiment
        except Exception as e:
            print(f"Error in VADER sentiment analysis: {e}")
            # Fallback to simple keyword-based analysis
            positive_keywords = ['good', 'great', 'excellent', 'amazing', 'helpful', 'love', 'perfect', 
                               'wonderful', 'awesome', 'fantastic', 'outstanding', 'superb', 'brilliant',
                               'satisfied', 'happy', 'pleased', 'delighted', 'impressed']
            negative_keywords = ['bad', 'poor', 'terrible', 'awful', 'hate', 'useless', 'worst',
                               'horrible', 'disappointing', 'frustrated', 'angry', 'confused',
                               'dissatisfied', 'unhappy', 'unpleasant', 'difficult', 'slow']
            
            comment_lower = comment.lower()
            
            positive_count = sum(1 for word in positive_keywords if word in comment_lower)
            negative_count = sum(1 for word in negative_keywords if word in comment_lower)
            
            # Adjust sentiment if comment strongly indicates different sentiment
            if positive_count > negative_count and positive_count >= 2:
                sentiment = "positive"
            elif negative_count > positive_count and negative_count >= 2:
                sentiment = "negative"
    
    return sentiment, sentiment_scores

def save_feedback(rating, comment=None, user_id=None, session_id=None):
    """
    Save user feedback to database with enhanced sentiment analysis
    
    Args:
        rating (int): Star rating from 1-5
        comment (str, optional): User's text feedback
        user_id (str, optional): User identifier
        session_id (str, optional): Session identifier
    
    Returns:
        dict: Result with success status and message
    """
    try:
        # Validate rating
        if not isinstance(rating, int) or rating < 1 or rating > 5:
            return {
                "success": False,
                "message": "Rating must be an integer between 1 and 5"
            }
        
        # Analyze sentiment using VADER
        sentiment, sentiment_scores = analyze_sentiment(rating, comment)
        
        # Prepare feedback document
        feedback_data = {
            "rating": rating,
            "comment": comment.strip() if comment else None,
            "user_id": user_id,
            "session_id": session_id,
            "sentiment": sentiment,
            "sentiment_scores": sentiment_scores,  # Store detailed sentiment scores
            "timestamp": datetime.today(),
            "created_at": datetime.today()
        }
        
        # Save to MongoDB
        result = feedback_collection.insert_one(feedback_data)
        
        if result.inserted_id:
            return {
                "success": True,
                "message": "Feedback saved successfully",
                "feedback_id": str(result.inserted_id),
                "sentiment": sentiment,
                "sentiment_scores": sentiment_scores
            }
        else:
            return {
                "success": False,
                "message": "Failed to save feedback"
            }
            
    except Exception as e:
        print(f"Error saving feedback: {e}")
        return {
            "success": False,
            "message": f"Error saving feedback: {str(e)}"
        }

def get_feedback_stats():
    """
    Get feedback statistics for dashboard
    
    Returns:
        dict: Feedback statistics
    """
    try:
        # Test database connection first
        feedback_collection.find_one()
        
        # Get total feedback count
        total_feedback = feedback_collection.count_documents({})
        
        # Get average rating
        pipeline = [
            {"$group": {"_id": None, "avg_rating": {"$avg": "$rating"}}}
        ]
        avg_result = list(feedback_collection.aggregate(pipeline))
        avg_rating = avg_result[0]["avg_rating"] if avg_result and avg_result[0].get("avg_rating") is not None else 0
        
        # Get rating distribution
        rating_dist = {}
        for i in range(1, 6):
            count = feedback_collection.count_documents({"rating": i})
            rating_dist[f"{i}_star"] = count
        
        # Get recent feedback
        recent_feedback = list(feedback_collection.find({}).sort("timestamp", -1).limit(10))
        
        return {
            "total_feedback": total_feedback,
            "average_rating": round(avg_rating, 2) if avg_rating else 0,
            "rating_distribution": rating_dist,
            "recent_feedback": recent_feedback
        }
        
    except Exception as e:
        print(f"Error getting feedback stats: {e}")
        import traceback
        print(traceback.format_exc())
        return {
            "total_feedback": 0,
            "average_rating": 0,
            "rating_distribution": {},
            "recent_feedback": []
        }

def get_feedback_by_rating(rating):
    """
    Get feedback by specific rating
    
    Args:
        rating (int): Rating to filter by (1-5)
    
    Returns:
        list: List of feedback documents
    """
    try:
        feedback = list(feedback_collection.find({"rating": rating}).sort("timestamp", -1))
        return feedback
    except Exception as e:
        print(f"Error getting feedback by rating: {e}")
        return []

def get_recent_feedback(limit=20):
    """
    Get recent feedback
    
    Args:
        limit (int): Maximum number of feedback items to return
    
    Returns:
        list: List of recent feedback documents
    """
    try:
        feedback = list(feedback_collection.find({}).sort("timestamp", -1).limit(limit))
        return feedback
    except Exception as e:
        print(f"Error getting recent feedback: {e}")
        return []

def get_shared_feedback_analytics(query=None):
    """
    Shared function to get feedback analytics with consistent calculation
    This ensures both main feedback and sub-feedback pages show the same data
    
    Args:
        query (dict, optional): MongoDB query filter
    
    Returns:
        dict: Analytics data with consistent calculation
    """
    try:
        if query is None:
            query = {}
            
        # Get all feedback data
        all_feedback = list(feedback_collection.find(query))
        
        if not all_feedback:
            return {
                "average_rating": 0,
                "total_reviews": 0,
                "positive_count": 0,
                "negative_count": 0,
                "neutral_count": 0,
                "positive_percentage": 0.0,
                "negative_percentage": 0.0,
                "neutral_percentage": 0.0
            }
        
        # Calculate metrics
        total_reviews = len(all_feedback)
        ratings = [f["rating"] for f in all_feedback if "rating" in f]
        average_rating = sum(ratings) / len(ratings) if ratings else 0
        
        # Calculate sentiment-based percentages (consistent with sub-feedback page)
        positive_count = sum(1 for f in all_feedback if f.get("sentiment") == "positive")
        negative_count = sum(1 for f in all_feedback if f.get("sentiment") == "negative")
        neutral_count = sum(1 for f in all_feedback if f.get("sentiment") == "neutral")
        
        # If no sentiment data exists, calculate and store sentiment
        if positive_count == 0 and negative_count == 0 and neutral_count == 0:
            for feedback in all_feedback:
                if "sentiment" not in feedback:
                    sentiment = analyze_sentiment(feedback.get("rating", 3), feedback.get("comment"))[0]
                    feedback_collection.update_one(
                        {"_id": feedback["_id"]},
                        {"$set": {"sentiment": sentiment}}
                    )
                    # Recalculate counts
                    if sentiment == "positive":
                        positive_count += 1
                    elif sentiment == "negative":
                        negative_count += 1
                    else:
                        neutral_count += 1
        
        # Calculate percentages
        positive_percentage = round((positive_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0
        negative_percentage = round((negative_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0
        neutral_percentage = round((neutral_count / total_reviews) * 100, 1) if total_reviews > 0 else 0.0
        
        return {
            "average_rating": round(average_rating, 2),
            "total_reviews": total_reviews,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": positive_percentage,
            "negative_percentage": negative_percentage,
            "neutral_percentage": neutral_percentage
        }
        
    except Exception as e:
        print(f"Error in get_shared_feedback_analytics: {e}")
        return {
            "average_rating": 0,
            "total_reviews": 0,
            "positive_count": 0,
            "negative_count": 0,
            "neutral_count": 0,
            "positive_percentage": 0.0,
            "negative_percentage": 0.0,
            "neutral_percentage": 0.0
        }

def get_feedback_analytics():
    """
    Get comprehensive feedback analytics for admin dashboard
    
    Returns:
        dict: Complete analytics data including KPIs and detailed feedback
    """
    try:
        # Use shared analytics function for consistent calculation
        analytics_data = get_shared_feedback_analytics({})
        
        # Get all feedback data for detailed table
        all_feedback = list(feedback_collection.find({}).sort("timestamp", -1))
        
        if not all_feedback:
            return {
                "success": True,
                "analytics": {
                    "average_rating": 0,
                    "total_feedback": 0,
                    "positive_feedback_percentage": 0,
                    "negative_feedback_percentage": 0,
                    "feedback_data": []
                }
            }
        
        # Extract values from shared analytics
        total_feedback = analytics_data["total_reviews"]
        average_rating = analytics_data["average_rating"]
        positive_count = analytics_data["positive_count"]
        negative_count = analytics_data["negative_count"]
        neutral_count = analytics_data["neutral_count"]
        positive_percentage = analytics_data["positive_percentage"]
        negative_percentage = analytics_data["negative_percentage"]
        
        # Prepare feedback data for table
        feedback_data = []
        for feedback in all_feedback:
            sentiment_scores = feedback.get("sentiment_scores", {
                'compound': 0.0,
                'pos': 0.0,
                'neu': 0.0,
                'neg': 0.0
            })
            feedback_data.append({
                "id": str(feedback["_id"]),
                "rating": feedback["rating"],
                "message": feedback.get("comment", ""),
                "sentiment": feedback.get("sentiment", "neutral"),
                "sentiment_scores": sentiment_scores,
                "date": feedback["timestamp"].isoformat() if feedback.get("timestamp") else None,
                "user_id": feedback.get("user_id"),
                "session_id": feedback.get("session_id")
            })
        
        return {
            "success": True,
            "analytics": {
                "average_rating": round(average_rating, 2),
                "total_feedback": total_feedback,
                "positive_feedback_percentage": round(positive_percentage, 2),
                "negative_feedback_percentage": round(negative_percentage, 2),
                "neutral_feedback_percentage": round((neutral_count / total_feedback) * 100, 2) if total_feedback > 0 else 0,
                "positive_count": positive_count,
                "negative_count": negative_count,
                "neutral_count": neutral_count,
                "feedback_data": feedback_data
            }
        }
        
    except Exception as e:
        print(f"Error getting feedback analytics: {e}")
        return {
            "success": False,
            "message": f"Error getting feedback analytics: {str(e)}",
            "analytics": {
                "average_rating": 0,
                "total_feedback": 0,
                "positive_feedback_percentage": 0,
                "negative_feedback_percentage": 0,
                "feedback_data": []
            }
        }

def get_feedback_by_sentiment(sentiment):
    """
    Get feedback filtered by sentiment
    
    Args:
        sentiment (str): Sentiment to filter by ('positive', 'negative', 'neutral')
    
    Returns:
        list: List of feedback documents with specified sentiment
    """
    try:
        feedback = list(feedback_collection.find({"sentiment": sentiment}).sort("timestamp", -1))
        return feedback
    except Exception as e:
        print(f"Error getting feedback by sentiment: {e}")
        return []

def reanalyze_feedback(feedback_id=None):
    """
    Re-analyze sentiment for existing feedback using the enhanced VADER analysis
    
    Args:
        feedback_id (str, optional): Specific feedback ID to re-analyze. If None, re-analyzes all.
    
    Returns:
        dict: Result with count of updated feedback
    """
    try:
        from bson import ObjectId
        
        # Get feedback to re-analyze
        if feedback_id:
            query = {"_id": ObjectId(feedback_id)}
        else:
            query = {}
        
        feedback_list = list(feedback_collection.find(query))
        updated_count = 0
        
        for fb in feedback_list:
            rating = fb.get("rating")
            comment = fb.get("comment")
            
            # Re-analyze sentiment
            sentiment, sentiment_scores = analyze_sentiment(rating, comment)
            
            # Update in database
            feedback_collection.update_one(
                {"_id": fb["_id"]},
                {
                    "$set": {
                        "sentiment": sentiment,
                        "sentiment_scores": sentiment_scores
                    }
                }
            )
            updated_count += 1
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Successfully re-analyzed {updated_count} feedback entries"
        }
        
    except Exception as e:
        print(f"Error re-analyzing feedback: {e}")
        return {
            "success": False,
            "message": f"Error re-analyzing feedback: {str(e)}"
        }