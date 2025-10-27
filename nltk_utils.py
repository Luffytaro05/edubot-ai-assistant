import numpy as np
import nltk
from nltk.stem.porter import PorterStemmer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import wordnet
import string
import re
from difflib import SequenceMatcher

# Initialize stemmer and lemmatizer
stemmer = PorterStemmer()
lemmatizer = WordNetLemmatizer()

# NLTK data initialization with error handling
def initialize_nltk_data():
    """Initialize NLTK data with fallback handling"""
    try:
        # Try to download required NLTK data
        nltk.download('punkt', quiet=True)
        nltk.download('punkt_tab', quiet=True)  # Newer NLTK versions
        nltk.download('wordnet', quiet=True)
        nltk.download('averaged_perceptron_tagger', quiet=True)
        return True
    except Exception as e:
        print(f"⚠️ NLTK data download failed: {e}")
        print("🔄 Using fallback tokenization methods")
        return False

# Initialize NLTK data
nltk_available = initialize_nltk_data()

def tokenize(sentence):
    """
    Split sentence into tokens/words with fallback.
    Example: "Hello, how are you?" -> ["Hello", ",", "how", "are", "you", "?"]
    """
    if nltk_available:
        try:
            return nltk.word_tokenize(sentence)
        except Exception as e:
            print(f"⚠️ NLTK tokenization failed: {e}, using fallback")
            return fallback_tokenize(sentence)
    else:
        return fallback_tokenize(sentence)

def fallback_tokenize(sentence):
    """
    Fallback tokenization using regex when NLTK is not available
    """
    # Simple regex-based tokenization
    import re
    # Split on word boundaries, keeping punctuation
    tokens = re.findall(r'\b\w+\b|[^\w\s]', sentence)
    return tokens

def stem(word):
    """
    Stem word to its root form in lowercase with fallback.
    Example: "Running" -> "run"
    """
    if nltk_available:
        try:
            return stemmer.stem(word.lower())
        except Exception as e:
            print(f"⚠️ NLTK stemming failed: {e}, using fallback")
            return fallback_stem(word)
    else:
        return fallback_stem(word)

def fallback_stem(word):
    """
    Simple fallback stemming using basic rules
    """
    word = word.lower()
    # Basic stemming rules
    if word.endswith('ing') and len(word) > 5:
        return word[:-3]
    elif word.endswith('ed') and len(word) > 4:
        return word[:-2]
    elif word.endswith('s') and len(word) > 3:
        return word[:-1]
    return word

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
    Enhanced text cleaning for better processing
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters but keep basic punctuation
    allowed_chars = set(string.ascii_letters + string.digits + ' .,!?-')
    text = ''.join(char for char in text if char in allowed_chars)
    
    # Remove common typos and normalize
    text = re.sub(r'\b(ur|u|r|y|u r|you are)\b', 'you are', text)
    text = re.sub(r'\b(pls|plz|please)\b', 'please', text)
    text = re.sub(r'\b(thx|thanks)\b', 'thank you', text)
    text = re.sub(r'\b(btw|by the way)\b', 'by the way', text)
    
    return text.strip()

def get_wordnet_pos(word):
    """Map POS tag to first character lemmatize() accepts"""
    try:
        tag = nltk.pos_tag([word])[0][1][0].upper()
        tag_dict = {"J": wordnet.ADJ,
                    "N": wordnet.NOUN,
                    "V": wordnet.VERB,
                    "R": wordnet.ADV}
        return tag_dict.get(tag, wordnet.NOUN)
    except:
        # Fallback to noun if POS tagging fails
        return wordnet.NOUN

def lemmatize_word(word):
    """Lemmatize a word using POS tagging"""
    return lemmatizer.lemmatize(word, get_wordnet_pos(word))

def advanced_tokenize(sentence):
    """
    Enhanced tokenization with lemmatization
    """
    tokens = tokenize(sentence)
    # Apply lemmatization to each token
    lemmatized_tokens = [lemmatize_word(token) for token in tokens]
    return lemmatized_tokens

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
    Enhanced similarity calculation with fuzzy matching
    """
    words1 = set(extract_keywords(text1))
    words2 = set(extract_keywords(text2))
    
    if not words1 or not words2:
        return 0.0
    
    # Jaccard similarity
    intersection = len(words1.intersection(words2))
    union = len(words1.union(words2))
    jaccard_sim = intersection / union if union > 0 else 0.0
    
    # Fuzzy string matching for similar words
    fuzzy_score = 0.0
    for word1 in words1:
        for word2 in words2:
            similarity = SequenceMatcher(None, word1, word2).ratio()
            if similarity > 0.8:  # High similarity threshold
                fuzzy_score += similarity
    
    # Combine Jaccard and fuzzy scores
    combined_score = (jaccard_sim * 0.7) + (fuzzy_score / max(len(words1), len(words2)) * 0.3)
    
    return min(combined_score, 1.0)

def fuzzy_match(query, patterns, threshold=0.6):
    """
    Find fuzzy matches between query and patterns
    """
    matches = []
    for pattern in patterns:
        similarity = calculate_similarity(query, pattern)
        if similarity >= threshold:
            matches.append((pattern, similarity))
    
    # Sort by similarity score
    matches.sort(key=lambda x: x[1], reverse=True)
    return matches

def expand_synonyms(text):
    """
    Expand text with common synonyms for better matching
    """
    synonym_map = {
        'help': ['assist', 'support', 'aid'],
        'information': ['info', 'details', 'data'],
        'problem': ['issue', 'trouble', 'difficulty'],
        'question': ['query', 'inquiry', 'ask'],
        'need': ['require', 'want', 'looking for'],
        'get': ['obtain', 'receive', 'acquire'],
        'find': ['locate', 'search', 'discover'],
        'how': ['what', 'where', 'when', 'why'],
        'can': ['able', 'possible', 'capable'],
        'will': ['shall', 'going to', 'plan to']
    }
    
    words = text.split()
    expanded_words = []
    
    for word in words:
        expanded_words.append(word)
        if word in synonym_map:
            expanded_words.extend(synonym_map[word])
    
    return ' '.join(expanded_words)

def enhanced_bag_of_words(tokenized_sentence, words):
    """
    Enhanced bag of words with fuzzy matching and synonym expansion
    """
    try:
        # Expand with synonyms
        expanded_sentence = expand_synonyms(' '.join(tokenized_sentence))
        expanded_tokens = tokenize(expanded_sentence)
        
        # Stem words and remove punctuation
        sentence_words = [stem(w) for w in expanded_tokens if w not in string.punctuation]
        
        # Initialize bag with fuzzy matching
        bag = np.zeros(len(words), dtype=np.float32)
        for idx, w in enumerate(words):
            if w in sentence_words:
                bag[idx] = 1.0
            else:
                # Check for fuzzy matches
                for sentence_word in sentence_words:
                    if SequenceMatcher(None, w, sentence_word).ratio() > 0.8:
                        bag[idx] = 0.8  # Partial match score
                        break
        
        return bag
    except Exception as e:
        # Fallback to standard bag of words if enhanced version fails
        print(f"Enhanced bag of words failed, using standard: {e}")
        sentence_words = [stem(w) for w in tokenized_sentence if w not in string.punctuation]
        bag = np.zeros(len(words), dtype=np.float32)
        for idx, w in enumerate(words):
            if w in sentence_words:
                bag[idx] = 1.0
        return bag