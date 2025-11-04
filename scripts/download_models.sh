#!/bin/bash
# Download Wan2.2 I2V models to RunPod network volume
# Run this script on a Pod with your network volume attached

set -e

echo "=== Wan2.2 I2V Model Download Script ==="
echo ""

# Check if we're in the right location
if [ ! -d "/runpod-volume" ]; then
    echo "ERROR: /runpod-volume not found!"
    echo "Please run this script on a RunPod Pod with a network volume attached."
    exit 1
fi

# Create directory structure
echo "Creating directory structure..."
MODELS_BASE="/runpod-volume/runpod-slim/ComfyUI/models"
mkdir -p "$MODELS_BASE"/{diffusion_models,loras,text_encoders,vae}

cd "$MODELS_BASE"
echo "Working directory: $(pwd)"
echo ""

# Function to download with progress
download_model() {
    local url="$1"
    local output="$2"
    local name=$(basename "$output")

    if [ -f "$output" ]; then
        echo "✓ $name already exists, skipping..."
        return 0
    fi

    echo "Downloading $name..."
    wget --progress=bar:force:noscroll "$url" -O "$output"

    if [ $? -eq 0 ]; then
        local size=$(du -h "$output" | cut -f1)
        echo "✓ Downloaded $name ($size)"
    else
        echo "✗ Failed to download $name"
        return 1
    fi
}

echo "Starting model downloads (~30GB total, this will take a while)..."
echo ""

# Download diffusion models (~14GB each)
echo "[1/6] Downloading high noise diffusion model..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
    "diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"

echo ""
echo "[2/6] Downloading low noise diffusion model..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
    "diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"

echo ""
echo "[3/6] Downloading high noise LoRA..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" \
    "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"

echo ""
echo "[4/6] Downloading low noise LoRA..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" \
    "loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"

echo ""
echo "[5/6] Downloading text encoder..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
    "text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

echo ""
echo "[6/6] Downloading VAE..."
download_model \
    "https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files/vae/wan_2.1_vae.safetensors" \
    "vae/wan_2.1_vae.safetensors"

echo ""
echo "=== Download Complete ==="
echo ""
echo "Model Summary:"
ls -lh diffusion_models/
ls -lh loras/
ls -lh text_encoders/
ls -lh vae/

echo ""
echo "Total size:"
du -sh "$MODELS_BASE"

echo ""
echo "✓ All models downloaded successfully!"
echo "You can now use this network volume with your serverless endpoint."
