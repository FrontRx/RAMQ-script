#!/usr/bin/env python3
"""
Test script to validate RAMQ extraction at different image sizes using Google Gemini.
Downloads test images, resizes them to various widths, and reports validation success rates.
"""

import os
import sys
from datetime import datetime
from typing import Dict, List, Tuple
from io import BytesIO
import httpx
from PIL import Image

from anthropic_vision_script import (
    get_ramq_from_bytes,
    resize_image_to_width,
    validate_ramq,
)

# Test image URLs
TEST_URLS = [
    "https://i.ibb.co/7Jm0KvX/IMG-2618.jpg",
    "https://i.ibb.co/m92CFv2/IMG-2608.jpg",
    "https://i.ibb.co/3MdsCGv/IMG-2610.jpg",
    "https://i.ibb.co/vV9MCcj/IMG-2611.jpg",
    "https://i.ibb.co/1qjwRbb/Screenshot-2024-09-13-at-9-25-47-PM.png",
]

# Test image widths (in pixels)
TEST_WIDTHS = [100, 200, 400, 800, 1200, 1600]

# Directory to save images
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Images")


def download_image(url: str, client: httpx.Client) -> Tuple[bytes, str]:
    """Download image from URL and return bytes and content type."""
    response = client.get(url)
    response.raise_for_status()
    content_type = response.headers.get('content-type', 'image/jpeg')
    return response.content, content_type


def save_image(image_data: bytes, filename: str) -> str:
    """Save image data to file and return the path."""
    os.makedirs(IMAGES_DIR, exist_ok=True)
    filepath = os.path.join(IMAGES_DIR, filename)
    with open(filepath, 'wb') as f:
        f.write(image_data)
    return filepath


def get_image_dimensions(image_data: bytes) -> Tuple[int, int]:
    """Get image width and height from bytes."""
    image = Image.open(BytesIO(image_data))
    return image.size


def get_image_format(content_type: str) -> Tuple[str, str]:
    """Get image format and extension from content type."""
    if "jpeg" in content_type.lower() or "jpg" in content_type.lower():
        return "JPEG", "jpg"
    elif "png" in content_type.lower():
        return "PNG", "png"
    else:
        return "PNG", "png"


def test_single_image_at_sizes(
    image_data: bytes,
    content_type: str,
    image_name: str,
    widths: List[int]
) -> Dict[int, Dict]:
    """
    Test RAMQ extraction on a single image at multiple sizes.
    Returns a dict mapping width to result info.
    """
    results = {}
    original_width, original_height = get_image_dimensions(image_data)
    img_format, ext = get_image_format(content_type)

    for width in widths:
        # Skip if target width is larger than original
        if width > original_width:
            print(f"  {width}px: Skipping (larger than original {original_width}px)")
            results[width] = {
                "status": "skipped",
                "reason": f"Target width larger than original ({original_width}px)",
                "ramq": None,
                "valid": None,
            }
            continue

        try:
            # Resize image (preserve format)
            resized_data = resize_image_to_width(image_data, width, img_format)

            # Save resized image
            save_filename = f"{image_name}_{width}px.{ext}"
            save_image(resized_data, save_filename)

            # Get RAMQ from resized image
            ramq, last_name, first_name, dob, gender, is_valid = get_ramq_from_bytes(
                resized_data, content_type
            )

            results[width] = {
                "status": "success",
                "ramq": ramq,
                "last_name": last_name,
                "first_name": first_name,
                "dob": dob.strftime("%Y-%m-%d") if dob else None,
                "gender": gender,
                "valid": is_valid,
            }
            print(f"  {width}px: RAMQ={ramq}, Valid={is_valid}")

        except Exception as e:
            results[width] = {
                "status": "error",
                "error": str(e),
                "ramq": None,
                "valid": None,
            }
            print(f"  {width}px: ERROR - {str(e)[:50]}...")

    return results


def run_tests():
    """Run all tests and generate summary."""
    print("=" * 70)
    print("RAMQ EXTRACTION SIZE VALIDATION TEST")
    print(f"Using Google Gemini API (gemini-2.0-flash)")
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    print()

    # Create HTTP client
    client = httpx.Client(timeout=httpx.Timeout(60.0, connect=30.0))

    all_results = {}

    # Download and test each image
    for i, url in enumerate(TEST_URLS, 1):
        image_name = f"image_{i}"
        print(f"\n[{i}/{len(TEST_URLS)}] Processing {url}")
        print("-" * 60)

        try:
            # Download original image
            image_data, content_type = download_image(url, client)
            orig_width, orig_height = get_image_dimensions(image_data)
            img_format, ext = get_image_format(content_type)
            print(f"  Original size: {orig_width}x{orig_height}px ({len(image_data)/1024:.1f}KB) [{ext.upper()}]")

            # Save original image
            save_image(image_data, f"{image_name}_original.{ext}")

            # Test at different sizes
            results = test_single_image_at_sizes(
                image_data, content_type, image_name, TEST_WIDTHS
            )
            all_results[image_name] = {
                "url": url,
                "original_size": (orig_width, orig_height),
                "results": results,
            }

        except Exception as e:
            print(f"  FAILED to download: {str(e)}")
            all_results[image_name] = {
                "url": url,
                "error": str(e),
            }

    client.close()

    # Generate summary
    print("\n")
    print("=" * 70)
    print("SUMMARY BY IMAGE SIZE")
    print("=" * 70)

    # Aggregate results by size
    size_stats = {width: {"total": 0, "valid": 0, "invalid": 0, "errors": 0, "skipped": 0}
                  for width in TEST_WIDTHS}

    for image_name, data in all_results.items():
        if "error" in data:
            continue
        for width, result in data.get("results", {}).items():
            if width not in size_stats:
                continue
            size_stats[width]["total"] += 1
            if result["status"] == "success":
                if result["valid"]:
                    size_stats[width]["valid"] += 1
                else:
                    size_stats[width]["invalid"] += 1
            elif result["status"] == "error":
                size_stats[width]["errors"] += 1
            elif result["status"] == "skipped":
                size_stats[width]["skipped"] += 1

    # Print summary table
    print()
    print(f"{'Size':<10} | {'Total':<6} | {'Valid':<6} | {'Invalid':<8} | {'Errors':<7} | {'Skipped':<8}")
    print("-" * 70)

    for width in TEST_WIDTHS:
        stats = size_stats[width]
        processed = stats["total"] - stats["skipped"]
        print(f"{width}px{'':<6} | {stats['total']:<6} | {stats['valid']:<6} | {stats['invalid']:<8} | {stats['errors']:<7} | {stats['skipped']:<8}")

    print()
    print("=" * 70)
    print("DETAILED RESULTS BY IMAGE")
    print("=" * 70)

    for image_name, data in all_results.items():
        print(f"\n{image_name}: {data.get('url', 'N/A')}")
        if "error" in data:
            print(f"  Download Error: {data['error']}")
            continue

        orig = data.get("original_size", (0, 0))
        print(f"  Original: {orig[0]}x{orig[1]}px")

        for width in TEST_WIDTHS:
            result = data.get("results", {}).get(width, {})
            status = result.get("status", "unknown")
            if status == "success":
                ramq = result.get("ramq", "N/A")
                valid = result.get("valid", False)
                status_str = "VALID" if valid else "INVALID"
                print(f"    {width}px: {status_str} - RAMQ: {ramq}")
            elif status == "error":
                print(f"    {width}px: ERROR - {result.get('error', 'Unknown')[:40]}")
            elif status == "skipped":
                print(f"    {width}px: SKIPPED - {result.get('reason', 'Unknown')}")

    print()
    print("=" * 70)
    print(f"Test completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Images saved to: {IMAGES_DIR}")
    print("=" * 70)

    return all_results


if __name__ == "__main__":
    results = run_tests()
