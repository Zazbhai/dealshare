# Multi-stage build for optimized Docker image

# Stage 1: Build frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including dev dependencies for build)
RUN npm install --legacy-peer-deps

# Copy frontend source
COPY src/ ./src/
COPY index.html ./
COPY vite.config.js ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# Build frontend
RUN npm run build

# Stage 2: Python backend + Playwright
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy AS backend

WORKDIR /app

# Install system dependencies for better performance
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (only Chromium for automation)
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy application code
COPY . .

# Copy built frontend from builder stage
COPY --from=frontend-builder /app/dist ./dist

# Create necessary directories
RUN mkdir -p logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BACKEND_HOST=0.0.0.0
ENV BACKEND_PORT=5000

# Set Docker environment variable for main.py
ENV DOCKER_CONTAINER=true

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application
CMD ["python", "-u", "backend/server.py"]

