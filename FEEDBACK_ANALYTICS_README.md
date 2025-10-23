# Sub-Admin Feedback Analytics System

## Overview

The Sub-Admin Feedback Analytics system provides comprehensive feedback statistics and insights for the EduChat portal. Sub-admins can view global feedback metrics, analyze sentiment, and monitor recent reviews across all offices.

## Features

✅ **Average Rating** - Calculated as: `Sum of All Ratings / Number of Ratings`  
✅ **Total Reviews** - Total number of feedback submissions collected  
✅ **Positive Feedback %** - `(Positive Reviews / Total Reviews) × 100` (4-5 stars)  
✅ **Negative Feedback %** - `(Negative Reviews / Total Reviews) × 100` (1-2 stars)  
✅ **Neutral Feedback %** - `(Neutral Reviews / Total Reviews) × 100` (3 stars)  
✅ **Recent Feedback** - Last 10-20 reviews shown chronologically  
✅ **Time Filters** - Filter by last N hours/days/weeks  
✅ **Rating Filters** - Filter feedback by star rating (1-5)  
✅ **Search Functionality** - Search through feedback comments  
✅ **Sentiment Analysis** - Automatic sentiment classification (positive, neutral, negative)

---

## MongoDB Schema

### Feedback Collection

Collection name: `feedback`

```javascript
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "rating": 5,                              // Integer: 1-5 star rating
  "comment": "Great chatbot! Very helpful", // String: Optional user comment
  "user_id": "user_12345",                  // String: Optional user identifier
  "session_id": "session_abc123",           // String: Optional session identifier
  "sentiment": "positive",                  // String: 'positive', 'neutral', 'negative'
  "timestamp": ISODate("2025-10-01T10:30:00Z"),  // DateTime: When feedback was submitted
  "created_at": ISODate("2025-10-01T10:30:00Z")  // DateTime: Record creation time
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `_id` | ObjectId | Yes | Unique MongoDB identifier |
| `rating` | Integer | Yes | Star rating from 1 to 5 |
| `comment` | String | No | User's text feedback/comment |
| `user_id` | String | No | Identifier for the user who submitted feedback |
| `session_id` | String | No | Session identifier for the feedback submission |
| `sentiment` | String | Yes | Auto-generated sentiment: 'positive', 'neutral', or 'negative' |
| `timestamp` | DateTime | Yes | When the feedback was submitted (UTC) |
| `created_at` | DateTime | Yes | Record creation timestamp (UTC) |

---

## Sample Data

### Example 1: Positive Feedback

```json
{
  "_id": "507f1f77bcf86cd799439011",
  "rating": 5,
  "comment": "Excellent service! The chatbot answered all my questions quickly.",
  "user_id": "student_2024_001",
  "session_id": "sess_20250101_123456",
  "sentiment": "positive",
  "timestamp": "2025-10-01T10:30:00.000Z",
  "created_at": "2025-10-01T10:30:00.000Z"
}
```

### Example 2: Neutral Feedback

```json
{
  "_id": "507f1f77bcf86cd799439012",
  "rating": 3,
  "comment": "It works okay, but could be more detailed in some areas.",
  "user_id": "student_2024_002",
  "session_id": "sess_20250101_234567",
  "sentiment": "neutral",
  "timestamp": "2025-10-01T11:45:00.000Z",
  "created_at": "2025-10-01T11:45:00.000Z"
}
```

### Example 3: Negative Feedback

```json
{
  "_id": "507f1f77bcf86cd799439013",
  "rating": 2,
  "comment": "The bot didn't understand my question and gave irrelevant answers.",
  "user_id": "student_2024_003",
  "session_id": "sess_20250101_345678",
  "sentiment": "negative",
  "timestamp": "2025-10-01T14:20:00.000Z",
  "created_at": "2025-10-01T14:20:00.000Z"
}
```

### Example 4: Feedback Without Comment

```json
{
  "_id": "507f1f77bcf86cd799439014",
  "rating": 4,
  "comment": null,
  "user_id": "anonymous_user",
  "session_id": "sess_20250101_456789",
  "sentiment": "positive",
  "timestamp": "2025-10-01T16:10:00.000Z",
  "created_at": "2025-10-01T16:10:00.000Z"
}
```

---

## File Structure

```
chatbot-deployment/
├── sub_feedback.py                        # Flask Blueprint for feedback analytics
├── feedback.py                            # Core feedback functions with sentiment analysis
├── app.py                                 # Main Flask app (registers sub_feedback_bp)
├── templates/
│   └── Sub-feedback.html                  # Frontend UI template
└── static/
    └── Sub-assets/
        └── js/
            └── modules/
                └── FeedbackManager.js     # JavaScript module for data fetching/rendering
```

---

## API Endpoints

### 1. Get Feedback Statistics

**Endpoint:** `/api/sub-admin/feedback/stats`  
**Method:** `GET`  
**Authentication:** Required (Sub-Admin session)

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `time_filter` | String | No | Filter type: 'hours', 'days', or 'weeks' |
| `time_value` | Integer | No | Number of hours/days/weeks to filter |

#### Example Request

```bash
GET /api/sub-admin/feedback/stats?time_filter=days&time_value=7
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "average_rating": 4.2,
    "total_reviews": 1248,
    "positive_count": 1024,
    "negative_count": 112,
    "neutral_count": 112,
    "positive_percentage": 82.1,
    "negative_percentage": 9.0,
    "neutral_percentage": 9.0,
    "rating_distribution": {
      "1_star": 45,
      "2_star": 67,
      "3_star": 112,
      "4_star": 456,
      "5_star": 568
    }
  }
}
```

---

### 2. Get Recent Feedback

**Endpoint:** `/api/sub-admin/feedback/recent`  
**Method:** `GET`  
**Authentication:** Required (Sub-Admin session)

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | Integer | No | Max number of results (default: 20, max: 50) |
| `rating` | Integer | No | Filter by specific rating (1-5) |
| `time_filter` | String | No | Filter type: 'hours', 'days', or 'weeks' |
| `time_value` | Integer | No | Number of hours/days/weeks to filter |
| `search` | String | No | Search term to filter comments |

#### Example Request

```bash
GET /api/sub-admin/feedback/recent?limit=10&rating=5&time_filter=days&time_value=7
```

#### Example Response

```json
{
  "success": true,
  "count": 10,
  "data": [
    {
      "_id": "507f1f77bcf86cd799439011",
      "rating": 5,
      "comment": "Excellent service!",
      "user_id": "student_2024_001",
      "session_id": "sess_20250101_123456",
      "sentiment": "positive",
      "timestamp": "2025-10-01T10:30:00.000Z",
      "created_at": "2025-10-01T10:30:00.000Z"
    }
    // ... more feedback items
  ]
}
```

---

## Frontend Implementation

### JavaScript Functions

```javascript
// Initialize the feedback manager
window.feedbackManager = new FeedbackManager();
window.feedbackManager.initialize();

// Load feedback statistics
await feedbackManager.loadFeedbackStats();

// Load recent feedback
await feedbackManager.loadRecentFeedback(20);

// Filter by rating
feedbackManager.filterByRating(5);

// Clear filters
feedbackManager.clearFilters();

// Search feedback
feedbackManager.searchFeedback("excellent");

// Set time filter
feedbackManager.setTimeFilter('days', 7);

// Clear time filter
feedbackManager.clearTimeFilter();
```

---

## Sentiment Analysis

The system automatically classifies feedback sentiment based on:

1. **Rating-based Classification:**
   - ⭐⭐⭐⭐⭐ or ⭐⭐⭐⭐ (4-5 stars) → **Positive**
   - ⭐⭐⭐ (3 stars) → **Neutral**
   - ⭐⭐ or ⭐ (1-2 stars) → **Negative**

2. **Comment-based Enhancement:**
   - Positive keywords: good, great, excellent, amazing, helpful, love, perfect
   - Negative keywords: bad, poor, terrible, awful, hate, useless, worst
   - Sentiment adjusted if strong keyword presence detected

---

## UI Components

### KPI Cards

1. **Average Rating Card** - Displays average rating with star icon
2. **Total Reviews Card** - Shows total number of feedback submissions
3. **Positive Feedback Card** - Percentage of positive reviews (green)
4. **Negative Feedback Card** - Percentage of negative reviews (red)

### Time Filter Section

- Dropdown to select time period (hours/days/weeks)
- Input field for time value
- Apply and Clear buttons
- Refresh button to reload data

### Recent Feedback Section

- Star rating filter buttons (1★ to 5★)
- Search functionality
- Feedback cards with:
  - Star rating display
  - Timestamp (relative or absolute)
  - Sentiment badge (colored)
  - Comment text
  - User ID (if available)

---

## Formulas

### Average Rating
```
Average Rating = Sum of All Ratings / Number of Ratings
```

### Total Reviews
```
Total Reviews = Number of Feedback Submissions Collected
```

### Positive Feedback Percentage
```
Positive Feedback % = (Positive Reviews / Total Reviews) × 100
where Positive Reviews = Ratings ≥ 4
```

### Negative Feedback Percentage
```
Negative Feedback % = (Negative Reviews / Total Reviews) × 100
where Negative Reviews = Ratings ≤ 2
```

### Neutral Feedback Percentage
```
Neutral Feedback % = (Neutral Reviews / Total Reviews) × 100
where Neutral Reviews = Rating = 3
```

---

## Security

- All endpoints require Sub-Admin authentication
- Session-based authentication using Flask sessions
- CORS enabled for cross-origin requests
- XSS protection with HTML escaping in frontend

---

## Testing

### Insert Sample Feedback (MongoDB Shell)

```javascript
db.feedback.insertMany([
  {
    rating: 5,
    comment: "Amazing chatbot! Very helpful and quick responses.",
    user_id: "test_user_001",
    session_id: "test_session_001",
    sentiment: "positive",
    timestamp: new Date(),
    created_at: new Date()
  },
  {
    rating: 4,
    comment: "Good experience overall, minor improvements needed.",
    user_id: "test_user_002",
    session_id: "test_session_002",
    sentiment: "positive",
    timestamp: new Date(),
    created_at: new Date()
  },
  {
    rating: 3,
    comment: "It works but could be better.",
    user_id: "test_user_003",
    session_id: "test_session_003",
    sentiment: "neutral",
    timestamp: new Date(),
    created_at: new Date()
  },
  {
    rating: 2,
    comment: "Not very helpful, needs improvement.",
    user_id: "test_user_004",
    session_id: "test_session_004",
    sentiment: "negative",
    timestamp: new Date(),
    created_at: new Date()
  },
  {
    rating: 1,
    comment: "Terrible experience, bot didn't understand anything.",
    user_id: "test_user_005",
    session_id: "test_session_005",
    sentiment: "negative",
    timestamp: new Date(),
    created_at: new Date()
  }
]);
```

---

## Troubleshooting

### Common Issues

1. **"Not authenticated" error**
   - Ensure Sub-Admin is logged in
   - Check Flask session is active
   - Verify `role` and `office` in session

2. **No feedback displayed**
   - Check MongoDB connection
   - Verify feedback collection has data
   - Check browser console for JavaScript errors

3. **Time filter not working**
   - Ensure both time type and value are selected
   - Check timestamp field exists in MongoDB documents
   - Verify date format is correct (ISODate)

---

## Future Enhancements

- [ ] Advanced NLP-based sentiment analysis
- [ ] Export feedback data to CSV/Excel
- [ ] Email notifications for negative feedback
- [ ] Feedback response/reply system
- [ ] Feedback trends over time (charts/graphs)
- [ ] Office-specific feedback filtering
- [ ] Multi-language sentiment support

---

## Authors

EduChat Development Team

## License

Proprietary - All rights reserved

