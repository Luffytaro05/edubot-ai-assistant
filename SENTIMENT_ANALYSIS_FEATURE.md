# Enhanced Sentiment Analysis for Feedback System

## Overview

The feedback system now includes **advanced sentiment analysis** using VADER (Valence Aware Dictionary and sEntiment Reasoner) to automatically detect whether user feedback comments are **positive**, **negative**, or **neutral**.

## How It Works

### 1. **VADER Sentiment Analysis**

VADER is a specialized sentiment analysis tool designed for social media and short texts. It provides:

- **Compound Score**: Overall sentiment from -1 (most negative) to +1 (most positive)
- **Positive Score**: Proportion of text that is positive (0 to 1)
- **Neutral Score**: Proportion of text that is neutral (0 to 1)
- **Negative Score**: Proportion of text that is negative (0 to 1)

### 2. **Sentiment Classification**

The system uses a sophisticated approach combining both star ratings and comment text:

#### Rating-Based Baseline:
- ⭐⭐⭐⭐⭐ or ⭐⭐⭐⭐ (4-5 stars) → **Positive**
- ⭐⭐⭐ (3 stars) → **Neutral**
- ⭐⭐ or ⭐ (1-2 stars) → **Negative**

#### Comment-Based Override:
If a comment is provided, VADER analyzes the text and can override the rating-based sentiment:

- **Strong sentiment** (|compound| > 0.5): Comment sentiment completely overrides rating
- **Moderate sentiment** (|compound| > 0.3): Comment sentiment overrides if different from rating
- **Weak sentiment** (|compound| ≤ 0.3): Rating-based sentiment is maintained

### 3. **Examples**

#### Example 1: Positive Comment
```
Rating: 5 stars
Comment: "Excellent service! Very helpful and quick responses."
VADER Scores: {compound: 0.836, pos: 0.567, neu: 0.433, neg: 0.0}
→ Detected: POSITIVE ✓
```

#### Example 2: Negative Comment Overriding High Rating
```
Rating: 5 stars
Comment: "The interface is confusing and difficult to use."
VADER Scores: {compound: -0.612, pos: 0.0, neu: 0.558, neg: 0.442}
→ Detected: NEGATIVE (overrides rating)
```

#### Example 3: Neutral Comment
```
Rating: 3 stars
Comment: "It's okay. Got some answers but could be better."
VADER Scores: {compound: 0.128, pos: 0.214, neu: 0.786, neg: 0.0}
→ Detected: NEUTRAL ✓
```

## Features

### 1. **Automatic Analysis**
- Every feedback submission is automatically analyzed
- Sentiment is stored in the database with detailed scores

### 2. **Enhanced Keywords**
Fallback keyword-based analysis includes:

**Positive keywords**: good, great, excellent, amazing, helpful, love, perfect, wonderful, awesome, fantastic, outstanding, superb, brilliant, satisfied, happy, pleased, delighted, impressed

**Negative keywords**: bad, poor, terrible, awful, hate, useless, worst, horrible, disappointing, frustrated, angry, confused, dissatisfied, unhappy, unpleasant, difficult, slow

### 3. **Database Storage**
Each feedback entry now includes:
```json
{
  "rating": 5,
  "comment": "Great service!",
  "sentiment": "positive",
  "sentiment_scores": {
    "compound": 0.7096,
    "pos": 0.618,
    "neu": 0.382,
    "neg": 0.0
  },
  "timestamp": "2025-10-21T10:30:00",
  "user_id": "user123",
  "session_id": "session_abc"
}
```

### 4. **Re-analysis Function**
Can re-analyze existing feedback with the enhanced algorithm:

```python
from feedback import reanalyze_feedback

# Re-analyze all feedback
result = reanalyze_feedback()

# Re-analyze specific feedback
result = reanalyze_feedback(feedback_id="507f1f77bcf86cd799439011")
```

## Technical Implementation

### Files Modified:

1. **feedback.py**
   - Added VADER sentiment analyzer
   - Enhanced `analyze_sentiment()` function
   - Updated `save_feedback()` to store sentiment scores
   - Added `reanalyze_feedback()` helper function

2. **requirements.txt**
   - Added `nltk==3.8.1` for VADER support

### API Response:

The `/api/feedback` endpoint now returns:
```json
{
  "success": true,
  "message": "Feedback saved successfully",
  "feedback_id": "507f1f77bcf86cd799439011",
  "sentiment": "positive",
  "sentiment_scores": {
    "compound": 0.7096,
    "pos": 0.618,
    "neu": 0.382,
    "neg": 0.0
  }
}
```

## Testing

Run the test script to see sentiment analysis in action:

```bash
python test_sentiment.py
```

This will test various scenarios including:
- Positive, negative, and neutral comments
- Comments that override ratings
- Sarcasm detection
- Rating-only feedback

## Benefits

1. **Accurate Sentiment Detection**: VADER is specifically designed for social media and informal text
2. **Context Awareness**: Can detect sentiment even with emojis, slang, and informal language
3. **Override Capability**: Prevents misclassification when rating and comment sentiment differ
4. **Detailed Insights**: Provides granular sentiment scores for advanced analytics
5. **Multilingual Support**: Works with various languages (though optimized for English)

## Dashboard Integration

The admin feedback dashboard displays:
- Sentiment badges (green for positive, red for negative, gray for neutral)
- Filter by sentiment type
- Sentiment statistics and trends
- Detailed sentiment scores on hover/expand

## Future Enhancements

Potential improvements:
- Emotion detection (happy, angry, frustrated, satisfied)
- Topic extraction (what specific features are mentioned)
- Trend analysis over time
- Multilingual sentiment analysis for Filipino comments
- Integration with customer support ticketing

## Support

For questions or issues with sentiment analysis:
1. Check the test script output for examples
2. Review VADER documentation: https://github.com/cjhutto/vaderSentiment
3. Examine sentiment scores in the database for specific feedback
4. Use the `reanalyze_feedback()` function to update existing data

---

**Last Updated**: October 21, 2025  
**Version**: 1.0  
**Author**: Chatbot Development Team

