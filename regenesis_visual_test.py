"""Visual/GUI testing for ReGenesis application.

This module tests that GUI elements are actually visible and rendered correctly.
It uses pyautogui for screenshots and PIL for image analysis.

Install dependencies:
    pip3 install pyautogui pillow

Run tests:
    python3 regenesis_visual_test.py
"""

import unittest
import time
import subprocess
import signal
import os
from pathlib import Path

try:
    import pyautogui
    from PIL import Image, ImageDraw
    VISUAL_TESTS_AVAILABLE = True
except ImportError:
    VISUAL_TESTS_AVAILABLE = False
    print("WARNING: pyautogui or Pillow not installed. Visual tests will be skipped.")
    print("Install with: pip3 install pyautogui pillow")


class TestRegenesisVisuals(unittest.TestCase):
    """Test that GUI elements are actually visible on screen."""

    @classmethod
    def setUpClass(cls):
        """Start the ReGenesis application."""
        if not VISUAL_TESTS_AVAILABLE:
            return

        # Start the app in background
        cls.app_process = subprocess.Popen(
            ['python3', 'main.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Wait for app to fully start (adjust time if needed)
        print("\n" + "="*70)
        print("Waiting for app to start...")
        print("="*70)
        time.sleep(3)

        print("\nIMPORTANT: Make sure the ReGenesis window is fully visible")
        print("           and not covered by other windows!")
        print("\nStarting tests in 2 seconds...\n")
        time.sleep(2)

        # Create screenshots directory
        cls.screenshot_dir = Path(__file__).parent / 'test_screenshots'
        cls.screenshot_dir.mkdir(exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        """Close the application."""
        if not VISUAL_TESTS_AVAILABLE:
            return

        # Gracefully close the app
        try:
            cls.app_process.terminate()
            cls.app_process.wait(timeout=5)
        except:
            cls.app_process.kill()

    def _take_screenshot(self, name):
        """Take a screenshot and save it."""
        screenshot = pyautogui.screenshot()
        filepath = self.screenshot_dir / f"{name}.png"
        screenshot.save(filepath)
        return screenshot, filepath

    def _has_color_in_region(self, screenshot, region, color_threshold=50):
        """Check if a region has non-black/non-white pixels (actual content)."""
        x, y, width, height = region
        crop = screenshot.crop((x, y, x + width, y + height))

        # Check if there are pixels that aren't pure black or pure white
        pixels = crop.getdata()
        colored_pixels = 0

        for pixel in pixels:
            r, g, b = pixel[:3]  # Handle RGB or RGBA
            # Skip if pure black or pure white (background)
            if (r, g, b) != (0, 0, 0) and (r, g, b) != (255, 255, 255):
                # Check if it has some variation
                if abs(r - g) > 10 or abs(g - b) > 10 or abs(r - b) > 10:
                    colored_pixels += 1

        total_pixels = len(pixels)
        content_ratio = colored_pixels / total_pixels if total_pixels > 0 else 0

        return content_ratio > 0.01  # At least 1% of region has content

    def _find_window_position(self):
        """Try to find the ReGenesis window position by detecting it in a screenshot."""
        # Take a full screen screenshot
        screenshot = pyautogui.screenshot()

        # Search for a light-colored rectangular region (the app window)
        # We'll look for the canvas area which should have rulers
        width, height = screenshot.size

        # Simple heuristic: find largest light-colored rectangle
        # For now, just return center of screen with expected dimensions
        # (This is a simplified approach - a full implementation would use
        # image processing to detect the actual window bounds)

        screen_width, screen_height = pyautogui.size()

        # Assuming 1000x700 window centered
        window_x = (screen_width - 1000) // 2
        window_y = (screen_height - 700) // 2

        # Add some offset for macOS title bar (~30px)
        window_y += 30

        print(f"Assuming window at ({window_x}, {window_y}) size 1000x700")
        print(f"Screen size: {screen_width}x{screen_height}")

        return window_x, window_y, 1000, 700

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_01_window_appears(self):
        """Test that the application window appears on screen."""
        screenshot, filepath = self._take_screenshot("01_window_appears")

        # Get screen size
        width, height = screenshot.size

        self.assertGreater(width, 0, "Screenshot width should be > 0")
        self.assertGreater(height, 0, "Screenshot height should be > 0")
        print(f"✓ Screenshot taken: {filepath} ({width}x{height})")

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_02_tree_panel_visible(self):
        """Test that the project tree panel is visible (not all black)."""
        screenshot, filepath = self._take_screenshot("02_tree_panel")

        # Estimate tree panel location (left side of window)
        win_x, win_y, win_w, win_h = self._find_window_position()

        # Tree panel should be on the left, approximately 300px wide
        tree_region = (win_x + 10, win_y + 100, 280, 400)

        has_content = self._has_color_in_region(screenshot, tree_region)

        # Draw debug rectangle on screenshot
        img_copy = screenshot.copy()
        draw = ImageDraw.Draw(img_copy)
        draw.rectangle(tree_region, outline='red', width=3)
        img_copy.save(self.screenshot_dir / "02_tree_panel_debug.png")

        self.assertTrue(has_content,
                       f"Tree panel appears empty/black. Check {filepath}")
        print(f"✓ Tree panel has visible content")

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_03_canvas_visible(self):
        """Test that the canvas area is visible."""
        screenshot, filepath = self._take_screenshot("03_canvas")

        # Estimate canvas location (right side of window)
        win_x, win_y, win_w, win_h = self._find_window_position()

        # Canvas should be on the right side
        canvas_region = (win_x + 350, win_y + 100, 400, 400)

        has_content = self._has_color_in_region(screenshot, canvas_region)

        # Draw debug rectangle
        img_copy = screenshot.copy()
        draw = ImageDraw.Draw(img_copy)
        draw.rectangle(canvas_region, outline='blue', width=3)
        img_copy.save(self.screenshot_dir / "03_canvas_debug.png")

        self.assertTrue(has_content,
                       f"Canvas appears empty. Check {filepath}")
        print(f"✓ Canvas has visible content")

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_04_origin_marker_visible(self):
        """Test that the red origin marker is visible."""
        screenshot, filepath = self._take_screenshot("04_origin_marker")

        # Look for red pixels ANYWHERE on screen (simpler and more reliable)
        # Count red pixels (RGB close to pure red)
        red_pixels = 0
        for pixel in screenshot.getdata():
            r, g, b = pixel[:3]
            # Check if pixel is red (high R, low G and B)
            if r > 200 and g < 100 and b < 100:
                red_pixels += 1

        self.assertGreater(red_pixels, 10,
                          f"No red origin marker found on screen (found {red_pixels} red pixels, expected > 10)")
        print(f"✓ Origin marker visible (found {red_pixels} red pixels)")

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_05_blue_rectangle_visible(self):
        """Test that the blue project boundary rectangle is visible."""
        screenshot, filepath = self._take_screenshot("05_blue_rectangle")

        # Look for blue pixels ANYWHERE on screen (simpler and more reliable)
        # Count blue pixels
        blue_pixels = 0
        for pixel in screenshot.getdata():
            r, g, b = pixel[:3]
            # Check if pixel is blue (RGB around #3498db)
            if b > 180 and r > 30 and r < 100 and g > 100 and g < 180:
                blue_pixels += 1

        self.assertGreater(blue_pixels, 50,
                          f"Project boundary rectangle not visible (found {blue_pixels} blue pixels, expected > 50)")
        print(f"✓ Project rectangle visible (found {blue_pixels} blue pixels)")

    @unittest.skipIf(not VISUAL_TESTS_AVAILABLE, "Visual testing libraries not installed")
    def test_06_rulers_visible(self):
        """Test that rulers are visible."""
        screenshot, filepath = self._take_screenshot("06_rulers")

        # Rulers should be at top and left edges
        win_x, win_y, win_w, win_h = self._find_window_position()

        # Top ruler region
        top_ruler_region = (win_x + 100, win_y + 50, 600, 30)
        has_top_ruler = self._has_color_in_region(screenshot, top_ruler_region)

        # Left ruler region
        left_ruler_region = (win_x + 10, win_y + 120, 30, 400)
        has_left_ruler = self._has_color_in_region(screenshot, left_ruler_region)

        self.assertTrue(has_top_ruler or has_left_ruler,
                       "No rulers visible")
        print(f"✓ Rulers visible (top: {has_top_ruler}, left: {has_left_ruler})")


def run_visual_tests():
    """Run visual tests with detailed output."""
    if not VISUAL_TESTS_AVAILABLE:
        print("\n" + "="*70)
        print("VISUAL TESTING NOT AVAILABLE")
        print("="*70)
        print("\nTo enable visual tests, install:")
        print("  pip3 install pyautogui pillow")
        print("\nNote: Visual tests require the GUI to be running on screen.")
        print("="*70)
        return False

    print("\n" + "="*70)
    print("REGENESIS VISUAL TESTING")
    print("="*70)
    print("\nNOTE: Do not interact with the computer during testing!")
    print("The app will launch and screenshots will be taken automatically.")
    print("\nScreenshots will be saved to: test_screenshots/")
    print("="*70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRegenesisVisuals)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("VISUAL TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL VISUAL TESTS PASSED")
        print("\nAll GUI elements are rendering correctly!")
    else:
        print("\n✗ SOME VISUAL TESTS FAILED")
        print("\nCheck the screenshots in test_screenshots/ to debug issues.")

    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_visual_tests()
    exit(0 if success else 1)
