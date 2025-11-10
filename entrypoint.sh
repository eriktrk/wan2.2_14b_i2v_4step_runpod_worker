#!/bin/bash
set -e

echo "=== Wan2.2 I2V Lightning Worker Starting ==="

# Check if network volume is mounted
if [ ! -d "/runpod-volume" ]; then
    echo "WARNING: Network volume not found at /runpod-volume"
    echo "Worker will start but job requests will fail without models."
    echo "For production use, attach a network volume with models at /runpod-volume/runpod-slim/ComfyUI/models/"
    MODELS_AVAILABLE=false
else
    # Verify network volume models are available
    echo "Verifying model availability on network volume..."
    NETWORK_MODELS_PATH="/runpod-volume/runpod-slim/ComfyUI/models"

    if [ ! -d "$NETWORK_MODELS_PATH" ]; then
        echo "WARNING: Models directory not found at $NETWORK_MODELS_PATH"
        echo "Worker will start but job requests will fail without models."
        MODELS_AVAILABLE=false
    else
        REQUIRED_MODELS=(
            "$NETWORK_MODELS_PATH/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"
            "$NETWORK_MODELS_PATH/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"
            "$NETWORK_MODELS_PATH/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"
            "$NETWORK_MODELS_PATH/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"
            "$NETWORK_MODELS_PATH/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"
            "$NETWORK_MODELS_PATH/vae/wan_2.1_vae.safetensors"
        )

        MODELS_AVAILABLE=true
        for model in "${REQUIRED_MODELS[@]}"; do
            if [ ! -f "$model" ]; then
                echo "WARNING: Model not found: $model"
                MODELS_AVAILABLE=false
            else
                echo "✓ Found: $(basename $model)"
            fi
        done

        if [ "$MODELS_AVAILABLE" = true ]; then
            echo "✓ All required models found on network volume"
        else
            echo "WARNING: Some models are missing. Worker will start but job requests may fail."
        fi
    fi
fi

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
