"""
RunPod serverless handler for Wan2.2 I2V Lightning worker.
"""

import os
import sys
import traceback
import runpod

from utils import (
    generate_job_id,
    download_image_from_url,
    decode_base64_image,
    encode_video_to_base64,
    cleanup_files,
    validate_image_file
)
from input_validator import validate_input, ValidationError
from comfy_runner import ComfyUIRunner, ComfyUIError


def handler(job):
    """
    RunPod handler function for video generation.

    Args:
        job: RunPod job object containing input parameters

    Returns:
        Dictionary with video_base64 and metadata, or error information
    """
    job_input = job['input']
    job_id = generate_job_id()

    # File paths
    input_image_path = f"/tmp/input_{job_id}.png"
    output_video_path = f"/tmp/output_{job_id}"  # ComfyUI will add extension

    try:
        # ===== Step 1: Validate Input =====
        print("Validating input parameters...")
        try:
            params = validate_input(job_input)
        except ValidationError as e:
            return {"error": f"Validation error: {str(e)}"}

        # ===== Step 2: Prepare Input Image =====
        print("Preparing input image...")
        try:
            if params['image_url']:
                print(f"Downloading image from URL: {params['image_url']}")
                download_image_from_url(params['image_url'], input_image_path)
            else:
                print("Decoding base64 image...")
                decode_base64_image(params['image_base64'], input_image_path)

            # Validate image file
            validate_image_file(input_image_path, max_size_mb=10)

        except Exception as e:
            cleanup_files(input_image_path)
            return {"error": f"Image processing error: {str(e)}"}

        # ===== Step 3: Run ComfyUI Workflow =====
        print("Initializing ComfyUI runner...")
        runner = ComfyUIRunner(
            server_address=os.getenv("COMFYUI_SERVER", "127.0.0.1:8188"),
            workflow_path="/app/workflows/wan22_14B_i2v_lightning.json"
        )

        print("Executing workflow...")
        print(f"  Prompt: {params['prompt'][:100]}...")
        print(f"  Dimensions: {params['width']}x{params['height']}")
        print(f"  Frames: {params['frames']} @ {params['fps']} fps")
        print(f"  CFG: {params['cfg']}, Steps: {params['steps']}")

        try:
            actual_output_path = runner.run_workflow(
                prompt=params['prompt'],
                negative_prompt=params['negative_prompt'],
                input_image_path=input_image_path,
                output_video_path=output_video_path,
                width=params['width'],
                height=params['height'],
                frames=params['frames'],
                fps=params['fps'],
                cfg=params['cfg'],
                steps=params['steps']
            )
        except ComfyUIError as e:
            cleanup_files(input_image_path)
            return {"error": f"ComfyUI execution error: {str(e)}"}

        # ===== Step 4: Encode Output Video =====
        print(f"Encoding output video: {actual_output_path}")
        try:
            video_base64 = encode_video_to_base64(actual_output_path)
        except Exception as e:
            cleanup_files(input_image_path, actual_output_path)
            return {"error": f"Video encoding error: {str(e)}"}

        # ===== Step 5: Cleanup and Return =====
        print("Cleaning up temporary files...")
        cleanup_files(input_image_path, actual_output_path)

        print("Video generation completed successfully!")
        return {
            "video_base64": video_base64,
            "metadata": {
                "width": params['width'],
                "height": params['height'],
                "frames": params['frames'],
                "fps": params['fps'],
                "cfg": params['cfg'],
                "steps": params['steps']
            }
        }

    except Exception as e:
        # Catch-all for unexpected errors
        print("Unexpected error occurred:")
        traceback.print_exc()

        cleanup_files(input_image_path, output_video_path)

        return {
            "error": f"Unexpected error: {str(e)}",
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    print("Starting Wan2.2 I2V Lightning RunPod Worker...")
    print(f"ComfyUI Server: {os.getenv('COMFYUI_SERVER', '127.0.0.1:8188')}")

    runpod.serverless.start({"handler": handler})
