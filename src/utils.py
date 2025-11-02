"""
Utility functions for image/video processing and file operations.
"""

import base64
import io
import os
import uuid
import requests
from PIL import Image
from typing import Optional


def generate_job_id() -> str:
    """Generate a unique job ID for file naming."""
    return str(uuid.uuid4())


def download_image_from_url(url: str, output_path: str) -> None:
    """
    Download an image from a URL and save to disk.

    Args:
        url: Image URL
        output_path: Destination file path

    Raises:
        requests.RequestException: If download fails
        IOError: If file write fails
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    with open(output_path, 'wb') as f:
        f.write(response.content)


def decode_base64_image(base64_string: str, output_path: str) -> None:
    """
    Decode a base64 image string and save to disk.

    Args:
        base64_string: Base64-encoded image data
        output_path: Destination file path

    Raises:
        ValueError: If base64 string is invalid
        IOError: If file write fails
    """
    # Remove data URI prefix if present
    if ',' in base64_string:
        base64_string = base64_string.split(',', 1)[1]

    # Decode base64
    image_data = base64.b64decode(base64_string)

    # Validate it's a valid image
    try:
        image = Image.open(io.BytesIO(image_data))
        image.verify()
    except Exception as e:
        raise ValueError(f"Invalid image data: {e}")

    # Save to disk
    with open(output_path, 'wb') as f:
        f.write(image_data)


def encode_video_to_base64(video_path: str) -> str:
    """
    Encode a video file to base64 string.

    Args:
        video_path: Path to video file

    Returns:
        Base64-encoded video string

    Raises:
        FileNotFoundError: If video file doesn't exist
        IOError: If file read fails
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    with open(video_path, 'rb') as f:
        video_bytes = f.read()

    return base64.b64encode(video_bytes).decode('utf-8')


def cleanup_files(*file_paths: str) -> None:
    """
    Remove temporary files.

    Args:
        *file_paths: Variable number of file paths to delete
    """
    for path in file_paths:
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception as e:
            print(f"Warning: Failed to delete {path}: {e}")


def validate_image_file(image_path: str, max_size_mb: int = 10) -> None:
    """
    Validate an image file exists and is within size limits.

    Args:
        image_path: Path to image file
        max_size_mb: Maximum file size in MB

    Raises:
        FileNotFoundError: If image doesn't exist
        ValueError: If image is too large or invalid format
    """
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image file not found: {image_path}")

    # Check file size
    file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"Image size {file_size_mb:.2f}MB exceeds maximum {max_size_mb}MB")

    # Validate it's a valid image
    try:
        with Image.open(image_path) as img:
            img.verify()
    except Exception as e:
        raise ValueError(f"Invalid image file: {e}")
