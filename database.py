"""
database.py
--------------
Utility helpers for connecting to MongoDB and managing static website content
used for manual context injection. The module exposes a light-weight interface
for retrieving the dedicated collection that stores scraped page sections and
for seeding example documents during development.
"""

from __future__ import annotations

import os
from typing import Iterable, Optional, Sequence

from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

# Environment-driven configuration with sensible defaults for local testing.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chatbot_db")
CONTEXT_COLLECTION_NAME = os.getenv("CONTEXT_COLLECTION_NAME", "website_sections")
SEED_SAMPLE_CONTEXTS = os.getenv("SEED_SAMPLE_CONTEXTS", "true").lower() in {"1", "true", "yes"}

_mongo_client: Optional[MongoClient] = None

# Small set of sample documents for local development and automated tests.
SAMPLE_CONTEXT_DOCUMENTS = [
    {
        "slug": "home-overview",
        "page": "home",
        "title": "Welcome Message",
        "content": (
            "Welcome to Tanauan City College. We empower minds, build futures, and serve the community "
            "through quality education. Explore our academic programs, modern facilities, and supportive "
            "student services designed to help you thrive."
        ),
        "tags": ["home", "welcome", "overview"],
    },
    {
        "slug": "admissions-overview",
        "page": "admissions",
        "title": "Admission Office Overview",
        "content": (
            "The Admission Office guides applicants through each step of the enrollment process. "
            "We provide accessible, student-centered services that promote inclusivity and academic excellence."
        ),
        "tags": ["admissions", "enrollment", "office"],
    },
    {
        "slug": "admissions-application-schedule",
        "page": "admissions",
        "title": "Admission Schedule",
        "content": (
            "Application period runs from March 1 to June 30. Entrance examinations are conducted between "
            "July 10 and July 20, followed by interviews and evaluations from July 21 to July 25. "
            "Enrollment typically takes place from August 1 to August 15."
        ),
        "tags": ["admissions", "timeline", "schedule"],
    },
    {
        "slug": "admissions-requirements",
        "page": "admissions",
        "title": "Admission Requirements",
        "content": (
            "Freshmen applicants must submit a completed application form, Form 138, a good moral certificate, "
            "PSA birth certificate, 2x2 ID photos, entrance exam results, and a medical certificate. "
            "Transferees should provide transfer credentials, transcript of records, a good moral certificate, "
            "ID photos, and birth certificate copies."
        ),
        "tags": ["admissions", "requirements", "documents"],
    },
    {
        "slug": "academics-programs",
        "page": "academics",
        "title": "Academic Programs",
        "content": (
            "Tanauan City College offers programs such as Bachelor of Technical-Vocational Teacher Education "
            "with majors in Computer Hardware Servicing, Automotive Technology, Electrical Technology, and "
            "Electronics Technology. Other offerings include BS in Entrepreneurship, BS in Computer Engineering, "
            "Bachelor of Public Administration, and BS in Management Accounting."
        ),
        "tags": ["academics", "programs", "courses"],
    },
    {
        "slug": "academics-excellence",
        "page": "academics",
        "title": "Excellence in Education",
        "content": (
            "TCC provides comprehensive academic programs that blend theoretical foundations with practical "
            "experiences. Students benefit from a quality curriculum, expert faculty, industry partnerships, "
            "and robust career support services."
        ),
        "tags": ["academics", "faculty", "support"],
    },
    {
        "slug": "community-overview",
        "page": "community",
        "title": "TCC Community",
        "content": (
            "The Tanauan City College community is a vibrant network of students, faculty, and organizations "
            "focused on leadership, collaboration, and social impact. Official Facebook pages keep everyone "
            "informed about events, updates, and opportunities for engagement."
        ),
        "tags": ["community", "engagement", "facebook"],
    },
    {
        "slug": "community-help",
        "page": "community",
        "title": "Community Support Contacts",
        "content": (
            "For community collaborations or inquiries, reach out via email at community@tcc.edu.ph or call "
            "(043) 778-1234. The college encourages participation in organizations, outreach programs, academic "
            "discussions, and innovation initiatives."
        ),
        "tags": ["community", "contact", "support"],
    },
    {
        "slug": "tcc-history",
        "page": "about",
        "title": "College History",
        "content": (
            "Tanauan City College was founded to provide accessible higher education for Tanauan City and nearby "
            "communities. It has grown into a comprehensive institution that upholds academic excellence and "
            "continues to expand its services and programs."
        ),
        "tags": ["history", "about", "overview"],
    },
    {
        "slug": "tcc-mission",
        "page": "about",
        "title": "Mission Statement",
        "content": (
            "TCC aims to offer relevant educational opportunities aligned with regional development, deliver quality "
            "training in technology, sciences, languages, and the arts, and advance studies, research, and extension "
            "services that reflect the patriotism of its visionary leaders."
        ),
        "tags": ["mission", "about", "values"],
    },
    {
        "slug": "tcc-vision",
        "page": "about",
        "title": "Vision Statement",
        "content": (
            "By 2030, Tanauan City College envisions itself as a globally competitive, self-sustaining institution "
            "that produces patriotic, highly skilled, and technology-driven professionals."
        ),
        "tags": ["vision", "about", "future"],
    },
    {
        "slug": "tcc-core-values",
        "page": "about",
        "title": "Core Values",
        "content": (
            "Core values include professionalism, integrity, value for excellence, openness to innovation, "
            "and teamwork—principles that guide decisions and relationships within the TCC community."
        ),
        "tags": ["values", "about", "culture"],
    },
]


def get_mongo_client() -> Optional[MongoClient]:
    """Return a shared MongoDB client, initialising it on first use."""
    global _mongo_client
    if _mongo_client:
        return _mongo_client

    try:
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10_000,
            connectTimeoutMS=10_000,
            socketTimeoutMS=10_000,
        )
        client.admin.command("ping")
    except Exception as exc:  # pragma: no cover - log for troubleshooting
        print(f"[database] Failed to initialise MongoDB client: {exc}")
        _mongo_client = None
        return None

    _mongo_client = client
    return _mongo_client


def get_context_collection() -> Optional[Collection]:
    """Return the MongoDB collection that stores static website sections."""
    client = get_mongo_client()
    if not client:
        return None
    db = client[MONGO_DB_NAME]
    return db[CONTEXT_COLLECTION_NAME]


def seed_sample_data(force: bool = False, documents: Optional[Sequence[dict]] = None) -> int:
    """
    Insert a small set of example documents into the context collection.

    Args:
        force: When True, seed even if documents already exist.
        documents: Optional list of custom documents to insert.

    Returns:
        The number of documents inserted.
    """
    if not SEED_SAMPLE_CONTEXTS and not force:
        return 0

    collection = get_context_collection()
    if not collection:
        return 0

    payload: Iterable[dict] = documents if documents is not None else SAMPLE_CONTEXT_DOCUMENTS
    if not payload:
        return 0

    inserted = 0
    try:
        for doc in payload:
            result = collection.update_one(
                {"slug": doc.get("slug")},
                {"$setOnInsert": doc},
                upsert=True,
            )
            if result.upserted_id is not None:
                inserted += 1
        if inserted:
            print(f"[database] Seeded {inserted} sample context document(s).")
        return inserted
    except PyMongoError as exc:  # pragma: no cover - best-effort seeding
        print(f"[database] Failed to seed sample data: {exc}")
        return 0

