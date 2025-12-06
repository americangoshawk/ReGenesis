import unittest
from regenesis import Regenesis
from plant import Plant


class TestRegenesis(unittest.TestCase):
    """Unit tests for the Regenesis class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.app = Regenesis()

    def test_initialization(self):
        """Test that Regenesis initializes with a plant database."""
        self.assertIsNotNone(self.app.plant_container)
        self.assertEqual(len(self.app.get_all_plants()), 9)
        self.assertEqual(len(self.app.selected_plants), 0)
        self.assertIsNone(self.app.plot_width)
        self.assertIsNone(self.app.plot_height)

    def test_set_plot_dimensions(self):
        """Test setting plot dimensions."""
        self.app.set_plot_dimensions(10, 15)
        self.assertEqual(self.app.plot_width, 10)
        self.assertEqual(self.app.plot_height, 15)

    def test_get_all_plants(self):
        """Test retrieving all plants."""
        plants = self.app.get_all_plants()
        self.assertEqual(len(plants), 9)
        self.assertIsInstance(plants[0], Plant)

    def test_filter_plants_by_height(self):
        """Test filtering plants by height range."""
        # Filter for plants 2ft or taller
        tall_plants = self.app.filter_plants_by_height(min_height=2)
        for plant in tall_plants:
            self.assertGreaterEqual(plant.height, 2)

        # Filter for plants 3ft or shorter
        short_plants = self.app.filter_plants_by_height(max_height=3)
        for plant in short_plants:
            self.assertLessEqual(plant.height, 3)

        # Filter for plants between 2-3ft
        medium_plants = self.app.filter_plants_by_height(min_height=2, max_height=3)
        for plant in medium_plants:
            self.assertGreaterEqual(plant.height, 2)
            self.assertLessEqual(plant.height, 3)

    def test_filter_plants_by_color(self):
        """Test filtering plants by color."""
        colors = ["white", "yellow", "purple", "pink"]

        for color in colors:
            filtered = self.app.filter_plants_by_color(color)
            for plant in filtered:
                self.assertEqual(plant.color, color)

    def test_add_plant_to_selection(self):
        """Test adding plants to selection."""
        plants = self.app.get_all_plants()
        self.assertEqual(len(self.app.selected_plants), 0)

        self.app.add_plant_to_selection(plants[0])
        self.assertEqual(len(self.app.selected_plants), 1)

        self.app.add_plant_to_selection(plants[1])
        self.assertEqual(len(self.app.selected_plants), 2)

    def test_clear_selection(self):
        """Test clearing plant selection."""
        plants = self.app.get_all_plants()
        self.app.add_plant_to_selection(plants[0])
        self.app.add_plant_to_selection(plants[1])
        self.assertEqual(len(self.app.selected_plants), 2)

        self.app.clear_selection()
        self.assertEqual(len(self.app.selected_plants), 0)

    def test_get_color_distribution(self):
        """Test getting color distribution of selected plants."""
        plants = self.app.get_all_plants()
        # Select a few plants
        self.app.add_plant_to_selection(plants[0])
        self.app.add_plant_to_selection(plants[1])
        self.app.add_plant_to_selection(plants[2])

        distribution = self.app.get_color_distribution()
        self.assertIsInstance(distribution, dict)

        # Check that the sum of counts equals number of selected plants
        total = sum(distribution.values())
        self.assertEqual(total, 3)


if __name__ == '__main__':
    unittest.main()
