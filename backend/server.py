from flask import Flask, jsonify, request, send_from_directory
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

def log_output(process, process_name="Worker"):
    """Read and print subprocess output in real-time"""
    def read_stdout():
        try:
            for line in iter(process.stdout.readline, b''):
                if line:
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    print(f"[{process_name} STDOUT] {decoded}")
        except Exception as e:
            print(f"[ERROR] Error reading stdout for {process_name}: {e}")
    
    def read_stderr():
        try:
            for line in iter(process.stderr.readline, b''):
                if line:
                    decoded = line.decode('utf-8', errors='replace').rstrip()
                    print(f"[{process_name} STDERR] {decoded}")
        except Exception as e:
            print(f"[ERROR] Error reading stderr for {process_name}: {e}")
    
    stdout_thread = threading.Thread(target=read_stdout, daemon=True)
    stderr_thread = threading.Thread(target=read_stderr, daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    return stdout_thread, stderr_thread

# ==================== AUTHENTICATION ENDPOINTS ====================

# Register endpoint removed - users must be created by admin

@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        from models.user import _db_connected
        if not _db_connected:
            return jsonify({
                "success": False,
                "error": "Database connection failed. Please check your MongoDB connection and try again."
            }), 503
        
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
    """Get current authenticated user with settings from JSON file"""
    try:
        user = request.current_user.copy()
        user_id = user.get('_id')
        
        # Load settings from JSON file
        from user_settings_storage import load_user_settings
        settings = load_user_settings(user_id)
        
        # Merge settings into user object
        user.update(settings)
        
        return jsonify({
            "success": True,
            "user": user
        })
    except Exception as e:
        # Fallback to just returning user if settings loading fails
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
        
        # Debug: Print received data
        print(f"[DEBUG] update_settings - Received data keys: {list(data.keys())}")
        print(f"[DEBUG] update_settings - Received data: {data}")
        
        # Users can update API settings, dashboard settings, product URLs, location settings, etc.
        allowed_fields = [
            'api_key',
            'name',
            'house_flat_no',
            'landmark',
            'total_orders',
            'max_parallel_windows',
            'retry_orders',
            'products',
            'order_all',
            # Keep old fields for backward compatibility (will be converted to products)
            'primary_product_url',
            'secondary_product_url',
            'third_product_url',
            'primary_product_quantity',
            'secondary_product_quantity',
            'third_product_quantity',
            'latitude',
            'longitude',
            'select_location_enabled',
            'search_input',
            'location_text'
        ]
        # Filter settings to only include allowed fields
        # Note: We include all values (including empty arrays, False, etc.) as they are valid
        settings = {k: v for k, v in data.items() if k in allowed_fields}
        
        # Debug: Print filtered settings
        print(f"[DEBUG] update_settings - Filtered settings keys: {list(settings.keys())}")
        print(f"[DEBUG] update_settings - Filtered settings: {settings}")
        
        # CRITICAL: Strip whitespace from API key when saving
        if 'api_key' in settings and settings['api_key']:
            api_key_raw = settings['api_key']
            settings['api_key'] = api_key_raw.strip()
        
        # Validate that we have at least one setting to update
        # Empty arrays and False values are valid, so we check if dict is not empty
        if not settings:
            print(f"[DEBUG] update_settings - ERROR: No valid settings after filtering.")
            print(f"[DEBUG] update_settings - Original data: {data}")
            print(f"[DEBUG] update_settings - Allowed fields: {allowed_fields}")
            return jsonify({
                "success": False,
                "error": "No valid settings provided"
            }), 400
        
        # Validate products array if present
        if 'products' in settings:
            print(f"[DEBUG] update_settings - Validating products array: {settings['products']}")
            if not isinstance(settings['products'], list):
                print(f"[DEBUG] update_settings - ERROR: products is not a list, type: {type(settings['products'])}")
                return jsonify({
                    "success": False,
                    "error": "Products must be an array"
                }), 400
            # Filter out products with empty URLs
            print(f"[DEBUG] update_settings - Products before filtering: {settings['products']}")
            valid_products = []
            for p in settings['products']:
                url = p.get('url', '') if isinstance(p, dict) else ''
                if url and str(url).strip():
                    valid_products.append(p)
                else:
                    print(f"[DEBUG] update_settings - Filtered out product (empty URL): {p}")
            
            print(f"[DEBUG] update_settings - Valid products after filtering: {valid_products}")
            if len(valid_products) == 0:
                print(f"[DEBUG] update_settings - ERROR: No valid products after filtering")
                return jsonify({
                    "success": False,
                    "error": "At least one product with a valid URL is required"
                }), 400
            # Update settings with only valid products
            settings['products'] = valid_products
            print(f"[DEBUG] update_settings - Final products in settings: {settings['products']}")
        
        # Save settings to JSON file instead of database
        print(f"[DEBUG] update_settings - About to save settings to JSON file")
        print(f"[DEBUG] update_settings - User ID: {user_id}")
        print(f"[DEBUG] update_settings - Settings to save: {settings}")
        
        try:
            try:
                from backend.user_settings_storage import save_user_settings
            except ImportError:
                # Fallback for different import paths
                try:
                    from user_settings_storage import save_user_settings
                except ImportError:
                    import sys
                    import os
                    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                    from user_settings_storage import save_user_settings
            result = save_user_settings(user_id, settings)
            print(f"[DEBUG] update_settings - Save result: {result}")
            
            if result.get('success'):
                print(f"[DEBUG] update_settings - Settings saved successfully to JSON file")
            else:
                print(f"[DEBUG] update_settings - Failed to save settings: {result.get('error')}")
            
            return jsonify(result)
        except ImportError as e:
            print(f"[ERROR] update_settings - Failed to import user_settings_storage: {e}")
            return jsonify({
                "success": False,
                "error": f"Failed to import settings storage: {str(e)}"
            }), 500
        except Exception as e:
            print(f"[ERROR] update_settings - Exception while saving: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({
                "success": False,
                "error": f"Failed to save settings: {str(e)}"
            }), 500
        
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

@app.route('/api/orders/report', methods=['GET'])
@require_auth
def get_orders_report():
    """Get orders report with success/failed separation"""
    try:
        import csv
        csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'my_orders.csv')
        
        if not os.path.exists(csv_file):
            return jsonify({
                "success": True,
                "orders": {
                    "success": [],
                    "failed": []
                }
            })
        
        success_orders = []
        failed_orders = []
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                order_data = {
                    "timestamp": row.get('timestamp', ''),
                    "screenshot_url": row.get('screenshot_url', ''),
                    "status": row.get('status', ''),
                    "pastebin_url": row.get('pastebin_url', '')
                }
                
                # Categorize based on status (case-insensitive)
                if str(order_data['status']).lower() == 'success':
                    success_orders.append(order_data)
                else:
                    failed_orders.append(order_data)
        
        # Sort by timestamp descending (latest first)
        success_orders.sort(key=lambda x: x['timestamp'], reverse=True)
        failed_orders.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({
            "success": True,
            "orders": {
                "success": success_orders,
                "failed": failed_orders
            },
            "total": {
                "success": len(success_orders),
                "failed": len(failed_orders)
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/orders/download', methods=['GET'])
@require_auth
def download_orders():
    """Download orders CSV file"""
    try:
        csv_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'my_orders.csv')
        
        if not os.path.exists(csv_file):
            return jsonify({
                "success": False,
                "error": "No orders file found"
            }), 404
        
        return send_file(
            csv_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name='my_orders.csv'
        )
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/orders/clear', methods=['DELETE'])
@require_auth
def clear_orders():
    """Clear all orders and screenshots"""
    try:
        import csv
        
        base_dir = os.path.dirname(os.path.dirname(__file__))
        
        # 1. Clear Screenshots
        screenshots_dir = os.path.join(base_dir, 'screenshots')
        if os.path.exists(screenshots_dir):
            for filename in os.listdir(screenshots_dir):
                file_path = os.path.join(screenshots_dir, filename)
                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")
        
        # 2. Clear CSV (keep header)
        csv_file = os.path.join(base_dir, 'my_orders.csv')
        if os.path.exists(csv_file):
            header = None
            try:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    header = f.readline()
                
                # If file was empty or header is empty/whitespace, set default
                if not header or not header.strip():
                     header = "Timestamp,Screenshot URL,Status\n"
                     
                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                    f.write(header)
            except Exception as e:
                # If error reading/writing, restore default header
                with open(csv_file, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "Screenshot URL", "Status"])
                    
        return jsonify({
            "success": True,
            "message": "All reports and screenshots cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==================== PROTECTED API ENDPOINTS ====================

def get_user_api_config():
    """Get API configuration from current user and global settings"""
    try:
        user = request.current_user
        user_id = user.get('_id') if user else None
        
        # Load settings from JSON file
        try:
            from backend.user_settings_storage import load_user_settings
        except ImportError:
            # Fallback for different import paths
            try:
                from user_settings_storage import load_user_settings
            except ImportError:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from user_settings_storage import load_user_settings
        settings = load_user_settings(user_id) if user_id else {}
        
        # Get API key from JSON settings (preferred) or user object (fallback)
        api_key_raw = settings.get('api_key', '') or (user.get('api_key', '') if user else '')
        
        # CRITICAL: Strip whitespace from API key (common issue)
        api_key = api_key_raw.strip() if api_key_raw else ''
        
        # Debug: Print user info (without sensitive data)
        print(f"[DEBUG] get_user_api_config - User: {user.get('username', 'unknown') if user else 'None'}")
        print(f"[DEBUG] get_user_api_config - API key present: {bool(api_key)}")
        print(f"[DEBUG] get_user_api_config - API key length: {len(api_key) if api_key else 0}")
        
        # Debug API key (masked) with detailed info
        if api_key:
            masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****'
            print(f"[DEBUG] get_user_api_config - API key (masked): {masked}")
        else:
            print(f"[DEBUG] get_user_api_config - WARNING: API key is empty!")
        
        global_settings = GlobalSettings.get_settings()
        api_url = global_settings.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php')
        print(f"[DEBUG] get_user_api_config - API URL from global settings: {api_url}")
        
        config = {
            'api_key': api_key,  # Use stripped version
            'api_url': api_url,
            'country': global_settings.get('country_code', '22'),
            'operator': global_settings.get('operator', '1'),
            'service': global_settings.get('service', 'pfk')
        }
        return config
    except Exception as e:
        # Fallback to defaults if there's an error
        print(f"[ERROR] Error in get_user_api_config: {e}")
        import traceback
        traceback.print_exc()
        user = request.current_user
        api_key = user.get('api_key', '') if user else ''
        global_settings = GlobalSettings.get_settings()
        return {
            'api_key': api_key,
            'api_url': global_settings.get('api_url', 'https://api.temporasms.com/stubs/handler_api.php'),
            'country': global_settings.get('country_code', '22'),
            'operator': global_settings.get('operator', '1'),
            'service': global_settings.get('service', 'pfk')
        }

@app.route('/api/balance', methods=['GET'])
@require_auth
def balance():
    try:
        config = get_user_api_config()
        api_key = config.get('api_key', '') if config else ''
        api_url = config.get('api_url', '') if config else ''
        
        print(f"[DEBUG] balance endpoint - API key present: {bool(api_key)}")
        print(f"[DEBUG] balance endpoint - API URL: {api_url}")
        
        if not config or not api_key or not api_key.strip():
            print(f"[DEBUG] balance endpoint - API key validation failed")
            return jsonify({
                "success": False,
                "error": "API key not configured. Please set your API key in Settings."
            }), 400
        
        print(f"[DEBUG] balance endpoint - Calling get_balance with API key length: {len(api_key)}")
        raw = get_balance(config['api_key'], config['api_url'])
        
        parsed = parse_balance(raw)
        
        return jsonify({
            "success": True,
            "raw": raw,
            "balance": parsed
        })
    except ValueError as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"[ERROR] API authentication failed - invalid API key")
            return jsonify({
                "success": False,
                "error": "Invalid API key. Please check your API credentials in Settings."
            }), 401
        else:
            print(f"[ERROR] API error: {e}")
            return jsonify({
                "success": False,
                "error": f"API error: {error_msg}"
            }), 400
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in balance endpoint: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
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
        api_key = config.get('api_key', '') if config else ''
        
        if not config or not api_key or not api_key.strip():
            return jsonify({
                "success": False,
                "error": "API key not configured. Please set your API key in Settings."
            }), 400
        
        country = request.args.get('country', config.get('country', '22'))
        operator = request.args.get('operator', config.get('operator', '1'))
        service = request.args.get('service', config.get('service', 'pfk'))
        
        
        price_result = get_price_for_service(
            service=service,
            country=country,
            operator=operator,
            api_key=config['api_key'],
            base_url=config['api_url']
        )
        
        return jsonify({
            "success": True,
            "price": price_result
        })
    except ValueError as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg:
            print(f"[ERROR] API authentication failed - invalid API key")
            return jsonify({
                "success": False,
                "error": "Invalid API key. Please check your API credentials in Settings."
            }), 401
        else:
            print(f"[ERROR] API error: {e}")
            return jsonify({
                "success": False,
                "error": f"API error: {error_msg}"
            }), 400
    except Exception as e:
        import traceback
        print(f"[ERROR] Error in price endpoint: {e}")
        print(f"[ERROR] Exception type: {type(e).__name__}")
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



@app.route('/api/logs/list', methods=['GET'])
@require_auth
def get_logs_list():
    """Get list of log files"""
    try:
        import os
        from datetime import datetime
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        
        if not os.path.exists(logs_dir):
            return jsonify({
                "success": True,
                "logs": []
            })
        
        log_files = []
        for filename in os.listdir(logs_dir):
            if filename.endswith('.log') or filename.endswith('.txt'):
                filepath = os.path.join(logs_dir, filename)
                stat = os.stat(filepath)
                log_files.append({
                    "filename": filename,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
        
        # Sort by modified time (newest first)
        log_files.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            "success": True,
            "logs": log_files
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/logs/view/<filename>', methods=['GET'])
@require_auth
def view_log_file(filename):
    """View log file content"""
    try:
        import os
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        filepath = os.path.join(logs_dir, filename)
        
        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(logs_dir)):
            return jsonify({
                "success": False,
                "error": "Invalid filename"
            }), 400
        
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": "Log file not found"
            }), 404
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        return jsonify({
            "success": True,
            "filename": filename,
            "content": content
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/logs/download/<filename>', methods=['GET'])
@require_auth
def download_log_file(filename):
    """Download log file"""
    try:
        import os
        from flask import send_file
        logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
        filepath = os.path.join(logs_dir, filename)
        
        # Security: prevent directory traversal
        if not os.path.abspath(filepath).startswith(os.path.abspath(logs_dir)):
            return jsonify({
                "success": False,
                "error": "Invalid filename"
            }), 400
        
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": "Log file not found"
            }), 404
        
        return send_file(
            filepath,
            mimetype='text/plain',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/debug/test-api-key', methods=['GET'])
@require_auth
def test_api_key():
    """Debug endpoint to test API key and show exact URL being sent"""
    try:
        config = get_user_api_config()
        api_key = config.get('api_key', '')
        api_url = config.get('api_url', '')
        
        if not api_key:
            return jsonify({
                "success": False,
                "error": "API key not configured"
            }), 400
        
        # Construct the exact URL that will be sent
        from urllib import parse
        test_params = {"action": "getBalance", "api_key": api_key}
        test_url = f"{api_url}?{parse.urlencode(test_params)}"
        
        print(f"  API Key: {api_key}")
        print(f"  API URL: {api_url}")
        print(f"  Full Test URL: {test_url}")
        print(f"  ⚠️  COPY THIS URL AND TEST IT IN YOUR BROWSER")
        
        # Try to make the actual request
        try:
            from api_dynamic import get_balance
            raw = get_balance(api_key, api_url)
            return jsonify({
                "success": True,
                "message": "API key is valid!",
                "response": raw,
                "test_url": test_url,
                "api_key_length": len(api_key),
                "api_key_first_8": api_key[:8],
                "api_key_last_4": api_key[-4:]
            })
        except ValueError as e:
            error_msg = str(e)
            return jsonify({
                "success": False,
                "error": error_msg,
                "test_url": test_url,
                "api_key_length": len(api_key),
                "api_key_first_8": api_key[:8],
                "api_key_last_4": api_key[-4:],
                "message": "API key test failed. Copy the test_url above and test it in your browser to verify."
            }), 401
    except Exception as e:
        import traceback
        traceback.print_exc()
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
        total_orders = data.get('total_orders', 1)  # Default to 1 if not specified
        max_parallel_windows = data.get('max_parallel_windows', 1)  # Default to 1 if not specified
        # Get products array (new format) or convert from old format
        products = data.get('products', [])
        
        # Convert from old format if products array is not provided (backward compatibility)
        if not products or len(products) == 0:
            products = []
            if data.get('primary_product_url'):
                products.append({
                    'url': data.get('primary_product_url', ''),
                    'quantity': int(data.get('primary_product_quantity', '1'))
                })
            if data.get('secondary_product_url'):
                products.append({
                    'url': data.get('secondary_product_url', ''),
                    'quantity': int(data.get('secondary_product_quantity', '1'))
                })
            if data.get('third_product_url'):
                products.append({
                    'url': data.get('third_product_url', ''),
                    'quantity': int(data.get('third_product_quantity', '1'))
                })
        
        # Validate products
        valid_products = [p for p in products if p.get('url') and p.get('url', '').strip()]
        if len(valid_products) == 0:
            return jsonify({
                "success": False,
                "error": "At least one product URL is required"
            }), 400
        
        order_all = data.get('order_all', False)
        retry_orders = data.get('retry_orders', False)
        latitude = data.get('latitude', '26.994880')
        longitude = data.get('longitude', '75.774836')
        select_location = data.get('select_location', True)
        search_input = data.get('search_input', 'chinu juice center')
        location_text = data.get('location_text', 'Chinu Juice Center, Jaswant Nagar, mod, Khatipura, Jaipur, Rajasthan, India')
        
        if not name or not house_flat_no or not landmark:
            return jsonify({
                "success": False,
                "error": "Name, house_flat_no, and landmark are required"
            }), 400
        
        # Products validation is done above
        
        # Validate numeric inputs
        try:
            total_orders = int(total_orders)
            max_parallel_windows = int(max_parallel_windows)
            if total_orders < 1:
                return jsonify({
                    "success": False,
                    "error": "Total orders must be at least 1"
                }), 400
            if max_parallel_windows < 1:
                return jsonify({
                    "success": False,
                    "error": "Max parallel windows must be at least 1"
                }), 400
            if max_parallel_windows > total_orders:
                max_parallel_windows = total_orders  # Cap max_parallel_windows to total_orders
        except (ValueError, TypeError):
            return jsonify({
                "success": False,
                "error": "total_orders and max_parallel_windows must be valid numbers"
            }), 400
        
        # Clear stop flag
        stop_flag.clear()
        
        # Clear/Initialize status file
        try:
            import json
            from datetime import datetime
            status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automation_status.json')
            status_data = {
                "is_running": True,
                "success": 0,
                "failure": 0,
                "all_products_failed": False,
                "start_time": datetime.now().isoformat(),
                "end_time": None
            }
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f)
            print(f"[INFO] Status file initialized: {status_file}")
        except Exception as e:
            print(f"[WARNING] Failed to initialize status file: {e}")
        
        # Clear logs folder before starting new batch
        try:
            import shutil
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
            if os.path.exists(logs_dir):
                # Remove all files in logs directory
                for filename in os.listdir(logs_dir):
                    filepath = os.path.join(logs_dir, filename)
                    try:
                        if os.path.isfile(filepath):
                            os.remove(filepath)
                        elif os.path.isdir(filepath):
                            shutil.rmtree(filepath)
                    except Exception as e:
                        print(f"[WARNING] Failed to remove {filepath}: {e}")
                print(f"[INFO] Logs folder cleared: {logs_dir}")
            else:
                # Create logs directory if it doesn't exist
                os.makedirs(logs_dir, exist_ok=True)
                print(f"[INFO] Created logs directory: {logs_dir}")
        except Exception as e:
            print(f"[WARNING] Failed to clear logs folder: {e}")
            import traceback
            traceback.print_exc()
        
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
        env['TOTAL_ORDERS'] = str(total_orders)
        env['MAX_PARALLEL_WINDOWS'] = str(max_parallel_windows)
        
        # Pass products as JSON string
        import json
        env['PRODUCTS_JSON'] = json.dumps(valid_products)
        
        # For backward compatibility, also set first 3 as PRIMARY/SECONDARY/THIRD
        if len(valid_products) > 0:
            env['PRIMARY_PRODUCT_URL'] = valid_products[0].get('url', '')
            env['PRIMARY_PRODUCT_QUANTITY'] = str(valid_products[0].get('quantity', 1))
        else:
            env['PRIMARY_PRODUCT_URL'] = ''
            env['PRIMARY_PRODUCT_QUANTITY'] = '1'
            
        if len(valid_products) > 1:
            env['SECONDARY_PRODUCT_URL'] = valid_products[1].get('url', '')
            env['SECONDARY_PRODUCT_QUANTITY'] = str(valid_products[1].get('quantity', 1))
        else:
            env['SECONDARY_PRODUCT_URL'] = ''
            env['SECONDARY_PRODUCT_QUANTITY'] = '1'
            
        if len(valid_products) > 2:
            env['THIRD_PRODUCT_URL'] = valid_products[2].get('url', '')
            env['THIRD_PRODUCT_QUANTITY'] = str(valid_products[2].get('quantity', 1))
        else:
            env['THIRD_PRODUCT_URL'] = ''
            env['THIRD_PRODUCT_QUANTITY'] = '1'
        
        env['ORDER_ALL'] = '1' if order_all else '0'
        env['RETRY_ORDERS'] = '1' if retry_orders else '0'
        env['LATITUDE'] = str(latitude)
        env['LONGITUDE'] = str(longitude)
        env['SELECT_LOCATION'] = '1' if select_location else '0'
        env['SEARCH_INPUT'] = search_input
        env['LOCATION_TEXT'] = location_text
        
        # Start automation worker that will manage parallel execution
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        worker_script = os.path.join(base_dir, 'automation_worker.py')
        
        
        process = subprocess.Popen(
            [sys.executable, '-u', worker_script],  # -u flag for unbuffered output
            cwd=base_dir,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
            universal_newlines=False  # Keep as bytes for better handling
        )
        
        
        # Start reading output in background threads
        log_output(process, f"Worker-{process.pid}")
        
        active_workers.append(process)
        
        response_data = {
            "success": True,
            "message": f"Automation started: {total_orders} orders, max {max_parallel_windows} parallel windows",
            "total_orders": total_orders,
            "max_parallel_windows": max_parallel_windows
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"[ERROR SERVER] Exception in automation_start: {e}")
        import traceback
        print(f"[ERROR SERVER] Traceback:")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/automation/status', methods=['GET'])
@require_auth
def automation_status():
    """Get current automation status"""
    try:
        import json
        import os
        status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automation_status.json')
        
        if not os.path.exists(status_file):
            return jsonify({
                "success": True,
                "is_running": False,
                "success": 0,
                "failure": 0,
                "all_products_failed": False
            })
        
        try:
            with open(status_file, 'r', encoding='utf-8') as f:
                status_data = json.load(f)
            # Ensure all_products_failed is included (for backward compatibility)
            if 'all_products_failed' not in status_data:
                status_data['all_products_failed'] = False
            return jsonify({
                "success": True,
                "is_running": status_data.get('is_running', False),
                "success_count": status_data.get('success', 0),
                "failure_count": status_data.get('failure', 0),
                "all_products_failed": status_data.get('all_products_failed', False),
                "start_time": status_data.get('start_time'),
                "end_time": status_data.get('end_time')
            })
        except Exception as e:
            print(f"[ERROR] Failed to read status file: {e}")
            return jsonify({
                "success": True,
                "is_running": False,
                "success": 0,
                "failure": 0,
                "all_products_failed": False
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
        
        # Update status file to mark as stopped
        try:
            import json
            import os
            from datetime import datetime
            status_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automation_status.json')
            if os.path.exists(status_file):
                with open(status_file, 'r', encoding='utf-8') as f:
                    status_data = json.load(f)
                status_data['is_running'] = False
                status_data['end_time'] = datetime.now().isoformat()
                with open(status_file, 'w', encoding='utf-8') as f:
                    json.dump(status_data, f)
        except Exception as e:
            print(f"[WARNING] Failed to update status file on stop: {e}")
        
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

@app.route('/api/global-settings', methods=['GET'])
@require_auth
def get_global_settings_user():
    """Get global settings for users (price only)"""
    try:
        settings = GlobalSettings.get_settings()
        # Users can only see price, not other settings
        return jsonify({
            "success": True,
            "price": settings.get('price', 0.0)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/admin/global-settings', methods=['PUT'])
@require_admin
def update_global_settings():
    """Update global settings (admin only) - api_url, country_code, operator, service, price"""
    try:
        data = request.json or {}
        
        api_url = data.get('api_url')
        country_code = data.get('country_code')
        operator = data.get('operator')
        service = data.get('service')
        price = data.get('price')
        
        # Only update fields that are provided
        update_data = {}
        if api_url is not None:
            update_data['api_url'] = api_url
        if country_code is not None:
            update_data['country_code'] = country_code
        if operator is not None:
            update_data['operator'] = operator
        if service is not None:
            update_data['service'] = service
        if price is not None:
            try:
                update_data['price'] = float(price)
            except (ValueError, TypeError):
                return jsonify({
                    "success": False,
                    "error": "Price must be a valid number"
                }), 400
        
        if not update_data:
            return jsonify({
                "success": False,
                "error": "No settings provided to update"
            }), 400
        
        result = GlobalSettings.update_settings(
            api_url=api_url,
            country_code=country_code,
            operator=operator,
            service=service,
            price=price
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


@app.route('/api/logs/failed', methods=['GET'])
@require_auth
def view_failed_log():
    """View content of a failed log file"""
    try:
        filename = request.args.get('filename')
        if not filename:
            return jsonify({
                "success": False,
                "error": "Filename is required"
            }), 400
            
        # Security: Allow only alphanumeric, underscores, dots, and hyphens
        # This prevents directory traversal
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
             return jsonify({
                "success": False,
                "error": "Invalid filename format"
            }), 400

        # Construct path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        failed_logs_dir = os.path.join(base_dir, 'failed_logs')
        filepath = os.path.join(failed_logs_dir, filename)
        
        print(f"[DEBUG] Looking for log file at: {filepath}")
        
        if not os.path.exists(filepath):
            print(f"[DEBUG] File not found at: {filepath}")
            return jsonify({
                "success": False,
                "error": f"Log file not found at: {filepath}",
                "debug_base": base_dir
            }), 404
            
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
            
        return jsonify({
            "success": True,
            "filename": filename,
            "content": content
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/screenshots/view', methods=['GET'])
@require_auth
def view_screenshot():
    """Serve a screenshot file"""
    try:
        filename = request.args.get('filename')
        if not filename:
            return jsonify({
                "success": False,
                "error": "Filename is required"
            }), 400
            
        # Security: Allow only alphanumeric, underscores, dots, and hyphens
        import re
        if not re.match(r'^[a-zA-Z0-9_.-]+$', filename):
             return jsonify({
                "success": False,
                "error": "Invalid filename format"
            }), 400

        # Construct path
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        screenshots_dir = os.path.join(base_dir, 'screenshots')
        filepath = os.path.join(screenshots_dir, filename)
        
        if not os.path.exists(filepath):
            return jsonify({
                "success": False,
                "error": f"Screenshot not found at: {filepath}",
                "debug_base": base_dir
            }), 404
            
        return send_from_directory(screenshots_dir, filename)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# Serve React Frontend (Catch-all route)

if __name__ == '__main__':
    host = os.environ.get('BACKEND_HOST', '0.0.0.0')
    port = int(os.environ.get('BACKEND_PORT', '5000'))
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    app.run(debug=debug_mode, host=host, port=port)
