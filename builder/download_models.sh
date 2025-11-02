#!/bin/bash
# Script to download required models to RunPod Network Volume
# Run this once to populate /runpod-volume/models/

set -e

BASE_URL="https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged/resolve/main/split_files"
MODEL_DIR="${1:-/runpod-volume/models}"

echo "Downloading Wan2.2 models to: $MODEL_DIR"

# Create directory structure
mkdir -p "$MODEL_DIR/diffusion_models"
mkdir -p "$MODEL_DIR/loras"
mkdir -p "$MODEL_DIR/text_encoders"
mkdir -p "$MODEL_DIR/vae"

# Download diffusion models (~14GB each)
echo "Downloading diffusion models..."
wget -c "$BASE_URL/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors" \
  -O "$MODEL_DIR/diffusion_models/wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors"

wget -c "$BASE_URL/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors" \
  -O "$MODEL_DIR/diffusion_models/wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors"

# Download LoRA models
echo "Downloading LoRA models..."
wget -c "$BASE_URL/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors" \
  -O "$MODEL_DIR/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors"

wget -c "$BASE_URL/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors" \
  -O "$MODEL_DIR/loras/wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors"

# Download text encoder
echo "Downloading text encoder..."
wget -c "https://huggingface.co/Comfy-Org/Wan_2.1_ComfyUI_repackaged/resolve/main/split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors" \
  -O "$MODEL_DIR/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors"

# Download VAE
echo "Downloading VAE..."
wget -c "$BASE_URL/vae/wan_2.1_vae.safetensors" \
  -O "$MODEL_DIR/vae/wan_2.1_vae.safetensors"

echo "✓ All models downloaded successfully!"
echo ""
echo "Model directory size:"
du -sh "$MODEL_DIR"
echo ""
echo "Files:"
find "$MODEL_DIR" -type f -name "*.safetensors" -exec ls -lh {} \;
