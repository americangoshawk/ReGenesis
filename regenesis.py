import random
import json
from plant_container import PlantContainer


class Regenesis:
    """Core application class for managing native plant selection and plot design."""

    def __init__(self):
        self.plant_container = PlantContainer()
        self.plot_width = None
        self.plot_height = None
        self.selected_plants = []
        self._initialize_plant_database()

    def _initialize_plant_database(self):
        """Initialize the plant database with sample native plants."""
        # Common native plant names
        plant_names = [
            "Purple Coneflower",
            "Black-Eyed Susan",
            "Wild Bergamot",
            "Butterfly Weed",
            "New England Aster",
            "Joe Pye Weed",
            "Wild Columbine",
            "Goldenrod",
            "Blazing Star"
        ]

        # Possible attributes
        heights = [1, 2, 3, 4]
        colors = ["white", "yellow", "purple", "pink"]

        # Add 9 plants with random attributes
        for name in plant_names:
            height = random.choice(heights)
            color = random.choice(colors)
            self.plant_container.add_plant(name, height, color)

    def set_plot_dimensions(self, width, height):
        """Set the dimensions of the plot in feet."""
        self.plot_width = width
        self.plot_height = height

    def get_all_plants(self):
        """Return all plants in the database."""
        return self.plant_container.get_all_plants()

    def filter_plants_by_height(self, min_height=None, max_height=None):
        """Filter plants by height range."""
        plants = self.get_all_plants()
        filtered = []
        for plant in plants:
            if min_height and plant.height < min_height:
                continue
            if max_height and plant.height > max_height:
                continue
            filtered.append(plant)
        return filtered

    def filter_plants_by_color(self, color):
        """Filter plants by color."""
        return [p for p in self.get_all_plants() if p.color == color]

    def add_plant_to_selection(self, plant):
        """Add a plant to the current selection."""
        self.selected_plants.append(plant)

    def clear_selection(self):
        """Clear the current plant selection."""
        self.selected_plants = []

    def get_color_distribution(self):
        """Get the distribution of colors in selected plants."""
        color_counts = {}
        for plant in self.selected_plants:
            color_counts[plant.color] = color_counts.get(plant.color, 0) + 1
        return color_counts

    def save_to_file(self, filepath):
        """Save the current project to a JSON file."""
        project_data = {
            "plot_dimensions": {
                "width": self.plot_width,
                "height": self.plot_height
            },
            "selected_plants": [
                {
                    "name": plant.name,
                    "height": plant.height,
                    "color": plant.color
                }
                for plant in self.selected_plants
            ]
        }

        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)

    def load_from_file(self, filepath):
        """Load a project from a JSON file."""
        with open(filepath, 'r') as f:
            project_data = json.load(f)

        # Restore plot dimensions
        dims = project_data.get("plot_dimensions", {})
        self.plot_width = dims.get("width")
        self.plot_height = dims.get("height")

        # Restore selected plants
        self.selected_plants = []
        for plant_data in project_data.get("selected_plants", []):
            # Find matching plant in database
            for plant in self.get_all_plants():
                if (plant.name == plant_data["name"] and
                    plant.height == plant_data["height"] and
                    plant.color == plant_data["color"]):
                    self.selected_plants.append(plant)
                    break

    def new_project(self):
        """Start a new project by clearing current selections."""
        self.plot_width = None
        self.plot_height = None
        self.selected_plants = []
