"""
context_search.py
------------------
Enhanced keyword and fuzzy search utilities for the manual context injection workflow.
Now includes TF-IDF weighting, phrase matching, semantic weighting, and improved
scoring algorithms for better prediction quality from TCC website content.
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


def normalise(text: str) -> str:
    """Lower-case text and collapse whitespace for consistent comparison."""
    return re.sub(r"\s+", " ", text.strip().lower())


def tokenise(text: str) -> List[str]:
    """Split the input text into alphanumeric tokens."""
    return WORD_PATTERN.findall(normalise(text))


def keyword_overlap_score(message_tokens: Iterable[str], content_tokens: Iterable[str]) -> float:
    """
    Enhanced overlap score with TF-IDF-like weighting and phrase matching.

    Returns:
        A float between 0 and 1 representing the weighted ratio of matching tokens.
    """
    message_list = list(message_tokens)
    content_list = list(content_tokens)
    
    if not message_list or not content_list:
        return 0.0
    
    # Filter out stop words for better matching
    message_filtered = [t for t in message_list if t not in STOP_WORDS and len(t) > 2]
    content_filtered = [t for t in content_list if t not in STOP_WORDS and len(t) > 2]
    
    if not message_filtered:
        return 0.0
    
    message_set = set(message_filtered)
    content_set = set(content_filtered)
    
    # Basic overlap
    matches = message_set.intersection(content_set)
    base_score = len(matches) / len(message_set) if message_set else 0.0
    
    # Phrase matching bonus (2-3 word phrases)
    phrase_bonus = 0.0
    if len(message_filtered) >= 2:
        # Check for 2-word phrases
        message_phrases = set()
        for i in range(len(message_filtered) - 1):
            phrase = f"{message_filtered[i]} {message_filtered[i+1]}"
            message_phrases.add(phrase)
        
        content_text = " ".join(content_filtered).lower()
        phrase_matches = sum(1 for phrase in message_phrases if phrase in content_text)
        if phrase_matches > 0:
            phrase_bonus = min(0.3, phrase_matches * 0.1)
    
    # Term frequency weighting (more frequent terms in content = higher score)
    content_counter = Counter(content_filtered)
    tf_weight = 0.0
    for match in matches:
        # Normalize by content length
        tf_weight += min(0.1, content_counter[match] / len(content_filtered))
    
    return min(1.0, base_score + phrase_bonus + tf_weight)


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
    - Enhanced keyword overlap with TF-IDF weighting
    - Title and tag matching with higher weights
    - Fuzzy similarity
    - Exact phrase matching
    - Content length normalization
    """
    content = document.get("content", "")
    title = document.get("title", "")
    tags = document.get("tags", [])
    page = document.get("page", "")

    message_tokens = tokenise(user_message)
    content_tokens = tokenise(content)
    title_tokens = tokenise(title)
    tag_tokens = tokenise(" ".join(tags) if tags else "")
    page_tokens = tokenise(page) if page else []

    # Enhanced keyword overlap
    overlap = keyword_overlap_score(message_tokens, content_tokens)
    
    # Title matching (higher weight for title matches)
    title_overlap = keyword_overlap_score(message_tokens, title_tokens)
    
    # Tag matching (boost for tag matches)
    tag_overlap = keyword_overlap_score(message_tokens, tag_tokens) if tag_tokens else 0.0
    
    # Page matching
    page_overlap = keyword_overlap_score(message_tokens, page_tokens) if page_tokens else 0.0
    
    # Fuzzy similarity
    fuzzy_score = fuzzy_similarity_score(normalise(user_message), normalise(content))
    
    # Exact phrase matching bonus
    exact_phrase_bonus = 0.0
    message_lower = normalise(user_message)
    content_lower = normalise(content)
    title_lower = normalise(title)
    
    # Check for exact 3+ word phrases
    message_words = message_lower.split()
    if len(message_words) >= 3:
        for i in range(len(message_words) - 2):
            phrase = " ".join(message_words[i:i+3])
            if phrase in content_lower:
                exact_phrase_bonus += 0.15
            if phrase in title_lower:
                exact_phrase_bonus += 0.2
    
    # Content length normalization (prefer moderately-sized content)
    content_length = len(content)
    length_factor = 1.0
    if content_length < 50:
        length_factor = 0.7  # Too short
    elif content_length > 5000:
        length_factor = 0.9  # Too long
    
    # Weighted sum with enhanced factors
    base_score = (
        overlap * 0.45 +           # Content overlap (primary)
        title_overlap * 0.25 +      # Title match (high importance)
        tag_overlap * 0.10 +        # Tag match
        page_overlap * 0.05 +       # Page match
        fuzzy_score * 0.10 +        # Fuzzy similarity
        exact_phrase_bonus          # Exact phrase bonus
    )
    
    return min(1.0, base_score * length_factor)


def find_relevant_content(
    user_message: str,
    collection: Optional[Collection],
    minimum_score: float = 0.12,  # Lowered threshold to catch more relevant content
    top_k: int = 1,
) -> Optional[Tuple[Dict[str, str], float]]:
    """
    Enhanced search with better ranking and multiple candidate consideration.

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

    try:
        # Increased limit to evaluate more documents
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
            limit=200,  # Increased from 100
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[context_search] Failed to query collection: {exc}")
        return None

    # Score all documents and rank them
    scored_docs: List[Tuple[Dict[str, str], float]] = []
    for doc in cursor:
        score = score_document(user_message, doc)
        if score >= minimum_score:
            scored_docs.append((doc, score))
    
    if not scored_docs:
        return None
    
    # Sort by score (descending) and return top result
    scored_docs.sort(key=lambda x: x[1], reverse=True)
    
    # Return the best match
    return scored_docs[0] if scored_docs else None


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
    Enhanced ranking with better scoring and diversity consideration.
    Returns top_k documents sorted by relevance score.
    """
    if not user_message or not documents:
        return []

    ranked: List[Tuple[Dict[str, str], float]] = []
    seen_pages = set()  # Track pages to avoid duplicates
    
    for doc in documents:
        score = score_document(user_message, doc)
        if score >= minimum_score:
            # Slight penalty for duplicate pages (prefer diversity)
            page_key = doc.get("page", "")
            if page_key in seen_pages:
                score *= 0.95  # Small penalty
            else:
                seen_pages.add(page_key)
            
            ranked.append((doc, score))

    # Sort by score (descending)
    ranked.sort(key=lambda item: item[1], reverse=True)
    
    # Return top_k, ensuring diversity
    result = []
    pages_used = defaultdict(int)  # Count occurrences per page
    for doc, score in ranked:
        if len(result) >= top_k:
            break
        page_key = doc.get("page", "")
        # Allow 2 documents per page max
        if pages_used[page_key] < 2:
            result.append((doc, score))
            pages_used[page_key] += 1
        elif score > 0.3:  # Very high score, include anyway
            result.append((doc, score))
    
    return result[:top_k]

