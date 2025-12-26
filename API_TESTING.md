# API Testing with cURL

This guide shows how to test all API endpoints using cURL commands.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Health Check
Check if the API server is running.

```bash
curl http://localhost:5000/api/health
```

**Expected Response:**
```json
{"status":"ok"}
```

---

### 2. Get Account Balance
Get the current account balance.

```bash
curl http://localhost:5000/api/balance
```

**Expected Response:**
```json
{
  "success": true,
  "raw": "ACCESS_BALANCE:123.45",
  "balance": 123.45
}
```

---

### 3. Get Service Price
Get the price for a specific service.

```bash
# Default (country=22, operator=1, service=pfk)
curl http://localhost:5000/api/price

# Custom parameters
curl "http://localhost:5000/api/price?country=22&operator=1&service=pfk"
```

**Expected Response:**
```json
{
  "success": true,
  "price": "2.99"
}
```

---

### 4. Get All Prices
Get all available prices for a country/operator.

```bash
# Default (country=22, operator=1)
curl http://localhost:5000/api/prices

# Custom parameters
curl "http://localhost:5000/api/prices?country=22&operator=1"
```

**Expected Response:**
```json
{
  "success": true,
  "prices": {
    "22": {
      "pfk": {
        "2.99": "467"
      }
    }
  }
}
```

---

### 5. Request Phone Number
Request a virtual phone number.

```bash
curl -X POST http://localhost:5000/api/number \
  -H "Content-Type: application/json" \
  -d '{
    "service": "pfk",
    "country": "22",
    "operator": "1"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "request_id": "12345678",
  "phone_number": "9876543210"
}
```

---

### 6. Get OTP
Get OTP for a phone number (polls for up to 2 minutes).

```bash
curl -X POST http://localhost:5000/api/otp \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "12345678",
    "timeout": 120.0,
    "poll_interval": 2.0
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "otp": "1234"
}
```

---

### 7. Cancel Number
Cancel a phone number request.

```bash
curl -X POST http://localhost:5000/api/cancel \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "12345678"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "status": "accepted",
  "raw": "ACCESS_CANCEL"
}
```

---

### 8. Start Automation
Start the automation workflow.

```bash
curl -X POST http://localhost:5000/api/automation/start \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "house_flat_no": "Ward 32",
    "landmark": "Chinu Juice Center"
  }'
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Automation started"
}
```

---

### 9. Stop Automation
Stop all automation workers and cancel all numbers.

```bash
curl -X POST http://localhost:5000/api/automation/stop \
  -H "Content-Type: application/json"
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Stopped all workers and cancelled 2 numbers"
}
```

---

## Windows PowerShell Examples

If you're using Windows PowerShell, use these commands:

### GET Request
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/health" -Method Get
```

### POST Request
```powershell
Invoke-RestMethod -Uri "http://localhost:5000/api/number" -Method Post -ContentType "application/json" -Body '{"service":"pfk","country":"22","operator":"1"}'
```

Or using curl in PowerShell (if available):
```powershell
curl.exe -X POST http://localhost:5000/api/number -H "Content-Type: application/json" -d '{\"service\":\"pfk\",\"country\":\"22\",\"operator\":\"1\"}'
```

---

## Pretty Print JSON (Optional)

To format JSON responses nicely, use `jq` (if installed):

```bash
curl http://localhost:5000/api/balance | jq
```

Or use Python:
```bash
curl http://localhost:5000/api/balance | python -m json.tool
```

---

## Testing Workflow Example

1. **Check server health:**
```bash
curl http://localhost:5000/api/health
```

2. **Check balance:**
```bash
curl http://localhost:5000/api/balance
```

3. **Get a phone number:**
```bash
curl -X POST http://localhost:5000/api/number \
  -H "Content-Type: application/json" \
  -d '{"service":"pfk","country":"22","operator":"1"}'
```

4. **Get OTP (use request_id from step 3):**
```bash
curl -X POST http://localhost:5000/api/otp \
  -H "Content-Type: application/json" \
  -d '{"request_id":"YOUR_REQUEST_ID","timeout":120.0,"poll_interval":2.0}'
```

5. **Cancel number:**
```bash
curl -X POST http://localhost:5000/api/cancel \
  -H "Content-Type: application/json" \
  -d '{"request_id":"YOUR_REQUEST_ID"}'
```

---

## Troubleshooting

### Connection Refused
- Make sure the backend server is running: `python backend/server.py`
- Check if port 5000 is available

### CORS Errors
- The server has CORS enabled, so this shouldn't be an issue
- If testing from browser console, make sure you're on the same origin

### Timeout Errors
- OTP endpoint can take up to 2 minutes
- Increase timeout: `curl --max-time 180 ...`


