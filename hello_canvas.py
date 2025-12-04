import tkinter as tk

# Create the main window
root = tk.Tk()
root.title("Canvas Demo")

# Create a canvas widget
canvas = tk.Canvas(root, width=400, height=300, bg='white')
canvas.pack(padx=20, pady=20)

# Draw "What's up?" text on the canvas
canvas.create_text(200, 150, text="What's up?", font=("Arial", 32), fill="black")

# Run the application
root.mainloop()
