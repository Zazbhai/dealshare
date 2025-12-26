"""Quick script to check MongoDB status and provide instructions"""
import sys
import os

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables only

print("=" * 60)
print("MongoDB Status Checker")
print("=" * 60)

# Check if pymongo is installed
try:
    import pymongo
    print("\n[OK] pymongo is installed")
except ImportError:
    print("\n[FAIL] pymongo is not installed")
    print("Install it with: pip install pymongo")
    sys.exit(1)

# Try to connect
print("\nAttempting to connect to MongoDB...")
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
    
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
    # Mask password in connection string for display
    display_uri = mongo_uri
    if '@' in mongo_uri:
        parts = mongo_uri.split('@')
        if len(parts) == 2:
            user_pass = parts[0].split('://')[1] if '://' in parts[0] else parts[0]
            if ':' in user_pass:
                user = user_pass.split(':')[0]
                display_uri = mongo_uri.replace(user_pass, f"{user}:***")
    print(f"Connection string: {display_uri}")
    
    client = MongoClient(mongo_uri, serverSelectionTimeoutMS=3000)
    client.admin.command('ping')
    print("\n[SUCCESS] MongoDB is running and connected!")
    
    # Show database info
    db_name = os.environ.get('DB_NAME', 'dealshare_automation')
    db = client[db_name]
    users_count = db.users.count_documents({})
    print(f"Database '{db_name}' is accessible")
    print(f"Users in database: {users_count}")
    
except ConnectionFailure:
    print("\n[ERROR] Cannot connect to MongoDB")
    print("\nMongoDB is not running. Please start it:")
    print("\nWindows:")
    print("  net start MongoDB")
    print("\nOr manually:")
    print("  mongod --dbpath C:\\data\\db")
    print("\nSee start_mongodb.md for detailed instructions")
    sys.exit(1)
    
except ServerSelectionTimeoutError:
    print("\n[ERROR] MongoDB connection timeout")
    print("\nMongoDB might not be running or is not accessible")
    print("Check if MongoDB service is running:")
    print("  net start | findstr MongoDB")
    sys.exit(1)
    
except Exception as e:
    print(f"\n[ERROR] Unexpected error: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("MongoDB is ready to use!")
print("=" * 60)

