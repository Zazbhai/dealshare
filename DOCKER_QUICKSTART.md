# Docker Quick Start Guide

## Quick Commands

### Build and Run (Recommended)
```bash
docker-compose up -d --build
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Container
```bash
docker-compose down
```

### Rebuild After Code Changes
```bash
docker-compose up -d --build
```

## Setup Steps

1. **Create `.env` file** (copy from example):
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` file** with your configuration:
   ```env
   MONGO_URI=mongodb+srv://dealshare_user:f9CiLYaaozkLdMxb@dealshare.oysqfuf.mongodb.net/dealshare_automation?retryWrites=true&w=majority&appName=dealshare
   DB_NAME=dealshare_automation
   JWT_SECRET_KEY=your-secret-key-change-in-production-make-it-long-and-random
   ```

3. **Build and Run**
   ```bash
   docker-compose up -d --build
   ```

4. **Access Application**
   - Open browser: http://localhost:5000
   - Health check: http://localhost:5000/api/health

## Editing Environment Variables

To edit environment variables later:

1. **Stop container**: `docker-compose down`
2. **Edit `.env` file** in project root
3. **Restart**: `docker-compose up -d`

See `DOCKER_ENV_GUIDE.md` for detailed instructions on editing environment variables and tunneling.

## Using Docker Directly (Alternative)

### Build Image
```bash
docker build -t deal-share-automation:latest .
```

### Run Container
```bash
docker run -d `
  --name deal-share-automation `
  -p 5000:5000 `
  -e MONGO_URI="mongodb://your-connection-string" `
  -e DB_NAME="dealshare_automation" `
  --shm-size=2gb `
  --security-opt seccomp=unconfined `
  deal-share-automation:latest
```

## Useful Commands

### Check if container is running
```bash
docker ps
```

### View container logs
```bash
docker logs deal-share-automation
docker logs -f deal-share-automation  # Follow logs
```

### Stop container
```bash
docker stop deal-share-automation
```

### Remove container
```bash
docker rm deal-share-automation
```

### Execute command in container
```bash
docker exec -it deal-share-automation bash
```

