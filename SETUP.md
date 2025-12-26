# Setup Guide - MongoDB Authentication

## Prerequisites

1. **MongoDB** - Install and run MongoDB locally or use MongoDB Atlas
2. **Python 3.8+**
3. **Node.js 18+**

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Node.js Dependencies

```bash
npm install
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGO_URI=mongodb://localhost:27017/
DB_NAME=dealshare_automation

# JWT Secret Key (Change this in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random
```

### 4. Start MongoDB

**Local MongoDB:**
```bash
# Windows
mongod

# Linux/Mac
sudo systemctl start mongod
# or
mongod --dbpath /path/to/data
```

**MongoDB Atlas (Cloud):**
- Create account at https://www.mongodb.com/cloud/atlas
- Get connection string
- Update `MONGO_URI` in `.env`

### 5. Start Backend Server

```bash
python backend/server.py
```

### 6. Start Frontend

```bash
npm run dev
```

## First Time Setup

1. **Open the app** at `http://localhost:3000`
2. You'll be redirected to `/login`
3. **Click "Register"** to create the first account
   - First user will automatically be assigned `admin` role
   - Enter your API credentials:
     - API URL
     - API Key
     - Country Code
     - Operator
     - Service
4. **Login** with your credentials

## Features

- ✅ **User Authentication** - Login/Register with JWT tokens
- ✅ **Role-Based Access** - Admin and User roles
- ✅ **User-Specific Settings** - Each user has their own:
  - API URL
  - API Key
  - Country Code
  - Operator
  - Service
- ✅ **Database Storage** - All settings stored in MongoDB
- ✅ **Protected Routes** - All API endpoints require authentication

## User Roles

- **Admin**: Can access admin panel and view all users
- **User**: Standard user with access to dashboard

## Updating Settings

Users can update their API settings through the API:
- `PUT /api/auth/settings` - Update user settings

## API Endpoints

All endpoints (except `/api/health`, `/api/auth/login`, `/api/auth/register`) require authentication.

Include token in header:
```
Authorization: Bearer <your-token>
```

## Troubleshooting

### MongoDB Connection Error
- Make sure MongoDB is running
- Check `MONGO_URI` in `.env`
- Verify MongoDB port (default: 27017)

### Authentication Errors
- Check JWT_SECRET_KEY is set
- Verify token is included in requests
- Token expires after 7 days

### API Errors
- Verify user's API credentials are correct
- Check API URL is accessible
- Ensure API key is valid


