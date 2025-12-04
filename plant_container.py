from plant import Plant


class PlantContainer:
    """Container class for managing a collection of native plants."""

    def __init__(self):
        self.plants = []

    def add_plant(self, name, height, color):
        """Add a plant to the container."""
        plant = Plant(name, height, color)
        self.plants.append(plant)
        return plant

    def get_all_plants(self):
        """Return all plants in the container."""
        return self.plants

    def __len__(self):
        return len(self.plants)

    def __repr__(self):
        return f"PlantContainer with {len(self.plants)} plants"
