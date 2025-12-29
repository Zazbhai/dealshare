"""
Utility for saving order reports to CSV
"""
import csv
import os
from datetime import datetime
from threading import Lock

# Thread-safe CSV writing
_csv_lock = Lock()
_csv_file = "my_orders.csv"

def ensure_csv_exists():
    """Create CSV file with headers if it doesn't exist"""
    if not os.path.exists(_csv_file):
        with open(_csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'screenshot_url', 'status'])

def save_order_to_csv(screenshot_url, status='success'):
    """
    Save order information to CSV file
    
    Args:
        screenshot_url: URL of the uploaded screenshot
        status: 'success' or 'failed'
    """
    ensure_csv_exists()
    
    with _csv_lock:
        try:
            with open(_csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp, screenshot_url or '', status])
        except Exception as e:
            print(f"[ERROR] Failed to save order to CSV: {e}")

