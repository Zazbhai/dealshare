"""
Dynamic API wrapper that accepts API URL and key as parameters
"""
import json
import re
import time
from typing import Any, Dict, Optional, Tuple
from urllib import error, parse, request

def _http_get(params: Dict[str, Any], api_key: str, base_url: str) -> str:
    """
    Perform a GET request with shared base URL and API key.
    Returns raw text from the API or raises ValueError on network/HTTP issues.
    """
    # CRITICAL: Strip whitespace from API key
    api_key = api_key.strip() if api_key else ''
    
    # #region agent log
    import json
    try:
        api_key_masked = api_key[:4] + '*' * (len(api_key) - 8) + api_key[-4:] if len(api_key) > 8 else '****' if api_key else ''
        with open(r'c:\Users\zgarm\OneDrive\Desktop\Deal share\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"api_dynamic.py:10","message":"_http_get entry","data":{"api_key_length":len(api_key),"api_key_masked":api_key_masked,"base_url":base_url,"params":params},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})+"\n")
    except: pass
    # #endregion
    
    # Validate API key before making request
    if not api_key:
        raise ValueError("API key is empty or None")
    
    merged = {"api_key": api_key, **params}
    url = f"{base_url}?{parse.urlencode(merged)}"
    # #region agent log
    try:
        url_masked = url.split('api_key=')[0] + 'api_key=' + api_key_masked if 'api_key=' in url else url
        with open(r'c:\Users\zgarm\OneDrive\Desktop\Deal share\.cursor\debug.log', 'a', encoding='utf-8') as f:
            f.write(json.dumps({"location":"api_dynamic.py:16","message":"URL constructed","data":{"url_masked":url_masked},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"D"})+"\n")
    except: pass
    # #endregion
    

    try:
        with request.urlopen(url, timeout=15) as resp:
            # API returns plain text like: ACCESS_BALANCE:123.45
            response = resp.read().decode("utf-8").strip()
            # #region agent log
            try:
                with open(r'c:\Users\zgarm\OneDrive\Desktop\Deal share\.cursor\debug.log', 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"location":"api_dynamic.py:21","message":"_http_get success","data":{"status_code":resp.status,"response_length":len(response),"response_preview":response[:50]},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})+"\n")
            except: pass
            # #endregion
            return response
    except error.HTTPError as exc:
        # #region agent log
        try:
            with open(r'c:\Users\zgarm\OneDrive\Desktop\Deal share\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"api_dynamic.py:23","message":"_http_get HTTPError","data":{"status_code":exc.code,"reason":exc.reason},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})+"\n")
        except: pass
        # #endregion
        error_body = exc.read().decode('utf-8') if hasattr(exc, 'read') else 'N/A'
        raise ValueError(f"API HTTP {exc.code}: {exc.reason}") from exc
    except error.URLError as exc:
        # #region agent log
        try:
            with open(r'c:\Users\zgarm\OneDrive\Desktop\Deal share\.cursor\debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location":"api_dynamic.py:25","message":"_http_get URLError","data":{"reason":str(exc.reason)},"timestamp":int(__import__('time').time()*1000),"sessionId":"debug-session","runId":"run1","hypothesisId":"E"})+"\n")
        except: pass
        # #endregion
        raise ValueError(f"Network error: {exc.reason}") from exc


def get_balance(api_key: str, base_url: str) -> str:
    """Check account balance."""
    return _http_get({"action": "getBalance"}, api_key, base_url)


def parse_balance(text: str) -> Optional[float]:
    """Extract numeric balance from API response."""
    if not text.startswith("ACCESS_BALANCE:"):
        return None
    try:
        return float(text.split(":", 1)[1])
    except ValueError:
        return None


def get_prices(country: str, operator: str, api_key: str, base_url: str) -> str:
    """Get pricing for the given country/operator."""
    return _http_get(
        {
            "action": "getPrices",
            "country": country,
            "operator": operator,
        },
        api_key,
        base_url
    )


def parse_prices(text: str) -> Dict[str, Any]:
    """Parse JSON-like price response into a dict; returns {} on failure."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {}


def get_price_for_service(
    service: str, country: str, operator: str, api_key: str, base_url: str
) -> Optional[str]:
    """
    Fetch price data and return the price string for the given service,
    or None if not found.
    """
    raw = get_prices(country=country, operator=operator, api_key=api_key, base_url=base_url)
    data = parse_prices(raw)

    # Expected shape: { "22": { "pbk": { "2.99": "467" } } }
    country_block = data.get(str(country), {})
    service_block = country_block.get(service, {})
    if not isinstance(service_block, dict):
        return None

    price_keys = list(service_block.keys())
    return price_keys[0] if price_keys else None


def get_number(
    service: str,
    country: str,
    operator: str,
    api_key: str,
    base_url: str,
) -> Optional[Tuple[str, str]]:
    """
    Request a virtual number for a service.
    Returns (request_id, phone_number) or None on parse failure.
    """
    raw = _http_get(
        {
            "action": "getNumber",
            "service": service,
            "country": country,
            "operator": operator,
        },
        api_key,
        base_url
    )
    result = parse_number(raw)
    # NOTE: Each worker process is isolated and gets its own unique number/request_id
    # No shared state needed - each process maintains its own request_id locally
    # This prevents race conditions between workers
    return result


def parse_number(text: str) -> Optional[Tuple[str, str]]:
    """
    Extract (request_id, phone_number) from ACCESS_NUMBER response.
    Strips leading '91' from the phone number if present.
    """
    if not text.startswith("ACCESS_NUMBER:"):
        return None
    try:
        _, req_id, raw_number = text.split(":", 2)
    except ValueError:
        return None

    number = raw_number
    if number.startswith("91") and len(number) > 2:
        number = number[2:]

    return req_id, number


def get_otp(
    request_id: str,
    api_key: str,
    base_url: str,
    timeout_seconds: float = 300.0,
    poll_interval: float = 1.0,
) -> Optional[str]:
    """
    Poll for OTP/status for up to timeout_seconds.
    Returns the OTP string if found; otherwise None.
    
    NOTE: This function polls for OTP using the specific request_id.
    Each worker process calls this with its own unique request_id,
    ensuring no race conditions between workers.
    """
    deadline = time.time() + timeout_seconds

    while True:
        # Poll using the specific request_id (isolated per worker)
        response = _http_get({"action": "getStatus", "id": request_id}, api_key, base_url)
        status, otp = parse_otp_response(response)

        if status in ("ok", "cancelled") and otp:
            return otp

        if time.time() >= deadline:
            return otp  # may be None

        time.sleep(poll_interval)


def set_status(status: int, request_id: str, api_key: str, base_url: str) -> str:
    """Generic status update helper (e.g., 3=request new OTP, 8=cancel)."""
    return _http_get({"action": "setStatus", "status": status, "id": request_id}, api_key, base_url)


def cancel_number(request_id: str, api_key: str, base_url: str) -> str:
    """Shortcut: cancel the number (status=8)."""
    return set_status(8, request_id, api_key, base_url)


def parse_cancel_status(text: str) -> str:
    """
    Interpret cancel response.
    Returns 'accepted', 'already_cancelled', or raw text if unknown.
    """
    if text.startswith("ACCESS_CANCEL"):
        return "accepted"
    if text.startswith("ACCESS_CANCEL_ALREADY"):
        return "already_cancelled"
    return text


def extract_otp(text: str) -> Optional[str]:
    """
    Extract the first 4-8 digit OTP from the provided text.
    Returns None if no OTP found.
    """
    matches = re.findall(r"\b(\d{4,8})\b", text)
    if not matches:
        return None
    # Prefer the last match (often the actual OTP)
    return matches[-1]


def parse_otp_response(text: str) -> Tuple[str, Optional[str]]:
    """
    Parse getStatus response.
    Returns a tuple of (status, otp_or_none).
    """
    if text.startswith("STATUS_OK:"):
        otp = extract_otp(text)
        return "ok", otp
    if text.startswith("STATUS_CANCEL"):
        return "cancelled", None
    if text.startswith("ACCESS_WAITING"):
        return "waiting", None
    return "unknown", extract_otp(text)

