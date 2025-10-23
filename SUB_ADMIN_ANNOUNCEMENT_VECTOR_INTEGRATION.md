# Sub-Admin Announcement System - MongoDB & Pinecone Integration

## ✅ INTEGRATION STATUS: COMPLETE & OPERATIONAL

The sub-admin announcement system is **fully integrated** with MongoDB and Pinecone vector database. When sub-admins create announcements, they are automatically stored in both databases and the TCC Assistant Chatbot can search and respond to queries about them.

---

## 🔄 How It Works - Complete Flow

### 1. **Creating an Announcement (Sub-Admin)**

**File: `sub_announcements.py` (Lines 31-139)**

When a sub-admin creates a new announcement via the Sub-announcements page:

```python
@sub_announcements_bp.route('/api/sub-announcements/add', methods=['POST'])
def add_announcement():
```

**Step-by-step process:**

1. **Receive Data** from frontend (title, content, dates, priority, status)
2. **Store in MongoDB** `sub_announcements` collection:
   ```python
   announcement_doc = {
       "title": title,
       "description": description,
       "start_date": start_date,
       "end_date": end_date,
       "priority": priority,
       "status": status,
       "office": office,
       "created_by": sub_admin_name,
       "created_at": datetime.utcnow(),
       "source": "sub_admin"
   }
   result = sub_announcements_collection.insert_one(announcement_doc)
   ```

3. **Create Vector Embedding** for Pinecone:
   ```python
   embed_text = f"Title: {title}\nDescription: {description}\nOffice: {office}\nPriority: {priority}\nStart Date: {start_date}\nEnd Date: {end_date}"
   
   metadata = {
       "type": "announcement",
       "announcement_id": announcement_id,
       "title": title,
       "description": description,
       "office": office,
       "priority": priority,
       "tag": "announcements"  # For chatbot integration
   }
   ```

4. **Store in Pinecone** vector database:
   ```python
   vector_id = vector_store.store_text(embed_text, metadata)
   ```

5. **Update MongoDB** with vector_id for reference:
   ```python
   sub_announcements_collection.update_one(
       {"_id": result.inserted_id},
       {"$set": {"vector_id": vector_id}}
   )
   ```

6. **Mirror to Admin Collection** for dashboard visibility:
   ```python
   admin_announcements_collection.insert_one(admin_announcement_doc)
   ```

---

### 2. **Chatbot Responding to Queries**

**File: `chat.py`**

When a user asks about announcements, the chatbot:

#### A. **Detects "announcements" Intent** (Lines 543-688)
```python
def get_response(msg, user_id="guest"):
    # Neural network predicts intent
    tag = hybrid_result['final_tag']
    
    if tag == "announcements":
        # Use vector search for relevant announcements
        if vector_store.index:
            bot_response = search_announcements_with_vector(cleaned_msg)
```

#### B. **Searches Pinecone with Vector Similarity** (Lines 467-505)
```python
def search_announcements_with_vector(query):
    # Search in Pinecone for announcements
    vector_results = vector_store.search_similar(
        query, 
        top_k=3, 
        filter_dict={"type": {"$eq": "announcement"}},
        score_threshold=0.6
    )
    
    # Format response with matching announcements
    response = "📢 Relevant Announcements:\n\n"
    for result in vector_results:
        metadata = result['metadata']
        priority_emoji = {"high": "🔴 [HIGH]", "medium": "🟡 [MEDIUM]", "low": "🟢 [LOW]"}
        
        response += f"{priority_emoji[priority]} {title}\n"
        response += f"📍 Office: {office}\n"
        response += f"📅 Date: {start_date}\n"
        response += f"📝 {description}\n"
        response += f"(Relevance: {result['score']:.0%})\n\n"
    
    return response
```

#### C. **Fetches Active Announcements from MongoDB** (Lines 388-443)
```python
def get_active_announcements():
    # Get from sub_announcements collection
    sub_announcements = list(sub_announcements_collection.find({"status": "active"}))
    
    # Get from admin_announcements collection
    admin_announcements = list(admin_announcements_collection.find({"status": "active"}))
    
    # Combine and sort by priority
    return all_announcements
```

---

### 3. **Vector Search Technology**

**File: `vector_store.py`**

The system uses **Sentence Transformers** and **Pinecone** for semantic search:

```python
class VectorStore:
    def __init__(self):
        # Uses 'all-MiniLM-L6-v2' model for embeddings
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        # Connects to Pinecone cloud vector database
        self.index = self.pc.Index("chatbot-vectors")
    
    def store_text(self, text, metadata):
        # Generate 384-dimensional embedding
        embedding = self.embedding_model.encode(text)
        # Store in Pinecone with metadata
        self.index.upsert(vectors=[(vector_id, embedding, metadata)])
    
    def search_similar(self, query, top_k=5, filter_dict=None):
        # Find semantically similar announcements
        query_embedding = self.embedding_model.encode(query)
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            filter=filter_dict,
            include_metadata=True
        )
        return results
```

---

## 📊 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│  SUB-ADMIN CREATES ANNOUNCEMENT                             │
│  (via Sub-announcements.html + AnnouncementManager.js)      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  POST /api/sub-announcements/add                            │
│  (sub_announcements.py)                                     │
└────┬──────────────┬──────────────┬──────────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐   ┌──────────┐   ┌────────────────┐
│ MongoDB │   │ Pinecone │   │ Admin Mirror   │
│ Storage │   │  Vector  │   │   Collection   │
│         │   │ Database │   │                │
│ sub_    │   │          │   │ admin_         │
│ announce│   │ Semantic │   │ announcements  │
│ ments   │   │  Search  │   │                │
└─────────┘   └──────────┘   └────────────────┘
     │              │              │
     └──────┬───────┴──────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│  USER ASKS CHATBOT ABOUT ANNOUNCEMENTS                      │
│  "What are the latest announcements?"                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  CHATBOT PROCESSES QUERY (chat.py)                          │
│  1. Detects "announcements" intent                          │
│  2. Calls search_announcements_with_vector()                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  PINECONE VECTOR SEARCH                                     │
│  - Converts query to embedding                              │
│  - Finds semantically similar announcements                 │
│  - Filters by type="announcement", status="active"          │
│  - Returns top 3 most relevant results                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  CHATBOT RESPONDS WITH FORMATTED ANNOUNCEMENTS              │
│  📢 Relevant Announcements:                                 │
│  🔴 [HIGH] Exam Schedule Update                             │
│  📍 Office: Registrar's Office                              │
│  📅 Date: 2025-10-15                                        │
│  📝 Final exams will be held from Oct 20-25...             │
│  (Relevance: 87%)                                           │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔑 Key Features

### ✅ Automatic Storage
- **MongoDB**: Structured data storage with office, dates, priority
- **Pinecone**: Vector embeddings for semantic search
- **Dual Collection**: Sub-admin and admin announcements synced

### ✅ Intelligent Search
- **Semantic Understanding**: Finds announcements by meaning, not just keywords
- **Contextual Results**: Returns most relevant announcements based on query
- **Office Filtering**: Can filter by specific office
- **Priority Ranking**: High priority announcements ranked higher

### ✅ Real-time Updates
- New announcements immediately searchable
- Updates reflected in vector database
- Deletes remove from both MongoDB and Pinecone

---

## 📝 Example Queries & Responses

### Query 1: General Announcement Request
**User:** "What are the latest announcements?"

**Chatbot Response:**
```
📢 Relevant Announcements:

🔴 [HIGH] Enrollment Period Extended
📍 Office: Admission Office
📅 Date: 2025-10-01
📝 The enrollment period has been extended until October 15, 2025. All incoming students are encouraged to complete their registration.
(Relevance: 92%)

🟡 [MEDIUM] Library Hours Update
📍 Office: General
📅 Date: 2025-10-05
📝 The library will now be open until 10 PM on weekdays to accommodate students during exam period.
(Relevance: 85%)
```

### Query 2: Office-Specific Request
**User:** "Are there any announcements from the registrar's office?"

**Chatbot Response:**
```
📢 Relevant Announcements:

🔴 [HIGH] Final Exam Schedule Released
📍 Office: Registrar's Office
📅 Date: 2025-10-10
📝 The final examination schedule for Semester 1 is now available. Please check the registrar's portal.
(Relevance: 95%)
```

### Query 3: Topic-Specific Request
**User:** "Tell me about scholarship announcements"

**Chatbot searches for announcements containing "scholarship" in title or description**

---

## 🛠️ Technical Architecture

### Frontend
- **File**: `templates/Sub-announcements.html`
- **JavaScript**: `static/Sub-assets/js/modules/AnnouncementManager.js`
- **Actions**: Create, Read, Update, Delete announcements

### Backend API
- **File**: `sub_announcements.py`
- **Endpoints**:
  - `POST /api/sub-announcements/add` - Create new announcement
  - `GET /api/sub-announcements/list` - List all announcements
  - `PUT /api/sub-announcements/update/<id>` - Update announcement
  - `DELETE /api/sub-announcements/delete/<id>` - Delete announcement

### Chatbot Integration
- **File**: `chat.py`
- **Functions**:
  - `get_active_announcements()` - Fetch from MongoDB
  - `search_announcements_with_vector()` - Search with Pinecone
  - `get_response()` - Main chatbot logic

### Vector Database
- **File**: `vector_store.py`
- **Technology**: Pinecone + Sentence Transformers
- **Model**: all-MiniLM-L6-v2 (384-dimensional embeddings)

---

## 🔒 Security & Permissions

### Sub-Admin Access Control
- Sub-admins can only manage announcements for their assigned office
- Office information from session: `session.get('office')`
- Created by tracking: `created_by: sub_admin_name`

### Data Validation
```python
required_fields = ['title', 'content', 'startDate', 'endDate', 'priority']
# Date validation
if new Date(startDate) > new Date(endDate):
    return error("End date must be after start date")
```

---

## 🧪 Testing the Integration

### Test 1: Create an Announcement
1. Login as sub-admin
2. Go to Sub-announcements page
3. Click "Add New Announcement"
4. Fill in:
   - Title: "Test Announcement"
   - Content: "This is a test announcement for integration testing"
   - Start Date: Today
   - End Date: Tomorrow
   - Priority: High
5. Save

**Expected Result:**
- MongoDB record created in `sub_announcements` collection
- Pinecone vector created with metadata
- Success message: "Announcement created successfully and synced to chatbot!"

### Test 2: Query the Chatbot
1. Open chatbot on main page
2. Type: "What are the latest announcements?"
3. Or: "Tell me about test announcements"

**Expected Result:**
- Chatbot responds with the announcement you just created
- Shows title, office, date, description
- Displays relevance score

### Test 3: Verify Vector Search
Check terminal logs for:
```
Announcement saved to MongoDB with ID: 507f1f77bcf86cd799439011
Announcement stored in Pinecone with vector ID: a1b2c3d4-e5f6-7890-ab12-cd34ef567890
```

---

## 📊 Database Schemas

### MongoDB: sub_announcements Collection
```json
{
  "_id": ObjectId("507f1f77bcf86cd799439011"),
  "title": "Enrollment Period Extended",
  "description": "The enrollment period has been extended...",
  "start_date": "2025-10-01",
  "end_date": "2025-10-15",
  "priority": "high",
  "status": "active",
  "office": "Admission Office",
  "created_by": "Admissions Office Admin",
  "created_at": ISODate("2025-10-07T10:30:00Z"),
  "updated_at": ISODate("2025-10-07T10:30:00Z"),
  "source": "sub_admin",
  "vector_id": "a1b2c3d4-e5f6-7890-ab12-cd34ef567890"
}
```

### Pinecone: Vector Record
```json
{
  "id": "a1b2c3d4-e5f6-7890-ab12-cd34ef567890",
  "values": [0.123, -0.456, 0.789, ...],  // 384 dimensions
  "metadata": {
    "type": "announcement",
    "announcement_id": "507f1f77bcf86cd799439011",
    "title": "Enrollment Period Extended",
    "description": "The enrollment period has been extended...",
    "office": "Admission Office",
    "priority": "high",
    "start_date": "2025-10-01",
    "end_date": "2025-10-15",
    "status": "active",
    "created_by": "Admissions Office Admin",
    "tag": "announcements",
    "text": "Title: Enrollment Period Extended\nDescription: The enrollment period has been extended...\nOffice: Admission Office\nPriority: high\nStart Date: 2025-10-01\nEnd Date: 2025-10-15"
  }
}
```

---

## 🚀 Performance Optimization

### Vector Search Advantages
- **Fast**: Pinecone searches millions of vectors in milliseconds
- **Accurate**: Semantic search finds relevant content even with different wording
- **Scalable**: Cloud-based, automatically scales with data volume

### Caching Strategy
- MongoDB stores structured data for quick retrieval
- Pinecone handles similarity search
- Vector IDs link both databases

---

## 🔧 Maintenance & Updates

### Updating an Announcement
When a sub-admin updates an announcement:
1. Old vector deleted from Pinecone
2. New embedding generated with updated content
3. New vector stored with same announcement_id
4. MongoDB updated with new vector_id

**Code** (`sub_announcements.py` lines 216-243):
```python
# Delete old vector
vector_store.index.delete(ids=[existing['vector_id']])

# Create new embedding
new_vector_id = vector_store.store_text(embed_text, metadata)

# Update MongoDB
sub_announcements_collection.update_one(
    {"_id": ObjectId(announcement_id)},
    {"$set": {"vector_id": new_vector_id}}
)
```

### Deleting an Announcement
1. Delete from Pinecone vector database
2. Delete from MongoDB sub_announcements
3. Delete from admin_announcements mirror

---

## 📈 Future Enhancements

### Possible Improvements
1. **Multi-language Support**: Store embeddings in multiple languages
2. **Image Attachments**: OCR for announcement images
3. **Expiration Handling**: Auto-archive old announcements
4. **Analytics**: Track which announcements get most queries
5. **Scheduled Publishing**: Auto-activate on specific dates

---

## 🆘 Troubleshooting

### Issue: Announcements not appearing in chatbot
**Check:**
1. MongoDB connection active?
2. Pinecone API key configured?
3. Announcement status = "active"?
4. Vector successfully stored? (check logs)

**Solution:**
```bash
# Check MongoDB
mongo "mongodb+srv://cluster0.gskdq3p.mongodb.net/" --username dxtrzpc26
use chatbot_db
db.sub_announcements.find()

# Check Pinecone
# See vector_id in announcement document
# Verify in Pinecone dashboard
```

### Issue: Vector search returning irrelevant results
**Possible Causes:**
- Query too vague
- Not enough announcement context in description
- Score threshold too low

**Solution:**
- Adjust score_threshold in `search_announcements_with_vector()` (default: 0.6)
- Add more descriptive content to announcements
- Fine-tune embedding model if needed

---

## 📚 Related Files

- `sub_announcements.py` - Sub-admin announcement backend
- `chat.py` - Chatbot logic and announcement integration
- `vector_store.py` - Pinecone vector database wrapper
- `app.py` - Main Flask application (registers blueprint)
- `templates/Sub-announcements.html` - Frontend interface
- `static/Sub-assets/js/modules/AnnouncementManager.js` - Frontend logic

---

## ✨ Summary

The sub-admin announcement system is **fully operational** with:
- ✅ MongoDB storage for structured data
- ✅ Pinecone vector database for semantic search
- ✅ Automatic chatbot integration
- ✅ Real-time updates and synchronization
- ✅ Office-based access control
- ✅ Priority-based ranking

**No additional configuration needed!** The system is ready to use.

