from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os
from typing import Optional, Dict, Any

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables only

# MongoDB connection
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'dealshare_automation')

# Initialize MongoDB connection with error handling
_db_connected = False
client = None
db = None
users_collection = None

try:
    # For MongoDB Atlas (mongodb+srv://), use longer timeout
    timeout = 10000 if MONGO_URI.startswith('mongodb+srv://') else 5000
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=timeout)
    # Test connection
    client.admin.command('ping')
    db = client[DB_NAME]
    users_collection = db.users
    _db_connected = True
    print(f"MongoDB connected successfully to: {MONGO_URI.split('@')[1] if '@' in MONGO_URI else 'localhost'}")
except Exception as e:
    _db_connected = False
    print(f"WARNING: MongoDB connection failed: {e}")
    if MONGO_URI.startswith('mongodb+srv://'):
        print("MongoDB Atlas connection failed. Check:")
        print("  1. Internet connection")
        print("  2. MongoDB Atlas IP whitelist (add 0.0.0.0/0 for testing)")
        print("  3. Username and password in connection string")
        print(f"  4. Connection string: {MONGO_URI[:50]}...")
    else:
        print("MongoDB is not running. Please start MongoDB service.")
        print("Windows: net start MongoDB")
        print("Or see start_mongodb.md for detailed instructions")
    # Create dummy collections to prevent import errors
    class DummyCollection:
        def find_one(self, *args, **kwargs): return None
        def find(self, *args, **kwargs): return []
        def insert_one(self, *args, **kwargs): raise Exception("MongoDB not connected")
        def update_one(self, *args, **kwargs): raise Exception("MongoDB not connected")
        def count_documents(self, *args, **kwargs): return 0
        def delete_one(self, *args, **kwargs): raise Exception("MongoDB not connected")
    users_collection = DummyCollection()

class User:
    @staticmethod
    def _check_connection():
        """Check if database is connected"""
        if not _db_connected:
            return {'success': False, 'error': 'MongoDB is not connected. Please start MongoDB service.'}
        return None
    
    @staticmethod
    def create_user(username: str, password: str, role: str = 'user', 
                   api_url: str = '', api_key: str = '') -> Dict[str, Any]:
        """Create a new user"""
        conn_check = User._check_connection()
        if conn_check:
            return conn_check
        
        # Check if user exists
        if users_collection.find_one({'username': username}):
            return {'success': False, 'error': 'Username already exists'}
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        user = {
            'username': username,
            'password': hashed_password.decode('utf-8'),
            'role': role,
            'api_url': api_url,
            'api_key': api_key,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        result = users_collection.insert_one(user)
        user['_id'] = str(result.inserted_id)
        user.pop('password', None)  # Don't return password
        return {'success': True, 'user': user}
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user and return user data"""
        if not _db_connected:
            return None
        user = users_collection.find_one({'username': username})
        
        if not user:
            return None
        
        # Check password
        if bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
            user['_id'] = str(user['_id'])
            user.pop('password', None)  # Don't return password
            return user
        return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        if not _db_connected:
            return None
        from bson import ObjectId
        try:
            user = users_collection.find_one({'_id': ObjectId(user_id)})
            if user:
                user['_id'] = str(user['_id'])
                user.pop('password', None)
            return user
        except:
            return None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        if not _db_connected:
            return None
        user = users_collection.find_one({'username': username})
        if user:
            user['_id'] = str(user['_id'])
            user.pop('password', None)
        return user
    
    @staticmethod
    def update_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings"""
        conn_check = User._check_connection()
        if conn_check:
            return conn_check
        from bson import ObjectId
        try:
            settings['updated_at'] = datetime.utcnow()
            result = users_collection.update_one(
                {'_id': ObjectId(user_id)},
                {'$set': settings}
            )
            if result.modified_count > 0:
                return {'success': True, 'message': 'Settings updated'}
            return {'success': False, 'error': 'No changes made'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_all_users() -> list:
        """Get all users (admin only)"""
        if not _db_connected:
            return []
        users = list(users_collection.find({}))
        for user in users:
            user['_id'] = str(user['_id'])
            user.pop('password', None)
        return users


