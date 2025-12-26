"""
Shared state for tracking active request IDs across processes
"""
import threading

# Thread-safe storage
_lock = threading.Lock()
_active_request_ids = []

def add_request_id(request_id):
    """Add a request ID to the active list"""
    with _lock:
        if request_id not in _active_request_ids:
            _active_request_ids.append(request_id)

def remove_request_id(request_id):
    """Remove a request ID from the active list"""
    with _lock:
        if request_id in _active_request_ids:
            _active_request_ids.remove(request_id)

def get_all_request_ids():
    """Get a copy of all active request IDs"""
    with _lock:
        return _active_request_ids.copy()

def clear_all_request_ids():
    """Clear all active request IDs"""
    with _lock:
        _active_request_ids.clear()


