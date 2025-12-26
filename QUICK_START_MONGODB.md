# Quick Start MongoDB - Windows

## Problem
You're seeing: "MongoDB is not connected" or "Database is not working"

## Solution

### Step 1: Check if MongoDB is installed
```powershell
mongod --version
```

If you see an error, MongoDB is not installed. Go to Step 2.
If you see a version number, skip to Step 3.

### Step 2: Install MongoDB (if not installed)

**Option A: Download and Install**
1. Download: https://www.mongodb.com/try/download/community
2. Run installer
3. Choose "Complete" installation
4. ✅ Check "Install MongoDB as a Service"
5. ✅ Check "Install MongoDB Compass" (optional GUI)

**Option B: Use MongoDB Atlas (Cloud - No Installation)**
1. Go to: https://www.mongodb.com/cloud/atlas
2. Create free account
3. Create free cluster
4. Get connection string
5. Update `.env` file:
   ```
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   ```

### Step 3: Start MongoDB

**If installed as service:**
```powershell
net start MongoDB
```

**If not installed as service:**
```powershell
# Create data directory
mkdir C:\data\db

# Start MongoDB manually
mongod --dbpath C:\data\db
```

### Step 4: Verify MongoDB is Running

```powershell
# Check if MongoDB service is running
net start | findstr MongoDB

# Or check if port 27017 is listening
netstat -an | findstr 27017
```

### Step 5: Test Connection

```powershell
python check_mongodb.py
```

You should see: `[SUCCESS] MongoDB is running and connected!`

## Common Issues

### Issue: "Access Denied"
**Fix:** Run PowerShell as Administrator

### Issue: "Port 27017 already in use"
**Fix:** Another MongoDB instance is running. Stop it:
```powershell
net stop MongoDB
```

### Issue: "Cannot create data directory"
**Fix:** Create it manually:
```powershell
mkdir C:\data\db
```

### Issue: "MongoDB service not found"
**Fix:** MongoDB is not installed. Install it (Step 2)

## After Starting MongoDB

1. **Start the backend server:**
   ```powershell
   python backend/server.py
   ```

2. **You should see:** `MongoDB connected successfully`

3. **If you see warnings:** MongoDB is still not running. Follow steps above.

## Need Help?

Run the diagnostic script:
```powershell
python test_db_connection.py
```

This will show exactly what's wrong and how to fix it.

