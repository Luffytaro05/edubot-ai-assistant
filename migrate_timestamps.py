"""
Migration script to add proper timestamps to existing conversation documents
Run this once to update all existing data in MongoDB
"""

from pymongo import MongoClient
from datetime import datetime
from dateutil import parser

# MongoDB connection
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations_col = db["conversations"]

def migrate_timestamps():
    """Add proper timestamp field to documents that only have date string"""
    
    print("Starting timestamp migration...")
    
    # Find documents without timestamp field
    docs_to_update = conversations_col.find({
        "timestamp": {"$exists": False},
        "date": {"$exists": True}
    })
    
    updated_count = 0
    error_count = 0
    
    for doc in docs_to_update:
        try:
            # Parse the ISO date string
            date_str = doc.get("date")
            
            if date_str:
                # Convert string to datetime object
                timestamp = parser.isoparse(date_str)
                
                # Update document
                conversations_col.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"timestamp": timestamp}}
                )
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"Updated {updated_count} documents...")
            
        except Exception as e:
            print(f"Error updating document {doc['_id']}: {e}")
            error_count += 1
            continue
    
    print(f"\nMigration complete!")
    print(f"Successfully updated: {updated_count} documents")
    print(f"Errors: {error_count} documents")
    
    # Verify the migration
    verify_migration()

def verify_migration():
    """Verify that all documents now have timestamp field"""
    
    print("\nVerifying migration...")
    
    total_docs = conversations_col.count_documents({})
    docs_with_timestamp = conversations_col.count_documents({"timestamp": {"$exists": True}})
    docs_without_timestamp = conversations_col.count_documents({"timestamp": {"$exists": False}})
    
    print(f"Total documents: {total_docs}")
    print(f"Documents with timestamp: {docs_with_timestamp}")
    print(f"Documents without timestamp: {docs_without_timestamp}")
    
    if docs_without_timestamp > 0:
        print("\n⚠️ Warning: Some documents still don't have timestamps")
        
        # Show sample of documents without timestamps
        sample = conversations_col.find_one({"timestamp": {"$exists": False}})
        if sample:
            print(f"Sample document without timestamp: {sample}")
    else:
        print("\n✅ All documents have timestamps!")

def add_missing_offices():
    """Add 'General' office to documents without office field"""
    
    print("\nChecking for documents without office field...")
    
    result = conversations_col.update_many(
        {"office": {"$exists": False}},
        {"$set": {"office": "General"}}
    )
    
    print(f"Added 'General' office to {result.modified_count} documents")

def create_indexes():
    """Create indexes for better query performance"""
    
    print("\nCreating indexes...")
    
    # Index on office and timestamp for weekly usage queries
    conversations_col.create_index([("office", 1), ("timestamp", -1)])
    
    # Index on user for distinct user counts
    conversations_col.create_index([("user", 1)])
    
    # Index on status for resolved/escalated queries
    conversations_col.create_index([("office", 1), ("status", 1)])
    
    print("Indexes created successfully")

if __name__ == "__main__":
    print("=" * 50)
    print("MongoDB Migration Script")
    print("=" * 50)
    
    # Run migrations
    migrate_timestamps()
    add_missing_offices()
    create_indexes()
    
    print("\n" + "=" * 50)
    print("Migration completed!")
    print("=" * 50)