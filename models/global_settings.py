"""Global settings model for universal configuration"""
from pymongo import MongoClient
from datetime import datetime
import os
from typing import Optional, Dict, Any

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# MongoDB connection (reuse from user model)
MONGO_URI = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
DB_NAME = os.environ.get('DB_NAME', 'dealshare_automation')

# Initialize MongoDB connection
_db_connected = False
client = None
db = None
settings_collection = None

try:
    # For MongoDB Atlas, use longer timeout
    timeout = 10000 if MONGO_URI.startswith('mongodb+srv://') else 5000
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=timeout)
    client.admin.command('ping')
    db = client[DB_NAME]
    settings_collection = db.global_settings
    _db_connected = True
    
    # Initialize default global settings if they don't exist
    if settings_collection.count_documents({}) == 0:
        default_settings = {
            'country_code': '22',
            'operator': '1',
            'service': 'pfk',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        settings_collection.insert_one(default_settings)
except Exception as e:
    _db_connected = False
    print(f"WARNING: MongoDB connection failed in global_settings: {e}")
    settings_collection = None

class GlobalSettings:
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Get global settings"""
        if not _db_connected or settings_collection is None:
            # Return defaults if DB not connected
            return {
                'country_code': '22',
                'operator': '1',
                'service': 'pfk'
            }
        
        settings = settings_collection.find_one({})
        if settings:
            return {
                'country_code': settings.get('country_code', '22'),
                'operator': settings.get('operator', '1'),
                'service': settings.get('service', 'pfk')
            }
        return {
            'country_code': '22',
            'operator': '1',
            'service': 'pfk'
        }
    
    @staticmethod
    def update_settings(country_code: str = None, operator: str = None, service: str = None) -> Dict[str, Any]:
        """Update global settings"""
        try:
            if not _db_connected or settings_collection is None:
                return {
                    'success': False,
                    'error': 'MongoDB is not connected'
                }
            
            update_data = {'updated_at': datetime.utcnow()}
            
            if country_code is not None:
                update_data['country_code'] = country_code
            if operator is not None:
                update_data['operator'] = operator
            if service is not None:
                update_data['service'] = service
            
            # If no settings exist, create them
            if settings_collection.count_documents({}) == 0:
                default_settings = {
                    'country_code': country_code or '22',
                    'operator': operator or '1',
                    'service': service or 'pfk',
                    'created_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }
                settings_collection.insert_one(default_settings)
            else:
                # Update existing settings
                result = settings_collection.update_one(
                    {},
                    {'$set': update_data},
                    upsert=True
                )
            
            return {
                'success': True,
                'message': 'Global settings updated successfully'
            }
        except Exception as e:
            print(f"Error updating global settings: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': str(e)
            }

