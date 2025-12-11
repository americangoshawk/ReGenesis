# ReGenesis Testing Guide

## Running Tests

To run the test suite:

```bash
python3 regenesis_gui_test.py
```

## Test Coverage

The test suite validates the following functionality:

### 1. Preferences Manager (`TestPreferencesManager`)
- ✓ Default preferences are set correctly
- ✓ Location coordinates can be saved and retrieved
- ✓ Theme preferences work correctly
- ✓ Development mode flag works correctly
- ✓ Nested key access with dot notation works

### 2. GUI Basics (`TestRegenesisGUIBasics`)
- ✓ Zoom levels stay within valid limits (0.01 to 10.0)
- ✓ Coordinate conversion between canvas pixels and world units
- ✓ Vertex size scales correctly with zoom (max 10px, min 3px)
- ✓ Drag threshold detection (5 pixel threshold)

### 3. Tree Operations (`TestTreeOperations`)
- ✓ Tree structure is created correctly
- ✓ Finding root project from any node works
- ✓ Tree item values can be accessed correctly

### 4. Polygon Operations (`TestPolygonOperations`)
- ✓ Polygons can be stored and retrieved
- ✓ Minimum 3 vertices maintained
- ✓ Point-to-vertex distance calculation
- ✓ Coordinate flattening for tkinter polygons

### 5. Auto-Zoom (`TestAutoZoom`)
- ✓ Auto-zoom correctly calculates zoom to fit rectangles

### 6. Performance (`TestPerformance`)
- ✓ Polygon redraw operations complete quickly
- ✓ Tree walking is fast even with deep hierarchies

## Best Practices

### Before Making Changes
1. Run the test suite to ensure all tests pass
2. Note any tests that are relevant to your changes

### After Making Changes
1. Run the test suite again
2. If tests fail, investigate why:
   - Did you break existing functionality? (regression)
   - Do the tests need to be updated for new behavior?
3. Add new tests for new functionality

### Adding New Tests

When adding new features, add corresponding tests:

```python
def test_new_feature(self):
    """Test description."""
    # Arrange - set up test data
    input_value = 42

    # Act - perform the operation
    result = some_function(input_value)

    # Assert - verify the result
    self.assertEqual(result, expected_value)
```

## Common Test Patterns

### Testing Values Within Range
```python
self.assertGreaterEqual(value, min_value)
self.assertLessEqual(value, max_value)
```

### Testing Calculations
```python
self.assertEqual(calculated, expected,
                f"Failed with input {input_val}")
```

### Testing Performance
```python
start = time.time()
# ... operation ...
elapsed = time.time() - start
self.assertLess(elapsed, max_allowed_time)
```

## Continuous Testing

Run tests frequently during development:
- Before committing changes
- After fixing bugs
- When refactoring code
- Before creating releases

## Known Issues

None currently - all 19 tests passing ✓

## Future Test Ideas

Consider adding tests for:
- [ ] Pan and zoom interactions
- [ ] Polygon vertex editing operations
- [ ] File save/load operations
- [ ] Tree drag-and-drop reordering
- [ ] Canvas rendering edge cases
- [ ] Multiple project support
- [ ] Undo/redo functionality (if added)
