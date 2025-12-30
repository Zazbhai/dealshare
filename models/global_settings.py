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
    # For MongoDB Atlas, use shorter timeout to fail faster
    timeout = 5000 if MONGO_URI.startswith('mongodb+srv://') else 3000
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=timeout, connectTimeoutMS=timeout)
    client.admin.command('ping')
    db = client[DB_NAME]
    settings_collection = db.global_settings
    _db_connected = True
    
    # Initialize default global settings if they don't exist
    if settings_collection.count_documents({}) == 0:
        default_settings = {
            'api_url': 'https://api.temporasms.com/stubs/handler_api.php',
            'country_code': '22',
            'operator': '1',
            'service': 'pfk',
            'price': 0.0,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        settings_collection.insert_one(default_settings)
except Exception as e:
    _db_connected = False
    error_msg = str(e)
    print(f"WARNING: MongoDB connection failed in global_settings: {error_msg}")
    if MONGO_URI.startswith('mongodb+srv://') and ("DNS" in error_msg or "resolution" in error_msg.lower()):
        print("  -> DNS resolution timeout detected. Check your internet connection.")
    settings_collection = None

class GlobalSettings:
    @staticmethod
    def get_settings() -> Dict[str, Any]:
        """Get global settings"""
        if not _db_connected or settings_collection is None:
            # Return defaults if DB not connected
            return {
                'api_url': 'https://api.temporasms.com/stubs/handler_api.php',
                'country_code': '22',
                'operator': '1',
                'service': 'pfk',
                'price': 0.0
            }
        
        settings = settings_collection.find_one({})
        if settings:
            return {
                'api_url': settings.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php'),
                'country_code': settings.get('country_code', '22'),
                'operator': settings.get('operator', '1'),
                'service': settings.get('service', 'pfk'),
                'price': settings.get('price', 0.0)
            }
        return {
            'api_url': 'https://api.temporasms.com/stubs/handler_api.php',
            'country_code': '22',
            'operator': '1',
            'service': 'pfk',
            'price': 0.0
        }
    
    @staticmethod
    def update_settings(api_url: str = None, country_code: str = None, operator: str = None, service: str = None, price: float = None) -> Dict[str, Any]:
        """Update global settings"""
        try:
            if not _db_connected or settings_collection is None:
                return {
                    'success': False,
                    'error': 'MongoDB is not connected'
                }
            
            update_data = {'updated_at': datetime.utcnow()}
            
            if api_url is not None:
                update_data['api_url'] = api_url
            if country_code is not None:
                update_data['country_code'] = country_code
            if operator is not None:
                update_data['operator'] = operator
            if service is not None:
                update_data['service'] = service
            if price is not None:
                update_data['price'] = float(price)
            
            # If no settings exist, create them
            if settings_collection.count_documents({}) == 0:
                default_settings = {
                    'api_url': api_url or 'https://api.temporasms.com/stubs/handler_api.php',
                    'country_code': country_code or '22',
                    'operator': operator or '1',
                    'service': service or 'pfk',
                    'price': float(price) if price is not None else 0.0,
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

