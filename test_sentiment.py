"""
Test script for sentiment analysis in feedback system
Demonstrates how VADER sentiment analysis works on different types of comments
"""

from feedback import analyze_sentiment

def test_sentiment_analysis():
    """Test sentiment analysis with various examples"""
    
    print("=" * 80)
    print("SENTIMENT ANALYSIS TESTING")
    print("=" * 80)
    print()
    
    # Test cases with different ratings and comments
    test_cases = [
        # Positive comments
        {
            "rating": 5,
            "comment": "Excellent service! Very helpful and quick responses. I love this chatbot!",
            "expected": "positive"
        },
        {
            "rating": 4,
            "comment": "Great experience, the assistant was very knowledgeable and friendly.",
            "expected": "positive"
        },
        {
            "rating": 5,
            "comment": "Amazing! Solved my problem in minutes. Highly recommend!",
            "expected": "positive"
        },
        
        # Negative comments
        {
            "rating": 1,
            "comment": "Terrible experience. The bot was slow and unhelpful. Very disappointing.",
            "expected": "negative"
        },
        {
            "rating": 2,
            "comment": "Poor service. Couldn't understand my questions and gave wrong answers.",
            "expected": "negative"
        },
        {
            "rating": 1,
            "comment": "Awful! Waste of time. This chatbot is useless and frustrating.",
            "expected": "negative"
        },
        
        # Neutral comments
        {
            "rating": 3,
            "comment": "It's okay. Got some answers but could be better.",
            "expected": "neutral"
        },
        {
            "rating": 3,
            "comment": "Average service. Nothing special but it works.",
            "expected": "neutral"
        },
        
        # Mixed sentiment - comment contradicts rating
        {
            "rating": 5,
            "comment": "The interface is confusing and it was difficult to get help.",
            "expected": "negative"  # Strong negative comment should override high rating
        },
        {
            "rating": 1,
            "comment": "Actually, after some time, I found it really helpful and easy to use!",
            "expected": "positive"  # Strong positive comment should override low rating
        },
        
        # No comment - rating only
        {
            "rating": 5,
            "comment": None,
            "expected": "positive"
        },
        {
            "rating": 1,
            "comment": None,
            "expected": "negative"
        },
        
        # Sarcasm and complex sentiment
        {
            "rating": 2,
            "comment": "Yeah, great job keeping me waiting for 10 minutes...",
            "expected": "negative"
        },
    ]
    
    correct_predictions = 0
    total_tests = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        rating = test["rating"]
        comment = test["comment"]
        expected = test["expected"]
        
        # Analyze sentiment
        sentiment, scores = analyze_sentiment(rating, comment)
        
        # Check if prediction matches expected
        is_correct = sentiment == expected
        correct_predictions += is_correct
        
        # Display results
        print(f"Test {i}:")
        print(f"  Rating: {rating} stars")
        print(f"  Comment: {comment if comment else '(No comment)'}")
        print(f"  Expected: {expected}")
        print(f"  Detected: {sentiment} {'✓' if is_correct else '✗'}")
        
        if comment:
            print(f"  VADER Scores:")
            print(f"    - Compound: {scores['compound']:.3f} (Overall sentiment)")
            print(f"    - Positive: {scores['pos']:.3f}")
            print(f"    - Neutral:  {scores['neu']:.3f}")
            print(f"    - Negative: {scores['neg']:.3f}")
        
        print()
    
    # Summary
    print("=" * 80)
    print(f"RESULTS: {correct_predictions}/{total_tests} correct predictions ({(correct_predictions/total_tests)*100:.1f}%)")
    print("=" * 80)
    print()
    
    # Explain VADER scores
    print("UNDERSTANDING VADER SCORES:")
    print("-" * 80)
    print("• Compound Score: Overall sentiment from -1 (most negative) to +1 (most positive)")
    print("  - Positive: >= 0.05")
    print("  - Neutral:  -0.05 to 0.05")
    print("  - Negative: <= -0.05")
    print()
    print("• Positive/Neutral/Negative: Proportion of text with each sentiment (0 to 1)")
    print()
    print("The system uses both rating and comment text to determine final sentiment,")
    print("with strong comment sentiment (|compound| > 0.5) able to override the rating.")
    print("=" * 80)

if __name__ == "__main__":
    test_sentiment_analysis()

