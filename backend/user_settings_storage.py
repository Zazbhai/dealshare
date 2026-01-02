"""User settings storage using JSON files"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

# Directory to store user settings JSON files
SETTINGS_DIR = Path(__file__).parent.parent / 'user_settings'

def ensure_settings_dir():
    """Ensure the settings directory exists"""
    SETTINGS_DIR.mkdir(exist_ok=True)

def get_settings_file_path(user_id: str) -> Path:
    """Get the path to a user's settings file"""
    ensure_settings_dir()
    # Sanitize user_id to be filesystem-safe
    safe_user_id = user_id.replace('/', '_').replace('\\', '_').replace('..', '_')
    return SETTINGS_DIR / f"{safe_user_id}.json"

def load_user_settings(user_id: str) -> Dict[str, Any]:
    """Load user settings from JSON file"""
    settings_file = get_settings_file_path(user_id)
    
    if not settings_file.exists():
        return {}
    
    try:
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[WARNING] Failed to load settings for user {user_id}: {e}")
        return {}

def save_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Save user settings to JSON file (merge with existing settings)"""
    print(f"[DEBUG] save_user_settings - User ID: {user_id}")
    print(f"[DEBUG] save_user_settings - Settings received: {settings}")
    print(f"[DEBUG] save_user_settings - Settings keys: {list(settings.keys())}")
    
    ensure_settings_dir()
    settings_file = get_settings_file_path(user_id)
    print(f"[DEBUG] save_user_settings - Settings file path: {settings_file}")
    
    # Load existing settings
    existing_settings = load_user_settings(user_id)
    print(f"[DEBUG] save_user_settings - Existing settings: {existing_settings}")
    
    # Merge new settings with existing
    existing_settings.update(settings)
    print(f"[DEBUG] save_user_settings - Merged settings: {existing_settings}")
    
    try:
        with open(settings_file, 'w', encoding='utf-8') as f:
            json.dump(existing_settings, f, indent=2, ensure_ascii=False)
        print(f"[DEBUG] save_user_settings - Settings saved successfully to {settings_file}")
        return {'success': True, 'message': 'Settings saved successfully'}
    except IOError as e:
        print(f"[ERROR] Failed to save settings for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}
    except Exception as e:
        print(f"[ERROR] Unexpected error saving settings for user {user_id}: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def update_user_settings(user_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
    """Update user settings (same as save_user_settings, but with different name for compatibility)"""
    return save_user_settings(user_id, settings)

