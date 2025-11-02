# Wan2.2 I2V Lightning RunPod Worker Dockerfile
FROM runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV COMFYUI_SERVER=127.0.0.1:8188
ENV MODEL_PATH=/runpod-volume/models

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
WORKDIR /comfyui
RUN git clone https://github.com/comfyanonymous/ComfyUI.git . && \
    pip install --no-cache-dir -r requirements.txt

# Install ComfyUI custom nodes (if needed)
# RUN cd custom_nodes && \
#     git clone https://github.com/Comfy-Org/ComfyUI_Base64_to_Image.git && \
#     cd ComfyUI_Base64_to_Image && \
#     pip install --no-cache-dir -r requirements.txt

# Set up worker application
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY workflows/ ./workflows/

# Create model path symlink for ComfyUI
RUN mkdir -p /comfyui/models && \
    ln -sf /runpod-volume/models/* /comfyui/models/ 2>/dev/null || true

# Expose ComfyUI port (not necessary for RunPod but good for documentation)
EXPOSE 8188

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8188/ || exit 1

# Set Python path
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Start script will launch ComfyUI and then the handler
CMD ["/bin/bash", "-c", "python /comfyui/main.py --listen 0.0.0.0 --port 8188 & sleep 10 && python -u /app/src/rp_handler.py"]
