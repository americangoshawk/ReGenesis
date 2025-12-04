import random

class Plant:
    """Represents a single native plant with height and color attributes."""

    def __init__(self, name, height, color):
        self.name = name
        self.height = height  # in feet
        self.color = color

    def __repr__(self):
        return f"Plant('{self.name}', {self.height}ft, '{self.color}')"


class PlantContainer:
    """Container class for managing a collection of native plants."""

    def __init__(self):
        self.plants = []

    def add_plant(self, name, height, color):
        """Add a plant to the container."""
        plant = Plant(name, height, color)
        self.plants.append(plant)

    def get_all_plants(self):
        """Return all plants in the container."""
        return self.plants

    def __len__(self):
        return len(self.plants)

    def __repr__(self):
        return f"PlantContainer with {len(self.plants)} plants"


# Create the container and populate with 9 native plants
def create_plant_database():
    """Create and populate a database of 9 native plants with random attributes."""
    container = PlantContainer()

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
        container.add_plant(name, height, color)

    return container


# Create the database
if __name__ == "__main__":
    db = create_plant_database()

    print(f"{db}\n")
    print("Plant Database:")
    print("-" * 50)
    for plant in db.get_all_plants():
        print(f"  {plant.name:25} | {plant.height}ft | {plant.color}")
