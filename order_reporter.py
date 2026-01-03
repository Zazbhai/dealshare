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
            writer.writerow(['timestamp', 'screenshot_url', 'status', 'pastebin_url'])

def save_order_to_csv(screenshot_url, status='success', worker_log_path=None, order_number=None):
    """
    Save order information to CSV file
    
    Args:
        screenshot_url: URL of the uploaded screenshot
        status: 'success' or 'failed' (or 'Failed - reason')
        worker_log_path: Path to worker log file (for failed orders)
        order_number: Order number for log identification
    """
    ensure_csv_exists()
    
    pastebin_url = ''
    
    # If order failed, save log locally
    if status != 'success' and status.lower().startswith('failed'):
        try:
            # Setup failed_logs directory
            failed_logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'failed_logs')
            os.makedirs(failed_logs_dir, exist_ok=True)
            
            # Read worker log if path provided
            log_content = ''
            if worker_log_path and os.path.exists(worker_log_path):
                with open(worker_log_path, 'r', encoding='utf-8', errors='replace') as f:
                    log_content = f.read()
            
            # Create comprehensive log with screenshot URL
            full_log = f"=== FAILED ORDER LOG ===\n"
            full_log += f"Order Number: {order_number or 'Unknown'}\n"
            full_log += f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            full_log += f"Status: {status}\n"
            full_log += f"Screenshot: {screenshot_url or 'N/A'}\n"
            full_log += f"\n{'='*50}\n"
            full_log += f"WORKER LOG:\n"
            full_log += f"{'='*50}\n\n"
            full_log += log_content if log_content else "No log file available"
            
            # Save to local file
            timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_filename = f"failed_order_{order_number or 'unknown'}_{timestamp_str}.txt"
            log_filepath = os.path.join(failed_logs_dir, log_filename)
            
            with open(log_filepath, 'w', encoding='utf-8') as f:
                f.write(full_log)
                
            print(f"✅ Saved failed order log to: {log_filepath}")
            pastebin_url = log_filepath
            
        except Exception as e:
            print(f"[ERROR] Failed to save local log: {e}")
            pastebin_url = ''
    
    with _csv_lock:
        try:
            with open(_csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                writer.writerow([timestamp, screenshot_url or '', status, pastebin_url])
        except Exception as e:
            print(f"[ERROR] Failed to save order to CSV: {e}")

