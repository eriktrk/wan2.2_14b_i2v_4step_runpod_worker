"""
Input validation for RunPod job parameters.
"""

from typing import Dict, Any, Optional


# Default Chinese negative prompt (optimized for Wan2.2 model)
DEFAULT_NEGATIVE_PROMPT = (
    "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，"
    "整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余的手指，"
    "画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，"
    "静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走"
)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def validate_input(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalize job input parameters.

    Args:
        job_input: Raw input dictionary from RunPod

    Returns:
        Validated and normalized parameters

    Raises:
        ValidationError: If validation fails
    """
    validated = {}

    # === Required: Prompt ===
    prompt = job_input.get('prompt', '').strip()
    if not prompt:
        raise ValidationError("'prompt' is required and cannot be empty")
    if len(prompt) > 1000:
        raise ValidationError("'prompt' exceeds maximum length of 1000 characters")
    validated['prompt'] = prompt

    # === Required: Image (either base64 or URL) ===
    image_base64 = job_input.get('image_base64')
    image_url = job_input.get('image_url')

    if not image_base64 and not image_url:
        raise ValidationError("Either 'image_base64' or 'image_url' must be provided")

    if image_base64 and image_url:
        raise ValidationError("Provide only one of 'image_base64' or 'image_url', not both")

    validated['image_base64'] = image_base64
    validated['image_url'] = image_url

    # === Optional: Negative Prompt ===
    negative_prompt = job_input.get('negative_prompt', DEFAULT_NEGATIVE_PROMPT).strip()
    if len(negative_prompt) > 1000:
        raise ValidationError("'negative_prompt' exceeds maximum length of 1000 characters")
    validated['negative_prompt'] = negative_prompt

    # === Optional: CFG Scale ===
    cfg = job_input.get('cfg', 1.0)
    try:
        cfg = float(cfg)
        if cfg < 0.1 or cfg > 20.0:
            raise ValidationError("'cfg' must be between 0.1 and 20.0")
    except (TypeError, ValueError):
        raise ValidationError("'cfg' must be a valid number")
    validated['cfg'] = cfg

    # === Optional: Width ===
    width = job_input.get('width', 512)
    try:
        width = int(width)
        if width < 64 or width > 1024:
            raise ValidationError("'width' must be between 64 and 1024")
        if width % 64 != 0:
            raise ValidationError("'width' must be a multiple of 64")
    except (TypeError, ValueError):
        raise ValidationError("'width' must be a valid integer")
    validated['width'] = width

    # === Optional: Height ===
    height = job_input.get('height', 512)
    try:
        height = int(height)
        if height < 64 or height > 1024:
            raise ValidationError("'height' must be between 64 and 1024")
        if height % 64 != 0:
            raise ValidationError("'height' must be a multiple of 64")
    except (TypeError, ValueError):
        raise ValidationError("'height' must be a valid integer")
    validated['height'] = height

    # === Optional: Frames ===
    frames = job_input.get('frames', 33)
    try:
        frames = int(frames)
        if frames < 9 or frames > 121:
            raise ValidationError("'frames' must be between 9 and 121")
        if frames % 8 != 1:  # Wan2.2 requires frames = 8n+1 (9, 17, 25, 33, 41, ...)
            raise ValidationError("'frames' must be 8n+1 (e.g., 9, 17, 25, 33, 41, 49, 57, 65, 73, 81...)")
    except (TypeError, ValueError):
        raise ValidationError("'frames' must be a valid integer")
    validated['frames'] = frames

    # === Optional: FPS ===
    fps = job_input.get('fps', 16)
    try:
        fps = int(fps)
        if fps < 8 or fps > 60:
            raise ValidationError("'fps' must be between 8 and 60")
    except (TypeError, ValueError):
        raise ValidationError("'fps' must be a valid integer")
    validated['fps'] = fps

    # === Optional: Steps ===
    steps = job_input.get('steps', 4)
    try:
        steps = int(steps)
        if steps < 1 or steps > 50:
            raise ValidationError("'steps' must be between 1 and 50")
    except (TypeError, ValueError):
        raise ValidationError("'steps' must be a valid integer")
    validated['steps'] = steps

    return validated
