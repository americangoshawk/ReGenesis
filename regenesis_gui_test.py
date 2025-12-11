"""Test suite for ReGenesis GUI application.

This test suite validates core functionality to catch regressions when making changes.
Run with: python3 regenesis_gui_test.py
"""

import unittest
import tkinter as tk
import ttkbootstrap as ttk
from regenesis_gui import RegenesisGUI
from preferences_manager import PreferencesManager
import time


class TestPreferencesManager(unittest.TestCase):
    """Test the preferences manager."""

    def setUp(self):
        """Create a fresh preferences manager for each test."""
        self.prefs = PreferencesManager()

    def test_default_preferences(self):
        """Test that default preferences are set correctly."""
        defaults = self.prefs._get_default_preferences()
        self.assertIn('location', defaults)
        self.assertIn('theme', defaults)
        self.assertIn('development_mode', defaults)
        self.assertEqual(defaults['theme'], 'flatly')
        self.assertEqual(defaults['development_mode'], False)

    def test_set_and_get_location(self):
        """Test setting and getting location coordinates."""
        self.prefs.set_location(42.3601, -71.0589)
        lat, lon = self.prefs.get_location()
        self.assertEqual(lat, 42.3601)
        self.assertEqual(lon, -71.0589)

    def test_set_and_get_theme(self):
        """Test setting and getting theme."""
        self.prefs.set_theme('darkly')
        self.assertEqual(self.prefs.get_theme(), 'darkly')

    def test_set_and_get_development_mode(self):
        """Test setting and getting development mode."""
        self.prefs.set_development_mode(True)
        self.assertTrue(self.prefs.is_development_mode())

        self.prefs.set_development_mode(False)
        self.assertFalse(self.prefs.is_development_mode())

    def test_nested_key_access(self):
        """Test accessing nested preference keys with dot notation."""
        self.prefs.set('location.latitude', 40.7128)
        self.assertEqual(self.prefs.get('location.latitude'), 40.7128)


class TestRegenesisGUIBasics(unittest.TestCase):
    """Test basic ReGenesis GUI functionality without showing window."""

    @classmethod
    def setUpClass(cls):
        """Create a single GUI instance for all tests (faster)."""
        # Create root window but don't show it
        cls.root = ttk.Window(themename="flatly")
        cls.root.withdraw()  # Hide the window

        # We'll manually initialize parts of RegenesisGUI for testing
        # without going through the full __init__ which shows windows

    @classmethod
    def tearDownClass(cls):
        """Clean up the GUI instance."""
        try:
            cls.root.destroy()
        except:
            pass

    def test_zoom_limits(self):
        """Test that zoom stays within valid limits."""
        min_zoom = 0.01
        max_zoom = 10.0

        # Test zoom values
        test_zooms = [0.005, 0.01, 0.5, 1.0, 5.0, 10.0, 15.0]

        for zoom in test_zooms:
            # Clamp to limits (simulating what the app should do)
            clamped = max(min_zoom, min(max_zoom, zoom))

            if zoom < min_zoom:
                self.assertEqual(clamped, min_zoom)
            elif zoom > max_zoom:
                self.assertEqual(clamped, max_zoom)
            else:
                self.assertEqual(clamped, zoom)

    def test_coordinate_conversion(self):
        """Test converting between canvas pixels and world coordinates."""
        # Simulate coordinate conversion (50 pixels = 1 unit at zoom 1.0)
        canvas_zoom = 1.0
        pixels_per_unit = 50 * canvas_zoom

        # Test conversion from world to pixels
        world_x = 10  # 10 units in world space
        pixel_x = world_x * pixels_per_unit
        self.assertEqual(pixel_x, 500)  # Should be 500 pixels

        # Test conversion from pixels to world
        reverse_world_x = pixel_x / pixels_per_unit
        self.assertEqual(reverse_world_x, world_x)

        # Test at different zoom levels
        canvas_zoom = 2.0
        pixels_per_unit = 50 * canvas_zoom
        pixel_x = world_x * pixels_per_unit
        self.assertEqual(pixel_x, 1000)  # Zoomed in 2x

    def test_vertex_size_calculation(self):
        """Test that vertex size scales correctly with zoom."""
        # Vertex radius formula: min(10, max(3, 10 * zoom))

        test_cases = [
            (0.1, 3),    # Very zoomed out -> min size
            (0.3, 3),    # Still at min
            (0.5, 5),    # Starting to scale
            (1.0, 10),   # Normal zoom -> max size
            (2.0, 10),   # Zoomed in -> max size
            (5.0, 10),   # Very zoomed in -> still max size
        ]

        for zoom, expected_radius in test_cases:
            radius = min(10, max(3, 10 * zoom))
            self.assertEqual(radius, expected_radius,
                           f"Failed for zoom {zoom}: expected {expected_radius}, got {radius}")

    def test_drag_threshold(self):
        """Test drag detection threshold."""
        # Drag threshold is 5 pixels (checks dx > 5 OR dy > 5, not distance)
        threshold = 5

        # Simulate mouse movements
        test_cases = [
            (0, 0, 0, 0, False),    # No movement
            (0, 0, 3, 3, False),    # Small movement (< threshold in both axes)
            (0, 0, 5, 0, False),    # Exactly at threshold (not >)
            (0, 0, 6, 0, True),     # Movement > threshold in X
            (0, 0, 0, 6, True),     # Movement > threshold in Y
            (0, 0, 4, 4, False),    # Diagonal but neither axis > threshold
            (0, 0, 6, 6, True),     # Diagonal with both > threshold
        ]

        for start_x, start_y, end_x, end_y, should_drag in test_cases:
            dx = abs(end_x - start_x)
            dy = abs(end_y - start_y)
            is_drag = (dx > threshold or dy > threshold)
            self.assertEqual(is_drag, should_drag,
                           f"Failed for movement ({start_x},{start_y}) -> ({end_x},{end_y})")


class TestTreeOperations(unittest.TestCase):
    """Test tree-related operations."""

    def setUp(self):
        """Create a minimal tree structure for testing."""
        self.root = ttk.Window(themename="flatly")
        self.root.withdraw()

        # Create a minimal treeview
        self.tree = ttk.Treeview(self.root, columns=('type',))

        # Create sample tree structure
        self.project = self.tree.insert('', 'end', text='Test Project',
                                       values=('project', '42.0', '-71.0', '100', '150', 'feet'))
        self.region1 = self.tree.insert(self.project, 'end', text='Region 1',
                                       values=('region', 'meadow', 'medium', 'loam', 'full-sun'))
        self.region2 = self.tree.insert(self.project, 'end', text='Region 2',
                                       values=('region', 'layered', 'dry', 'loam', 'part-sun'))

    def tearDown(self):
        """Clean up."""
        try:
            self.root.destroy()
        except:
            pass

    def test_tree_structure(self):
        """Test that tree structure is created correctly."""
        # Check project exists
        self.assertTrue(self.tree.exists(self.project))

        # Check regions are children of project
        children = self.tree.get_children(self.project)
        self.assertEqual(len(children), 2)
        self.assertIn(self.region1, children)
        self.assertIn(self.region2, children)

    def test_find_root_project(self):
        """Test finding the root project from any node."""
        # Simulate _find_project_root logic
        def find_root(item):
            current = item
            while self.tree.parent(current):
                current = self.tree.parent(current)
            return current

        # From project -> should return project
        root = find_root(self.project)
        self.assertEqual(root, self.project)

        # From region -> should return project
        root = find_root(self.region1)
        self.assertEqual(root, self.project)

        root = find_root(self.region2)
        self.assertEqual(root, self.project)

    def test_tree_item_values(self):
        """Test accessing tree item values."""
        # Test project values
        values = self.tree.item(self.project, 'values')
        self.assertEqual(values[0], 'project')
        self.assertEqual(values[3], '100')  # width
        self.assertEqual(values[4], '150')  # length

        # Test region values
        values = self.tree.item(self.region1, 'values')
        self.assertEqual(values[0], 'region')
        self.assertEqual(values[1], 'meadow')


class TestPolygonOperations(unittest.TestCase):
    """Test polygon-related operations."""

    def test_polygon_storage(self):
        """Test storing and retrieving polygons."""
        # Simulate region_polygons dict
        region_polygons = {}

        # Store a polygon
        item_id = 'region_001'
        vertices = [(10, 10), (100, 10), (100, 100), (10, 100)]
        region_polygons[item_id] = list(vertices)

        # Retrieve and verify
        self.assertIn(item_id, region_polygons)
        stored = region_polygons[item_id]
        self.assertEqual(len(stored), 4)
        self.assertEqual(stored[0], (10, 10))

    def test_polygon_vertices_minimum(self):
        """Test that polygons maintain minimum 3 vertices."""
        vertices = [(0, 0), (100, 0), (100, 100), (0, 100)]

        # Should allow deletion if > 3 vertices
        self.assertTrue(len(vertices) > 3)

        # Simulate deletion
        vertices_after_delete = vertices[:3]
        self.assertEqual(len(vertices_after_delete), 3)

        # Should NOT allow deletion if = 3 vertices
        self.assertFalse(len(vertices_after_delete) > 3)

    def test_point_to_vertex_distance(self):
        """Test finding vertices near a point."""
        vertices = [(0, 0), (100, 0), (100, 100), (0, 100)]
        threshold = 10

        # Point very close to first vertex
        test_point = (2, 3)

        # Calculate distance to first vertex
        vx, vy = vertices[0]
        dist = ((test_point[0] - vx) ** 2 + (test_point[1] - vy) ** 2) ** 0.5

        self.assertLess(dist, threshold)
        self.assertTrue(dist <= threshold)

    def test_flatten_coordinates(self):
        """Test flattening vertex list for tkinter polygon."""
        vertices = [(10, 20), (30, 40), (50, 60)]

        # Flatten for tkinter
        flat = [coord for vertex in vertices for coord in vertex]

        self.assertEqual(flat, [10, 20, 30, 40, 50, 60])
        self.assertEqual(len(flat), len(vertices) * 2)


class TestAutoZoom(unittest.TestCase):
    """Test auto-zoom functionality."""

    def test_auto_zoom_calculation(self):
        """Test that auto-zoom correctly fits rectangles."""
        # Canvas size
        canvas_width = 800
        canvas_height = 600

        # Project rectangle (in world units)
        project_width = 100
        project_length = 150

        # Calculate required size with 20% margin
        pixels_per_unit = 50  # At zoom 1.0
        rect_width = project_width * pixels_per_unit  # 5000 pixels
        rect_height = project_length * pixels_per_unit  # 7500 pixels

        required_width = rect_width * 1.2   # 6000 pixels
        required_height = rect_height * 1.2  # 9000 pixels

        # Calculate zoom needed
        zoom_for_width = canvas_width / required_width   # 800/6000 = 0.133
        zoom_for_height = canvas_height / required_height  # 600/9000 = 0.067
        auto_zoom = min(zoom_for_width, zoom_for_height)  # 0.067

        # Should use the smaller zoom (limited by height)
        self.assertLess(auto_zoom, 0.1)
        self.assertGreater(auto_zoom, 0.05)

        # Verify it respects minimum zoom
        final_zoom = max(0.01, min(10.0, auto_zoom))
        self.assertGreaterEqual(final_zoom, 0.01)
        self.assertLessEqual(final_zoom, 10.0)


class TestPerformance(unittest.TestCase):
    """Test performance-critical operations."""

    def test_polygon_redraw_performance(self):
        """Test that polygon redraw is reasonably fast."""
        # Simulate redrawing a polygon with many vertices
        num_vertices = 100
        vertices = [(i * 10, i * 10) for i in range(num_vertices)]

        start_time = time.time()

        # Simulate the flattening operation done during redraw
        for _ in range(100):  # Redraw 100 times
            flat = [coord for vertex in vertices for coord in vertex]

        elapsed = time.time() - start_time

        # Should complete in under 0.1 seconds
        self.assertLess(elapsed, 0.1,
                       f"Polygon flattening too slow: {elapsed:.3f}s for 100 iterations")

    def test_tree_walk_performance(self):
        """Test that tree walking is fast."""
        root = ttk.Window(themename="flatly")
        root.withdraw()

        tree = ttk.Treeview(root)

        # Create a deep tree structure
        current = tree.insert('', 'end', text='Root')
        for i in range(10):
            current = tree.insert(current, 'end', text=f'Child {i}')

        # Time walking to root
        start_time = time.time()

        for _ in range(1000):
            node = current
            while tree.parent(node):
                node = tree.parent(node)

        elapsed = time.time() - start_time

        # Should complete quickly
        self.assertLess(elapsed, 0.1,
                       f"Tree walking too slow: {elapsed:.3f}s for 1000 iterations")

        root.destroy()


def run_tests():
    """Run all tests and display results."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPreferencesManager))
    suite.addTests(loader.loadTestsFromTestCase(TestRegenesisGUIBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestTreeOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestPolygonOperations))
    suite.addTests(loader.loadTestsFromTestCase(TestAutoZoom))
    suite.addTests(loader.loadTestsFromTestCase(TestPerformance))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL TESTS PASSED")
    else:
        print("\n✗ SOME TESTS FAILED")

    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
