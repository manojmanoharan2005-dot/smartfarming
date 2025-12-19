"""
Test MongoDB Atlas Connection
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient

# Load environment variables
load_dotenv()

def test_mongodb_connection():
    """Test connection to MongoDB Atlas"""
    
    # Get connection string from environment
    MONGODB_URI = os.getenv('MONGODB_URI')
    
    if not MONGODB_URI:
        print("❌ Error: MONGODB_URI not found in .env file")
        return False
    
    print("🔄 Testing MongoDB Atlas connection...")
    print(f"📡 Connection URI: {MONGODB_URI[:50]}...")
    
    try:
        # Create MongoDB client
        client = MongoClient(
            MONGODB_URI,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000
        )
        
        # Test connection by pinging the server
        client.admin.command('ping')
        print("✅ Successfully connected to MongoDB Atlas!")
        
        # Get database
        db_name = os.getenv('MONGODB_DB', 'myVirtualDatabase')
        db = client[db_name]
        print(f"📊 Using database: {db_name}")
        
        # List collections
        collections = db.list_collection_names()
        print(f"📂 Available collections: {collections if collections else 'None (empty database)'}")
        
        # Test write operation (if supported)
        try:
            test_collection = db['test_collection']
            result = test_collection.insert_one({'test': 'data', 'timestamp': 'test'})
            print(f"✅ Write test successful! Inserted ID: {result.inserted_id}")
            
            # Clean up test data
            test_collection.delete_one({'_id': result.inserted_id})
            print("🧹 Test data cleaned up")
            
        except Exception as write_error:
            print(f"⚠️ Write operation failed: {write_error}")
            print("   Note: This may be expected if using Atlas SQL (read-only) endpoint")
        
        # Close connection
        client.close()
        print("✅ Connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print("\n🔧 Troubleshooting steps:")
        print("   1. Verify your MongoDB Atlas credentials")
        print("   2. Check if your IP address is whitelisted in MongoDB Atlas")
        print("   3. Ensure the cluster is running")
        print("   4. Verify network connectivity")
        return False

if __name__ == "__main__":
    test_mongodb_connection()
