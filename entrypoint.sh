#!/bin/bash
set -e

echo "=== Wan2.2 I2V Lightning Worker Starting ==="

# Wait for ComfyUI models to be available
echo "Checking model availability..."
MODEL_DIR="${MODEL_PATH:-/runpod-volume/models}"

if [ ! -d "$MODEL_DIR" ]; then
    echo "ERROR: Model directory not found: $MODEL_DIR"
    echo "Please ensure network volume is mounted at /runpod-volume"
    exit 1
fi

# Check for required models
REQUIRED_MODELS=(
    "$MODEL_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    "$MODEL_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    "$MODEL_DIR/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
    "$MODEL_DIR/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
    "$MODEL_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    "$MODEL_DIR/vae/wan_2.1_vae.safetensors"
)

for model in "${REQUIRED_MODELS[@]}"; do
    if [ ! -f "$model" ]; then
        echo "WARNING: Model not found: $model"
    else
        echo "✓ Found: $(basename $model)"
    fi
done

# Create symlinks for ComfyUI models
echo "Setting up ComfyUI model paths..."
mkdir -p /comfyui/models/diffusion_models
mkdir -p /comfyui/models/loras
mkdir -p /comfyui/models/text_encoders
mkdir -p /comfyui/models/vae

ln -sf "$MODEL_DIR/diffusion_models"/* /comfyui/models/diffusion_models/ 2>/dev/null || true
ln -sf "$MODEL_DIR/loras"/* /comfyui/models/loras/ 2>/dev/null || true
ln -sf "$MODEL_DIR/text_encoders"/* /comfyui/models/text_encoders/ 2>/dev/null || true
ln -sf "$MODEL_DIR/vae"/* /comfyui/models/vae/ 2>/dev/null || true

# Start ComfyUI server in background
echo "Starting ComfyUI server..."
cd /comfyui
python main.py --listen 0.0.0.0 --port 8188 > /tmp/comfyui.log 2>&1 &
COMFYUI_PID=$!

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to initialize..."
MAX_WAIT=60
WAIT_COUNT=0

while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if curl -s http://localhost:8188/ > /dev/null 2>&1; then
        echo "✓ ComfyUI is ready!"
        break
    fi
    sleep 1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [ $WAIT_COUNT -eq $MAX_WAIT ]; then
    echo "ERROR: ComfyUI failed to start within $MAX_WAIT seconds"
    echo "ComfyUI logs:"
    cat /tmp/comfyui.log
    exit 1
fi

# Start RunPod handler
echo "Starting RunPod handler..."
cd /app
python -u src/rp_handler.py
