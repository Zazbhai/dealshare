# How to Start MongoDB

## Windows

### Option 1: MongoDB Service (Recommended)
```powershell
# Start MongoDB service
net start MongoDB

# Check if MongoDB is running
net start | findstr MongoDB
```

### Option 2: Manual Start
```powershell
# Navigate to MongoDB bin directory (usually)
cd "C:\Program Files\MongoDB\Server\<version>\bin"

# Start MongoDB
mongod.exe --dbpath "C:\data\db"
```

**Note:** Make sure the data directory exists:
```powershell
mkdir C:\data\db
```

### Option 3: MongoDB Compass (GUI)
1. Download MongoDB Compass from https://www.mongodb.com/try/download/compass
2. Install and open MongoDB Compass
3. It will automatically start MongoDB service

## Check MongoDB Status

```powershell
# Check if MongoDB is listening on port 27017
netstat -an | findstr 27017
```

## Install MongoDB (If Not Installed)

1. Download MongoDB Community Server: https://www.mongodb.com/try/download/community
2. Run the installer
3. Choose "Complete" installation
4. Install as a Windows Service (recommended)
5. Install MongoDB Compass (optional GUI)

## Alternative: Use MongoDB Atlas (Cloud)

If you don't want to install MongoDB locally:

1. Go to https://www.mongodb.com/cloud/atlas
2. Create a free account
3. Create a free cluster
4. Get connection string
5. Update `.env` file:
   ```
   MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/
   DB_NAME=dealshare_automation
   ```

## Troubleshooting

### Error: "MongoDB service not found"
- MongoDB is not installed
- Install MongoDB Community Server

### Error: "Access denied"
- Run PowerShell/Command Prompt as Administrator

### Error: "Port 27017 already in use"
- Another MongoDB instance is running
- Stop it first: `net stop MongoDB`

### Error: "Cannot create data directory"
- Create the directory manually: `mkdir C:\data\db`
- Or specify a different path: `mongod --dbpath "D:\mongodb\data"`

