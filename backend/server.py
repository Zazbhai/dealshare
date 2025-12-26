from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import threading
import subprocess
import time

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables only

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api_dynamic import (
    get_balance,
    parse_balance,
    get_price_for_service,
    get_number,
    get_otp,
    cancel_number,
    parse_cancel_status,
    get_prices,
    parse_prices,
)
from shared_state import get_all_request_ids, clear_all_request_ids
from models.user import User, users_collection
from models.global_settings import GlobalSettings
from auth.jwt_auth import create_access_token, verify_token
from backend.middleware import require_auth, require_admin

app = Flask(__name__)
CORS(app, supports_credentials=True)

# Global state for automation
active_workers = []
stop_flag = threading.Event()

# ==================== AUTHENTICATION ENDPOINTS ====================

# Register endpoint removed - users must be created by admin

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password are required"
            }), 400
        
        user = User.authenticate(username, password)
        
        if user:
            # Create token
            token = create_access_token({
                'sub': user['_id'],
                'username': user['username'],
                'role': user['role']
            })
            return jsonify({
                "success": True,
                "token": token,
                "user": user
            })
        else:
            return jsonify({
                "success": False,
                "error": "Invalid username or password"
            }), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/auth/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current authenticated user"""
    return jsonify({
        "success": True,
        "user": request.current_user
    })

@app.route('/api/auth/settings', methods=['PUT'])
@require_auth
def update_settings():
    """Update user settings - Users can only update API settings"""
    try:
        data = request.json or {}
        user_id = request.current_user['_id']
        
        # Users can only update API settings (country_code, operator, service are now global)
        allowed_fields = ['api_url', 'api_key']
        settings = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not settings:
            return jsonify({
                "success": False,
                "error": "No valid settings provided"
            }), 400
        
        result = User.update_user_settings(user_id, settings)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== PUBLIC ENDPOINTS ====================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint - checks both server and database"""
    from models.user import _db_connected, client
    
    health_status = {
        "server": "ok",
        "database": "connected" if _db_connected else "disconnected"
    }
    
    # Test database connection if not already connected
    if not _db_connected:
        try:
            if client:
                client.admin.command('ping')
                health_status["database"] = "connected"
            else:
                health_status["database"] = "not_configured"
        except:
            health_status["database"] = "disconnected"
            health_status["database_error"] = "MongoDB is not running. Please start MongoDB service."
    
    status_code = 200 if health_status["database"] == "connected" else 503
    return jsonify(health_status), status_code

# ==================== PROTECTED API ENDPOINTS ====================

def get_user_api_config():
    """Get API configuration from current user and global settings"""
    try:
        user = request.current_user
        global_settings = GlobalSettings.get_settings()
        return {
            'api_key': user.get('api_key', ''),
            'api_url': user.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php'),
            'country': global_settings.get('country_code', '22'),
            'operator': global_settings.get('operator', '1'),
            'service': global_settings.get('service', 'pfk')
        }
    except Exception as e:
        # Fallback to defaults if there's an error
        print(f"Error in get_user_api_config: {e}")
        user = request.current_user
        return {
            'api_key': user.get('api_key', ''),
            'api_url': user.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php'),
            'country': '22',
            'operator': '1',
            'service': 'pfk'
        }

@app.route('/api/balance', methods=['GET'])
@require_auth
def balance():
    try:
        config = get_user_api_config()
        if not config.get('api_key'):
            return jsonify({
                "success": False,
                "error": "API key not configured. Please set your API key in Settings."
            }), 400
        raw = get_balance(config['api_key'], config['api_url'])
        parsed = parse_balance(raw)
        return jsonify({
            "success": True,
            "raw": raw,
            "balance": parsed
        })
    except Exception as e:
        import traceback
        print(f"Error in balance endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/price', methods=['GET'])
@require_auth
def price():
    try:
        config = get_user_api_config()
        if not config.get('api_key'):
            return jsonify({
                "success": False,
                "error": "API key not configured. Please set your API key in Settings."
            }), 400
        country = request.args.get('country', config['country'])
        operator = request.args.get('operator', config['operator'])
        service = request.args.get('service', config['service'])
        
        price = get_price_for_service(
            service=service,
            country=country,
            operator=operator,
            api_key=config['api_key'],
            base_url=config['api_url']
        )
        return jsonify({
            "success": True,
            "price": price
        })
    except Exception as e:
        import traceback
        print(f"Error in price endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/prices', methods=['GET'])
@require_auth
def prices():
    try:
        config = get_user_api_config()
        country = request.args.get('country', config['country'])
        operator = request.args.get('operator', config['operator'])
        
        raw = get_prices(country=country, operator=operator, api_key=config['api_key'], base_url=config['api_url'])
        parsed = parse_prices(raw)
        return jsonify({
            "success": True,
            "prices": parsed
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/number', methods=['POST'])
@require_auth
def number():
    try:
        config = get_user_api_config()
        data = request.json or {}
        service = data.get('service', config['service'])
        country = data.get('country', config['country'])
        operator = data.get('operator', config['operator'])
        
        result = get_number(
            service=service,
            country=country,
            operator=operator,
            api_key=config['api_key'],
            base_url=config['api_url']
        )
        
        if result:
            request_id, phone_number = result
            return jsonify({
                "success": True,
                "request_id": request_id,
                "phone_number": phone_number
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to get number"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/otp', methods=['POST'])
@require_auth
def otp():
    try:
        config = get_user_api_config()
        data = request.json or {}
        request_id = data.get('request_id')
        timeout = data.get('timeout', 120.0)
        poll_interval = data.get('poll_interval', 2.0)
        
        if not request_id:
            return jsonify({
                "success": False,
                "error": "request_id is required"
            }), 400
        
        otp = get_otp(
            request_id=request_id,
            api_key=config['api_key'],
            base_url=config['api_url'],
            timeout_seconds=timeout,
            poll_interval=poll_interval
        )
        
        return jsonify({
            "success": True,
            "otp": otp
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/cancel', methods=['POST'])
@require_auth
def cancel():
    try:
        config = get_user_api_config()
        data = request.json or {}
        request_id = data.get('request_id')
        
        if not request_id:
            return jsonify({
                "success": False,
                "error": "request_id is required"
            }), 400
        
        result = cancel_number(request_id, config['api_key'], config['api_url'])
        status = parse_cancel_status(result)
        
        return jsonify({
            "success": True,
            "status": status,
            "raw": result
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/start', methods=['POST'])
@require_auth
def automation_start():
    try:
        config = get_user_api_config()
        data = request.json or {}
        name = data.get('name', '')
        house_flat_no = data.get('house_flat_no', '')
        landmark = data.get('landmark', '')
        
        if not name or not house_flat_no or not landmark:
            return jsonify({
                "success": False,
                "error": "Name, house_flat_no, and landmark are required"
            }), 400
        
        # Clear stop flag
        stop_flag.clear()
        
        # Set user config in environment
        env = os.environ.copy()
        env['AUTOMATION_NAME'] = name
        env['AUTOMATION_HOUSE_FLAT'] = house_flat_no
        env['AUTOMATION_LANDMARK'] = landmark
        env['API_KEY'] = config['api_key']
        env['API_URL'] = config['api_url']
        env['COUNTRY'] = config['country']
        env['OPERATOR'] = config['operator']
        env['SERVICE'] = config['service']
        
        # Start automation in background thread
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_script = os.path.join(base_dir, 'main.py')
        
        process = subprocess.Popen(
            [sys.executable, main_script],
            cwd=base_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        active_workers.append(process)
        
        return jsonify({
            "success": True,
            "message": "Automation started"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/stop', methods=['POST'])
@require_auth
def automation_stop():
    try:
        config = get_user_api_config()
        # Set stop flag
        stop_flag.set()
        
        # Get all active request IDs from shared state
        request_ids = get_all_request_ids()
        
        # Cancel all active numbers
        cancelled_count = 0
        for request_id in request_ids:
            try:
                cancel_number(request_id, config['api_key'], config['api_url'])
                cancelled_count += 1
            except Exception as e:
                print(f"Error cancelling {request_id}: {e}")
        
        # Terminate all active workers
        for process in active_workers[:]:
            try:
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
            except Exception as e:
                print(f"Error terminating process: {e}")
        
        # Clear lists and shared state
        active_workers.clear()
        clear_all_request_ids()
        
        return jsonify({
            "success": True,
            "message": f"Stopped all workers and cancelled {cancelled_count} numbers"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ==================== ADMIN ENDPOINTS ====================

@app.route('/api/admin/users', methods=['GET'])
@require_admin
def get_all_users():
    """Get all users (admin only)"""
    users = User.get_all_users()
    return jsonify({
        "success": True,
        "users": users
    })

@app.route('/api/admin/users', methods=['POST'])
@require_admin
def create_user_admin():
    """Create a new user (admin only)"""
    try:
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '')
        role = data.get('role', 'user')
        api_url = data.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php')
        api_key = data.get('api_key', '')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username and password are required"
            }), 400
        
        result = User.create_user(
            username=username,
            password=password,
            role=role,
            api_url=api_url,
            api_key=api_key
        )
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/admin/global-settings', methods=['GET'])
@require_admin
def get_global_settings():
    """Get global settings (admin only)"""
    try:
        settings = GlobalSettings.get_settings()
        return jsonify({
            "success": True,
            "settings": settings
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/admin/global-settings', methods=['PUT'])
@require_admin
def update_global_settings():
    """Update global settings (admin only) - country_code, operator, service"""
    try:
        data = request.json or {}
        
        country_code = data.get('country_code')
        operator = data.get('operator')
        service = data.get('service')
        
        # Only update fields that are provided
        update_data = {}
        if country_code is not None:
            update_data['country_code'] = country_code
        if operator is not None:
            update_data['operator'] = operator
        if service is not None:
            update_data['service'] = service
        
        if not update_data:
            return jsonify({
                "success": False,
                "error": "No settings provided to update"
            }), 400
        
        result = GlobalSettings.update_settings(
            country_code=country_code,
            operator=operator,
            service=service
        )
        
        return jsonify(result)
        
    except Exception as e:
        import traceback
        print(f"Error in update_global_settings endpoint: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/admin/users/<user_id>', methods=['DELETE'])
@require_admin
def delete_user(user_id):
    """Delete a user (admin only)"""
    try:
        from bson import ObjectId
        from models.user import users_collection
        
        result = users_collection.delete_one({'_id': ObjectId(user_id)})
        
        if result.deleted_count > 0:
            return jsonify({
                "success": True,
                "message": "User deleted successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
