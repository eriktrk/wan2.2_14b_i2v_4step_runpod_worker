#!/bin/bash
set -e

echo "=== Wan2.2 I2V Lightning Worker Starting ==="

# Verify models are available in Docker image
echo "Verifying model availability..."
MODELS_PATH="/ComfyUI/models"

REQUIRED_MODELS=(
    "$MODELS_PATH/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
    "$MODELS_PATH/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
    "$MODELS_PATH/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
    "$MODELS_PATH/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
    "$MODELS_PATH/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
    "$MODELS_PATH/vae/wan_2.1_vae.safetensors"
)

MODELS_AVAILABLE=true
for model in "${REQUIRED_MODELS[@]}"; do
    if [ ! -f "$model" ]; then
        echo "ERROR: Model not found: $model"
        MODELS_AVAILABLE=false
    else
        echo "✓ Found: $(basename $model)"
    fi
done

if [ "$MODELS_AVAILABLE" = false ]; then
    echo "ERROR: Some models are missing from the Docker image"
    echo "The image may not have been built correctly"
    exit 1
fi

echo "✓ All required models found"

# Start ComfyUI server in background
echo "Starting ComfyUI server..."
cd /ComfyUI
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
python -u handler.py
