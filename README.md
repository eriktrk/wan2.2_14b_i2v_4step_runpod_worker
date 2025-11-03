# Wan2.2 14B I2V Lightning RunPod Worker

A RunPod serverless worker for generating videos from static images using the Wan2.2 14B Image-to-Video Lightning model with 4-step LoRA acceleration.

**Built on the official 2025 ComfyUI Wan2.2 template**: This worker is based on the [default ComfyUI workflow](https://docs.comfy.org/tutorials/video/wan/wan2_2) and optimized for serverless deployment.

**For game development**: Suitable for animating 2D game characters, sprites, assets, and UI elements with smooth, natural motion.

## Features

- **Fast Generation**: 4-step Lightning LoRA for ~90% faster inference (~30-40s for 512x512x33)
- **Flexible Input**: Accepts images via URL or Base64 encoding
- **Base64 Output**: Returns generated videos as Base64-encoded strings
- **Self-Contained**: Models baked into Docker image, no external volumes required
- **Production Ready**: Full error handling, validation, and logging
- **Game Asset Animation**: Specialized for 2D character idle animations, attack animations, and sprite sheets

## Requirements

### GPU
- NVIDIA GPU with 24GB+ VRAM (RTX 4090, A40, A100)
- CUDA 11.8+

### Models
Models are automatically downloaded during Docker image build (~30GB total) and stored in `/ComfyUI/models/`:

- Diffusion models: wan2.2_i2v_high_noise_14B_fp8_scaled.safetensors (~14GB)
- Diffusion models: wan2.2_i2v_low_noise_14B_fp8_scaled.safetensors (~14GB)
- LoRA models: wan2.2_i2v_lightx2v_4steps_lora_v1_high_noise.safetensors
- LoRA models: wan2.2_i2v_lightx2v_4steps_lora_v1_low_noise.safetensors
- Text encoder: umt5_xxl_fp8_e4m3fn_scaled.safetensors
- VAE: wan_2.1_vae.safetensors

**Source**: [Hugging Face - Comfy-Org/Wan_2.2_ComfyUI_Repackaged](https://huggingface.co/Comfy-Org/Wan_2.2_ComfyUI_Repackaged)

## API Reference

### Input Schema

```json
{
  "input": {
    "prompt": "string (required)",
    "image_url": "string (optional)",
    "image_base64": "string (optional)",
    "negative_prompt": "string (optional, defaults to Chinese optimized)",
    "cfg": 1.0,
    "width": 512,
    "height": 512,
    "frames": 33,
    "fps": 16,
    "steps": 4
  }
}
```

**Note**: Either `image_url` OR `image_base64` must be provided (not both).

### Input Parameters

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `prompt` | string | *required* | 1-1000 chars | Motion description for the video |
| `image_url` | string | null | Valid URL | Input image URL |
| `image_base64` | string | null | Base64 string | Input image as Base64 |
| `negative_prompt` | string | Chinese default | 1-1000 chars | Negative prompt (defaults to model-optimized Chinese) |
| `cfg` | float | 1.0 | 0.1-20.0 | CFG scale (guidance strength) |
| `width` | int | 512 | 64-1024 (×64) | Video width (must be multiple of 64) |
| `height` | int | 512 | 64-1024 (×64) | Video height (must be multiple of 64) |
| `frames` | int | 33 | 9-121 (8n+1) | Number of frames (must be 8n+1: 9, 17, 25, 33, 41...) |
| `fps` | int | 16 | 8-60 | Frames per second |
| `steps` | int | 4 | 1-50 | Sampling steps (4 recommended for LoRA) |

### Output Schema

**Success:**
```json
{
  "video_base64": "base64-encoded-video-string",
  "metadata": {
    "width": 512,
    "height": 512,
    "frames": 33,
    "fps": 16,
    "cfg": 1.0,
    "steps": 4
  }
}
```

**Error:**
```json
{
  "error": "Error message description"
}
```

## Deployment

### 1. Build Docker Image

**Note**: Building will download ~30GB of models. Ensure sufficient bandwidth and disk space.

```bash
docker build --platform linux/amd64 -t your-dockerhub/wan22-i2v-worker:latest .
docker push your-dockerhub/wan22-i2v-worker:latest
```

### 2. Create Serverless Endpoint

**RunPod Console Settings:**
- **Container Image**: `your-dockerhub/wan22-i2v-worker:latest`
- **GPU Type**: RTX 4090 / A40 / A100 (24GB+ VRAM)
- **Container Disk**: 50GB minimum (to accommodate ~30GB models)
- **Environment Variables**:
  - `COMFYUI_SERVER=127.0.0.1:8188`

**Advanced Settings:**
- Max Workers: 3-5 (based on budget)
- Idle Timeout: 60 seconds
- Execution Timeout: 600 seconds

### 3. Test Endpoint

```bash
curl -X POST https://api.runpod.ai/v2/{endpoint_id}/run \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "prompt": "A character smoothly shifting weight in an idle stance",
      "image_url": "https://example.com/character.png",
      "width": 512,
      "height": 512,
      "frames": 33,
      "fps": 16
    }
  }'
```

## Performance

**Benchmarks (RTX 4090 24GB):**

| Resolution | Frames | With LoRA | Without LoRA |
|------------|--------|-----------|--------------|
| 512×512 | 33 | ~30-40s | ~180s |
| 640×640 | 81 | ~97s | ~536s |

**VRAM Usage**: ~83-84% on RTX 4090 (20GB)

## Local Development

### Prerequisites
- Python 3.10+
- CUDA 11.8+
- Docker (recommended) OR ComfyUI installed locally

### Setup with Docker

```bash
# Clone repository
git clone https://github.com/eriktrk/wan2.2_14b_i2v_4step_runpod_worker.git
cd wan2.2_14b_i2v_4step_runpod_worker

# Build Docker image (downloads models automatically)
docker build -t wan22-i2v-worker:local .

# Run locally
docker run --gpus all -p 8188:8188 wan22-i2v-worker:local
```

### Setup without Docker

```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
cd /ComfyUI
pip install -r requirements.txt

# Download models manually to /ComfyUI/models/
# (See Dockerfile for wget commands)

# Install worker dependencies
cd /path/to/wan2.2_14b_i2v_4step_runpod_worker
pip install -r requirements.txt

# Start ComfyUI server
cd /ComfyUI
python main.py --listen 0.0.0.0 --port 8188 &

# Run handler
cd /path/to/wan2.2_14b_i2v_4step_runpod_worker
python src/rp_handler.py
```

## File Structure

```
wan2.2_14b_i2v_4step_runpod_worker/
├── src/
│   ├── rp_handler.py          # Main RunPod handler
│   ├── comfy_runner.py        # ComfyUI workflow executor
│   ├── input_validator.py     # Input validation
│   └── utils.py               # Helper functions
├── workflows/
│   └── wan22_14B_i2v_lightning.json  # Optimized workflow
├── tests/
│   └── test_input.json        # Sample test input
├── Dockerfile                  # Container configuration (includes model downloads)
├── entrypoint.sh              # Startup script
├── requirements.txt           # Python dependencies
└── README.md
```

## Troubleshooting

### "Model not found" errors
- Verify models were downloaded during Docker build
- Check all 6 model files exist in `/ComfyUI/models/` subdirectories
- Ensure model filenames match exactly (case-sensitive)
- Review Docker build logs for download failures

### ComfyUI fails to start
- Check logs: `docker logs <container_id>`
- Verify CUDA/GPU drivers are working
- Increase startup wait time in `entrypoint.sh`

### Out of memory errors
- Reduce resolution (e.g., 512×512 instead of 640×640)
- Reduce frame count
- Ensure only 4-step LoRA workflow is active

### Slow generation times
- Verify LoRA models are loaded (check entrypoint logs)
- Confirm `steps=4` is being used
- Check GPU utilization with `nvidia-smi`

## License

MIT License - See LICENSE file for details

## Use Cases

This worker excels at:
- **2D Game Character Animation**: Idle states, breathing animations, stance shifts
- **Sprite Sheet Animation**: Convert static sprites into dynamic animated sequences
- **UI Element Animation**: Animate buttons, icons, and menu elements
- **Asset Variation**: Generate multiple animation variations from single reference images
- **Concept Previewing**: Quick previews of how static game assets will look in motion

**Example Prompts for Game Assets:**
- *"Character smoothly shifts weight from one foot to the other in a combat-ready idle stance"*
- *"Gentle breathing animation with slight shoulder movement, maintaining alert posture"*
- *"Subtle weapon sway while character remains stationary in guard position"*
- *"Soft fabric and hair movement from ambient wind, character standing still"*

## Credits

- **Wan2.2 Model**: [Comfy-Org](https://huggingface.co/Comfy-Org)
- **Base Template**: [ComfyUI Wan2.2 Tutorial](https://docs.comfy.org/tutorials/video/wan/wan2_2)
- **ComfyUI**: [comfyanonymous](https://github.com/comfyanonymous/ComfyUI)
- **RunPod**: [RunPod.io](https://runpod.io)
