"""
context_search.py
------------------
Enhanced keyword and fuzzy search utilities for the manual context injection workflow.
Now includes TF-IDF weighting, phrase matching, semantic weighting, query expansion,
and improved scoring algorithms for better prediction quality from TCC website content.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from pymongo.collection import Collection

# Regular expression for basic tokenisation.
WORD_PATTERN = re.compile(r"\w+")

# Common stop words to filter out for better matching
STOP_WORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must',
    'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
    'what', 'which', 'who', 'where', 'when', 'why', 'how', 'can', 'about', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'up', 'down', 'out',
    'off', 'over', 'under', 'again', 'further', 'then', 'once'
}

# TCC-specific synonyms and query expansion terms
TCC_SYNONYMS = {
    'admission': ['admission', 'admissions', 'apply', 'application', 'enroll', 'enrollment', 'applicant'],
    'registrar': ['registrar', 'transcript', 'records', 'grades', 'academic records', 'document'],
    'guidance': ['guidance', 'counseling', 'counselor', 'scholarship', 'financial aid'],
    'ict': ['ict', 'misu', 'information technology', 'computer', 'portal', 'password', 'login'],
    'osa': ['osa', 'student affairs', 'student activities', 'clubs', 'organizations'],
    'tuition': ['tuition', 'fee', 'fees', 'payment', 'pay', 'cost'],
    'course': ['course', 'program', 'degree', 'major', 'curriculum'],
    'requirement': ['requirement', 'requirements', 'needed', 'need', 'required', 'prerequisite'],
    'schedule': ['schedule', 'time', 'when', 'date', 'deadline', 'period'],
    'contact': ['contact', 'phone', 'email', 'address', 'location', 'office hours']
}


def normalise(text: str) -> str:
    """Lower-case text and collapse whitespace for consistent comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenise(text: str) -> List[str]:
    """Split the input text into alphanumeric tokens."""
    return WORD_PATTERN.findall(normalise(text))


def expand_query_terms(tokens: List[str]) -> set:
    """
    Expand query terms using TCC-specific synonyms for better matching.
    """
    expanded = set(tokens)
    tokens_lower = [t.lower() for t in tokens]
    
    for token in tokens_lower:
        # Check if token matches any synonym key
        for key, synonyms in TCC_SYNONYMS.items():
            if token in synonyms or any(syn in token for syn in synonyms):
                expanded.update(synonyms)
                break
    
    return expanded


def keyword_overlap_score(message_tokens: Iterable[str], content_tokens: Iterable[str]) -> float:
    """
    Enhanced overlap score with TF-IDF-like weighting, phrase matching, and query expansion.

    Returns:
        A float between 0 and 1 representing the weighted ratio of matching tokens.
    """
    message_list = list(message_tokens)
    content_list = list(content_tokens)
    
    if not message_list or not content_list:
        return 0.0
    
    # Filter out stop words for better matching
    message_filtered = [t.lower() for t in message_list if t.lower() not in STOP_WORDS and len(t) > 2]
    content_filtered = [t.lower() for t in content_list if t.lower() not in STOP_WORDS and len(t) > 2]
    
    if not message_filtered:
        return 0.0
    
    # Expand query terms with synonyms
    message_expanded = expand_query_terms(message_filtered)
    message_set = set(message_filtered) | message_expanded
    content_set = set(content_filtered)
    
    # Basic overlap (exact matches)
    exact_matches = message_set.intersection(content_set)
    base_score = len(exact_matches) / len(message_filtered) if message_filtered else 0.0
    
    # Partial word matching (e.g., "admission" matches "admissions")
    partial_bonus = 0.0
    for msg_token in message_filtered:
        for content_token in content_filtered:
            # Check if one contains the other (for plurals, variations)
            if msg_token in content_token or content_token in msg_token:
                if msg_token != content_token:  # Don't double count exact matches
                    partial_bonus += 0.05
                    break
    
    partial_bonus = min(0.2, partial_bonus)
    
    # Phrase matching bonus (2-3 word phrases)
    phrase_bonus = 0.0
    if len(message_filtered) >= 2:
        # Check for 2-word phrases
        message_phrases = set()
        for i in range(len(message_filtered) - 1):
            phrase = f"{message_filtered[i]} {message_filtered[i+1]}"
            message_phrases.add(phrase)
        
        # Check for 3-word phrases
        if len(message_filtered) >= 3:
            for i in range(len(message_filtered) - 2):
                phrase = f"{message_filtered[i]} {message_filtered[i+1]} {message_filtered[i+2]}"
                message_phrases.add(phrase)
        
        content_text = " ".join(content_filtered).lower()
        phrase_matches = sum(1 for phrase in message_phrases if phrase in content_text)
        if phrase_matches > 0:
            # Higher bonus for longer phrases
            phrase_bonus = min(0.4, phrase_matches * 0.15)
    
    # Term frequency weighting (more frequent terms in content = higher score)
    content_counter = Counter(content_filtered)
    tf_weight = 0.0
    for match in exact_matches:
        # Normalize by content length, but give more weight to important matches
        freq_ratio = content_counter[match] / len(content_filtered) if content_filtered else 0
        tf_weight += min(0.15, freq_ratio * 2)  # Increased weight
    
    # Position bonus (terms appearing early in content are more important)
    position_bonus = 0.0
    content_text_lower = " ".join(content_filtered).lower()
    for match in exact_matches:
        if match in content_text_lower:
            position = content_text_lower.find(match)
            # First 20% of content gets bonus
            if position < len(content_text_lower) * 0.2:
                position_bonus += 0.05
    
    position_bonus = min(0.15, position_bonus)
    
    return min(1.0, base_score + partial_bonus + phrase_bonus + tf_weight + position_bonus)


def fuzzy_similarity_score(message: str, content: str) -> float:
    """
    Use difflib's SequenceMatcher to gauge similarity between two strings.

    The score ranges between 0 and 1.
    """
    if not message or not content:
        return 0.0
    return SequenceMatcher(None, message, content).ratio()


def score_document(user_message: str, document: Dict[str, str]) -> float:
    """
    Enhanced composite scoring with multiple factors for better prediction quality.
    
    Now includes:
    - Enhanced keyword overlap with TF-IDF weighting and query expansion
    - Title and tag matching with higher weights
    - Fuzzy similarity
    - Exact phrase matching (2-4 word phrases)
    - Content length normalization
    - Question word detection and matching
    - Office-specific context matching
    """
    content = document.get("content", "")
    title = document.get("title", "")
    tags = document.get("tags", [])
    page = document.get("page", "")
    slug = document.get("slug", "")

    message_tokens = tokenise(user_message)
    content_tokens = tokenise(content)
    title_tokens = tokenise(title)
    tag_tokens = tokenise(" ".join(tags) if tags else "")
    page_tokens = tokenise(page) if page else []
    slug_tokens = tokenise(slug) if slug else []

    # Enhanced keyword overlap with query expansion
    overlap = keyword_overlap_score(message_tokens, content_tokens)
    
    # Title matching (higher weight for title matches - titles are very important)
    title_overlap = keyword_overlap_score(message_tokens, title_tokens)
    
    # Tag matching (boost for tag matches)
    tag_overlap = keyword_overlap_score(message_tokens, tag_tokens) if tag_tokens else 0.0
    
    # Page matching
    page_overlap = keyword_overlap_score(message_tokens, page_tokens) if page_tokens else 0.0
    
    # Slug matching (often contains key terms)
    slug_overlap = keyword_overlap_score(message_tokens, slug_tokens) if slug_tokens else 0.0
    
    # Fuzzy similarity (for partial matches)
    fuzzy_score = fuzzy_similarity_score(normalise(user_message), normalise(content))
    
    # Enhanced exact phrase matching (2-4 word phrases)
    exact_phrase_bonus = 0.0
    message_lower = normalise(user_message)
    content_lower = normalise(content)
    title_lower = normalise(title)
    
    message_words = message_lower.split()
    # Check for 2-word phrases
    if len(message_words) >= 2:
        for i in range(len(message_words) - 1):
            phrase = " ".join(message_words[i:i+2])
            if phrase in content_lower:
                exact_phrase_bonus += 0.1
            if phrase in title_lower:
                exact_phrase_bonus += 0.15
    
    # Check for 3-word phrases
    if len(message_words) >= 3:
        for i in range(len(message_words) - 2):
            phrase = " ".join(message_words[i:i+3])
            if phrase in content_lower:
                exact_phrase_bonus += 0.15
            if phrase in title_lower:
                exact_phrase_bonus += 0.2
    
    # Check for 4-word phrases (very specific matches)
    if len(message_words) >= 4:
        for i in range(len(message_words) - 3):
            phrase = " ".join(message_words[i:i+4])
            if phrase in content_lower:
                exact_phrase_bonus += 0.2
            if phrase in title_lower:
                exact_phrase_bonus += 0.25
    
    # Question word detection (boost if question words match content topics)
    question_words = {'what', 'when', 'where', 'who', 'why', 'how', 'which', 'can', 'do', 'does', 'is', 'are'}
    message_question_words = set(message_words) & question_words
    if message_question_words:
        # If content contains answers to question words, boost score
        question_bonus = 0.0
        for qw in message_question_words:
            if qw in content_lower or qw in title_lower:
                question_bonus += 0.05
        exact_phrase_bonus += min(0.1, question_bonus)
    
    # Office-specific context matching
    office_bonus = 0.0
    office_keywords = {
        'admission', 'registrar', 'guidance', 'ict', 'misu', 'osa', 
        'student affairs', 'accounting', 'finance'
    }
    message_lower_set = set(message_lower.split())
    content_lower_set = set(content_lower.split())
    title_lower_set = set(title_lower.split())
    
    for office_kw in office_keywords:
        if office_kw in message_lower:
            if office_kw in content_lower_set or office_kw in title_lower_set:
                office_bonus += 0.1
    
    office_bonus = min(0.2, office_bonus)
    
    # Content length normalization (prefer moderately-sized content)
    content_length = len(content)
    length_factor = 1.0
    if content_length < 50:
        length_factor = 0.7  # Too short
    elif content_length > 5000:
        length_factor = 0.9  # Too long
    elif 200 <= content_length <= 2000:
        length_factor = 1.05  # Optimal length gets slight boost
    
    # Weighted sum with enhanced factors
    base_score = (
        overlap * 0.40 +           # Content overlap (primary, slightly reduced)
        title_overlap * 0.30 +      # Title match (increased importance)
        tag_overlap * 0.10 +        # Tag match
        page_overlap * 0.05 +       # Page match
        slug_overlap * 0.05 +       # Slug match (new)
        fuzzy_score * 0.05 +        # Fuzzy similarity (reduced)
        exact_phrase_bonus +        # Exact phrase bonus
        office_bonus                # Office context bonus (new)
    )
    
    return min(1.0, base_score * length_factor)


def find_relevant_content(
    user_message: str,
    collection: Optional[Collection],
    minimum_score: float = 0.10,  # Lowered threshold to catch more relevant content
    top_k: int = 1,
) -> Optional[Tuple[Dict[str, str], float]]:
    """
    Optimized search with early exit, query preprocessing, and improved document evaluation.

    Args:
        user_message: The raw user question.
        collection: The MongoDB collection holding website sections.
        minimum_score: Minimum score threshold required to consider a match.
        top_k: Number of top results to consider (returns best one).

    Returns:
        A tuple of (document, score) for the best match, or None if nothing
        meets the threshold.
    """
    if not user_message or not collection:
        return None

    # Preprocess query: expand with synonyms and normalize
    normalized_query = normalise(user_message)
    
    try:
        # Use MongoDB text search if available (faster initial filtering)
        # Fallback to full scan if text index not available
        try:
            # Try text search first (if text index exists)
            cursor = collection.find(
                {"$text": {"$search": normalized_query}},
                {
                    "_id": False,
                    "slug": True,
                    "title": True,
                    "page": True,
                    "content": True,
                    "tags": True,
                },
                limit=150,  # Increased limit for better coverage
            )
        except Exception:
            # Fallback to full scan with keyword filtering
            # Extract key terms for MongoDB regex search
            key_terms = [t for t in tokenise(normalized_query) if t not in STOP_WORDS and len(t) > 2]
            if key_terms:
                # Search in title, content, and tags
                regex_pattern = "|".join(key_terms[:5])  # Limit to 5 terms for performance
                cursor = collection.find(
                    {
                        "$or": [
                            {"title": {"$regex": regex_pattern, "$options": "i"}},
                            {"content": {"$regex": regex_pattern, "$options": "i"}},
                            {"tags": {"$in": key_terms}},
                            {"page": {"$regex": regex_pattern, "$options": "i"}}
                        ]
                    },
                    {
                        "_id": False,
                        "slug": True,
                        "title": True,
                        "page": True,
                        "content": True,
                        "tags": True,
                    },
                    limit=150,
                )
            else:
                # Last resort: full scan
                cursor = collection.find(
                    {},
                    {
                        "_id": False,
                        "slug": True,
                        "title": True,
                        "page": True,
                        "content": True,
                        "tags": True,
                    },
                    limit=150,
                )
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[context_search] Failed to query collection: {exc}")
        return None

    # Score documents with early exit for high confidence matches
    best_match: Optional[Tuple[Dict[str, str], float]] = None
    best_score = 0.0
    candidates = []  # Store top candidates for comparison
    
    for doc in cursor:
        score = score_document(user_message, doc)
        if score >= minimum_score:
            candidates.append((doc, score))
            if score > best_score:
                best_match = (doc, score)
                best_score = score
                # Early exit if we find an excellent match
                if score > 0.80:
                    print(f"[context_search] Early exit with high score: {score:.3f}")
                    break
    
    # If we have multiple candidates, verify the best one
    if candidates and len(candidates) > 1:
        # Sort by score and take the best
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_match = candidates[0]
        print(f"[context_search] Found {len(candidates)} candidates, best score: {best_match[1]:.3f}")
    
    return best_match


def find_best_in_documents(
    user_message: str,
    documents: Sequence[Dict[str, str]],
    minimum_score: float = 0.15,
) -> Optional[Tuple[Dict[str, str], float]]:
    """
    Search a list of pre-loaded documents (e.g., local template sections) and
    return the best match based on the shared scoring logic.
    """
    if not user_message or not documents:
        return None

    best_match: Optional[Tuple[Dict[str, str], float]] = None
    for doc in documents:
        score = score_document(user_message, doc)
        if score < minimum_score:
            continue
        if best_match is None or score > best_match[1]:
            best_match = (doc, score)

    return best_match


def rank_documents(
    user_message: str,
    documents: Sequence[Dict[str, str]],
    *,
    minimum_score: float = 0.08,  # Lowered to catch more relevant content
    top_k: int = 5,  # Increased to provide more context
) -> List[Tuple[Dict[str, str], float]]:
    """
    Enhanced ranking with better scoring, diversity consideration, and relevance boosting.
    Returns top_k documents sorted by relevance score.
    """
    if not user_message or not documents:
        return []

    ranked: List[Tuple[Dict[str, str], float]] = []
    seen_slugs = set()  # Track slugs to avoid exact duplicates
    seen_pages = set()  # Track pages to avoid duplicates
    
    # Preprocess query for better matching
    normalized_query = normalise(user_message)
    query_tokens = set(tokenise(normalized_query))
    
    for doc in documents:
        slug = doc.get("slug", "")
        
        # Skip exact duplicates
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        
        score = score_document(user_message, doc)
        
        # Boost score if document has high keyword density
        if score >= minimum_score:
            # Calculate keyword density (how many query terms appear in doc)
            doc_text = f"{doc.get('title', '')} {doc.get('content', '')} {doc.get('page', '')}"
            doc_tokens = set(tokenise(doc_text))
            keyword_density = len(query_tokens & doc_tokens) / len(query_tokens) if query_tokens else 0
            if keyword_density > 0.5:  # More than 50% of query terms present
                score *= 1.1  # 10% boost
            
            # Slight penalty for duplicate pages (prefer diversity)
            page_key = doc.get("page", "")
            if page_key in seen_pages:
                score *= 0.92  # Slightly increased penalty
            else:
                seen_pages.add(page_key)
            
            ranked.append((doc, score))

    # Sort by score (descending)
    ranked.sort(key=lambda item: item[1], reverse=True)
    
    # Return top_k, ensuring diversity while prioritizing high scores
    result = []
    pages_used = defaultdict(int)  # Count occurrences per page
    slugs_used = set()  # Track used slugs
    
    for doc, score in ranked:
        if len(result) >= top_k:
            break
        
        slug = doc.get("slug", "")
        page_key = doc.get("page", "")
        
        # Skip if already used
        if slug in slugs_used:
            continue
        
        # Allow 2 documents per page max, unless score is very high
        if pages_used[page_key] < 2:
            result.append((doc, score))
            pages_used[page_key] += 1
            slugs_used.add(slug)
        elif score > 0.35:  # Very high score, include anyway (increased threshold)
            result.append((doc, score))
            pages_used[page_key] += 1
            slugs_used.add(slug)
    
    return result[:top_k]

