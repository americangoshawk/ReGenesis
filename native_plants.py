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
    """Create and populate a database of 9 native plants with specific colors and random heights."""
    container = PlantContainer()

    # Native plants with their characteristic colors
    plants_data = [
        ("Purple Coneflower", "purple"),
        ("Black-Eyed Susan", "yellow"),
        ("Wild Bergamot", "pink"),
        ("Butterfly Weed", "orange"),
        ("New England Aster", "purple"),
        ("Joe Pye Weed", "purple"),
        ("Wild Columbine", "red"),
        ("Goldenrod", "yellow"),
        ("Blazing Star", "purple")
    ]

    # Possible heights
    heights = [1, 2, 3, 4]

    # Add plants with random heights but specific colors
    for name, color in plants_data:
        height = random.choice(heights)
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
