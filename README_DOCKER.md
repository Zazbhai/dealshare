# Docker Deployment Guide

This guide explains how to build and run the Deal Share Automation application using Docker.

## Prerequisites

- Docker (version 20.10 or higher)
- Docker Compose (version 2.0 or higher)
- MongoDB connection string (or MongoDB running separately)

## Quick Start

### Using Docker Compose (Recommended)

1. **Create a `.env` file** in the project root:
```env
MONGO_URI=mongodb://your-mongodb-connection-string
DB_NAME=dealshare_automation
BACKEND_HOST=0.0.0.0
BACKEND_PORT=5000
```

2. **Build and run:**
```bash
docker-compose up -d --build
```

3. **Access the application:**
- Frontend/Backend: http://localhost:5000
- Health Check: http://localhost:5000/api/health

### Using Docker directly

1. **Build the image:**
```bash
docker build -t deal-share-automation:latest .
```

2. **Run the container:**
```bash
docker run -d \
  --name deal-share-automation \
  -p 5000:5000 \
  -e MONGO_URI="mongodb://your-mongodb-connection-string" \
  -e DB_NAME="dealshare_automation" \
  --shm-size=2gb \
  --security-opt seccomp=unconfined \
  deal-share-automation:latest
```

## Build for Linux

The Dockerfile is already optimized for Linux. To build specifically for Linux/amd64:

```bash
docker buildx build --platform linux/amd64 -t deal-share-automation:latest .
```

Or using Docker Compose:
```bash
DOCKER_DEFAULT_PLATFORM=linux/amd64 docker-compose build
```

## Environment Variables

Key environment variables:

- `MONGO_URI`: MongoDB connection string (required)
- `DB_NAME`: Database name (default: `dealshare_automation`)
- `BACKEND_HOST`: Server host (default: `0.0.0.0`)
- `BACKEND_PORT`: Server port (default: `5000`)
- `FLASK_DEBUG`: Enable Flask debug mode (default: `false`)
- `DOCKER_CONTAINER`: Automatically set to `true` in Docker

## Volumes

The following directories are mounted as volumes for data persistence:

- `./logs` - Application logs
- `./my_orders.csv` - Order results CSV file
- `./automation_status.json` - Automation status file

## Resource Requirements

Recommended minimum:
- CPU: 2 cores
- RAM: 4GB
- Disk: 10GB

For parallel automation workers:
- CPU: 4+ cores
- RAM: 8GB+
- Shared memory: 2GB (configured via `--shm-size`)

## Troubleshooting

### Browser/Playwright issues in Docker

The Dockerfile uses the official Playwright image which includes all necessary dependencies. If you encounter browser-related errors:

1. Check that `--shm-size=2gb` is set
2. Verify `--security-opt seccomp=unconfined` is present
3. Check logs: `docker logs deal-share-automation`

### MongoDB connection issues

1. Verify your MongoDB connection string is correct
2. Ensure MongoDB is accessible from the Docker container
3. For MongoDB Atlas, whitelist the Docker host IP

### Port conflicts

If port 5000 is already in use, change it in `docker-compose.yml`:

```yaml
ports:
  - "8080:5000"  # Use port 8080 on host
```

## Production Deployment

For production:

1. Set `FLASK_DEBUG=false` (default in Docker)
2. Use a production WSGI server (waitress is included)
3. Set up proper MongoDB credentials
4. Configure reverse proxy (nginx/traefik) if needed
5. Enable HTTPS/TLS
6. Set up log rotation
7. Configure resource limits appropriately

## Multi-architecture Build

To build for multiple architectures:

```bash
docker buildx create --use
docker buildx build --platform linux/amd64,linux/arm64 -t deal-share-automation:latest .
```

