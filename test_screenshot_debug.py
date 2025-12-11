"""Debug script to help locate the ReGenesis window in screenshots.

This script takes a screenshot and helps you identify where the window is.
Run while ReGenesis is open and visible.
"""

import pyautogui
from PIL import Image, ImageDraw, ImageFont
import time

print("="*70)
print("REGENESIS WINDOW LOCATION DEBUGGER")
print("="*70)
print("\nMake sure ReGenesis is running and fully visible!")
print("Taking screenshot in 3 seconds...")
print()

time.sleep(3)

# Take screenshot
print("Capturing screenshot...")
screenshot = pyautogui.screenshot()
width, height = screenshot.size

print(f"Screen size: {width} x {height}")

# Save original
screenshot.save('test_screenshots/debug_original.png')
print(f"✓ Saved: test_screenshots/debug_original.png")

# Create a copy with grid overlay to help locate window
debug_img = screenshot.copy()
draw = ImageDraw.Draw(debug_img)

# Draw grid lines every 100 pixels
grid_spacing = 100
for x in range(0, width, grid_spacing):
    draw.line([(x, 0), (x, height)], fill='red', width=1)

for y in range(0, height, grid_spacing):
    draw.line([(0, y), (width, y)], fill='red', width=1)

# Draw coordinate labels
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
except:
    font = None

for x in range(0, width, grid_spacing):
    draw.text((x+5, 5), str(x), fill='red', font=font)

for y in range(0, height, grid_spacing):
    draw.text((5, y+5), str(y), fill='red', font=font)

# Save grid overlay
debug_img.save('test_screenshots/debug_grid.png')
print(f"✓ Saved: test_screenshots/debug_grid.png")

# Analyze colors
print("\nAnalyzing colors in screenshot...")

# Count specific colors
red_pixels = 0
blue_pixels = 0
total_pixels = width * height

for pixel in screenshot.getdata():
    r, g, b = pixel[:3]

    # Red (origin marker)
    if r > 200 and g < 100 and b < 100:
        red_pixels += 1

    # Blue (project rectangle #3498db)
    if b > 180 and r > 30 and r < 100 and g > 100 and g < 180:
        blue_pixels += 1

print(f"\nColor analysis:")
print(f"  Total pixels: {total_pixels:,}")
print(f"  Red pixels (origin marker): {red_pixels}")
print(f"  Blue pixels (project rect): {blue_pixels}")

if red_pixels > 0:
    print(f"\n✓ Found red origin marker! ({red_pixels} pixels)")
else:
    print(f"\n✗ No red origin marker found")

if blue_pixels > 50:
    print(f"✓ Found blue project rectangle! ({blue_pixels} pixels)")
else:
    print(f"✗ No blue project rectangle found")

# Find bounding box of red pixels to locate origin marker
if red_pixels > 0:
    print("\nLocating origin marker position...")
    min_x = width
    max_x = 0
    min_y = height
    max_y = 0

    pixels = screenshot.load()
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y][:3]
            if r > 200 and g < 100 and b < 100:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2

    print(f"  Origin marker location: ({center_x}, {center_y})")
    print(f"  Bounding box: ({min_x}, {min_y}) to ({max_x}, {max_y})")

    # Draw a circle around it
    highlight_img = screenshot.copy()
    draw2 = ImageDraw.Draw(highlight_img)

    # Draw large circle around origin marker
    radius = 50
    draw2.ellipse([center_x - radius, center_y - radius,
                   center_x + radius, center_y + radius],
                  outline='yellow', width=3)

    # Draw crosshairs
    draw2.line([(center_x - 100, center_y), (center_x + 100, center_y)],
              fill='yellow', width=2)
    draw2.line([(center_x, center_y - 100), (center_x, center_y + 100)],
              fill='yellow', width=2)

    highlight_img.save('test_screenshots/debug_origin_marker.png')
    print(f"  ✓ Saved: test_screenshots/debug_origin_marker.png")

print("\n" + "="*70)
print("INSTRUCTIONS:")
print("="*70)
print("1. Open test_screenshots/debug_grid.png")
print("2. Find the ReGenesis window in the image")
print("3. Note the coordinates (marked on the grid)")
print("4. The window should be somewhere on the screen!")
print("\nIf you found red/blue pixels, check debug_origin_marker.png")
print("to see where the origin marker is located.")
print("="*70)
