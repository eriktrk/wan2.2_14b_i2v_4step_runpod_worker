#!/usr/bin/env python3
"""
Local test script for Wan2.2 I2V worker.
Tests all components without requiring GPU or ComfyUI server.
"""

import sys
import os
import json
from PIL import Image

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.comfy_runner import ComfyUIRunner, ComfyUIError
from src.input_validator import validate_input, ValidationError
from src.utils import generate_job_id, validate_image_file, decode_base64_image, encode_video_to_base64


def test_imports():
    """Test that all modules import successfully."""
    print("\n=== Test 1: Imports ===")
    try:
        from src.rp_handler import handler
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_input_validation():
    """Test input validation logic."""
    print("\n=== Test 2: Input Validation ===")

    # Test valid input
    try:
        result = validate_input({
            'prompt': 'walking animation',
            'image_base64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',  # 1x1 red pixel
            'width': 512,
            'height': 512,
            'frames': 33,
            'fps': 16,
            'cfg': 1.0,
            'steps': 4
        })
        print(f"✓ Valid input accepted: '{result['prompt'][:30]}...'")
    except ValidationError as e:
        print(f"✗ Valid input rejected: {e}")
        return False

    # Test invalid input (missing image)
    try:
        validate_input({'prompt': 'test'})
        print("✗ Should have failed - missing image")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected invalid input: {str(e)[:60]}")

    # Test invalid frame count
    try:
        validate_input({
            'prompt': 'test',
            'image_base64': 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
            'frames': 30  # Invalid - must be 8n+1
        })
        print("✗ Should have rejected invalid frame count")
        return False
    except ValidationError as e:
        print(f"✓ Correctly rejected invalid frames: {str(e)[:60]}")

    return True


def test_workflow_loading():
    """Test workflow loading and structure."""
    print("\n=== Test 3: Workflow Loading ===")

    try:
        # Override workflow path for local testing
        workflow_path = os.path.join(os.path.dirname(__file__), '..', 'workflows', 'wan22_14B_i2v_lightning.json')
        runner = ComfyUIRunner(workflow_path=workflow_path)
        workflow = runner.load_workflow()
        print(f"✓ Workflow loaded: {len(workflow)} nodes")

        # Verify it's API format
        assert isinstance(workflow, dict), "Workflow should be a dict"
        assert '137' in workflow, "Should have node 137 (LoadImage)"
        assert '93' in workflow, "Should have node 93 (Positive prompt)"
        assert '89' in workflow, "Should have node 89 (Negative prompt)"
        assert '98' in workflow, "Should have node 98 (WanImageToVideo)"
        assert '108' in workflow, "Should have node 108 (SaveVideo)"

        # Verify node structure
        assert 'inputs' in workflow['137'], "Nodes should have inputs"
        assert 'class_type' in workflow['137'], "Nodes should have class_type"

        print(f"  Node 137 class: {workflow['137']['class_type']}")
        print(f"  Node 93 class: {workflow['93']['class_type']}")
        print(f"  Node 98 class: {workflow['98']['class_type']}")
        print(f"  Node 108 class: {workflow['108']['class_type']}")

        return True
    except Exception as e:
        print(f"✗ Workflow loading failed: {e}")
        return False


def test_parameter_injection():
    """Test workflow parameter injection."""
    print("\n=== Test 4: Parameter Injection ===")

    try:
        # Override workflow path for local testing
        workflow_path = os.path.join(os.path.dirname(__file__), '..', 'workflows', 'wan22_14B_i2v_lightning.json')
        runner = ComfyUIRunner(workflow_path=workflow_path)
        workflow = runner.load_workflow()

        # Inject test parameters
        modified = runner.inject_parameters(
            workflow=workflow,
            prompt="test prompt for video generation",
            negative_prompt="test negative prompt",
            input_image_path="test_image.png",
            output_video_path="/tmp/output_video.mp4",
            width=640,
            height=480,
            frames=25,
            fps=24,
            cfg=1.5,
            steps=8
        )

        # Verify all modifications
        checks = [
            (modified['93']['inputs']['text'] == "test prompt for video generation", "Positive prompt"),
            (modified['89']['inputs']['text'] == "test negative prompt", "Negative prompt"),
            (modified['98']['inputs']['width'] == 640, "Width"),
            (modified['98']['inputs']['height'] == 480, "Height"),
            (modified['98']['inputs']['length'] == 25, "Frames"),
            (modified['94']['inputs']['fps'] == 24, "FPS"),
            (modified['86']['inputs']['cfg'] == 1.5, "CFG (high noise)"),
            (modified['85']['inputs']['cfg'] == 1.5, "CFG (low noise)"),
            (modified['86']['inputs']['steps'] == 8, "Steps (high noise)"),
            (modified['85']['inputs']['steps'] == 8, "Steps (low noise)"),
            (modified['137']['inputs']['image'] == "test_image.png", "Image path"),
            (modified['108']['inputs']['filename_prefix'] == "output_video", "Output filename"),
        ]

        all_passed = True
        for check, name in checks:
            if check:
                print(f"  ✓ {name} injected correctly")
            else:
                print(f"  ✗ {name} injection failed")
                all_passed = False

        return all_passed
    except Exception as e:
        print(f"✗ Parameter injection failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_utility_functions():
    """Test utility functions."""
    print("\n=== Test 5: Utility Functions ===")

    try:
        # Test job ID generation
        job_id = generate_job_id()
        assert len(job_id) == 36, "Job ID should be UUID format"
        print(f"✓ Job ID generated: {job_id[:16]}...")

        # Create a test image
        test_img_path = '/tmp/test_worker_image.png'
        test_img = Image.new('RGB', (100, 100), color='red')
        test_img.save(test_img_path)

        # Test image validation
        validate_image_file(test_img_path, max_size_mb=10)
        print("✓ Image validation passed")

        # Test base64 decode (using the 1x1 pixel from earlier)
        test_base64_path = '/tmp/test_base64_image.png'
        decode_base64_image(
            'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==',
            test_base64_path
        )
        print("✓ Base64 image decode works")

        # Cleanup
        os.remove(test_img_path)
        os.remove(test_base64_path)

        return True
    except Exception as e:
        print(f"✗ Utility function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_workflow_api_format():
    """Verify workflow is in correct API format for ComfyUI."""
    print("\n=== Test 6: Workflow API Format ===")

    try:
        workflow_path = os.path.join(os.path.dirname(__file__), '..', 'workflows', 'wan22_14B_i2v_lightning.json')
        with open(workflow_path) as f:
            wf = json.load(f)

        # Verify API format structure
        assert isinstance(wf, dict), "Workflow should be a dict"
        assert 'nodes' not in wf, "Should NOT be UI format (no 'nodes' array)"

        # Check all node IDs are strings
        for node_id in wf.keys():
            assert isinstance(node_id, str), f"Node ID {node_id} should be string"
            assert 'class_type' in wf[node_id], f"Node {node_id} missing class_type"
            assert 'inputs' in wf[node_id], f"Node {node_id} missing inputs"

        print(f"✓ Workflow is valid API format (not UI format)")
        print(f"✓ All {len(wf)} nodes have correct structure")

        # Verify critical nodes exist
        critical_nodes = {
            '137': 'LoadImage',
            '93': 'CLIPTextEncode',
            '89': 'CLIPTextEncode',
            '98': 'WanImageToVideo',
            '85': 'KSamplerAdvanced',
            '86': 'KSamplerAdvanced',
            '94': 'CreateVideo',
            '108': 'SaveVideo'
        }

        for node_id, expected_type in critical_nodes.items():
            assert node_id in wf, f"Missing critical node {node_id}"
            assert wf[node_id]['class_type'] == expected_type, f"Node {node_id} has wrong type"
            print(f"  ✓ Node {node_id} ({expected_type}) present")

        return True
    except Exception as e:
        print(f"✗ Workflow format check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Wan2.2 I2V Worker - Local Tests")
    print("=" * 60)

    tests = [
        test_imports,
        test_input_validation,
        test_workflow_loading,
        test_parameter_injection,
        test_utility_functions,
        test_workflow_api_format,
    ]

    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test {test_func.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
