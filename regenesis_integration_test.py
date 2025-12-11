"""Integration tests for ReGenesis that test actual GUI interactions.

These tests create real GUI instances and verify they work correctly.
Unlike unit tests, these test the actual behavior, not just logic.

Run with: python3 regenesis_integration_test.py
Run with visible window: python3 regenesis_integration_test.py --visible
"""

import unittest
import sys
import tkinter as tk
import ttkbootstrap as ttk
from regenesis_gui import RegenesisGUI
from preferences_manager import PreferencesManager
import time


# Module-level variable to control window visibility
# This is set by run_integration_tests() before loading the test suite
SHOW_WINDOW = False


class TestRegenesisGUIIntegration(unittest.TestCase):
    """Integration tests that create actual GUI instances."""

    @classmethod
    def setUpClass(cls):
        """Set up test configuration."""
        # Use the module-level SHOW_WINDOW variable set by run_integration_tests()
        cls.show_window = SHOW_WINDOW
        print(f"[DEBUG] setUpClass: SHOW_WINDOW (module var) = {SHOW_WINDOW}")
        print(f"[DEBUG] setUpClass: show_window (class var) = {cls.show_window}")
        if cls.show_window:
            print("\n" + "="*70)
            print("RUNNING TESTS WITH VISIBLE WINDOW")
            print("You will see the ReGenesis window appear during tests")
            print("="*70 + "\n")

    def setUp(self):
        """Set up test configuration."""
        # Set preferences to development mode for testing
        self.prefs = PreferencesManager()
        self.prefs.set_development_mode(True)

        # GUI instance will be created in each test
        self.gui = None

    def tearDown(self):
        """Clean up GUI instance."""
        try:
            if self.gui:
                # Give a moment to see the window if visible
                if self.show_window:
                    time.sleep(0.5)

                # Process any remaining events in the queue
                try:
                    self.gui.root.update()
                except:
                    pass

                # Cancel all pending after() callbacks before destroying
                # This prevents "invalid command name" errors
                try:
                    for after_id in self.gui.root.tk.call('after', 'info'):
                        self.gui.root.after_cancel(after_id)
                except:
                    pass

                # Disable the bgerror handler to suppress error messages
                # during window destruction
                try:
                    self.gui.root.tk.call('rename', 'bgerror', '')
                except:
                    pass

                # Also disable event command to prevent ThemeChanged errors
                try:
                    self.gui.root.tk.call('rename', 'event', '_event')
                    self.gui.root.tk.eval('proc event {args} {}')
                except:
                    pass

                # Now safely destroy the window
                self.gui.root.destroy()
        except:
            pass

    def _create_gui(self):
        """Helper to create GUI instance for testing."""
        self.gui = RegenesisGUI()

        # The GUI __init__ shows the window at the end via _finish_startup
        # which is scheduled via after() with up to 2 seconds delay for splash screen
        # We need to wait for that callback to execute and window to be shown

        # Wait long enough for splash screen (2+ seconds) plus a bit extra
        time.sleep(2.2)

        # Process all pending events (including the splash finish callback)
        self.gui.root.update()

        # Now the window should be visible (deiconified) and geometry calculated
        # Force one more geometry update to ensure all widgets are sized
        self.gui.root.update_idletasks()
        self.gui.root.update()

        # Make sure window is visible/hidden based on mode
        if self.show_window:
            # Ensure window is visible and brought to front
            self.gui.root.deiconify()
            self.gui.root.lift()
            self.gui.root.focus_force()
        else:
            # Hide window for faster testing (after geometry is calculated)
            self.gui.root.withdraw()

        self.gui.root.update()
        return self.gui

    def test_01_gui_initializes(self):
        """Test that GUI initializes without errors."""
        try:
            gui = self._create_gui()

            self.assertIsNotNone(gui)
            self.assertIsNotNone(gui.tree)
            self.assertIsNotNone(gui.canvas)
            print("✓ GUI initialized successfully")
        except Exception as e:
            self.fail(f"GUI failed to initialize: {e}")

    def test_02_sample_tree_loads(self):
        """Test that sample tree loads in development mode."""
        gui = self._create_gui()

        # Check that tree has items
        children = gui.tree.get_children()
        self.assertGreater(len(children), 0, "Tree should have items in development mode")

        # Check that first item is the project
        first_item = children[0]
        values = gui.tree.item(first_item, 'values')
        self.assertEqual(values[0], 'project', "First item should be project")

        print(f"✓ Sample tree loaded with {len(children)} root item(s)")

    def test_03_tree_has_regions(self):
        """Test that sample tree has region children."""
        gui = self._create_gui()

        # Get project item
        children = gui.tree.get_children()
        project = children[0]

        # Get regions
        regions = gui.tree.get_children(project)
        self.assertGreater(len(regions), 0, "Project should have regions")

        # Check that regions have correct type
        for region in regions:
            values = gui.tree.item(region, 'values')
            self.assertEqual(values[0], 'region', f"Child should be a region")

        print(f"✓ Project has {len(regions)} region(s)")

    def test_04_tree_selection_works(self):
        """Test that selecting tree items works."""
        gui = self._create_gui()

        # Get items
        children = gui.tree.get_children()
        project = children[0]

        # Select project
        gui.tree.selection_set(project)
        gui.tree.focus(project)
        gui.root.update()

        # Trigger selection event manually
        gui._on_tree_select(None)
        gui.root.update()

        # Check that selected_item is set
        self.assertEqual(gui.selected_item, project, "Selected item should be project")

        print("✓ Tree selection works")

    def test_05_canvas_exists(self):
        """Test that canvas is created and has proper size."""
        gui = self._create_gui()

        # Canvas dimensions should already be calculated by _create_gui
        width = gui.canvas.winfo_width()
        height = gui.canvas.winfo_height()

        self.assertGreater(width, 100, "Canvas width should be > 100")
        self.assertGreater(height, 100, "Canvas height should be > 100")

        print(f"✓ Canvas created: {width}x{height}")

    def test_06_canvas_draws_when_project_selected(self):
        """Test that canvas has items when project is selected."""
        gui = self._create_gui()

        # Select project
        children = gui.tree.get_children()
        project = children[0]
        gui.tree.selection_set(project)
        gui._on_tree_select(None)
        gui.root.update()

        # Check that canvas has items
        canvas_items = gui.canvas.find_all()
        self.assertGreater(len(canvas_items), 0,
                          "Canvas should have items when project is selected")

        print(f"✓ Canvas has {len(canvas_items)} items drawn")

    def test_07_zoom_state_initialized(self):
        """Test that zoom and pan state is initialized."""
        gui = self._create_gui()

        self.assertIsNotNone(gui.canvas_zoom)
        self.assertIsNotNone(gui.canvas_pan_x)
        self.assertIsNotNone(gui.canvas_pan_y)

        # Check zoom is within valid range (may be auto-zoomed to fit project)
        self.assertGreaterEqual(gui.canvas_zoom, 0.01, "Zoom should be >= 0.01")
        self.assertLessEqual(gui.canvas_zoom, 10.0, "Zoom should be <= 10.0")
        self.assertEqual(gui.canvas_pan_x, 0, "Initial pan X should be 0")
        self.assertEqual(gui.canvas_pan_y, 0, "Initial pan Y should be 0")

        print(f"✓ Zoom/pan state initialized correctly (zoom={gui.canvas_zoom:.3f})")

    def test_08_drawing_mode_state(self):
        """Test that drawing mode state is initialized."""
        gui = self._create_gui()

        self.assertIsNotNone(gui.drawing_mode)
        self.assertIsNotNone(gui.polygon_vertices)
        self.assertIsNotNone(gui.region_polygons)

        # Initially not in drawing mode
        self.assertFalse(gui.drawing_mode, "Should not be in drawing mode initially")

        print("✓ Drawing mode state initialized")

    def test_09_region_selection_enters_drawing_mode(self):
        """Test that selecting a region enters drawing mode."""
        gui = self._create_gui()

        # Get project and a region
        children = gui.tree.get_children()
        project = children[0]
        regions = gui.tree.get_children(project)

        if len(regions) > 0:
            region = regions[0]

            # Select region
            gui.tree.selection_set(region)
            gui._on_tree_select(None)
            gui.root.update()

            # Should now be in drawing mode
            self.assertTrue(gui.drawing_mode,
                          "Should be in drawing mode when region is selected")

            # Should have default polygon vertices
            self.assertGreater(len(gui.polygon_vertices), 0,
                             "Should have polygon vertices")

            print(f"✓ Selecting region enters drawing mode ({len(gui.polygon_vertices)} vertices)")
        else:
            self.skipTest("No regions in sample tree")

    def test_10_polygon_persistence(self):
        """Test that polygons persist when switching between regions."""
        gui = self._create_gui()

        # Get regions
        children = gui.tree.get_children()
        project = children[0]
        regions = gui.tree.get_children(project)

        if len(regions) >= 2:
            region1 = regions[0]
            region2 = regions[1]

            # Select first region
            gui.tree.selection_set(region1)
            gui._on_tree_select(None)
            gui.root.update()

            # Remember vertices
            original_vertices = list(gui.polygon_vertices)

            # Select second region
            gui.tree.selection_set(region2)
            gui._on_tree_select(None)
            gui.root.update()

            # Select first region again
            gui.tree.selection_set(region1)
            gui._on_tree_select(None)
            gui.root.update()

            # Should have same vertices as before
            self.assertEqual(gui.polygon_vertices, original_vertices,
                           "Polygon should persist when returning to region")

            print("✓ Polygons persist across region switches")
        else:
            self.skipTest("Need at least 2 regions for this test")

    def test_11_console_logging_works(self):
        """Test that console logging doesn't crash."""
        gui = self._create_gui()

        # Try logging at different levels
        try:
            gui._log_info("Test info message")
            gui._log_warning("Test warning message")
            gui._log_error("Test error message")
            print("✓ Console logging works")
        except Exception as e:
            self.fail(f"Console logging failed: {e}")

    def test_12_node_focusing(self):
        """Test node focusing by selecting specific nodes with delays."""
        # Override show_window for this test to run without visible window
        original_show_window = self.show_window
        self.show_window = False

        try:
            gui = self._create_gui()

            # 1) Verify development mode is enabled
            self.assertTrue(gui.prefs.is_development_mode(),
                           "Development mode should be enabled for this test")
            print("✓ Development mode verified")

            # Helper function to find node by text
            def find_node_by_text(text, parent=''):
                """Find a tree node by its text."""
                children = gui.tree.get_children(parent)
                for child in children:
                    child_text = gui.tree.item(child, 'text')
                    if child_text == text:
                        return child
                    # Search recursively in children
                    found = find_node_by_text(text, child)
                    if found:
                        return found
                return None

            # Find the nodes we need
            patio = find_node_by_text('Patio')
            side_yard = find_node_by_text('Side Yard')
            smith_residence = find_node_by_text('Smith Residence')

            # Verify we found all nodes
            self.assertIsNotNone(patio, "Patio node should exist")
            self.assertIsNotNone(side_yard, "Side Yard node should exist")
            self.assertIsNotNone(smith_residence, "Smith Residence node should exist")

            # 2) Select 'Patio' node
            print("Selecting: Patio")
            gui.tree.selection_set(patio)
            gui.tree.focus(patio)
            gui.tree.see(patio)
            gui._on_tree_select(None)
            gui.root.update()
            self.assertEqual(gui.selected_item, patio, "Patio should be selected")

            # 3) Select 'Side Yard' node
            print("Selecting: Side Yard")
            gui.tree.selection_set(side_yard)
            gui.tree.focus(side_yard)
            gui.tree.see(side_yard)
            gui._on_tree_select(None)
            gui.root.update()
            self.assertEqual(gui.selected_item, side_yard, "Side Yard should be selected")

            # 4) Select 'Smith Residence'
            print("Selecting: Smith Residence")
            gui.tree.selection_set(smith_residence)
            gui.tree.focus(smith_residence)
            gui.tree.see(smith_residence)
            gui._on_tree_select(None)
            gui.root.update()
            self.assertEqual(gui.selected_item, smith_residence, "Smith Residence should be selected")

            # 5) Select 'Patio' node again
            print("Selecting: Patio (again)")
            gui.tree.selection_set(patio)
            gui.tree.focus(patio)
            gui.tree.see(patio)
            gui._on_tree_select(None)
            gui.root.update()
            self.assertEqual(gui.selected_item, patio, "Patio should be selected again")

            print("✓ Node focusing test completed successfully")
        finally:
            # Restore original show_window setting
            self.show_window = original_show_window


def run_integration_tests():
    """Run integration tests with detailed output."""
    global SHOW_WINDOW  # Need to modify the module-level variable

    print("\n" + "="*70)
    print("REGENESIS GUI INTEGRATION TESTS")
    print("="*70)

    # Set the module-level SHOW_WINDOW variable BEFORE loading tests
    # This is critical because setUpClass reads this variable when the test class is loaded
    SHOW_WINDOW = '--visible' in sys.argv
    print(f"[DEBUG] Set SHOW_WINDOW = {SHOW_WINDOW}")

    if SHOW_WINDOW:
        print("\nRunning with VISIBLE windows (slower)")
        print("You will see test windows appear and disappear")
    else:
        print("\nRunning with HIDDEN windows (faster)")
        print("Use --visible flag to see windows during testing")

    print("="*70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()

    # Check if a specific test was requested
    # Look for args that look like test names (contain a dot and aren't --flags)
    test_name_arg = None
    for arg in sys.argv[1:]:
        if '.' in arg and not arg.startswith('-'):
            test_name_arg = arg
            break

    print(f"[DEBUG] Before loading suite: sys.argv = {sys.argv}")
    print(f"[DEBUG] test_name_arg = {test_name_arg}")

    if test_name_arg:
        # Load specific test (e.g., TestRegenesisGUIIntegration.test_12_node_focusing)
        # Need to prepend __main__ since we're running as a script
        test_name = test_name_arg
        if not test_name.startswith('__main__.'):
            test_name = '__main__.' + test_name
        print(f"[DEBUG] Loading test: {test_name}")
        suite = loader.loadTestsFromName(test_name)
        print(f"[DEBUG] After loading suite")
    else:
        # Load all tests from the test case
        print(f"[DEBUG] Loading all tests from TestRegenesisGUIIntegration")
        suite = loader.loadTestsFromTestCase(TestRegenesisGUIIntegration)
        print(f"[DEBUG] After loading suite")

    print(f"[DEBUG] Before removing --visible: sys.argv = {sys.argv}")
    # NOW remove --visible from argv so unittest doesn't complain about unknown args
    sys.argv = [arg for arg in sys.argv if arg != '--visible']
    print(f"[DEBUG] After removing --visible: sys.argv = {sys.argv}")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n✓ ALL INTEGRATION TESTS PASSED")
        print("\nThe GUI creates successfully and core interactions work!")
    else:
        print("\n✗ SOME INTEGRATION TESTS FAILED")
        print("\nCheck the failures above for details.")

    print("="*70)

    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)
