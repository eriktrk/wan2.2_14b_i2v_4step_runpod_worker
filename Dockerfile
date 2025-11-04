# Wan2.2 I2V Lightning RunPod Worker Dockerfile
FROM runpod/pytorch:2.8.0-py3.11-cuda12.8.1-cudnn-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV COMFYUI_SERVER=127.0.0.1:8188

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI
WORKDIR /ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git . && \
    pip install --no-cache-dir -r requirements.txt

# Create model directories for network volume symlinks
RUN mkdir -p /ComfyUI/models

# Set up worker application
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY handler.py .
COPY src/ ./src/
COPY workflows/ ./workflows/
COPY extra_model_paths.yaml /ComfyUI/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ComfyUI port (not necessary for RunPod but good for documentation)
EXPOSE 8188

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Use entrypoint script to start ComfyUI and handler
CMD ["/entrypoint.sh"]
