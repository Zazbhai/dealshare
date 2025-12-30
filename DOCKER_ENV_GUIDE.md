# Docker Environment Variables Guide

This guide explains how to configure and edit environment variables for Docker deployment.

## Quick Start

1. **Create a `.env` file** in the project root (copy from `.env.example`):
```bash
cp .env.example .env
```

2. **Edit `.env` file** with your configuration:
```env
# MongoDB Atlas Configuration
MONGO_URI=mongodb+srv://dealshare_user:f9CiLYaaozkLdMxb@dealshare.oysqfuf.mongodb.net/dealshare_automation?retryWrites=true&w=majority&appName=dealshare
DB_NAME=dealshare_automation

# JWT Secret Key (Change this in production!)
JWT_SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=5000
FLASK_DEBUG=false
```

3. **Start Docker**:
```bash
docker-compose up -d --build
```

## Editing Environment Variables

### Method 1: Edit `.env` file (Recommended)

1. Stop the container:
```bash
docker-compose down
```

2. Edit the `.env` file in the project root

3. Restart the container:
```bash
docker-compose up -d
```

### Method 2: Edit `docker-compose.yml`

You can directly edit the environment variables in `docker-compose.yml`:

```yaml
environment:
  - MONGO_URI=${MONGO_URI:-mongodb+srv://...}
  - DB_NAME=${DB_NAME:-dealshare_automation}
  - JWT_SECRET_KEY=${JWT_SECRET_KEY:-your-secret-key}
```

Then restart:
```bash
docker-compose down
docker-compose up -d
```

### Method 3: Override with command line

```bash
MONGO_URI="mongodb+srv://..." docker-compose up -d
```

## For Tunneling (ngrok, Cloudflare Tunnel, etc.)

When tunneling your application, you typically don't need to change environment variables unless:

1. **You need to change the backend URL for the frontend**: Update `VITE_BACKEND_URL` in `.env` (but this won't affect Docker, only local dev)

2. **You're using a reverse proxy**: The backend should still listen on `0.0.0.0:5000` inside Docker

### Example with ngrok:

1. **Start Docker normally**:
```bash
docker-compose up -d
```

2. **Start ngrok tunnel**:
```bash
ngrok http 5000
```

3. **No environment variable changes needed** - Docker is already listening on `0.0.0.0:5000`

### Example with Cloudflare Tunnel:

1. **Install cloudflared** (if not installed)

2. **Create tunnel** (one-time setup):
```bash
cloudflared tunnel create dealshare
```

3. **Run tunnel**:
```bash
cloudflared tunnel --url http://localhost:5000
```

4. **No Docker environment changes needed**

## Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONGO_URI` | MongoDB connection string | `mongodb://localhost:27017/` | Yes (for production) |
| `DB_NAME` | Database name | `dealshare_automation` | No |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | Random string | Yes (for production) |
| `BACKEND_HOST` | Backend server host | `0.0.0.0` | No |
| `BACKEND_PORT` | Backend server port | `5000` | No |
| `FLASK_DEBUG` | Enable Flask debug mode | `false` | No |

## Security Notes

⚠️ **Important Security Considerations**:

1. **Never commit `.env` file to Git** - it's already in `.gitignore`
2. **Change JWT_SECRET_KEY in production** - use a long, random string
3. **Use strong MongoDB credentials** - don't use default passwords
4. **Restrict MongoDB IP whitelist** - in MongoDB Atlas, whitelist only your server IP or `0.0.0.0/0` for testing only

## Generating a Secure JWT Secret Key

### Using Python:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Using OpenSSL:
```bash
openssl rand -hex 32
```

### Using Node.js:
```bash
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Updating MongoDB Connection String

If you need to change your MongoDB connection:

1. **Edit `.env` file**:
```env
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority
```

2. **Restart Docker**:
```bash
docker-compose down
docker-compose up -d
```

3. **Check logs** to verify connection:
```bash
docker-compose logs -f
```

## Troubleshooting

### Environment variables not updating?

1. Make sure you're editing `.env` in the project root (same directory as `docker-compose.yml`)
2. Restart containers: `docker-compose down && docker-compose up -d`
3. Verify variables: `docker-compose config` (shows resolved environment variables)

### MongoDB connection fails?

1. Check `MONGO_URI` in `.env` file
2. Verify MongoDB Atlas IP whitelist includes `0.0.0.0/0` (or your server IP)
3. Check credentials in connection string
4. View logs: `docker-compose logs app | grep -i mongo`

### JWT authentication fails?

1. Verify `JWT_SECRET_KEY` is set and not the default value
2. Ensure it's the same across all instances (if using multiple containers)
3. Check backend logs: `docker-compose logs app | grep -i jwt`

