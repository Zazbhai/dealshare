# Quick Setup: Docker Environment Variables

## Step 1: Create .env file

Create a `.env` file in the project root (same folder as `docker-compose.yml`) with these contents:

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

## Step 2: Start Docker

```bash
docker-compose up -d --build
```

## Editing Later (For Tunneling or Changes)

### To Edit Environment Variables:

1. **Stop the container**:
   ```bash
   docker-compose down
   ```

2. **Edit the `.env` file** in the project root

3. **Restart**:
   ```bash
   docker-compose up -d
   ```

### For Tunneling (ngrok, Cloudflare, etc.)

**You typically DON'T need to change environment variables** when tunneling:

- Docker already listens on `0.0.0.0:5000` (accessible from outside)
- Just tunnel port 5000 to the internet
- Example with ngrok: `ngrok http 5000`
- Example with Cloudflare: `cloudflared tunnel --url http://localhost:5000`

The `.env` file is already in `.gitignore`, so your secrets won't be committed to Git.

## Quick Reference

| Variable | What it does | Need to change? |
|----------|--------------|-----------------|
| `MONGO_URI` | MongoDB connection | Only if changing database |
| `DB_NAME` | Database name | Only if changing database |
| `JWT_SECRET_KEY` | Security key for tokens | Yes, in production (use a random string) |
| `BACKEND_PORT` | Port Docker uses | Only if port 5000 is in use |
| `FLASK_DEBUG` | Debug mode | Keep `false` for production |

For more details, see `DOCKER_ENV_GUIDE.md`

