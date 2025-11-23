#(chat.py):
import random
import json
import torch
import os
import ssl
import sys
import pymongo
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from model import NeuralNet, HybridChatModel
from vector_store import VectorStore
from nltk_utils import bag_of_words, tokenize, clean_text, enhanced_bag_of_words, fuzzy_match, expand_synonyms
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, ConnectionFailure
from datetime import datetime, UTC, date
import certifi
import time
from openai import OpenAI

from database import get_context_collection, seed_sample_data
from context_search import find_relevant_content, find_best_in_documents, rank_documents, score_document

SYSTEM_PROMPT = """
You are TCC Assistant, the official AI chatbot of Tanauan City College.
Your job is to answer questions ONLY about:
- The college (courses, admission, enrollment, departments)
- Events, facilities, offices, and student services

If the question is unrelated to TCC (for example, math, personal advice, or general knowledge),
you MUST respond with EXACTLY this message:

"I'm sorry, but I can only assist with questions related to Tanauan City College (TCC).
For further assistance, you may reach out to the appropriate TCC office below:

📞 TCC Official
(043) 702 6979 / 📧 tanauancitycollege@gmail.com

🏛️ Office of Student Affairs (OSA)
0998 457 4389 / 📧 tanauancitycollege.osa@gmail.com

💻 MISU Office
0994 189 7696 / 📧 tanauancitycollege013@gmail.com

🗂️ Registrar's Office
0981 349 1038 / 📧 tanauancitycollege.registrar@gmail.com

🎓 Iskolar ng Lungsod Council (ILC)
0971 745 6791 / 📧 iskolarnglungsodcouncil.tcc@gmail.com

📝 Admission Office
0956 641 9801 / 📧 tanauancitycollege.admission@gmail.com

💬 Guidance Office
0985 402 6745 / 📧 tanauancitycollege.guidance@gmail.com

Thank you for reaching out! Please contact the relevant office for your specific concern. 💚"

Do not create your own version of this message. Use it exactly as provided above.
""".strip()

DOMAIN_REFUSAL_MESSAGE = (
    "I'm sorry, but I can only assist with questions related to Tanauan City College (TCC).\n"
    "For further assistance, you may reach out to the appropriate TCC office below:\n\n"
    "📞 TCC Official\n"
    "(043) 702 6979 / 📧 tanauancitycollege@gmail.com\n\n"
    "🏛️ Office of Student Affairs (OSA)\n"
    "0998 457 4389 / 📧 tanauancitycollege.osa@gmail.com\n\n"
    "💻 MISU Office\n"
    "0994 189 7696 / 📧 tanauancitycollege013@gmail.com\n\n"
    "🗂️ Registrar’s Office\n"
    "0981 349 1038 / 📧 tanauancitycollege.registrar@gmail.com\n\n"
    "🎓 Iskolar ng Lungsod Council (ILC)\n"
    "0971 745 6791 / 📧 iskolarnglungsodcouncil.tcc@gmail.com\n\n"
    "📝 Admission Office\n"
    "0956 641 9801 / 📧 tanauancitycollege.admission@gmail.com\n\n"
    "💬 Guidance Office\n"
    "0985 402 6745 / 📧 tanauancitycollege.guidance@gmail.com\n\n"
    "Thank you for reaching out! Please contact the relevant office for your specific concern. 💚"
)

# Load environment variables
load_dotenv()

LOCAL_TEMPLATE_MIN_SCORE = float(os.getenv("LOCAL_TEMPLATE_MIN_SCORE", "0.12"))

# Print diagnostic information
print("System Information:")
print(f"Python version: {sys.version}")
print(f"PyMongo version: {pymongo.__version__}")
print(f"SSL version: {ssl.OPENSSL_VERSION}")
print(f"Certifi version: {certifi.__version__}")
print()

# MongoDB Announcements Collections
sub_announcements_collection = None
admin_announcements_collection = None

# Secure MongoDB connection using environment variable and TLS
def create_mongo_connection():
    """Create a secure MongoDB connection using MONGODB_URI and TLS."""
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("[WARNING] MONGODB_URI is not set. Database features will be disabled.")
        return None
    try:
        client = MongoClient(
            mongodb_uri,
            tls=True,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=15000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000,
            maxPoolSize=5,
            retryWrites=True
        )
        client.admin.command('ping')
        print("✅ MongoDB connected securely (TLS enabled)")
        return client
    except Exception as e:
        print(f"❌ Secure MongoDB connection failed: {e}")
        return None

# Initialize MongoDB connection
print("Initializing MongoDB connection...")
mongo_client = create_mongo_connection()

if mongo_client:
    db = mongo_client["chatbot_db"]
    conversations = db["conversations"]
    sub_announcements_collection = db["sub_announcements"]
    admin_announcements_collection = db["admin_announcements"]
    print("MongoDB database and collections initialized")
else:
    print("Failed to connect to MongoDB. Running in offline mode.")
    db = None
    conversations = None
    sub_announcements_collection = None
    admin_announcements_collection = None

# Load intents
with open("intents.json", "r") as f:
    intents = json.load(f)

# Initialize Vector Store
vector_store = VectorStore()

# -------- Website Scraping Configuration --------
SITE_BASE_URL = os.getenv("SITE_BASE_URL", "https://tanauancitycollege.edu.ph")
SITE_PAGE_CACHE_TTL = int(os.getenv("SITE_PAGE_CACHE_TTL", "600"))  # seconds
SITE_PAGE_MAX_CHARS = int(os.getenv("SITE_PAGE_MAX_CHARS", "20000"))

# Simple keyword-based routing to known public pages
SITE_PAGE_CATALOG = [
    {
        "name": "About",
        "path": "/about",
        "keywords": [
            "about", "history", "mission", "vision", "president", "leadership", "overview", "this is tcc"
        ],
    },
    {
        "name": "Admissions",
        "path": "/admissions",
        "keywords": [
            "admission", "enrollment", "apply", "requirements", "transferee", "freshmen", "acceptance",
            "psa", "form 137", "form 138"
        ],
    },
    {
        "name": "Academics",
        "path": "/academics",
        "keywords": [
            "program", "course", "academics", "curriculum", "college", "department", "degree"
        ],
    },
    {
        "name": "News",
        "path": "/news",
        "keywords": [
            "news", "announcement", "event", "updates", "press", "latest"
        ],
    },
    {
        "name": "Contact",
        "path": "/contact",
        "keywords": [
            "contact", "phone", "email", "address", "location", "office hours", "visit", "map"
        ],
    },
    {
        "name": "Student Affairs",
        "path": "/student-affairs",
        "keywords": [
            "osa", "student affairs", "clubs", "organizations", "activities"
        ],
    },
]

SITE_LOCAL_PAGE_MAP = {
    "/": "templates/home.html",
    "/home": "templates/home.html",
    "/about": "templates/tcc.html",
    "/admissions": "templates/admission.html",
    "/admission": "templates/admission.html",
    "/academics": "templates/academics.html",
    "/community": "templates/community.html",
    "/tcc": "templates/tcc.html",
}

LOCAL_TEMPLATE_SOURCES = {
    "base_template": {"path": "templates/base_template.html", "title": "Base Template"},
    "home": {"path": "templates/home.html", "title": "Home"},
    "admission": {"path": "templates/admission.html", "title": "Admission"},
    "academics": {"path": "templates/academics.html", "title": "Academics"},
    "community": {"path": "templates/community.html", "title": "Community"},
    "tcc": {"path": "templates/tcc.html", "title": "This is TCC"},
}

PATH_TO_TEMPLATE_KEY = {meta["path"]: key for key, meta in LOCAL_TEMPLATE_SOURCES.items()}

PATH_TO_TEMPLATE_KEY = {meta["path"]: key for key, meta in LOCAL_TEMPLATE_SOURCES.items()}

_page_cache: Dict[str, Dict[str, object]] = {}
_http_session = requests.Session()
_context_collection = None
_context_seed_attempted = False
LOCAL_TEMPLATE_DOCS: List[Dict[str, str]] = []
LOCAL_TEMPLATE_CACHE: Dict[str, Dict[str, str]] = {}
LOCAL_TEMPLATE_PAGE_DOCS: Dict[str, Dict[str, str]] = {}
LOCAL_TEMPLATE_PAGE_DOCS: Dict[str, Dict[str, str]] = {}


# Note: Announcements are now stored exclusively in MongoDB and Pinecone
# No JSON file fallback - all announcements come from database

"""
Model loading (global single initialization)
"""
# Global variables for lazy loading
model_loaded = False
model = None
hybrid_model = None
all_words = []
tags = []

def load_models_if_needed():
    """Load models once globally if not already loaded."""
    global model_loaded, model, hybrid_model, all_words, tags
    if model_loaded:
        return model, hybrid_model, all_words, tags
    print("🔄 Loading neural network model...")
    load_start = time.time()
    try:
        data = torch.load("data.pth")
        input_size = data["input_size"]
        hidden_size = data["hidden_size"]
        output_size = data["output_size"]
        all_words = data["all_words"]
        tags = data["tags"]
        model_state = data["model_state"]
        model = NeuralNet(input_size, hidden_size, output_size)
        model.load_state_dict(model_state)
        model.eval()
        hybrid_model = HybridChatModel(model, vector_store, tags)
        print(f"✅ Neural network loaded successfully (took {time.time()-load_start:.2f}s)")
    except FileNotFoundError:
        print("[WARNING] Model file not found. Using fallback mode.")
        model = None
        hybrid_model = None
        all_words = ["hello", "help", "thanks", "goodbye"] * 25
        tags = ["greeting", "help", "thanks", "goodbye"]
    except Exception as e:
        print(f"[ERROR] Error loading model: {e}. Using fallback mode.")
        model = None
        hybrid_model = None
        all_words = ["hello", "help", "thanks", "goodbye"] * 25
        tags = ["greeting", "help", "thanks", "goodbye"]
    model_loaded = True
    return model, hybrid_model, all_words, tags

# Eagerly load models at import time (disable lazy loading)
model, hybrid_model, all_words, tags = load_models_if_needed()

# Store conversation contexts for each user per office
# Structure: user_contexts[user_id] = {
#     "current_office": "admission_office",  # Currently active office
#     "offices": {
#         "admission_office": {...},  # Office-specific context data
#         "registrar_office": {...},
#         ...
#     }
# }
user_contexts = {}

# Office mapping for context switching
office_tags = {
    'admission_office': 'Admissions Office',
    'registrar_office': "Registrar's Office",
    'ict_office': 'ICT Office',
    'guidance_office': 'Guidance Office',
    'osa_office': 'Office of the Student Affairs (OSA)'
}

# ---------- OpenAI Fallback Integration ----------
_openai_client = None

def _get_openai_client():
    global _openai_client
    if _openai_client is not None:
        return _openai_client
    try:
        # API key is read from environment (OPENAI_API_KEY)
        _openai_client = OpenAI()
        return _openai_client
    except Exception as e:
        print(f"[OpenAI] Client init failed: {e}")
        return None


def call_openai_with_prompt(
    user_content: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 300,
    user_id: str = "guest",
    extra_messages: Optional[List[Dict[str, str]]] = None,
    timeout: float = 30.0,
) -> Optional[str]:
    """
    Helper to send a guarded request to GPT with the global system prompt.
    
    Args:
        timeout: Maximum time to wait for API response in seconds (default: 30s)
    """
    client = _get_openai_client()
    if not client:
        return None

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "user", "content": user_content})
    if extra_messages:
        messages.extend(extra_messages)

    start_time = time.perf_counter()
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=temperature,
            max_tokens=max_tokens,
            messages=messages,
            timeout=timeout,
        )
    except Exception as exc:
        duration = time.perf_counter() - start_time
        print(f"[OpenAI] Request failed after {duration:.2f}s: {exc}")
        return None
    finally:
        duration = time.perf_counter() - start_time
        if duration > 10:
            print(f"[OpenAI] ⚠️ Slow completion: {duration:.2f}s | user={user_id}")
        else:
            print(
                f"[OpenAI] Completion in {duration:.2f}s | user={user_id} | temp={temperature}"
            )

    content = completion.choices[0].message.content if completion and completion.choices else None
    if content:
        summary = content.strip()
        print(f"[DomainGuard] response_preview={summary[:120].replace(chr(10), ' ')}")
        
        # Check if OpenAI's response indicates an unrelated question and replace with exact DOMAIN_REFUSAL_MESSAGE
        summary_lower = summary.lower()
        
        # Detect the specific problematic pattern: "I'm here to provide information specifically about..."
        # combined with "For questions unrelated to TCC" or similar phrasing
        problematic_patterns = [
            "i'm here to provide information specifically about tanauan city college",
            "for questions unrelated to tcc, such as",
            "i recommend checking with the appropriate office or resource",
            "you can find the official tcc office directory for further assistance"
        ]
        
        # Check if the response matches the problematic pattern (OpenAI's own refusal message)
        # but is NOT the exact DOMAIN_REFUSAL_MESSAGE we want
        has_problematic_pattern = any(pattern in summary_lower for pattern in problematic_patterns)
        is_exact_message = summary.strip().startswith("I'm sorry, but I can only assist with questions related to Tanauan City College (TCC).")
        
        if has_problematic_pattern and not is_exact_message:
            print(f"[DomainGuard] Detected OpenAI-generated refusal message, replacing with exact DOMAIN_REFUSAL_MESSAGE")
            return DOMAIN_REFUSAL_MESSAGE
        
        return summary
    return None


def get_openai_fallback(message, user_id="guest"):
    """Generate a response using OpenAI GPT-4o mini as a fallback.

    Returns a plain string response or None if unavailable.
    """
    return call_openai_with_prompt(message, temperature=0.2, max_tokens=300, user_id=user_id, timeout=25.0)


def _score_page_entry(question: str, entry: Dict[str, object]) -> int:
    """Score a catalog entry based on keyword matches."""
    question_lower = question.lower()
    keywords = entry.get("keywords", [])
    score = sum(1 for word in keywords if word in question_lower)
    # Prefer exact name matches slightly
    if entry.get("name", "").lower() in question_lower:
        score += 2
    return score


def _select_relevant_page(question: str) -> Optional[Dict[str, object]]:
    """Choose the most relevant page config for the question."""
    best_entry = None
    best_score = 0
    for entry in SITE_PAGE_CATALOG:
        score = _score_page_entry(question, entry)
        if score > best_score:
            best_entry = entry
            best_score = score

    if best_entry and best_score > 0:
        return best_entry
        return None


def _extract_visible_text(html: str) -> str:
    """Extract visible text from HTML using BeautifulSoup."""
    soup = BeautifulSoup(html, "html.parser")

    for element in soup(["script", "style", "noscript", "svg"]):
        element.decompose()

    text_chunks = [chunk.strip() for chunk in soup.stripped_strings if chunk.strip()]
    text = " ".join(text_chunks)
    text = re.sub(r"\s+", " ", text)
    return text


def _get_cached_page(path: str) -> Optional[Dict[str, object]]:
    """Retrieve cached page content if available and fresh."""
    cached = _page_cache.get(path)
    if not cached:
        return None

    age = time.time() - cached["timestamp"]
    if age > SITE_PAGE_CACHE_TTL:
        _page_cache.pop(path, None)
        return None
    return cached


def _cache_page(path: str, data: Dict[str, object]) -> None:
    """Store page data in cache."""
    _page_cache[path] = {**data, "timestamp": time.time()}


def _fetch_page_text(path: str) -> Optional[Dict[str, object]]:
    """Fetch and extract visible text for the given page path."""
    if not SITE_BASE_URL:
        return None

    cached = _get_cached_page(path)
    if cached:
        return {**cached, "source": "cache"}

    url = urljoin(SITE_BASE_URL.rstrip("/") + "/", path.lstrip("/"))
    fetch_start = time.perf_counter()
    page_data: Optional[Dict[str, object]] = None

    try:
        response = _http_session.get(url, timeout=15)
        response.raise_for_status()
    except Exception as exc:
        print(f"[WebsiteQA] Failed to fetch {url}: {exc}")
    else:
        fetch_duration = time.perf_counter() - fetch_start
        text = _extract_visible_text(response.text)
        if text:
            trimmed_text = text[:SITE_PAGE_MAX_CHARS]
            page_data = {
                "url": url,
                "text": trimmed_text,
                "fetch_duration": fetch_duration,
                "source": "live",
            }
            print(
                f"[WebsiteQA] Fetched {url} in {fetch_duration:.2f}s "
                f"(length: {len(trimmed_text)} chars)"
            )
        else:
            print(f"[WebsiteQA] No visible text found for {url}")

    if not page_data:
        local_data = _load_local_page_text(path)
        if local_data:
            _cache_page(path, local_data)
        return local_data

    _cache_page(path, page_data)
    return page_data


def _load_local_page_text(path: str) -> Optional[Dict[str, object]]:
    """Fall back to local template files when live fetching fails."""
    template_path = SITE_LOCAL_PAGE_MAP.get(path)
    if not template_path:
        print(f"[WebsiteQA] No local template mapping for path {path}")
        return None

    full_path = Path(__file__).resolve().parent / template_path
    if not full_path.exists():
        print(f"[WebsiteQA] Local template not found: {full_path}")
        return None

    try:
        html = full_path.read_text(encoding="utf-8")
    except Exception as exc:
        print(f"[WebsiteQA] Failed to read local template {full_path}: {exc}")
        return None

    text = _extract_visible_text(html)
    if not text:
        print(f"[WebsiteQA] No visible text extracted from local template {full_path}")
        return None

    trimmed_text = text[:SITE_PAGE_MAX_CHARS]
    print(f"[WebsiteQA] Using local template for path {path} ({full_path})")
    return {
        "url": f"local://{path.lstrip('/') or 'home'}",
        "text": trimmed_text,
        "fetch_duration": 0.0,
        "source": "local-template",
    }


def _split_template_sections(html: str, base_title: str, page_key: str) -> List[Dict[str, str]]:
    """
    Enhanced section splitting with better content extraction.
    Now extracts more granular sections including paragraphs, lists, and structured content.
    """
    soup = BeautifulSoup(html, "html.parser")
    heading_tags = ["h1", "h2", "h3", "h4", "h5"]
    sections: List[Dict[str, str]] = []

    headings = soup.find_all(heading_tags)
    if not headings:
        # If no headings, try to extract by paragraphs or divs with class/id
        paragraphs = soup.find_all(["p", "div"], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ["content", "section", "info", "detail"]
        ))
        if paragraphs:
            for idx, para in enumerate(paragraphs[:10]):  # Limit to 10 sections
                text = para.get_text(separator=" ", strip=True)
                if text and len(text) > 40:
                    sections.append({
                        "slug": f"local-{page_key}-para-{idx+1}",
                        "title": f"{base_title} - Content Section {idx+1}",
                        "page": page_key,
                        "content": text[:SITE_PAGE_MAX_CHARS],
                        "tags": [page_key, "content"],
                        "source": "local-template-section",
                    })
        return sections

    for idx, heading in enumerate(headings):
        section_title = heading.get_text(separator=" ", strip=True) or f"{base_title} Section {idx + 1}"
        collected_parts: List[str] = [section_title]

        # Enhanced content collection - get all content until next heading
        current = heading.next_sibling
        while current:
            if getattr(current, "name", None) in heading_tags:
                break
            
            # Extract text from various elements
            if isinstance(current, str):
                text = current.strip()
                if text:
                    collected_parts.append(text)
            else:
                # Get text from element, including lists
                if current.name in ["p", "div", "span", "li"]:
                    text = current.get_text(separator=" ", strip=True)
                    if text:
                        collected_parts.append(text)
                elif current.name in ["ul", "ol"]:
                    # Extract list items
                    list_items = current.find_all("li")
                    for li in list_items:
                        li_text = li.get_text(separator=" ", strip=True)
                        if li_text:
                            collected_parts.append(f"• {li_text}")
            
            current = current.next_sibling

        section_text = " ".join(collected_parts).strip()
        if not section_text or len(section_text) < 40:
            continue

        # Extract additional tags from heading classes/ids
        heading_classes = heading.get("class", [])
        heading_id = heading.get("id", "")
        tags = [page_key, section_title.lower()]
        if heading_classes:
            tags.extend([str(cls).lower() for cls in heading_classes[:2]])
        if heading_id:
            tags.append(heading_id.lower())

        sections.append(
            {
                "slug": f"local-{page_key}-section-{idx+1}",
                "title": f"{base_title} - {section_title}",
                "page": page_key,
                "content": section_text[:SITE_PAGE_MAX_CHARS],
                "tags": tags,
                "source": "local-template-section",
            }
        )

    return sections


def _load_local_template_contexts() -> None:
    """Load static template files into in-memory documents for manual search."""
    global LOCAL_TEMPLATE_DOCS, LOCAL_TEMPLATE_CACHE, LOCAL_TEMPLATE_PAGE_DOCS
    LOCAL_TEMPLATE_DOCS = []
    LOCAL_TEMPLATE_CACHE = {}
    LOCAL_TEMPLATE_PAGE_DOCS = {}
    base_dir = Path(__file__).resolve().parent

    for key, meta in LOCAL_TEMPLATE_SOURCES.items():
        rel_path = meta.get("path")
        if not rel_path:
            continue

        full_path = base_dir / rel_path
        if not full_path.exists():
            print(f"[LocalContext] Template not found: {full_path}")
            continue

        try:
            html = full_path.read_text(encoding="utf-8")
        except Exception as exc:
            print(f"[LocalContext] Failed to read template {full_path}: {exc}")
            continue

        text = _extract_visible_text(html)
        if not text:
            print(f"[LocalContext] No visible text extracted from {full_path}")
            continue

        trimmed_text = text[:SITE_PAGE_MAX_CHARS]
        doc = {
            "slug": f"local-{key}",
            "title": meta.get("title", key.replace("_", " ").title()),
            "page": key,
            "content": trimmed_text,
            "tags": [key],
            "source": "local-template",
            "path": str(full_path),
        }
        LOCAL_TEMPLATE_DOCS.append(doc)
        LOCAL_TEMPLATE_CACHE[doc["slug"]] = doc
        LOCAL_TEMPLATE_PAGE_DOCS[key] = doc.copy()

        sections = _split_template_sections(html, doc["title"], key)
        LOCAL_TEMPLATE_DOCS.extend(sections)
        for section in sections:
            LOCAL_TEMPLATE_CACHE[section["slug"]] = section

    print(f"[LocalContext] Loaded {len(LOCAL_TEMPLATE_DOCS)} local template document(s).")


_load_local_template_contexts()


def _get_page_key_for_route(route_path: str) -> Optional[str]:
    template_path = SITE_LOCAL_PAGE_MAP.get(route_path)
    if not template_path:
        return None
    return PATH_TO_TEMPLATE_KEY.get(template_path)


def _get_documents_for_page(page_key: Optional[str]) -> List[Dict[str, str]]:
    if not page_key:
        return []
    if not LOCAL_TEMPLATE_DOCS:
        _load_local_template_contexts()

    documents: List[Dict[str, str]] = []
    base_doc = LOCAL_TEMPLATE_PAGE_DOCS.get(page_key)
    if base_doc:
        documents.append(base_doc)

    for doc in LOCAL_TEMPLATE_DOCS:
        if doc.get("page") == page_key:
            if base_doc and doc.get("slug") == base_doc.get("slug"):
                continue
            documents.append(doc)
    return documents[:5]


def _ensure_context_collection_seeded() -> None:
    """Populate the context collection with sample data on first access."""
    global _context_seed_attempted
    if _context_seed_attempted:
        return
    try:
        seed_sample_data()
    except Exception as exc:  # pragma: no cover - defensive logging
        print(f"[ContextSeed] Unable to seed sample documents: {exc}")
    finally:
        _context_seed_attempted = True


def _get_manual_context_collection():
    """Lazy-load the MongoDB collection that stores static website sections."""
    global _context_collection
    if _context_collection is not None:
        return _context_collection

    _ensure_context_collection_seeded()
    collection = get_context_collection()
    if not collection:
        print("[ContextSearch] Context collection unavailable; skipping manual injection.")
        return None

    _context_collection = collection
    return _context_collection



def generate_manual_context_answer(user_message: str, user_id: str = "guest") -> Optional[str]:
    """
    Generate answer using manual context injection from MongoDB and local templates.
    Enhanced with better ranking, context aggregation, and relevance filtering.
    """
    collection = _get_manual_context_collection()
    
    # Search MongoDB with improved scoring
    all_candidates: List[Tuple[Dict[str, str], float]] = []
    if collection:
        try:
            # Try to find multiple relevant documents, not just one
            match = find_relevant_content(user_message, collection, minimum_score=0.08)
            if match:
                all_candidates.append(match)
                # If we found a good match, try to find more related documents
                if match[1] > 0.15:  # Good match found
                    # Search for additional documents from same page/topic
                    try:
                        best_doc = match[0]
                        page = best_doc.get("page", "")
                        if page:
                            # Find related documents from same page
                            related_docs = collection.find(
                                {"page": page, "slug": {"$ne": best_doc.get("slug", "")}},
                                {"_id": False, "slug": True, "title": True, "page": True, "content": True, "tags": True},
                                limit=3
                            )
                            for doc in related_docs:
                                score = score_document(user_message, doc)
                                if score >= 0.08:
                                    all_candidates.append((doc, score))
                    except Exception as e:
                        print(f"[ContextSearch] Related document search error: {e}")
        except Exception as e:
            print(f"[ContextSearch] MongoDB search error: {e}")
    
    # Search local templates with improved ranking
    try:
        if not LOCAL_TEMPLATE_DOCS:
            _load_local_template_contexts()
        local_results = rank_documents(
            user_message,
            LOCAL_TEMPLATE_DOCS,
            minimum_score=max(0.08, LOCAL_TEMPLATE_MIN_SCORE),  # Use higher of the two
            top_k=7,  # Increased to get more context
        )
        all_candidates.extend(local_results)
    except Exception as e:
        print(f"[ContextSearch] Local template search error: {e}")
    
    # Try page-based selection as fallback (only if no candidates)
    if not all_candidates:
        entry = _select_relevant_page(user_message)
        if entry:
            page_key = _get_page_key_for_route(entry["path"])
            for doc in _get_documents_for_page(page_key):
                all_candidates.append((doc, LOCAL_TEMPLATE_MIN_SCORE))
    
    if not all_candidates:
        return None
    
    # Sort all candidates by score and take top documents
    all_candidates.sort(key=lambda x: x[1], reverse=True)
    
    # Filter out low-quality matches and take top 5-7
    top_documents = [c for c in all_candidates[:7] if c[1] >= 0.08]
    
    if not top_documents:
        return None
    
    # Aggregate content from documents with better deduplication
    context_chunks = []
    seen_slugs = set()
    seen_content_hashes = set()
    total_context_length = 0
    max_context_length = 3000  # Limit total context to avoid token limits
    
    for doc, score in top_documents:
        slug = doc.get("slug", "")
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        
        content = (doc.get("content") or "").strip()
        if not content or len(content) < 30:
            continue
        
        # Deduplicate by content hash (first 100 chars)
        content_hash = hash(content[:100])
        if content_hash in seen_content_hashes:
            continue
        seen_content_hashes.add(content_hash)
        
        # Truncate very long content
        if len(content) > 800:
            content = content[:797] + "..."
        
        # Check if adding this would exceed limit
        if total_context_length + len(content) > max_context_length:
            # Add partial content if we have space
            remaining = max_context_length - total_context_length
            if remaining > 100:
                content = content[:remaining] + "..."
            else:
                break
        
        # Include title for better context
        title = doc.get("title", "")
        if title:
            context_chunks.append(f"[{title}]\n{content}")
        else:
            context_chunks.append(content)
        
        total_context_length += len(content)
    
    if not context_chunks:
        return None
    
    # Combine contexts with better formatting
    combined_context = "\n\n---\n\n".join(context_chunks)
    
    # Enhanced prompt for better utilization of website content
    prompt = (
        "You are TCC Assistant chatbot for Tanauan City College.\n"
        "Answer ONLY about TCC using this information from the college website:\n\n"
        f"{combined_context}\n\n"
        f"User Question: {user_message}\n\n"
        "Instructions:\n"
        "- Provide a clear, helpful, and accurate answer based on the provided information.\n"
        "- If the information doesn't fully answer the question, provide what you can and suggest contacting the relevant office.\n"
        "- Keep your answer concise (2-4 sentences) unless more detail is needed.\n"
        "- Use natural, friendly language appropriate for a college chatbot.\n"
        "- If multiple pieces of information are relevant, synthesize them into a coherent answer."
    )

    start_time = time.perf_counter()
    answer = call_openai_with_prompt(
        prompt,
        temperature=0.2,
        max_tokens=400,  # Increased for better answers
        user_id=user_id,
        timeout=25.0,  # 25 second timeout for context search
    )
    duration = time.perf_counter() - start_time
    
    if answer:
        print(
            f"[ContextSearch] Answer in {duration:.2f}s "
            f"({len(context_chunks)} docs, best score: {top_documents[0][1]:.3f})"
        )
    else:
        print(f"[ContextSearch] No answer in {duration:.2f}s")
    
    if not answer:
        return None

    return answer.strip()


def generate_live_site_answer(question: str, user_id: str = "guest") -> Optional[str]:
    """
    Fetch the most relevant website page, extract its content, and ask GPT-4o-mini
    to answer the user's question based on the live text.
    """
    entry = _select_relevant_page(question)
    page_data = None
    if entry:
        page_data = _fetch_page_text(entry["path"])

    if not page_data:
        local_context_answer = answer_from_local_templates(question, user_id=user_id)
        if local_context_answer:
            return local_context_answer
        script_answer = answer_from_local_templates(question, user_id=user_id)
        if script_answer:
            return script_answer
        if not entry:
            print("[WebsiteQA] No relevant page found; skipping live lookup.")
            return None
        return None

    user_prompt = (
        f"User question: {question}\n\n"
        f"Website page: {page_data['url']}\n"
        f"Visible text:\n{page_data['text']}"
    )

    start_time = time.perf_counter()
    content = call_openai_with_prompt(
        user_prompt,
        temperature=0.1,
        max_tokens=300,
        user_id=user_id,
        timeout=25.0,  # 25 second timeout for live site answer
    )
    duration = time.perf_counter() - start_time
    print(
        f"[WebsiteQA] GPT response generated in {duration:.2f}s "
        f"(page source: {page_data['source']})"
    )
    if not content:
        return None

    answer = content.strip()
    if not answer:
        return None

    # Return answer without source citation
    return answer


def answer_from_local_templates(question: str, user_id: str = "guest") -> Optional[str]:
    """
    Search local template files and generate answer using GPT.
    Enhanced with better ranking and context aggregation.
    """
    if not LOCAL_TEMPLATE_DOCS:
        _load_local_template_contexts()

    # Get candidates with improved minimum score
    ranked = rank_documents(
        question,
        LOCAL_TEMPLATE_DOCS,
        minimum_score=max(0.08, LOCAL_TEMPLATE_MIN_SCORE),  # Use higher threshold
        top_k=7,  # Increased for more context
    )

    if ranked and ranked[0][1] >= max(0.08, LOCAL_TEMPLATE_MIN_SCORE):
        candidate_docs = ranked
    else:
        candidate_docs: List[Tuple[Dict[str, str], float]] = []
        entry = _select_relevant_page(question)
        if entry:
            page_key = _get_page_key_for_route(entry["path"])
            page_documents = _get_documents_for_page(page_key)
            candidate_docs = [(doc, LOCAL_TEMPLATE_MIN_SCORE) for doc in page_documents]
        if not candidate_docs:
            return None
        candidate_docs = candidate_docs[:7]  # Increased
        ranked = candidate_docs

    # Aggregate content with improved deduplication
    context_chunks = []
    seen_content = set()
    seen_slugs = set()
    total_length = 0
    max_length = 3000
    
    for doc, score in ranked:
        slug = doc.get("slug", "")
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        
        content = doc.get("content", "").strip()
        if len(content) < 30:
            continue
        
        # Better deduplication
        content_hash = hash(content[:100])
        if content_hash in seen_content:
            continue
        seen_content.add(content_hash)
        
        # Truncate long content
        if len(content) > 800:
            content = content[:797] + "..."
        
        # Check length limit
        if total_length + len(content) > max_length:
            remaining = max_length - total_length
            if remaining > 100:
                content = content[:remaining] + "..."
            else:
                break
        
        # Include title for context
        title = doc.get("title", "")
        if title:
            context_chunks.append(f"[{title}]\n{content}")
        else:
            context_chunks.append(content)
        
        total_length += len(content)

    if not context_chunks:
        return None

    # Combine contexts
    context_text = "\n\n---\n\n".join(context_chunks)

    # Enhanced prompt for better utilization of website content
    prompt = (
        "You are TCC Assistant chatbot for Tanauan City College.\n"
        "Answer ONLY about TCC using this information from the college website:\n\n"
        f"{context_text}\n\n"
        f"User Question: {question}\n\n"
        "Instructions:\n"
        "- Provide a clear, helpful, and accurate answer based on the provided information.\n"
        "- If the information doesn't fully answer the question, provide what you can and suggest contacting the relevant office.\n"
        "- Keep your answer concise (2-4 sentences) unless more detail is needed.\n"
        "- Use natural, friendly language appropriate for a college chatbot.\n"
        "- If multiple pieces of information are relevant, synthesize them into a coherent answer."
    )

    start_time = time.perf_counter()
    answer = call_openai_with_prompt(
        prompt,
        temperature=0.2,
        max_tokens=300,
        user_id=user_id,
        timeout=25.0,  # 25 second timeout for local template answer
    )
    duration = time.perf_counter() - start_time
    
    if answer:
        print(
            f"[LocalTemplates] Answer in {duration:.2f}s "
            f"({len(context_chunks)} docs, score: {ranked[0][1]:.3f})"
        )
        return answer.strip()

    print(f"[LocalTemplates] No answer in {duration:.2f}s")
    return None


def get_tcc_guarded_response(user_message: str, user_id: str = "guest") -> str:
    """
    Generate a GPT-backed response that strictly adheres to the TCC domain guard.
    """
    if not user_message:
        return DOMAIN_REFUSAL_MESSAGE

    manual_answer = generate_manual_context_answer(user_message, user_id=user_id)
    if manual_answer:
        return manual_answer

    if not LOCAL_TEMPLATE_DOCS:
        _load_local_template_contexts()

    local_template_answer = answer_from_local_templates(user_message, user_id=user_id)
    if local_template_answer:
        return local_template_answer

    live_answer = generate_live_site_answer(user_message, user_id=user_id)
    if live_answer:
        return live_answer

    fallback_answer = call_openai_with_prompt(
        user_message,
        temperature=0.2,
        max_tokens=300,
        user_id=user_id,
        timeout=25.0,  # 25 second timeout for fallback answer
    )
    if fallback_answer:
        return fallback_answer

    return DOMAIN_REFUSAL_MESSAGE

def get_user_current_office(user_id):
    """Get the current office context for a user"""
    if user_id not in user_contexts:
        return None
    return user_contexts[user_id].get("current_office")

def set_user_current_office(user_id, office_tag):
    """Set the current office context for a user"""
    if user_id not in user_contexts:
        user_contexts[user_id] = {"current_office": None, "offices": {}}
    user_contexts[user_id]["current_office"] = office_tag
    # Initialize office context if not exists
    if office_tag and office_tag not in user_contexts[user_id]["offices"]:
        user_contexts[user_id]["offices"][office_tag] = {"messages": [], "last_intent": None}

def detect_office_from_message(msg):
    """
    Detect which office the user is asking about based on comprehensive keyword matching
    Returns office tag (e.g., 'admission_office') or None
    """
    msg_lower = msg.lower()
    
    # ✅ ADMISSION OFFICE - Enhanced patterns
    admission_keywords = [
        'admission', 'apply', 'applying', 'enroll', 'enrollment', 'application',
        'transferee', 'transferees', 'requirements', 'requirement', 'psa',
        "voter's certificate", 'form 137', 'form 138', 'deadline', 'period',
        'graduate programs', 'masteral', 'programs offered', 'courses available',
        'offered courses', 'available programs', 'how to apply', 'how to enroll',
        'incoming first-year', 'first year', 'freshmen'
    ]
    admission_score = sum(1 for keyword in admission_keywords if keyword in msg_lower)
    
    # ✅ REGISTRAR'S OFFICE - Enhanced patterns  
    registrar_keywords = [
        'registrar', 'transcript', 'tor', 'transcript of records', 'grades', 
        'academic records', 'documents', 'document', 'claiming', 'claim',
        'certificate', 'certification', 'certified copy', 'tuition fee',
        'tuition', 'free tuition', 'slots', 'available slots', 'entrance exam',
        'psychological test', 'student portal', 'form 137', 'good moral',
        'valid id', 'authorization letter', 'graduation'
    ]
    registrar_score = sum(1 for keyword in registrar_keywords if keyword in msg_lower)
    
    # ✅ ICT OFFICE - Enhanced patterns
    ict_keywords = [
        'ict', 'e-hub', 'ehub', 'tcc ehub', 'tcc e-hub', 'password', 'username',
        'student id', 'login', 'login attempts', 'failed login', 'account locked',
        'deactivated account', 'recovery email', 'forgot password', 'password reset',
        'reset password', 'student portal', 'access', 'locked out', 'misu',
        'qr code', 'web browser', 'update button', 'my account'
    ]
    ict_score = sum(1 for keyword in ict_keywords if keyword in msg_lower)
    
    # ✅ GUIDANCE OFFICE - Enhanced patterns
    guidance_keywords = [
        'guidance', 'counseling', 'counselor', 'scholarship', 'career advice',
        'career guidance', 'personal counseling', 'academic counseling',
        'financial aid', 'mental health', 'psychological', 'stress',
        'study habits', 'time management', 'goal setting', 'resume',
        'interview preparation', 'job placement', 'internship', 'career assessment',
        'academic planning', 'course selection', 'career opportunities',
        'job search', 'graduate school preparation', 'personal problems',
        'peer counseling', 'academic difficulties'
    ]
    guidance_score = sum(1 for keyword in guidance_keywords if keyword in msg_lower)
    
    # ✅ OSA OFFICE - Enhanced patterns
    osa_keywords = [
        'osa', 'student affairs', 'office of student affairs', 'clubs', 
        'organizations', 'student activities', 'activities', 'discipline',
        'student government', 'extracurricular', 'sports', 'cultural events',
        'leadership programs', 'student council', 'campus events',
        'social activities', 'volunteer', 'community service', 'student handbook',
        'code of conduct', 'disciplinary', 'student rights', 'campus policies',
        'event planning', 'organization registration', 'club membership'
    ]
    osa_score = sum(1 for keyword in osa_keywords if keyword in msg_lower)
    
    # Find office with highest score (must have at least 1 match)
    scores = {
        'admission_office': admission_score,
        'registrar_office': registrar_score,
        'ict_office': ict_score,
        'guidance_office': guidance_score,
        'osa_office': osa_score
    }
    
    max_score = max(scores.values())
    if max_score > 0:
        # Return the office with highest score
        detected_office = max(scores, key=scores.get)
        print(f"🎯 Office detected: {detected_office} (score: {max_score})")
        return detected_office
    
    return None

def save_message(user_id, sender, message, detected_office=None):
    """Save message to MongoDB with error handling and office detection"""
    global mongo_client, db, conversations
    
    if conversations is None:
        print("MongoDB not available. Message not saved to database.")
        return False
    
    # Determine office based on context or detection
    office = None
    
    # First check if office was explicitly provided
    if detected_office:
        office = office_tags.get(detected_office, detected_office)
    
    # If no office provided, check user context
    else:
        current_office = get_user_current_office(user_id)
        if current_office:
            office = office_tags.get(current_office)
    
    # If still no office, try to detect from message content
    if not office and sender == "user":
        detected_tag = detect_office_from_message(message)
        if detected_tag:
            office = office_tags.get(detected_tag)
    
    # Default to General if no office detected
    if not office:
        office = "General"
    
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Use UTC datetime for accurate timestamp
            timestamp = datetime.now(UTC)
            # Create document with office field and proper UTC timestamp
            document = {
                "user": user_id,
                "sender": sender,
                "message": message,
                "office": office,
                "timestamp": timestamp,  # UTC datetime object
                "date": timestamp.isoformat()  # ISO string for backward compatibility
            }
            
            conversations.insert_one(document)
            return True
            
        except (ServerSelectionTimeoutError, ConnectionFailure) as e:
            retry_count += 1
            print(f"MongoDB connection error (attempt {retry_count}/{max_retries}): {e}")
            
            if retry_count < max_retries:
                print("Retrying in 2 seconds...")
                time.sleep(2)
                
                # Try to reconnect
                mongo_client = create_mongo_connection()
                if mongo_client:
                    db = mongo_client["chatbot_db"]
                    conversations = db["conversations"]
                else:
                    break
            else:
                print("Failed to save message after all retries")
                return False
                
        except Exception as e:
            print(f"Unexpected error saving message: {e}")
            return False
    
    return False

def _maybe_save(user_id, sender, message, detected_office=None, save=True):
    if save:
        try:
            return save_message(user_id, sender, message, detected_office)
        except Exception as _e:
            print(f"[warn] save skipped due to error: {_e}")
    return False

def clear_chat_history(user):
    """Clear all chat history for a specific user"""
    global conversations
    
    if conversations is None:
        print("MongoDB not available. Cannot clear chat history.")
        return 0
    
    try:
        result = conversations.delete_many({"user": user})
        return result.deleted_count
    except Exception as e:
        print(f"Error clearing chat history: {e}")
        return 0

def get_active_announcements():
    """Get all active announcements from MongoDB only, sorted by priority and date"""
    all_announcements = []
    
    # Get announcements from MongoDB collections only
    try:
        if sub_announcements_collection is not None:
            # Fetch sub-admin announcements
            sub_announcements = list(sub_announcements_collection.find({"status": "active"}))
            for ann in sub_announcements:
                # Convert MongoDB format to consistent format
                all_announcements.append({
                    "id": str(ann.get("_id")),
                    "title": ann.get("title", ""),
                    "message": ann.get("description", ""),
                    "date": ann.get("start_date", ""),
                    "priority": ann.get("priority", "medium"),
                    "category": ann.get("office", "general"),
                    "office": ann.get("office", "General"),
                    "active": True,
                    "source": "mongodb",
                    "created_by": ann.get("created_by", "")
                })
        
        if admin_announcements_collection is not None:
            # Fetch admin announcements
            admin_announcements = list(admin_announcements_collection.find({"status": "active"}))
            for ann in admin_announcements:
                all_announcements.append({
                    "id": str(ann.get("_id")),
                    "title": ann.get("title", ""),
                    "message": ann.get("description", ""),
                    "date": ann.get("start_date", ""),
                    "priority": ann.get("priority", "medium"),
                    "category": ann.get("office", "general"),
                    "office": ann.get("office", "General"),
                    "active": True,
                    "source": "mongodb",
                    "created_by": ann.get("created_by", "")
                })
    except Exception as e:
        print(f"Error fetching announcements from MongoDB: {e}")
        import traceback
        traceback.print_exc()
    
    # Sort by priority (high, medium, low) then by date (newest first)
    priority_order = {"high": 0, "medium": 1, "low": 2}
    all_announcements.sort(
        key=lambda x: (priority_order.get(x.get("priority", "medium"), 1), x.get("date", "")),
        reverse=True  # Newest first
    )
    
    print(f"Loaded {len(all_announcements)} active announcements from MongoDB")
    return all_announcements

def format_announcements_response():
    """Format announcements for chatbot response"""
    announcements = get_active_announcements()
    
    if not announcements:
        return "There are no active announcements at this time."
    
    response = "Latest College Announcements:\n\n"
    
    for i, ann in enumerate(announcements[:3], 1):  # Show top 3 announcements
        priority_emoji = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}
        priority = priority_emoji.get(ann.get("priority", "medium"), "[INFO]")
        
        response += f"{priority} {ann['title']}\n"
        response += f"Date: {ann['date']}\n"
        response += f"{ann['message']}\n\n"
    
    if len(announcements) > 3:
        response += f"And {len(announcements) - 3} more announcements available..."
    
    return response

def search_announcements_with_vector(query):
    """Search announcements using vector similarity from Pinecone with enhanced formatting"""
    # Search in Pinecone for announcements
    try:
        vector_results = vector_store.search_similar(
            query, 
            top_k=5,  # Increased from 3 to show more results
            filter_dict={
                "$or": [
                    {"type": {"$eq": "announcement"}},
                    {"intent_type": {"$eq": "announcement"}}
                ]
            },
            score_threshold=0.5  # Lowered threshold to catch more relevant results
        )
        
        if not vector_results:
            # Fallback to traditional search
            return format_announcements_response()
        
        # Enhanced header with decorative line
        response = "╔═══════════════════════════════════════╗\n"
        response += "║     📢 COLLEGE ANNOUNCEMENTS 📢      ║\n"
        response += "╚═══════════════════════════════════════╝\n\n"
        response += f"Found {len(vector_results)} relevant announcement(s) for your query.\n\n"
        
        for idx, result in enumerate(vector_results, 1):
            metadata = result['metadata']
            
            # Priority styling with emojis
            priority_emoji = {
                "high": "🔴 [HIGH PRIORITY]", 
                "medium": "🟡 [MEDIUM PRIORITY]", 
                "low": "🟢 [LOW PRIORITY]"
            }
            priority = priority_emoji.get(metadata.get("priority", "medium").lower(), "ℹ️ [INFO]")
            
            # Extract metadata
            title = metadata.get('title', metadata.get('text', 'Untitled')).strip()
            description = metadata.get('description', metadata.get('text', 'No description available')).strip()
            office = metadata.get('office', metadata.get('category', 'General'))
            start_date = metadata.get('start_date', metadata.get('date', 'N/A'))
            created_by = metadata.get('created_by', '')
            
            # Format each announcement with enhanced styling
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"📌 ANNOUNCEMENT #{idx}\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            response += f"{priority}\n"
            response += f"📋 Title: {title}\n\n"
            
            response += f"📍 Office: {office}\n"
            response += f"📅 Date: {start_date}\n"
            
            if created_by:
                response += f"👤 Posted by: {created_by}\n"
            
            response += f"🎯 Relevance: {result['score']:.0%}\n\n"
            
            # Format description with better readability
            response += f"📝 Details:\n"
            # Truncate long descriptions
            if len(description) > 300:
                description = description[:297] + "..."
            response += f"{description}\n\n"
        
        # Footer with helpful tip
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += "💡 Tip: Click the 📢 button in the chat header to view all announcements!\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        return response
        
    except Exception as e:
        print(f"Error searching announcements with vector: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to traditional format
        return format_announcements_response()

def get_context_switch_response(current_context, requested_office, user_id):
    """Generate context switch response"""
    office_name = office_tags.get(requested_office, "that office")
    current_office_name = office_tags.get(current_context, "the current topic")
    
    response = f"I think you might be asking about the {office_name}. Right now, I can only assist you with {current_office_name} concerns. Would you like me to connect you to the {office_name} information instead?"
    
    return response

def get_vector_enhanced_response(msg, predicted_tag, confidence):
    """Get enhanced response using vector search"""
    # Search for similar patterns
    vector_results = vector_store.search_similar(msg, top_k=3)
    
    if not vector_results:
        return None
    
    # Check if vector search provides better results
    best_vector_match = vector_results[0]
    
    # If vector search has high confidence and different tag, consider it
    if best_vector_match['score'] > 0.8 and best_vector_match['score'] > confidence:
        vector_tag = best_vector_match['metadata'].get('tag')
        if vector_tag and vector_tag != predicted_tag:
            # Use vector search result
            for intent in intents["intents"]:
                if intent["tag"] == vector_tag:
                    return {
                        'tag': vector_tag,
                        'responses': intent['responses'],
                        'method': 'vector_search',
                        'confidence': best_vector_match['score']
                    }
    
    return None

def search_faq_database(query, office=None):
    """
    Search FAQ database in Pinecone
    Returns the FAQ answer if a match is found, otherwise None
    """
    if not vector_store or not vector_store.index:
        return None
    
    try:
        # Generate query embedding
        query_embedding = vector_store.embedding_model.encode(query)
        
        # Build filter for FAQs
        filter_dict = {
            'type': {'$eq': 'faq'},
            'status': {'$eq': 'published'}
        }
        
        if office:
            filter_dict['office'] = {'$eq': office}
        
        # Search in Pinecone
        results = vector_store.index.query(
            vector=query_embedding.tolist(),
            top_k=3,
            filter=filter_dict,
            include_metadata=True
        )
        
        # Return best match if score is good enough
        if results.matches and len(results.matches) > 0:
            best = results.matches[0]
            if best.score >= 0.70:  # 70% similarity threshold
                print(f"✅ FAQ found: {best.metadata.get('question', 'N/A')} (score: {best.score:.3f})")
                return best.metadata.get('answer', None)
        
        return None
    except Exception as e:
        print(f"FAQ search error: {e}")
        return None

def get_fallback_response(msg, user_id="guest"):
    """Simple fallback response when model is not available"""
    msg_lower = msg.lower()
    
    # Simple keyword matching
    if any(word in msg_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon"]):
        return "Hello! Welcome to TCC Assistant. How can I help you today?"
    elif any(word in msg_lower for word in ["help", "assist", "support"]):
        return "I'm here to help! You can ask me about admissions, registrar services, ICT support, guidance, or student affairs."
    elif any(word in msg_lower for word in ["admission", "apply", "enroll"]):
        return "For admission inquiries, please contact the Admissions Office. They can help with requirements and application procedures."
    elif any(word in msg_lower for word in ["registrar", "transcript", "grades"]):
        return "The Registrar's Office handles academic records and transcripts. Please visit them for document requests."
    elif any(word in msg_lower for word in ["ict", "password", "login", "portal"]):
        return "For ICT support and password issues, please contact the ICT Office. They can help with student portal access."
    elif any(word in msg_lower for word in ["guidance", "counseling", "scholarship"]):
        return "The Guidance Office provides counseling services and scholarship information. Visit them for career guidance."
    elif any(word in msg_lower for word in ["osa", "student affairs", "clubs", "activities"]):
        return "The Office of Student Affairs manages student activities and clubs. Contact them for organization information."
    elif any(word in msg_lower for word in ["thank", "thanks", "salamat"]):
        return "You're welcome! Feel free to ask if you need more help."
    elif any(word in msg_lower for word in ["bye", "goodbye", "see you"]):
        return "Goodbye! Have a great day!"
    else:
        return "I'm TCC Assistant! I can help you with information about admissions, registrar services, ICT support, guidance, and student affairs. What would you like to know?"

def get_response(msg, user_id="guest", save_messages=True):
    """
    Get chatbot response.
    
    Args:
        msg: User message
        user_id: User identifier
        save_messages: Whether to save messages to database
    """
    # Lazy load model if not already loaded
    global model, hybrid_model, all_words, tags
    if model is None or hybrid_model is None or not model_loaded:
        model, hybrid_model, all_words, tags = load_models_if_needed()
    
    # Check if model is available, use fallback if not
    if model is None or hybrid_model is None:
        print("⚠️ Using fallback response (model not available)")
        return get_fallback_response(msg, user_id)
    
    # Enhanced text preprocessing with error handling
    try:
        cleaned_msg = clean_text(msg)
        sentence = tokenize(cleaned_msg)
        
        # Expand with synonyms for better matching
        expanded_msg = expand_synonyms(cleaned_msg)
        expanded_sentence = tokenize(expanded_msg)
    except Exception as e:
        print(f"⚠️ Text preprocessing failed: {e}, using fallback")
        # Use simple fallback tokenization
        cleaned_msg = msg.lower().strip()
        sentence = cleaned_msg.split()
        expanded_msg = cleaned_msg
        expanded_sentence = sentence
    
    # Detect office from message for context
    detected_office = detect_office_from_message(msg)
    
    # Save user message with office context
    _maybe_save(user_id, "user", msg, detected_office, save=save_messages)
    
    # If office is detected, prioritize office-specific responses
    if detected_office:
        # Check if we have current context and it matches detected office
        current_context = get_user_current_office(user_id)
        if not current_context or current_context != detected_office:
            set_user_current_office(user_id, detected_office)

    # Check if user is asking to switch context or confirming switch
    msg_lower = msg.lower()
    if any(word in msg_lower for word in ['yes', 'switch', 'connect', 'change']):
        # User wants to switch context
        requested_office = detect_office_from_message(msg)
        if requested_office:
            set_user_current_office(user_id, requested_office)
            bot_response = f"Great! I've switched to help you with {office_tags[requested_office]} information. How can I assist you?"
            _maybe_save(user_id, "bot", bot_response, requested_office, save=save_messages)
            return bot_response

    # Detect which office the user is asking about
    requested_office = detect_office_from_message(msg)
    
    # Check if user has an active context
    current_context = get_user_current_office(user_id)
    
    # If user is asking about a different office than current context
    if current_context and requested_office and requested_office != current_context:
        bot_response = get_context_switch_response(current_context, requested_office, user_id)
        _maybe_save(user_id, "bot", bot_response, current_context, save=save_messages)
        return bot_response
    
    # ============= SEARCH FAQ DATABASE (with early exit) =============
    # Map office tags to office names
    office_name_map = {
        'registrar_office': "Registrar's Office",
        'admission_office': "Admission Office",
        'guidance_office': "Guidance Office",
        'ict_office': "ICT Office",
        'osa_office': "Office of the Student Affairs (OSA)"
    }
    
    # Try FAQ search with detected office first (most likely to match)
    faq_answer = None
    if detected_office and detected_office in office_name_map:
        faq_answer = search_faq_database(cleaned_msg, office=office_name_map[detected_office])
        if faq_answer:
            office_context = detected_office
            _maybe_save(user_id, "bot", faq_answer, office_context, save=save_messages)
            return faq_answer  # Early exit
    
    # Try FAQ search with current context office
    if current_context and current_context in office_name_map:
        faq_answer = search_faq_database(cleaned_msg, office=office_name_map[current_context])
        if faq_answer:
            office_context = current_context
            _maybe_save(user_id, "bot", faq_answer, office_context, save=save_messages)
            return faq_answer  # Early exit
    
    # Try general FAQ search (all offices) - only if no office-specific match
    faq_answer = search_faq_database(cleaned_msg, office=None)
    if faq_answer:
        office_context = detected_office if detected_office else current_context
        _maybe_save(user_id, "bot", faq_answer, office_context, save=save_messages)
        return faq_answer  # Early exit
    # ============= END FAQ SEARCH =============
    
    # Use hybrid model for prediction with enhanced features
    if hybrid_model and all_words:
        # Prepare input for neural network with enhanced bag of words
        X = enhanced_bag_of_words(expanded_sentence, all_words)
        X = torch.from_numpy(X).unsqueeze(0)
        
        # Get current context for better prediction
        current_context = get_user_current_office(user_id)
        
        # Get hybrid prediction with context
        hybrid_result = hybrid_model.get_hybrid_response(cleaned_msg, X, current_context)
        
        tag = hybrid_result['final_tag']
        confidence = hybrid_result['confidence']
        
        print(f"Hybrid prediction: tag={tag}, confidence={confidence:.3f}, method={hybrid_result['response_source']}")
        
        # High confidence threshold for proceeding
        if confidence > 0.7 and tag:
            # PRIORITY 1: If office is detected from message, prioritize office-specific responses
            if detected_office:
                for intent in intents["intents"]:
                    if intent["tag"] == detected_office:
                        # Use office-specific responses based on detected office
                        bot_response = random.choice(intent["responses"])
                        _maybe_save(user_id, "bot", bot_response, detected_office, save=save_messages)
                        return bot_response
            
            # PRIORITY 2: Handle the predicted tag normally
            for intent in intents["intents"]:
                if tag == intent["tag"]:
                    # Handle announcements with vector search
                    if tag == "announcements":
                        # Use vector search for more relevant announcements
                        if vector_store.index:
                            bot_response = search_announcements_with_vector(cleaned_msg)
                        else:
                            bot_response = format_announcements_response()
                        _maybe_save(user_id, "bot", bot_response, None, save=save_messages)  # Announcements are general
                    else:
                        # Set user context based on the detected office
                        if tag in office_tags:
                            set_user_current_office(user_id, tag)
                        
                        # ✅ ONLY reset context on goodbye (not greeting/thanks as they can happen mid-conversation)
                        if tag in ['goodbye']:
                            reset_user_context(user_id)
                            print(f"🔄 Context reset for user '{user_id}' due to goodbye intent")
                        
                        # Choose response - prioritize vector search if available
                        if hybrid_result['vector_results'] and hybrid_result['response_source'] == 'vector_search':
                            # Use similar response from vector database
                            similar_responses = hybrid_result['vector_results']
                            if similar_responses:
                                best_match = similar_responses[0]
                                if best_match['metadata'].get('intent_type') == 'response':
                                    bot_response = best_match['text']
                                else:
                                    bot_response = random.choice(intent["responses"])
                            else:
                                bot_response = random.choice(intent["responses"])
                        else:
                            bot_response = random.choice(intent["responses"])
                        
                        # Save bot response with appropriate office context
                        office_context = tag if tag in office_tags else None
                        _maybe_save(user_id, "bot", bot_response, office_context, save=save_messages)
                    
                    return bot_response
    
    # Fallback to vector search only (but still prioritize detected office)
    if detected_office:
        # If we detected an office but hybrid model didn't work, use office-specific responses
        for intent in intents["intents"]:
            if intent["tag"] == detected_office:
                bot_response = random.choice(intent["responses"])
                _maybe_save(user_id, "bot", bot_response, detected_office, save=save_messages)
                return bot_response
    
    # If no office detected, fall back to vector search
    if vector_store.index:
        vector_results = vector_store.search_similar(cleaned_msg, top_k=3, score_threshold=0.6)
        
        if vector_results:
            best_match = vector_results[0]
            tag = best_match['metadata'].get('tag')
            
            if tag:
                for intent in intents["intents"]:
                    if intent["tag"] == tag:
                        if tag in office_tags:
                            set_user_current_office(user_id, tag)
                        
                        bot_response = random.choice(intent["responses"])
                        office_context = tag if tag in office_tags else None
                        _maybe_save(user_id, "bot", bot_response, office_context, save=save_messages)
                        return bot_response
    
    # Manual context injection via MongoDB (keyword/fuzzy search)
    contextual_answer = None
    try:
        contextual_answer = generate_manual_context_answer(msg, user_id=user_id)
    except Exception as e:
        print(f"[ContextSearch] Unexpected error: {e}")
        contextual_answer = None

    if contextual_answer:
        office_context = detected_office if detected_office in office_tags else None
        _maybe_save(user_id, "bot", contextual_answer, office_context, save=save_messages)
        return contextual_answer

    # Live website lookup as a final intelligent fallback
    live_answer = None
    try:
        live_answer = generate_live_site_answer(msg, user_id=user_id)
    except Exception as e:
        print(f"[WebsiteQA] Unexpected error during live lookup: {e}")
        live_answer = None

    if live_answer:
        office_context = detected_office if detected_office in office_tags else None
        _maybe_save(user_id, "bot", live_answer, office_context, save=save_messages)
        return live_answer
    
    # Last resort: Try FAQ search with lower threshold
    try:
        query_embedding = vector_store.embedding_model.encode(cleaned_msg)
        results = vector_store.index.query(
            vector=query_embedding.tolist(),
            top_k=3,
            filter={'type': {'$eq': 'faq'}, 'status': {'$eq': 'published'}},
            include_metadata=True
        )
        if results.matches and len(results.matches) > 0:
            best = results.matches[0]
            if best.score >= 0.60:  # Lower threshold for last resort
                print(f"✅ Last resort FAQ found: {best.metadata.get('question', 'N/A')} (score: {best.score:.3f})")
                faq_answer = best.metadata.get('answer', None)
                if faq_answer:
                    office_context = None
                    for tag, name in office_name_map.items():
                        if name == best.metadata.get('office'):
                            office_context = tag
                            break
                    _maybe_save(user_id, "bot", faq_answer, office_context, save=save_messages)
                    return faq_answer
    except Exception as e:
        print(f"Last resort FAQ search error: {e}")
    
    # Enhanced fallback with fuzzy matching
    if current_context:
        office_name = office_tags[current_context]
        
        # Try fuzzy matching with current context patterns
        context_patterns = []
        for intent in intents["intents"]:
            if intent["tag"] == current_context:
                context_patterns.extend(intent["patterns"])
                break
        
        if context_patterns:
            fuzzy_matches = fuzzy_match(cleaned_msg, context_patterns, threshold=0.4)
            if fuzzy_matches:
                best_match = fuzzy_matches[0]
                print(f"Fuzzy match found: {best_match[0]} (similarity: {best_match[1]:.3f})")
                bot_response = f"I think you're asking about something related to {office_name}. Could you provide more details about: {best_match[0]}?"
                _maybe_save(user_id, "bot", bot_response, current_context, save=save_messages)
                return bot_response
        
        bot_response = f"I'm currently helping you with {office_name} information. Could you rephrase your question about this office, or would you like to switch to a different topic?"
        _maybe_save(user_id, "bot", bot_response, current_context, save=save_messages)
    else:
        # Try fuzzy matching across all patterns
        all_patterns = []
        for intent in intents["intents"]:
            all_patterns.extend(intent["patterns"])
        
        fuzzy_matches = fuzzy_match(cleaned_msg, all_patterns, threshold=0.3)
        if fuzzy_matches:
            best_match = fuzzy_matches[0]
            print(f"Global fuzzy match found: {best_match[0]} (similarity: {best_match[1]:.3f})")
            bot_response = f"I think you might be asking about: {best_match[0]}. Could you provide more details?"
            _maybe_save(user_id, "bot", bot_response, None, save=save_messages)
            return bot_response
        
        bot_response = DOMAIN_REFUSAL_MESSAGE
        _maybe_save(user_id, "bot", bot_response, None, save=save_messages)
    
    return bot_response

def reset_user_context(user_id, office=None):
    """
    Reset user's conversation context
    
    Args:
        user_id: The user identifier
        office: Optional office tag (e.g., 'admission_office'). 
                If provided, only resets that office's context.
                If None, resets all contexts for the user.
    """
    if user_id not in user_contexts:
        print(f"🔄 No context found for user '{user_id}' - nothing to reset")
        return
    
    # Get current context info for logging
    current_context = user_contexts[user_id]
    print(f"🔍 Context before reset: {current_context}")
    
    if office:
        # ✅ Reset only the specified office's context
        if isinstance(user_contexts[user_id], dict):
            # Check if this is the current office
            current_office = user_contexts[user_id].get("current_office")
            if current_office == office:
                # Clear the current office
                user_contexts[user_id]["current_office"] = None
                print(f"✅ Reset context for user '{user_id}' - Office: {office_tags.get(office, office)} (cleared current office)")
            else:
                print(f"⚠️ Office '{office}' is not the current office (current: {current_office})")
            
            # Also clear from offices dict if it exists
            if "offices" in user_contexts[user_id] and office in user_contexts[user_id]["offices"]:
                user_contexts[user_id]["offices"][office] = {"messages": [], "last_intent": None}
                print(f"✅ Cleared office data for: {office_tags.get(office, office)}")
        else:
            # Old format: string - just clear it if it matches
            if user_contexts[user_id] == office:
                user_contexts.pop(user_id, None)
                print(f"✅ Reset context for user '{user_id}' - Office: {office_tags.get(office, office)}")
    else:
        # ✅ Reset ALL contexts for the user
        if isinstance(user_contexts[user_id], dict):
            current_office = user_contexts[user_id].get("current_office")
            office_count = len(user_contexts[user_id].get("offices", {}))
            user_contexts.pop(user_id, None)
            print(f"✅ Reset ALL contexts for user '{user_id}' (cleared {office_count} office contexts, last office: {current_office})")
        else:
            # Old format
            user_contexts.pop(user_id, None)
            print(f"✅ Reset context for user '{user_id}'")
    
    print(f"🔍 Context after reset: {user_contexts.get(user_id, 'Removed from dictionary')}")

def get_announcement_by_id(announcement_id):
    """Get a specific announcement by ID from MongoDB"""
    try:
        from bson import ObjectId
        if admin_announcements_collection is not None:
            announcement = admin_announcements_collection.find_one({"_id": ObjectId(announcement_id)})
            if announcement:
                return {
                    "id": str(announcement["_id"]),
                    "title": announcement.get("title", ""),
                    "message": announcement.get("description", ""),
                    "date": announcement.get("start_date", ""),
                    "priority": announcement.get("priority", "medium"),
                    "category": announcement.get("office", "general"),
                    "active": announcement.get("status") == "active"
                }
    except Exception as e:
        print(f"Error getting announcement by ID: {e}")
    return None

def add_announcement(title, date, message, priority="medium", category="general"):
    """Add a new announcement to MongoDB and Pinecone"""
    try:
        from bson import ObjectId
        
        # Create announcement document for MongoDB
        announcement_doc = {
            "title": title,
            "description": message,
            "start_date": date,
            "end_date": date,  # Same as start date if not specified
            "priority": priority.lower(),
            "status": "active",
            "office": category,
            "created_by": "System",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "source": "system"
        }
        
        # Save to MongoDB admin_announcements collection
        if admin_announcements_collection is not None:
            result = admin_announcements_collection.insert_one(announcement_doc)
            announcement_id = str(result.inserted_id)
            
            # Create embedding text for Pinecone
            embed_text = f"Title: {title}\nDescription: {message}\nOffice: {category}\nPriority: {priority}\nDate: {date}"
            
            # Store in Pinecone with metadata
            metadata = {
                "type": "announcement",
                "intent_type": "announcement",
                "announcement_id": announcement_id,
                "title": title,
                "description": message,
                "office": category,
                "priority": priority.lower(),
                "start_date": date,
                "end_date": date,
                "status": "active",
                "tag": "announcements"
            }
            
            vector_id = vector_store.store_text(embed_text, metadata)
            
            # Update MongoDB document with vector_id
            admin_announcements_collection.update_one(
                {"_id": result.inserted_id},
                {"$set": {"vector_id": vector_id}}
            )
            
            print(f"Announcement added to MongoDB (ID: {announcement_id}) and Pinecone (Vector ID: {vector_id})")
            
            return {
                "id": announcement_id,
                "title": title,
                "date": date,
                "priority": priority,
                "message": message,
                "category": category,
                "active": True
            }
    except Exception as e:
        print(f"Error adding announcement: {e}")
        import traceback
        traceback.print_exc()
    
    return None

# Health check function
def check_mongodb_connection():
    """Check MongoDB connection status"""
    if mongo_client is None:
        return False
    
    try:
        mongo_client.admin.command('ping')
        return True
    except Exception as e:
        print(f"MongoDB health check failed: {e}")
        return False

def get_chatbot_response(message):
    """
    Simple rules-based chatbot for TCC Assistant.
    Returns appropriate responses based on keyword matching.
    This function provides basic responses without AI/NLP.
    
    Returns:
        dict: {
            'response': str - The chatbot response text
            'status': str - 'resolved', 'unresolved', or 'escalated'
            'office': str - Detected office or 'General'
        }
    """
    message_lower = message.lower()
    office = "General"
    status = "resolved"
    response = ""

    # TCC E-Hub / Portal
    if "tcc e-hub" in message_lower or "ehub" in message_lower or "e-hub" in message_lower:
        response = "You can access TCC E-Hub by searching 'TCC eHub' or scanning the QR code provided in your student guide."
        office = "ICT Office"
        status = "resolved"
    
    # Username queries
    elif "username" in message_lower and ("what" in message_lower or "default" in message_lower):
        response = "Your default username is your Student ID number (e.g., TCC-0000-0000)."
        office = "ICT Office"
        status = "resolved"
    
    # Password queries
    elif "password" in message_lower and not "reset" in message_lower:
        response = "Your password is provided by your department or ICT office upon enrollment."
        office = "ICT Office"
        status = "resolved"
    
    # Password reset
    elif "password" in message_lower and "reset" in message_lower:
        response = "To reset your password, visit the ICT Office at the IT Building, Room 101, or contact them during office hours (8:00 AM - 5:00 PM, Monday to Friday)."
        office = "ICT Office"
        status = "escalated"  # Requires office visit
    
    # Registrar's Office
    elif "registrar" in message_lower:
        response = "The Registrar's Office handles student records and enrollment. Visit the 2nd floor of the Admin Building during office hours (8:00 AM - 5:00 PM, Monday to Friday)."
        office = "Registrar's Office"
        status = "resolved"
    
    # Office hours
    elif "office hours" in message_lower or "open" in message_lower:
        response = "TCC offices are open from 8:00 AM to 5:00 PM, Monday to Friday."
        status = "resolved"
    
    # Admission
    elif "admission" in message_lower or "apply" in message_lower or "enroll" in message_lower:
        response = "For admission and enrollment inquiries, please visit the Admission Office or contact them during office hours. Requirements and application forms are available at the main building."
        office = "Admission Office"
        status = "escalated"  # Requires office visit
    
    # ICT / Technical Support
    elif "ict" in message_lower or "wifi" in message_lower or "internet" in message_lower:
        response = "The ICT Office handles technical support, WiFi issues, and student portal problems. They're located at the IT Building, Room 101."
        office = "ICT Office"
        status = "resolved"
    
    # Guidance Office
    elif "guidance" in message_lower or "counseling" in message_lower or "scholarship" in message_lower:
        response = "The Guidance Office offers counseling services, scholarship information, and career guidance. Visit them at the Main Building, Room 210."
        office = "Guidance Office"
        status = "resolved"
    
    # Student Affairs / OSA
    elif "osa" in message_lower or "student affairs" in message_lower or "clubs" in message_lower or "activities" in message_lower:
        response = "The Office of Student Affairs (OSA) manages student activities, clubs, and organizations. They're at the Student Center, Room 305."
        office = "Office of Student Affairs"
        status = "resolved"
    
    # Greetings
    elif any(word in message_lower for word in ["hello", "hi", "hey", "good morning", "good afternoon", "good evening"]):
        response = "Hello! Welcome to TCC Assistant. How can I help you today?"
        status = "resolved"
    
    # Thank you
    elif "thank" in message_lower or "salamat" in message_lower:
        response = "You're welcome! Have a great day!"
        status = "resolved"
    
    # Goodbye
    elif "bye" in message_lower or "goodbye" in message_lower:
        response = "Goodbye! Feel free to chat with me again anytime."
        status = "resolved"
    
    # Default fallback
    else:
        response = "I'm sorry, I don't have information about that yet. Please try asking about: TCC E-Hub, student portal, office hours, admissions, registrar, ICT support, guidance services, or student affairs."
        status = "unresolved"
    
    return {
        'response': response,
        'status': status,
        'office': office
    }


if __name__ == "__main__":
    print("Enhanced Chatbot with Vector Search is running! Type 'quit' to exit.\n")
    
    # Display connection status
    if check_mongodb_connection():
        print("MongoDB connection is healthy")
    else:
        print("MongoDB connection issues detected - running in limited mode")
    
    print()
    user = "guest"

    while True:
        user_message = input("You: ")
        if user_message.lower() == "quit":
            print("Bot: Goodbye!")
            break

        bot_reply = get_response(user_message, user)
        print(f"Bot: {bot_reply}")