class Plant:
    """Represents a single native plant with height and color attributes."""

    def __init__(self, name, height, color):
        self.name = name
        self.height = height  # in feet
        self.color = color

    def __repr__(self):
        return f"Plant('{self.name}', {self.height}ft, '{self.color}')"

    def __eq__(self, other):
        if not isinstance(other, Plant):
            return False
        return (self.name == other.name and
                self.height == other.height and
                self.color == other.color)
