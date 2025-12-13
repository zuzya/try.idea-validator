FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g. for build tools or chroma)
# git is often needed for pip install from git
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage cache
COPY requirements.txt .

# Install Python deps
# No-cache-dir to keep image smaller (though torch is huge anyway)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Environment variables can be overridden
ENV PORT=8000

# Run FastAPI with uvicorn
# Host 0.0.0.0 is crucial for Docker networking
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
