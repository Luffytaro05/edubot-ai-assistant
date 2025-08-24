import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer
import string

# Initialize stemmer
stemmer = PorterStemmer()

# Ensure tokenizer data is available
nltk.download('punkt', quiet=True)

def tokenize(sentence):
    """
    Split sentence into tokens/words.
    Example: "Hello, how are you?" -> ["Hello", ",", "how", "are", "you", "?"]
    """
    return nltk.word_tokenize(sentence)

def stem(word):
    """
    Stem word to its root form in lowercase.
    Example: "Running" -> "run"
    """
    return stemmer.stem(word.lower())

def bag_of_words(tokenized_sentence, words):
    """
    Return a bag-of-words vector:
    - tokenized_sentence: ["hello", "how", "are", "you"]
    - words: vocabulary list (all stemmed)
    """
    # Stem words and remove punctuation tokens
    sentence_words = [stem(w) for w in tokenized_sentence if w not in string.punctuation]
    
    # Initialize bag
    bag = np.zeros(len(words), dtype=np.float32)
    for idx, w in enumerate(words):
        if w in sentence_words:
            bag[idx] = 1.0
    return bag

def clean_text(text):
    """
    Clean text for better processing
    """
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    allowed_chars = set(string.ascii_letters + string.digits + ' .,!?-')
    text = ''.join(char for char in text if char in allowed_chars)
    
    return text.strip()

def extract_keywords(sentence):
    """
    Extract important keywords from a sentence
    """
    tokens = tokenize(sentence.lower())
    
    # Common stop words to filter out
    stop_words = {'the', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has', 'had',
                  'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
                  'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
                  'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
                  'before', 'after', 'above', 'below', 'between', 'among', 'i', 'you',
                  'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
                  'my', 'your', 'his', 'her', 'its', 'our', 'their', 'this', 'that',
                  'these', 'those', 'what', 'where', 'when', 'why', 'how'}
    
    # Filter out stop words and punctuation
    keywords = []
    for token in tokens:
        if (token not in stop_words and 
            token not in string.punctuation and 
            len(token) > 2):
            keywords.append(stem(token))
    
    return keywords

def calculate_similarity(text1, text2):
    """
    Calculate simple similarity between two texts based on common words
    """
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    
    return intersection / union if union > 0 else 0.0