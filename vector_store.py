import os
import json
import uuid
from typing import List, Dict, Any, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
try:
    from pinecone import Pinecone, ServerlessSpec
except Exception as _pinecone_import_error:
    Pinecone = None
    ServerlessSpec = None
import time
from dotenv import load_dotenv
load_dotenv()  


class VectorStore:
    def __init__(self, 
                 index_name: str = "chatbot-vectors",
                 model_name: str = "all-MiniLM-L6-v2",
                 dimension: int = 384,
                 enhanced_embeddings: bool = True):
        """
        Initialize Pinecone vector store
        
        Args:
            index_name: Name of Pinecone index
            model_name: SentenceTransformers model name
            dimension: Vector dimension (384 for all-MiniLM-L6-v2)
        """
        self.index_name = index_name
        self.model_name = model_name
        self.dimension = dimension
        self.enhanced_embeddings = enhanced_embeddings
        
        # Initialize embedding model (resilient to offline/deploy environments)
        self.embedding_model = None
        try:
            print(f"Loading embedding model: {model_name}")
            self.embedding_model = SentenceTransformer(model_name)
        except Exception as e:
            print(f"WARNING: Failed to load SentenceTransformer '{model_name}': {e}")
            print("Running without embeddings - vector features will be disabled")
        
        # Enhanced similarity thresholds
        self.similarity_thresholds = {
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }
        
        # Initialize Pinecone
        self.pc = None
        self.index = None
        self._initialize_pinecone()
        
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index with performance optimizations"""
        try:
            if Pinecone is None or ServerlessSpec is None:
                print("WARNING: pinecone client not installed; running in offline mode")
                return
            # Get API key from environment
            api_key = os.getenv('PINECONE_API_KEY')
            if not api_key:
                print("WARNING: PINECONE_API_KEY not found in environment variables")
                print("Running in offline mode - vector search will be disabled")
                return
            
            print(f"🔗 Initializing Pinecone connection...")
            init_start = time.time()
            
            # Initialize Pinecone client
            self.pc = Pinecone(api_key=api_key)
            
            # Check if index exists, create if not
            existing_indexes = [idx.name for idx in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                print(f"📦 Creating new Pinecone index: {self.index_name}")
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric='cosine',
                    spec=ServerlessSpec(
                        cloud='aws',
                        region='us-east-1'
                    )
                )
                # Reduced wait time for faster startup
                print("⏳ Waiting for index to be ready...")
                time.sleep(5)  # Reduced from 10 to 5 seconds
            
            # Connect to index
            self.index = self.pc.Index(self.index_name)
            
            init_time = time.time() - init_start
            print(f"✅ Connected to Pinecone index: {self.index_name} (took {init_time:.2f}s)")
            
        except Exception as e:
            print(f"❌ Error initializing Pinecone: {e}")
            print("Running in offline mode - vector search will be disabled")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate enhanced embedding for text using SentenceTransformers"""
        try:
            if not self.embedding_model:
                # No embedding model available; return zero vector
                return [0.0] * self.dimension
            if self.enhanced_embeddings:
                # Enhanced embedding with multiple strategies
                # 1. Original text
                embedding1 = self.embedding_model.encode(text, convert_to_tensor=False)
                
                # 2. Lowercased text
                embedding2 = self.embedding_model.encode(text.lower(), convert_to_tensor=False)
                
                # 3. Cleaned text (remove punctuation)
                import re
                cleaned_text = re.sub(r'[^\w\s]', '', text.lower())
                embedding3 = self.embedding_model.encode(cleaned_text, convert_to_tensor=False)
                
                # Average the embeddings for better representation
                combined_embedding = (embedding1 + embedding2 + embedding3) / 3
                return combined_embedding.tolist()
            else:
                # Standard embedding
                embedding = self.embedding_model.encode(text, convert_to_tensor=False)
                return embedding.tolist()
        except Exception as e:
            print(f"Error generating embedding: {e}")
            return [0.0] * self.dimension
    
    def store_text(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """
        Store text with its embedding in Pinecone
        
        Args:
            text: Text to store
            metadata: Additional metadata to store with the text
            
        Returns:
            Unique ID of stored vector
        """
        if not self.index:
            print("Pinecone not available, skipping vector storage")
            return ""
        
        try:
            # Generate unique ID
            vector_id = str(uuid.uuid4())
            
            # Generate embedding
            embedding = self.generate_embedding(text)
            
            # Prepare metadata
            if metadata is None:
                metadata = {}
            
            metadata['text'] = text
            metadata['timestamp'] = time.time()
            
            # Store in Pinecone
            self.index.upsert(
                vectors=[(vector_id, embedding, metadata)]
            )
            
            return vector_id
            
        except Exception as e:
            print(f"Error storing text in vector database: {e}")
            return ""
    
    def search_similar(self, 
                      query: str, 
                      top_k: int = 5, 
                      filter_dict: Dict = None,
                      score_threshold: float = 0.7,
                      similarity_level: str = 'medium') -> List[Dict]:
        """
        Enhanced search for similar texts with adaptive thresholds
        
        Args:
            query: Query text
            top_k: Number of results to return
            filter_dict: Metadata filter
            score_threshold: Minimum similarity score
            similarity_level: 'high', 'medium', or 'low' for adaptive thresholds
            
        Returns:
            List of similar texts with scores and metadata
        """
        if not self.index:
            print("Pinecone not available, returning empty results")
            return []
        
        try:
            # Use adaptive threshold based on similarity level
            adaptive_threshold = self.similarity_thresholds.get(similarity_level, score_threshold)
            final_threshold = max(score_threshold, adaptive_threshold)
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search in Pinecone with enhanced parameters
            search_results = self.index.query(
                vector=query_embedding,
                top_k=top_k * 2,  # Get more results for better filtering
                filter=filter_dict,
                include_metadata=True,
                include_values=False
            )
            
            # Process results with enhanced scoring
            results = []
            for match in search_results.matches:
                if match.score >= final_threshold:
                    # Calculate enhanced score with metadata weighting
                    enhanced_score = self.calculate_enhanced_score(match, query)
                    
                    result = {
                        'id': match.id,
                        'score': float(enhanced_score),
                        'original_score': float(match.score),
                        'text': match.metadata.get('text', ''),
                        'metadata': match.metadata
                    }
                    results.append(result)
            
            # Sort by enhanced score and return top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:top_k]
            
        except Exception as e:
            print(f"Error searching vectors: {e}")
            return []
    
    def calculate_enhanced_score(self, match, query):
        """Calculate enhanced similarity score with metadata weighting"""
        base_score = match.score
        
        # Metadata weighting
        metadata = match.metadata
        weight_multiplier = 1.0
        
        # Boost score for exact tag matches
        if metadata.get('tag'):
            weight_multiplier += 0.1
        
        # Boost score for recent content
        if metadata.get('timestamp'):
            import time
            age_days = (time.time() - metadata['timestamp']) / (24 * 3600)
            if age_days < 30:  # Recent content gets slight boost
                weight_multiplier += 0.05
        
        # Boost score for high-priority content
        if metadata.get('priority') == 'high':
            weight_multiplier += 0.15
        elif metadata.get('priority') == 'medium':
            weight_multiplier += 0.05
        
        return min(base_score * weight_multiplier, 1.0)
    
    def search_by_tag(self, 
                     query: str, 
                     tag: str, 
                     top_k: int = 3) -> List[Dict]:
        """
        Search for similar texts within a specific tag/intent
        
        Args:
            query: Query text
            tag: Intent tag to filter by
            top_k: Number of results to return
            
        Returns:
            List of similar texts from the specified tag
        """
        filter_dict = {"tag": {"$eq": tag}}
        return self.search_similar(query, top_k, filter_dict)
    
    def get_responses_by_tag(self, tag: str) -> List[str]:
        """Get all responses for a specific tag"""
        if not self.index:
            return []
        
        try:
            # Query for responses with specific tag
            filter_dict = {
                "tag": {"$eq": tag},
                "intent_type": {"$eq": "response"}
            }
            
            results = self.index.query(
                vector=[0] * self.dimension,  # Dummy vector for metadata-only search
                top_k=10,
                filter=filter_dict,
                include_metadata=True,
                include_values=False
            )
            
            responses = []
            for match in results.matches:
                text = match.metadata.get('text', '')
                if text and text not in responses:
                    responses.append(text)
            
            return responses
            
        except Exception as e:
            print(f"Error getting responses by tag: {e}")
            return []
    
    def store_announcements(self, announcements: List[Dict]) -> None:
        """Store announcements in vector database"""
        if not self.index:
            return
        
        print("Storing announcements in vector database...")
        
        for announcement in announcements:
            # Create searchable text from announcement
            searchable_text = f"{announcement['title']} {announcement['message']}"
            
            metadata = {
                'tag': 'announcements',
                'intent_type': 'announcement',
                'announcement_id': announcement['id'],
                'title': announcement['title'],
                'date': announcement['date'],
                'priority': announcement['priority'],
                'category': announcement['category'],
                'active': announcement.get('active', True)
            }
            
            self.store_text(searchable_text, metadata)
    
    def search_announcements(self, query: str, top_k: int = 3) -> List[Dict]:
        """Search announcements by content"""
        filter_dict = {
            "intent_type": {"$eq": "announcement"},
            "active": {"$eq": True}
        }
        return self.search_similar(query, top_k, filter_dict)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get vector database statistics"""
        if not self.index:
            return {"status": "offline", "total_vectors": 0}
        
        try:
            stats = self.index.describe_index_stats()
            return {
                "status": "online",
                "total_vectors": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "total_vectors": 0}
    
    def save_index(self, filename: str) -> None:
        """Save index metadata (Pinecone handles vector storage)"""
        try:
            metadata = {
                "index_name": self.index_name,
                "model_name": self.model_name,
                "dimension": self.dimension,
                "stats": self.get_stats()
            }
            
            with open(f"{filename}_metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"Vector store metadata saved to {filename}_metadata.json")
            
        except Exception as e:
            print(f"Error saving index metadata: {e}")
    
    def load_index(self, filename: str) -> bool:
        """Load index metadata"""
        try:
            with open(f"{filename}_metadata.json", 'r') as f:
                metadata = json.load(f)
            
            print(f"Loaded vector store metadata: {metadata}")
            return True
            
        except Exception as e:
            print(f"Error loading index metadata: {e}")
            return False
    
    def clear_index(self) -> bool:
        """Clear all vectors from the index"""
        if not self.index:
            return False
        
        try:
            # Delete all vectors
            self.index.delete(delete_all=True)
            print("Vector index cleared successfully")
            return True
            
        except Exception as e:
            print(f"Error clearing index: {e}")
            return False

# ============ Convenience helpers for GPT context ============
_singleton_store: Optional[VectorStore] = None

def _get_store() -> VectorStore:
    global _singleton_store
    if _singleton_store is None:
        _singleton_store = VectorStore()
    return _singleton_store

def get_relevant_context(query: str, office: Optional[str] = None, top_k: int = 3) -> str:
    try:
        store = _get_store()
        if not store.index:
            return ""
        filter_dict = {
            "$or": [
                {"intent_type": {"$eq": "faq"}},
                {"intent_type": {"$eq": "announcement"}},
                {"type": {"$eq": "faq"}},
                {"type": {"$eq": "announcement"}}
            ],
            "status": {"$eq": "published"}
        }
        if office:
            # Support either office field or category metadata
            filter_dict = {
                "$and": [
                    filter_dict,
                    {"$or": [
                        {"office": {"$eq": office}},
                        {"category": {"$eq": office}}
                    ]}
                ]
            }

        results = store.search_similar(query, top_k=top_k, filter_dict=filter_dict, score_threshold=0.6)
        if not results:
            return ""
        snippets = []
        for r in results:
            md = r.get("metadata", {})
            # Prefer explicit answers; fallback to stored text
            snippet = md.get("answer") or md.get("description") or md.get("text") or ""
            if snippet:
                snippets.append(snippet.strip())
        return "\n\n".join(snippets[:top_k])
    except Exception as e:
        print("Vector fetch error:", e)
        return ""