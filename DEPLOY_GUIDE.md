# 🚀 Deployment Guide: AI Unicorn Validator

This guide explains how to deploy the application to a Virtual Private Server (VPS) using Docker and Docker Compose.

## Prerequisites

Your VPS must have:
1.  **Docker** installed (v20.10+ recommended)
2.  **Docker Compose** installed (v2.0+)
3.  **Git** (to clone the repo)

## Step-by-Step Deployment

### 1. Local Machine: Build & Push
The scripts default to `zuzyadocker` and repository `idea-validator`.

1.  **Build Default (latest):**
    ```bash
    ./build_and_push.sh
    ```
2.  **Build Specific Version (e.g. v1.0):**
    ```bash
    ./build_and_push.sh v1.0
    ```

### 2. VPS: Prepare Environment
1.  Create a folder `iterative_validator`.
2.  Copy ONLY these files to the VPS folder:
    *   `docker-compose.yml`
    *   `deploy.sh`
    *   `.env` (with API keys)
    *   `personas_index.json` (optional persistence)

### 3. VPS: Deploy
SSH into your VPS and run the deploy script.

**Deploy Latest:**
```bash
chmod +x deploy.sh
./deploy.sh
```

**Deploy Specific Version:**
```bash
./deploy.sh v1.0
```

### 4. Verify Deployment
Open your browser and navigate to your VPS IP address with the port:
`http://<your-vps-ip>:5173/`

## Troubleshooting

### Architecture Warning (Mac vs VPS)
Since you are building on macOS (likely ARM64) and deploying to Ubuntu (likely AMD64), we added `export DOCKER_DEFAULT_PLATFORM=linux/amd64` to the build script. This ensures the images run correctly on your VPS.

### Authentication
If pulling fails, make sure you are logged into Docker on the VPS:
```bash
docker login
```

## Troubleshooting

### Check Logs
If something isn't working, check the container logs:
```bash
# All logs
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Nginx/API Connection Issues
The frontend container talks to the backend via the internal Docker network name `backend` on port `8000`. The Nginx config is set up to proxy `/api` requests to `http://backend:8000`.
- If the frontend loads but API calls fail, check `docker-compose logs backend` to see if the Python app crashed.
- Check if Nginx timeouts are hit (validation takes time!). The config sets a 600s (10 min) timeout.

### Disk Space
The Python image can be large (due to Torch/Chroma/Transformers). Ensure your VPS has at least **8GB-10GB free disk space**.
To prune old docker objects:
```bash
docker system prune -a
```

## Structure
- **Frontend**: Served by Nginx on Port 80.
- **Backend**: Python/FastAPI app running on Port 8000 (exposed but also accessible internally by Nginx).
