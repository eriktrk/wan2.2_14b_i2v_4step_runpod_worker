"""
ComfyUI workflow runner for Wan2.2 I2V Lightning.
"""

import json
import os
import time
import uuid
import websocket
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional


class ComfyUIError(Exception):
    """Custom exception for ComfyUI execution errors."""
    pass


class ComfyUIRunner:
    """Manages ComfyUI workflow execution via API."""

    def __init__(
        self,
        server_address: str = "127.0.0.1:8188",
        workflow_path: str = "/app/workflows/wan22_14B_i2v_lightning.json"
    ):
        """
        Initialize ComfyUI runner.

        Args:
            server_address: ComfyUI server address (host:port)
            workflow_path: Path to workflow JSON file
        """
        self.server_address = server_address
        self.workflow_path = workflow_path
        self.client_id = str(uuid.uuid4())

    def load_workflow(self) -> Dict[str, Any]:
        """Load workflow JSON from disk."""
        if not os.path.exists(self.workflow_path):
            raise ComfyUIError(f"Workflow file not found: {self.workflow_path}")

        with open(self.workflow_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def inject_parameters(
        self,
        workflow: Dict[str, Any],
        prompt: str,
        negative_prompt: str,
        input_image_path: str,
        output_video_path: str,
        width: int,
        height: int,
        frames: int,
        fps: int,
        cfg: float,
        steps: int
    ) -> Dict[str, Any]:
        """
        Inject dynamic parameters into workflow (API format).

        Args:
            workflow: Original workflow dict (API format with node IDs as keys)
            prompt: Positive prompt
            negative_prompt: Negative prompt
            input_image_path: Path to input image
            output_video_path: Path for output video
            width: Video width
            height: Video height
            frames: Number of frames
            fps: Frames per second
            cfg: CFG scale
            steps: Sampling steps

        Returns:
            Modified workflow dict in API format
        """
        # Create a deep copy to avoid modifying original
        workflow = json.loads(json.dumps(workflow))

        # Node 137: LoadImage - Input image filename
        if "137" in workflow:
            workflow["137"]["inputs"]["image"] = os.path.basename(input_image_path)

        # Node 93: CLIPTextEncode (Positive prompt)
        if "93" in workflow:
            workflow["93"]["inputs"]["text"] = prompt

        # Node 89: CLIPTextEncode (Negative prompt)
        if "89" in workflow:
            workflow["89"]["inputs"]["text"] = negative_prompt

        # Node 98: WanImageToVideo - Dimensions and frames
        if "98" in workflow:
            workflow["98"]["inputs"]["width"] = width
            workflow["98"]["inputs"]["height"] = height
            workflow["98"]["inputs"]["length"] = frames

        # Node 86: KSamplerAdvanced (High Noise) - Steps & CFG
        if "86" in workflow:
            workflow["86"]["inputs"]["steps"] = steps
            workflow["86"]["inputs"]["cfg"] = cfg

        # Node 85: KSamplerAdvanced (Low Noise) - Steps & CFG
        if "85" in workflow:
            workflow["85"]["inputs"]["steps"] = steps
            workflow["85"]["inputs"]["cfg"] = cfg

        # Node 94: CreateVideo - FPS
        if "94" in workflow:
            workflow["94"]["inputs"]["fps"] = fps

        # Node 108: SaveVideo - Output filename prefix
        if "108" in workflow:
            output_filename = os.path.splitext(os.path.basename(output_video_path))[0]
            workflow["108"]["inputs"]["filename_prefix"] = output_filename

        return workflow

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Queue a prompt for execution.

        Args:
            workflow: Workflow dictionary

        Returns:
            Prompt ID

        Raises:
            ComfyUIError: If queueing fails
        """
        payload = {
            "prompt": workflow,
            "client_id": self.client_id
        }

        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"http://{self.server_address}/prompt",
            data=data,
            headers={'Content-Type': 'application/json'}
        )

        try:
            response = urllib.request.urlopen(req)
            result = json.loads(response.read())
            return result['prompt_id']
        except Exception as e:
            raise ComfyUIError(f"Failed to queue prompt: {e}")

    def get_history(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution history for a prompt.

        Args:
            prompt_id: Prompt ID

        Returns:
            History dict or None if not found
        """
        try:
            req = urllib.request.Request(
                f"http://{self.server_address}/history/{prompt_id}"
            )
            response = urllib.request.urlopen(req)
            history = json.loads(response.read())
            return history.get(prompt_id)
        except Exception:
            return None

    def wait_for_completion(self, prompt_id: str, timeout: int = 600) -> Dict[str, Any]:
        """
        Wait for prompt execution to complete.

        Args:
            prompt_id: Prompt ID
            timeout: Maximum wait time in seconds

        Returns:
            Execution history

        Raises:
            ComfyUIError: If execution fails or times out
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            history = self.get_history(prompt_id)

            if history is not None:
                # Check if execution completed
                if 'outputs' in history:
                    return history

                # Check for errors
                if 'status' in history and history['status'].get('completed') is False:
                    error_msg = history['status'].get('messages', ['Unknown error'])
                    raise ComfyUIError(f"Execution failed: {error_msg}")

            time.sleep(2)

        raise ComfyUIError(f"Execution timed out after {timeout} seconds")

    def get_output_path(self, history: Dict[str, Any], output_dir: str = "/tmp") -> str:
        """
        Extract output video path from execution history.

        Args:
            history: Execution history
            output_dir: Expected output directory

        Returns:
            Path to generated video

        Raises:
            ComfyUIError: If output not found
        """
        # Node 108 (SaveVideo) produces the output
        outputs = history.get('outputs', {})

        # Look for SaveVideo output (Node 108)
        if '108' in outputs:
            node_output = outputs['108']
            if 'gifs' in node_output and len(node_output['gifs']) > 0:
                # ComfyUI may save as .mp4 or .gif - check both
                video_info = node_output['gifs'][0]
                filename = video_info['filename']
                subfolder = video_info.get('subfolder', '')

                # Construct full path
                if subfolder:
                    output_path = os.path.join(output_dir, subfolder, filename)
                else:
                    output_path = os.path.join(output_dir, filename)

                if os.path.exists(output_path):
                    return output_path

        raise ComfyUIError("Output video not found in execution history")

    def run_workflow(
        self,
        prompt: str,
        negative_prompt: str,
        input_image_path: str,
        output_video_path: str,
        width: int = 512,
        height: int = 512,
        frames: int = 33,
        fps: int = 16,
        cfg: float = 1.0,
        steps: int = 4
    ) -> str:
        """
        Execute complete workflow and return output video path.

        Args:
            prompt: Positive prompt
            negative_prompt: Negative prompt
            input_image_path: Path to input image
            output_video_path: Desired output path
            width: Video width
            height: Video height
            frames: Number of frames
            fps: Frames per second
            cfg: CFG scale
            steps: Sampling steps

        Returns:
            Path to generated video file

        Raises:
            ComfyUIError: If execution fails
        """
        # Load and modify workflow
        workflow = self.load_workflow()
        workflow = self.inject_parameters(
            workflow=workflow,
            prompt=prompt,
            negative_prompt=negative_prompt,
            input_image_path=input_image_path,
            output_video_path=output_video_path,
            width=width,
            height=height,
            frames=frames,
            fps=fps,
            cfg=cfg,
            steps=steps
        )

        # Queue prompt
        prompt_id = self.queue_prompt(workflow)
        print(f"Queued prompt: {prompt_id}")

        # Wait for completion
        history = self.wait_for_completion(prompt_id)
        print(f"Execution completed: {prompt_id}")

        # Get output path
        output_path = self.get_output_path(history, os.path.dirname(output_video_path))
        print(f"Output video: {output_path}")

        return output_path
