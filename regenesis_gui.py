import tkinter as tk
from regenesis import Regenesis


class RegenesisGUI:
    """GUI class for the Regenesis application."""

    def __init__(self):
        self.app = Regenesis()
        self.root = tk.Tk()
        self.root.title("Regenesis - Native Plant Designer")
        self.root.geometry("800x600")

        self._setup_ui()

    def _setup_ui(self):
        """Set up the user interface components."""
        # Title
        title_label = tk.Label(
            self.root,
            text="Regenesis",
            font=("Arial", 24, "bold")
        )
        title_label.pack(pady=10)

        # Subtitle
        subtitle_label = tk.Label(
            self.root,
            text="Native Plant Plot Designer",
            font=("Arial", 14)
        )
        subtitle_label.pack(pady=5)

        # Canvas for visualization
        self.canvas = tk.Canvas(self.root, width=600, height=400, bg='lightgreen')
        self.canvas.pack(pady=20)

        # Initial message on canvas
        self.canvas.create_text(
            300, 200,
            text="Your native plant plot will be visualized here",
            font=("Arial", 16),
            fill="darkgreen"
        )

        # Plant list frame
        list_frame = tk.Frame(self.root)
        list_frame.pack(pady=10)

        tk.Label(list_frame, text="Available Plants:", font=("Arial", 12, "bold")).pack()

        # Display plants
        for plant in self.app.get_all_plants():
            plant_text = f"{plant.name} - {plant.height}ft - {plant.color}"
            tk.Label(list_frame, text=plant_text, font=("Arial", 10)).pack()

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
