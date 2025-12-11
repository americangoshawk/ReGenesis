import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox
import tkinter as tk
import os
from regenesis import Regenesis
from preferences_manager import PreferencesManager


class RegenesisGUI:
    """GUI class for the Regenesis application."""

    def __init__(self):
        import time

        # Initialize preferences manager
        self.prefs = PreferencesManager()

        # Create main window with ttkbootstrap theme
        # Load theme from preferences
        theme = self.prefs.get_theme()
        self.root = ttk.Window(themename=theme)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(__file__), 'oak_leaf_icon_512.png')
        if os.path.exists(icon_path):
            try:
                icon_image = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon_image)
            except Exception:
                pass  # If icon fails to load, continue without it

        # Move it completely off-screen before any update
        self.root.geometry('1x1+-10000+-10000')
        self.root.withdraw()  # Hide it immediately

        # Set application name for macOS menu bar
        self.root.createcommand('tk::mac::ShowPreferences', self._show_preferences)

        # Create splash screen as a Toplevel
        splash = self._create_splash_screen()
        splash_start_time = time.time()

        # Force splash to display and process events
        splash.update()

        # Initialize app
        self.app = Regenesis()
        splash.update()  # Keep splash responsive

        self.root.title("Regenesis - Native Plant Designer")

        # Center the main window on the screen (same monitor as splash)
        window_width = 1000
        window_height = 700
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.current_file = None  # Track the currently open file
        self.selected_item = None  # Track selected tree item
        self._updating_properties = False  # Flag to prevent update loops
        self._drag_item = None  # Track item being dragged
        self._drop_target = None  # Track current drop target
        self._drop_position = None  # Track drop position: 'above', 'below', or 'inside'

        # Canvas pan/zoom state
        self.canvas_pan_x = 0  # Pan offset in pixels
        self.canvas_pan_y = 0
        self.canvas_zoom = 1.0  # Zoom level (1.0 = 100%)
        self._pan_start_x = 0  # Track panning start position
        self._pan_start_y = 0
        self._is_panning = False
        self._current_project_item = None  # Track which project is displayed
        self._has_auto_zoomed = False  # Track if we've auto-zoomed for current project

        # Drawing mode state
        self.drawing_mode = False  # True when in drawing mode
        self.current_polygon = None  # Canvas polygon ID
        self.polygon_vertices = []  # List of (x, y) tuples
        self.vertex_handles = []  # List of canvas circle IDs for vertices
        self.selected_vertex = None  # Index of selected vertex
        self._dragging_vertex = False
        self.region_polygons = {}  # Dict mapping tree item IDs to polygon vertices

        # Track drag state for tree drag-and-drop
        self._drag_start_x = 0
        self._drag_start_y = 0
        self._has_moved = False

        # Setup UI
        splash.update()
        self._setup_ui()

        # Ensure splash shows for at least 2 seconds
        min_splash_time = 2.0  # seconds
        elapsed = time.time() - splash_start_time
        if elapsed < min_splash_time:
            remaining = min_splash_time - elapsed
            splash.after(int(remaining * 1000), lambda: self._finish_startup(splash))
        else:
            self._finish_startup(splash)

    def _finish_startup(self, splash):
        """Complete the startup sequence by closing splash and showing main window."""
        # Close splash and show main window
        splash.destroy()
        self.root.deiconify()

        # Bring window to front on macOS
        self.root.lift()
        self.root.attributes('-topmost', True)
        self.root.after_idle(self.root.attributes, '-topmost', False)

    def _create_splash_screen(self):
        """Create and display a splash screen during startup."""
        splash = tk.Toplevel(self.root)
        splash.title("ReGenesis")

        # Set size and center the splash screen
        width = 400
        height = 300

        # Get screen dimensions from the root window (which knows about the main monitor)
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")
        splash.update_idletasks()

        # Remove window decorations
        splash.overrideredirect(True)

        # Keep splash on top of all windows
        splash.attributes('-topmost', True)

        # Create a frame with border
        frame = tk.Frame(splash, relief=tk.RAISED, borderwidth=3, bg='#e8f5e9')
        frame.pack(fill=tk.BOTH, expand=True)

        # Add title
        tk.Label(
            frame,
            text="ReGenesis",
            font=("Arial", 32, "bold"),
            bg='#e8f5e9',
            fg='#2e7d32'
        ).pack(pady=(40, 10))

        # Add subtitle
        tk.Label(
            frame,
            text="Native Plant Designer",
            font=("Arial", 14),
            bg='#e8f5e9',
            fg='#558b2f'
        ).pack(pady=5)

        # Add a simple plant icon using text
        tk.Label(
            frame,
            text="🦋 🌸",
            font=("Arial", 48),
            bg='#e8f5e9'
        ).pack(pady=20)

        # Add loading message
        tk.Label(
            frame,
            text="Loading...",
            font=("Arial", 12, "italic"),
            bg='#e8f5e9',
            fg='#666666'
        ).pack(pady=10)

        splash.update()
        return splash

    def _setup_ui(self):
        """Set up the user interface components."""
        # Create menu bar
        self._create_menu()

        # Main container with resizable paned window
        main_container = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, sashrelief=tk.RAISED, bg='#d0d0d0')
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # LEFT PANEL - contains tree and definitions (initial width 300)
        left_panel = tk.Frame(main_container, width=300, relief=tk.SUNKEN, borderwidth=1)
        main_container.add(left_panel, minsize=200)

        # Create a vertical PanedWindow to split tree and properties
        left_paned = tk.PanedWindow(left_panel, orient=tk.VERTICAL, sashwidth=5, sashrelief=tk.RAISED, bg='#d0d0d0')
        left_paned.pack(fill=tk.BOTH, expand=True)

        # Top section - tree
        tree_section = tk.Frame(left_paned, relief=tk.SUNKEN, borderwidth=1)
        left_paned.add(tree_section, minsize=200)

        # Project tree section
        tree_label = tk.Label(tree_section, text="Project Structure", font=("Arial", 12, "bold"))
        tree_label.pack(pady=(5, 0))

        # Scrollable tree
        tree_frame = tk.Frame(tree_section)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, height=15, bootstyle="primary")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)

        # Configure tree item styles - make project largest, regions bold
        self.tree.tag_configure('project', font=("Helvetica", 14, "bold"))
        self.tree.tag_configure('region', font=("Helvetica", 11, "bold"))

        # Bind tree selection event
        self.tree.bind('<<TreeviewSelect>>', self._on_tree_select)

        # Bind right-click for context menu
        self.tree.bind('<Button-2>', self._show_context_menu)  # macOS right-click
        self.tree.bind('<Control-Button-1>', self._show_context_menu)  # macOS ctrl-click

        # Bind double-click for in-tree renaming (alternative to Properties panel)
        self.tree.bind('<Double-Button-1>', self._start_tree_rename)

        # Bind drag-and-drop events
        self.tree.bind('<ButtonPress-1>', self._on_drag_start)
        self.tree.bind('<B1-Motion>', self._on_drag_motion)
        self.tree.bind('<ButtonRelease-1>', self._on_drag_release)

        # PROPERTIES PANEL (bottom section of left paned window)
        properties_section = tk.Frame(left_paned, relief=tk.SUNKEN, borderwidth=1)
        left_paned.add(properties_section, minsize=150)

        # Container for switching between project and region properties
        self.properties_container = tk.Frame(properties_section)
        self.properties_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # PROJECT PROPERTIES FORM
        self.project_props_frame = ttk.Labelframe(self.properties_container, text="Project Properties", bootstyle="primary", padding=10)

        # Name
        ttk.Label(self.project_props_frame, text="Name:", font=("Helvetica", 10)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.project_name_var = tk.StringVar()
        self.project_name_entry = ttk.Entry(self.project_props_frame, textvariable=self.project_name_var, width=20)
        self.project_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.project_name_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.project_name_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        # Latitude
        ttk.Label(self.project_props_frame, text="Latitude:", font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.project_latitude_var = tk.StringVar()
        self.project_latitude_entry = ttk.Entry(self.project_props_frame, textvariable=self.project_latitude_var, width=20)
        self.project_latitude_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        self.project_latitude_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.project_latitude_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        # Longitude
        ttk.Label(self.project_props_frame, text="Longitude:", font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.project_longitude_var = tk.StringVar()
        self.project_longitude_entry = ttk.Entry(self.project_props_frame, textvariable=self.project_longitude_var, width=20)
        self.project_longitude_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)
        self.project_longitude_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.project_longitude_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        # Width and Length
        dims_frame = ttk.Frame(self.project_props_frame)
        dims_frame.grid(row=3, column=0, columnspan=2, sticky=tk.EW, padx=5, pady=5)

        ttk.Label(dims_frame, text="Width:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.project_width_var = tk.StringVar()
        self.project_width_entry = ttk.Entry(dims_frame, textvariable=self.project_width_var, width=8)
        self.project_width_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.project_width_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.project_width_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        ttk.Label(dims_frame, text="Length:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(0, 5))
        self.project_length_var = tk.StringVar()
        self.project_length_entry = ttk.Entry(dims_frame, textvariable=self.project_length_var, width=8)
        self.project_length_entry.pack(side=tk.LEFT)
        self.project_length_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.project_length_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        # Units (radio buttons)
        units_frame = ttk.Frame(self.project_props_frame)
        units_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(units_frame, text="Units:", font=("Helvetica", 10)).pack(side=tk.LEFT, padx=(0, 10))
        self.project_units_var = tk.StringVar(value="feet")
        ttk.Radiobutton(units_frame, text="Feet", variable=self.project_units_var, value="feet",
                       command=self._apply_property_change, bootstyle="primary").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(units_frame, text="Meters", variable=self.project_units_var, value="meters",
                       command=self._apply_property_change, bootstyle="primary").pack(side=tk.LEFT, padx=5)

        self.project_props_frame.columnconfigure(1, weight=1)

        # REGION PROPERTIES FORM
        self.region_props_frame = ttk.Labelframe(self.properties_container, text="Region Properties", bootstyle="success", padding=10)

        # Name
        ttk.Label(self.region_props_frame, text="Name:", font=("Helvetica", 10)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.region_name_var = tk.StringVar()
        self.region_name_entry = ttk.Entry(self.region_props_frame, textvariable=self.region_name_var, width=20)
        self.region_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.region_name_entry.bind('<Return>', lambda _: self._apply_property_change())
        self.region_name_entry.bind('<FocusOut>', lambda _: self._apply_property_change())

        # Region Type
        ttk.Label(self.region_props_frame, text="Region Type:", font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.region_type_var = tk.StringVar(value="meadow")
        self.region_type_menu = ttk.OptionMenu(
            self.region_props_frame,
            self.region_type_var,
            "meadow",
            "meadow", "layered", "pond", "stream", "building", "drive", "patio/deck", "path", "wire fence", "solid fence",
            command=lambda _: self._apply_property_change(),
            bootstyle="success"
        )
        self.region_type_menu.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)

        # Soil Moisture
        ttk.Label(self.region_props_frame, text="Soil Moisture:", font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.soil_moisture_var = tk.StringVar(value="medium")
        self.soil_moisture_menu = ttk.OptionMenu(
            self.region_props_frame,
            self.soil_moisture_var,
            "medium",
            "dry", "med-dry", "medium", "medium-wet", "wet",
            command=lambda _: self._apply_property_change(),
            bootstyle="info"
        )
        self.soil_moisture_menu.grid(row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        # Soil Type
        ttk.Label(self.region_props_frame, text="Soil Type:", font=("Helvetica", 10)).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.soil_type_var = tk.StringVar(value="loam")
        self.soil_type_menu = ttk.OptionMenu(
            self.region_props_frame,
            self.soil_type_var,
            "loam",
            "sand", "clay", "loam",
            command=lambda _: self._apply_property_change(),
            bootstyle="info"
        )
        self.soil_type_menu.grid(row=3, column=1, padx=5, pady=5, sticky=tk.EW)

        # Sun
        ttk.Label(self.region_props_frame, text="Sun:", font=("Helvetica", 10)).grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.sun_var = tk.StringVar(value="full-sun")
        self.sun_menu = ttk.OptionMenu(
            self.region_props_frame,
            self.sun_var,
            "full-sun",
            "shade", "part-sun", "full-sun",
            command=lambda _: self._apply_property_change(),
            bootstyle="warning"
        )
        self.sun_menu.grid(row=4, column=1, padx=5, pady=5, sticky=tk.EW)

        self.region_props_frame.columnconfigure(1, weight=1)

        # Initially hide both (will show based on selection)
        self.project_props_frame.pack_forget()
        self.region_props_frame.pack_forget()

        # RIGHT PANEL - Workspace
        workspace_frame = tk.Frame(main_container, relief=tk.SUNKEN, borderwidth=1, bg='white')
        main_container.add(workspace_frame, minsize=400)

        # Toolbar section (top of workspace)
        toolbar_frame = tk.Frame(workspace_frame, bg='#e0e0e0', height=50)
        toolbar_frame.pack(side=tk.TOP, fill=tk.X)
        toolbar_frame.pack_propagate(False)

        # Workspace label
        tk.Label(toolbar_frame, text="Workspace", font=("Arial", 14, "bold"), bg='#e0e0e0').pack(side=tk.LEFT, padx=10)

        # Drawing mode toggle button (now starts drawing immediately when viewing a region)
        # Removed - drawing starts automatically, exits when switching nodes

        # Clear polygon button
        self.clear_polygon_button = ttk.Button(
            toolbar_frame,
            text="Clear Shape",
            command=self._clear_polygon,
            bootstyle="warning",
            width=12,
            state=tk.DISABLED
        )
        self.clear_polygon_button.pack(side=tk.LEFT, padx=5)
        self._clear_button_visible = True  # Track visibility to avoid unnecessary pack/unpack

        # Canvas/Workspace section (takes most of the space)
        canvas_section = tk.Frame(workspace_frame, bg='white')
        canvas_section.pack(fill=tk.BOTH, expand=True)

        # Canvas for visualization with rulers
        # Create a container for canvas and rulers
        canvas_container = tk.Frame(canvas_section, bg='white')
        canvas_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Top ruler (horizontal)
        self.ruler_top = tk.Canvas(canvas_container, bg='#ffffff', height=25, highlightthickness=0)
        self.ruler_top.pack(side=tk.TOP, fill=tk.X)

        # Left ruler (vertical)
        self.ruler_left = tk.Canvas(canvas_container, bg='#ffffff', width=40, highlightthickness=0)
        self.ruler_left.pack(side=tk.LEFT, fill=tk.Y)

        # Main canvas
        self.canvas = tk.Canvas(canvas_container, bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Bind canvas resize to update rulers and reposition items
        self.canvas.bind('<Configure>', lambda _e: self._on_canvas_resize())

        # Bind canvas pan/zoom events
        self.canvas.bind('<Button-2>', self._start_pan)  # Middle click on macOS (Button-2)
        self.canvas.bind('<B2-Motion>', self._pan_canvas)
        self.canvas.bind('<ButtonRelease-2>', self._end_pan)
        # Also support space+drag for panning
        self.root.bind('<space>', self._space_pressed)
        self.root.bind('<KeyRelease-space>', self._space_released)
        self._space_is_pressed = False

        # Bind mouse wheel for zooming
        self.canvas.bind('<MouseWheel>', self._zoom_canvas)  # macOS and Windows
        self.canvas.bind('<Button-4>', self._zoom_canvas)  # Linux scroll up
        self.canvas.bind('<Button-5>', self._zoom_canvas)  # Linux scroll down

        # Bind canvas drawing/editing events
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_canvas_release)
        self.canvas.bind('<Control-Button-1>', self._on_canvas_right_click)  # macOS ctrl-click for delete

        # Initial message
        self.canvas_text = self.canvas.create_text(
            400, 300,
            text="Select an item from the project tree",
            font=("Arial", 16),
            fill="#999999"
        )

        # Bottom section - Console (fixed height, not in PanedWindow)
        console_section = tk.Frame(workspace_frame, relief=tk.SUNKEN, borderwidth=1, height=144)
        console_section.pack(side=tk.BOTTOM, fill=tk.X)
        console_section.pack_propagate(False)  # Prevent it from shrinking

        # Console label
        console_label_frame = tk.Frame(console_section, bg='#2b2b2b')
        console_label_frame.pack(fill=tk.X)
        tk.Label(console_label_frame, text="Console", font=("Arial", 9, "bold"), bg='#2b2b2b', fg='white').pack(pady=2, padx=5, anchor=tk.W)

        # Console text widget with scrollbar and buttons
        console_container = tk.Frame(console_section)
        console_container.pack(fill=tk.BOTH, expand=True)

        # Buttons on the left side
        console_buttons_frame = tk.Frame(console_container, bg='#1e1e1e', width=35)
        console_buttons_frame.pack(side=tk.LEFT, fill=tk.Y)
        console_buttons_frame.pack_propagate(False)

        # Copy button (top) - using Label for better color control
        self.copy_button = tk.Label(
            console_buttons_frame,
            text="C",
            bg='#4EC9B0',
            fg='#000000',
            relief=tk.RAISED,
            borderwidth=2,
            font=("Helvetica", 12, "bold"),
            cursor='hand2',
            padx=8,
            pady=4
        )
        self.copy_button.pack(side=tk.TOP, pady=(4, 2), padx=2, fill=tk.BOTH, expand=True)
        self.copy_button.bind('<Button-1>', lambda _e: self._copy_console_text())
        self._create_tooltip(self.copy_button, "Copy console text to clipboard")

        # Clear button (below) - using Label for better color control
        self.clear_button = tk.Label(
            console_buttons_frame,
            text="X",
            bg='#F48771',
            fg='#000000',
            relief=tk.RAISED,
            borderwidth=2,
            font=("Helvetica", 12, "bold"),
            cursor='hand2',
            padx=8,
            pady=4
        )
        self.clear_button.pack(side=tk.TOP, pady=(2, 4), padx=2, fill=tk.BOTH, expand=True)
        self.clear_button.bind('<Button-1>', lambda _e: self._clear_console())
        self._create_tooltip(self.clear_button, "Clear console")

        console_scrollbar = tk.Scrollbar(console_container)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.console = tk.Text(
            console_container,
            bg='#1e1e1e',
            fg='#cccccc',
            font=("Courier", 9),
            wrap=tk.WORD,
            yscrollcommand=console_scrollbar.set,
            state=tk.DISABLED,
            height=3
        )
        self.console.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scrollbar.config(command=self.console.yview)

        # Configure console text tags for different message types
        self.console.tag_config('info', foreground='#4EC9B0')
        self.console.tag_config('warning', foreground='#DCDCAA')
        self.console.tag_config('error', foreground='#F48771')

        # Add initial welcome message
        self._log_info("Console initialized. Ready.")

        # Populate with sample data (only in development mode)
        if self.prefs.is_development_mode():
            self._populate_sample_tree()
        else:
            # Show helpful message when tree is empty
            self._log_info("No projects loaded. Use File → New to create a project.")
            self._show_empty_tree_message()

    def _create_menu(self):
        """Create the menu bar with File menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)

        file_menu.add_command(label="New", command=self._new_project, accelerator="Cmd+N")
        file_menu.add_command(label="New Window", command=self._new_window, accelerator="Shift+Cmd+N")
        file_menu.add_command(label="Open...", command=self._open_project, accelerator="Cmd+O")
        file_menu.add_separator()
        file_menu.add_command(label="Save", command=self._save_project, accelerator="Cmd+S")
        file_menu.add_command(label="Save As...", command=self._save_as_project, accelerator="Shift+Cmd+S")
        file_menu.add_separator()
        file_menu.add_command(label="Rename...", command=self._rename_project)
        file_menu.add_separator()
        file_menu.add_command(label="Close Window", command=self.root.destroy)
        file_menu.add_command(label="Exit", command=self._exit_app)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)

        # On macOS, we need to use createcommand to properly register shortcuts
        # This makes them appear active (not grayed out) in the menu
        self.root.createcommand('zoom_in', self._zoom_in)
        self.root.createcommand('zoom_out', self._zoom_out)
        self.root.createcommand('reset_zoom', self._reset_view)
        self.root.createcommand('fit_to_design', self._fit_to_design_extents)
        self.root.createcommand('fit_to_region', self._fit_to_region)

        view_menu.add_command(label="Zoom In", command=self._zoom_in, accelerator="Cmd++")
        view_menu.add_command(label="Zoom Out", command=self._zoom_out, accelerator="Cmd+-")
        view_menu.add_command(label="Reset Zoom", command=self._reset_view, accelerator="Cmd+0")
        view_menu.add_separator()
        view_menu.add_command(label="Fit to Design Extents", command=self._fit_to_design_extents, accelerator="Cmd+1")
        view_menu.add_command(label="Fit to Region", command=self._fit_to_region, accelerator="Cmd+2")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", command=self._toggle_grid)

        # Bind keyboard shortcuts for View menu
        self.root.bind_all('<Command-plus>', lambda _e: self._zoom_in())
        self.root.bind_all('<Command-equal>', lambda _e: self._zoom_in())  # Cmd+= (same key as +)
        self.root.bind_all('<Command-minus>', lambda _e: self._zoom_out())
        self.root.bind_all('<Command-0>', lambda _e: self._reset_view())
        self.root.bind_all('<Command-1>', lambda _e: self._fit_to_design_extents())
        self.root.bind_all('<Command-2>', lambda _e: self._fit_to_region())

        # Also bind File menu shortcuts
        self.root.bind_all('<Command-n>', lambda _e: self._new_project())
        self.root.bind_all('<Command-Shift-N>', lambda _e: self._new_window())
        self.root.bind_all('<Command-o>', lambda _e: self._open_project())
        self.root.bind_all('<Command-s>', lambda _e: self._save_project())
        self.root.bind_all('<Command-Shift-S>', lambda _e: self._save_as_project())

    def _new_project(self):
        """Create a new project."""
        if messagebox.askyesno("New Project", "Start a new project? Any unsaved changes will be lost."):
            self.app.new_project()
            self.current_file = None
            self._update_title()
            messagebox.showinfo("New Project", "New project created.")

    def _new_window(self):
        """Open a new window with a new project."""
        import subprocess
        import sys
        import os
        # Launch a new instance of the application
        script_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(script_dir, 'main.py')
        subprocess.Popen([sys.executable, main_script])

    def _exit_app(self):
        """Exit the entire application (close all windows)."""
        import sys
        sys.exit(0)

    def _open_project(self):
        """Open an existing project file."""
        filepath = filedialog.askopenfilename(
            title="Open Project",
            defaultextension=".json",
            filetypes=[("ReGenesis Projects", "*.json"), ("All Files", "*.*")]
        )

        if filepath:
            try:
                self._load_tree_from_file(filepath)
                self.current_file = filepath
                self._update_title()
                self._log_info(f"Project opened: {os.path.basename(filepath)}")
                messagebox.showinfo("Project Opened", f"Loaded: {os.path.basename(filepath)}")
            except Exception as e:
                self._log_error(f"Failed to open project: {e}")
                messagebox.showerror("Error", f"Failed to open project:\n{str(e)}")

    def _save_project(self):
        """Save the current project."""
        if self.current_file:
            try:
                self._save_tree_to_file(self.current_file)
                self._log_info(f"Project saved: {os.path.basename(self.current_file)}")
                messagebox.showinfo("Project Saved", f"Saved: {os.path.basename(self.current_file)}")
            except Exception as e:
                self._log_error(f"Failed to save project: {e}")
                messagebox.showerror("Error", f"Failed to save project:\n{str(e)}")
        else:
            self._save_as_project()

    def _save_as_project(self):
        """Save the current project with a new name."""
        filepath = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".json",
            filetypes=[("ReGenesis Projects", "*.json"), ("All Files", "*.*")]
        )

        if filepath:
            try:
                self._save_tree_to_file(filepath)
                self.current_file = filepath
                self._update_title()
                self._log_info(f"Project saved as: {os.path.basename(filepath)}")
                messagebox.showinfo("Project Saved", f"Saved as: {os.path.basename(filepath)}")
            except Exception as e:
                self._log_error(f"Failed to save project: {e}")
                messagebox.showerror("Error", f"Failed to save project:\n{str(e)}")

    def _rename_project(self):
        """Rename the current project file."""
        if not self.current_file:
            messagebox.showwarning("Rename Project", "No project file is currently open.")
            return

        current_dir = os.path.dirname(self.current_file)
        current_name = os.path.basename(self.current_file)

        new_filepath = filedialog.asksaveasfilename(
            title="Rename Project",
            initialdir=current_dir,
            initialfile=current_name,
            defaultextension=".json",
            filetypes=[("ReGenesis Projects", "*.json"), ("All Files", "*.*")]
        )

        if new_filepath and new_filepath != self.current_file:
            try:
                os.rename(self.current_file, new_filepath)
                self.current_file = new_filepath
                self._update_title()
                messagebox.showinfo("Project Renamed", f"Renamed to: {os.path.basename(new_filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to rename project:\n{str(e)}")

    def _update_title(self):
        """Update the window title to show the current file name."""
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.root.title(f"Regenesis - {filename}")
        else:
            self.root.title("Regenesis - Native Plant Designer")

    def _show_preferences(self):
        """Show preferences dialog with theme selection and other settings."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Preferences")
        dialog.geometry("550x750")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 550) // 2
        y = (dialog.winfo_screenheight() - 750) // 2
        dialog.geometry(f"550x750+{x}+{y}")

        # Main frame with padding and scrollbar
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Application Preferences", font=("Helvetica", 14, "bold")).pack(pady=(0, 20))

        # LOCATION SECTION
        location_frame = ttk.Labelframe(main_frame, text="Location", bootstyle="info", padding=15)
        location_frame.pack(fill=tk.X, pady=(0, 10))

        # Get current location
        current_location = self.prefs.get_location()
        lat_value = current_location[0] if current_location else ""
        lon_value = current_location[1] if current_location else ""

        # Latitude
        lat_container = ttk.Frame(location_frame)
        lat_container.pack(fill=tk.X, pady=5)
        ttk.Label(lat_container, text="Latitude:", width=10).pack(side=tk.LEFT, padx=(0, 10))
        lat_var = tk.StringVar(value=str(lat_value) if lat_value else "")
        lat_entry = ttk.Entry(lat_container, textvariable=lat_var, width=20)
        lat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Longitude
        lon_container = ttk.Frame(location_frame)
        lon_container.pack(fill=tk.X, pady=5)
        ttk.Label(lon_container, text="Longitude:", width=10).pack(side=tk.LEFT, padx=(0, 10))
        lon_var = tk.StringVar(value=str(lon_value) if lon_value else "")
        lon_entry = ttk.Entry(lon_container, textvariable=lon_var, width=20)
        lon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # DEVELOPMENT MODE SECTION
        dev_frame = ttk.Labelframe(main_frame, text="Development", bootstyle="warning", padding=15)
        dev_frame.pack(fill=tk.X, pady=(0, 10))

        dev_var = tk.BooleanVar(value=self.prefs.is_development_mode())
        dev_check = ttk.Checkbutton(
            dev_frame,
            text="Development Mode (loads sample 'Smith Residence' project on startup)",
            variable=dev_var,
            bootstyle="success-round-toggle"
        )
        dev_check.pack(anchor=tk.W)

        # Theme selection section
        theme_frame = ttk.Labelframe(main_frame, text="Theme", bootstyle="primary", padding=15)
        theme_frame.pack(fill=tk.X, pady=10)

        ttk.Label(theme_frame, text="Choose a theme:", font=("Helvetica", 11)).pack(anchor=tk.W, pady=(0, 10))

        # Get current theme
        current_theme = self.root.style.theme.name

        # Theme options with descriptions
        themes = {
            "flatly": "Modern & Clean (Default)",
            "litera": "Nature-Friendly Earth Tones",
            "minty": "Fresh Green",
            "cosmo": "Clean & Bright",
            "yeti": "Soft & Modern",
            "journal": "Classic & Professional",
            "sandstone": "Warm & Natural",
            "darkly": "Dark Mode",
            "superhero": "Dark Blue",
            "solar": "Dark with High Contrast"
        }

        # Create a container frame for the grid layout
        buttons_container = ttk.Frame(theme_frame)
        buttons_container.pack(fill=tk.BOTH, expand=True)

        # Track the selected theme (for preview without saving)
        selected_theme = {'name': current_theme}

        # Theme preview function
        def preview_theme(theme_name):
            """Preview a theme without saving it."""
            self.root.style.theme_use(theme_name)
            selected_theme['name'] = theme_name

        # Create theme buttons in a grid
        row, col = 0, 0
        for theme_name, description in themes.items():
            # Determine button style based on whether it's selected
            btn_style = "success" if theme_name == current_theme else "outline-primary"

            btn = ttk.Button(
                buttons_container,
                text=f"{description}",
                width=22,
                bootstyle=btn_style,
                command=lambda t=theme_name: preview_theme(t)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky=tk.EW)

            col += 1
            if col > 1:  # 2 columns
                col = 0
                row += 1

        # Make columns expandable
        buttons_container.columnconfigure(0, weight=1)
        buttons_container.columnconfigure(1, weight=1)

        # Info label
        info_label = ttk.Label(
            main_frame,
            text="💡 Click a theme to preview. Click 'Save' to keep your changes.",
            font=("Helvetica", 10),
            bootstyle="info"
        )
        info_label.pack(pady=15)

        # Save function (without closing)
        def save_preferences():
            # Save location
            try:
                lat_str = lat_var.get().strip()
                lon_str = lon_var.get().strip()
                if lat_str and lon_str:
                    latitude = float(lat_str)
                    longitude = float(lon_str)
                    self.prefs.set_location(latitude, longitude)
                elif not lat_str and not lon_str:
                    # Both empty - clear location
                    self.prefs.set_location(None, None)
                else:
                    messagebox.showwarning("Invalid Location", "Please provide both latitude and longitude, or leave both empty.")
                    return False
            except ValueError:
                messagebox.showwarning("Invalid Location", "Latitude and longitude must be valid numbers.")
                return False

            # Save development mode
            self.prefs.set_development_mode(dev_var.get())

            # Save theme (if it changed)
            if selected_theme['name'] != self.prefs.get_theme():
                self.prefs.set_theme(selected_theme['name'])

            return True

        # Save and close function
        def save_and_close():
            if save_preferences():
                dialog.destroy()

        # Cancel function - revert theme to original and close
        def cancel_and_close():
            # Revert theme to original if it was changed
            if self.root.style.theme.name != self.prefs.get_theme():
                self.root.style.theme_use(self.prefs.get_theme())
            dialog.destroy()

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        # Save button (without closing)
        save_btn = ttk.Button(
            btn_frame,
            text="Save",
            width=12,
            bootstyle="info",
            command=save_preferences
        )
        save_btn.pack(side=tk.LEFT, padx=5)

        # Save & Close button
        save_close_btn = ttk.Button(
            btn_frame,
            text="Save & Close",
            width=12,
            bootstyle="success",
            command=save_and_close
        )
        save_close_btn.pack(side=tk.LEFT, padx=5)

        # Cancel button
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            width=12,
            bootstyle="secondary",
            command=cancel_and_close
        )
        cancel_btn.pack(side=tk.LEFT, padx=5)

        # Ensure dialog is properly displayed and interactive
        dialog.update_idletasks()
        dialog.deiconify()
        dialog.lift()

        dialog.wait_window()

    def _apply_theme(self, theme_name, dialog=None):
        """Apply the selected theme."""
        try:
            self.root.style.theme_use(theme_name)

            # Save theme to preferences
            self.prefs.set_theme(theme_name)

            # Show confirmation
            if dialog:
                # Update button styles in the dialog to show selection
                for widget in dialog.winfo_children():
                    if isinstance(widget, ttk.Frame):
                        for child in widget.winfo_children():
                            if isinstance(child, ttk.Labelframe):
                                # Look for the buttons_container frame
                                for container in child.winfo_children():
                                    if isinstance(container, ttk.Frame):
                                        for btn in container.winfo_children():
                                            if isinstance(btn, ttk.Button):
                                                # Reset all buttons to outline
                                                btn.configure(bootstyle="outline-primary")
                                                # Highlight the selected one
                                                if theme_name in btn.cget('text').lower():
                                                    btn.configure(bootstyle="success")
        except Exception as e:
            messagebox.showerror("Theme Error", f"Could not apply theme: {str(e)}")

    def _show_empty_tree_message(self):
        """Display a helpful message in the canvas when no projects are loaded."""
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width // 2
        center_y = height // 2

        # Display welcome message
        self.canvas.create_text(
            center_x, center_y - 40,
            text="Welcome to ReGenesis",
            font=("Arial", 24, "bold"),
            fill="#2c3e50",
            justify=tk.CENTER
        )

        self.canvas.create_text(
            center_x, center_y + 20,
            text="No projects loaded\n\nUse File → New to create a project\nor File → Open to load an existing one",
            font=("Arial", 14),
            fill="#7f8c8d",
            justify=tk.CENTER
        )

    def _populate_sample_tree(self):
        """Populate the tree with sample design structure."""
        # Root node - the project itself
        # Project values: (type, latitude, longitude, width, length, units)
        root = self.tree.insert('', 'end', text='Smith Residence',
                               values=('project', '42.3601', '-71.0589', '100', '150', 'feet'),
                               open=True, tags=('project',))

        # Front yard - meadow region
        # Region values: (type, region_type, soil_moisture, soil_type, sun)
        front_yard = self.tree.insert(root, 'end', text='Front Yard',
                                      values=('region', 'meadow', 'medium', 'loam', 'full-sun'),
                                      tags=('region',))

        # Side yard - layered region
        side_yard = self.tree.insert(root, 'end', text='Side Yard',
                                     values=('region', 'layered', 'med-dry', 'loam', 'part-sun'),
                                     tags=('region',))

        # Backyard - container region with children
        backyard = self.tree.insert(root, 'end', text='Backyard',
                                   values=('region', 'meadow', 'medium', 'loam', 'full-sun'),
                                   open=True, tags=('region',))

        # Backyard children - nested regions
        self.tree.insert(backyard, 'end', text='Pond',
                        values=('region', 'pond', 'wet', 'clay', 'full-sun'),
                        tags=('region',))
        self.tree.insert(backyard, 'end', text='Woodland Edge',
                        values=('region', 'layered', 'medium', 'loam', 'shade'),
                        tags=('region',))
        self.tree.insert(backyard, 'end', text='Patio',
                        values=('region', 'patio/deck', 'dry', 'sand', 'full-sun'),
                        tags=('region',))

        # Auto-select the project root to show the rectangle
        self.tree.selection_set(root)
        self.tree.focus(root)

        # Defer workspace update until window is properly sized
        # Use after with delay to ensure canvas is fully rendered
        self.root.after(100, lambda: self._on_tree_select(None))

        self._log_info("Loaded sample project: Smith Residence (Development Mode)")

    def _on_tree_select(self, event):
        """Handle tree selection event."""
        import time
        start_time = time.time()
        self._log_info("=== Tree select START ===")

        # Save current polygon if in drawing mode
        if self.drawing_mode and self.selected_item and self.polygon_vertices:
            self.region_polygons[self.selected_item] = list(self.polygon_vertices)
            self._log_info(f"Saved polygon with {len(self.polygon_vertices)} vertices")

        # Exit drawing mode when switching nodes
        if self.drawing_mode:
            self.drawing_mode = False
            self.canvas.config(cursor='')
            # Hide the Clear Shape button when exiting drawing mode (only if currently visible)
            if self._clear_button_visible:
                self.clear_polygon_button.pack_forget()
                self._clear_button_visible = False
            self._log_info("Exited drawing mode (node switch)")

        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        self.selected_item = item

        # Get item details
        item_text = self.tree.item(item, 'text')
        item_values = self.tree.item(item, 'values')

        # Determine item type
        item_type = item_values[0] if item_values and len(item_values) > 0 else 'project'

        # Update properties panel based on type
        self._updating_properties = True

        # Hide both forms first
        self.project_props_frame.pack_forget()
        self.region_props_frame.pack_forget()

        if item_type == 'project':
            # Show project properties form
            self.project_props_frame.pack(fill=tk.BOTH, expand=True)

            # Load project properties
            self.project_name_var.set(item_text)
            self.project_latitude_var.set(item_values[1] if len(item_values) > 1 else '')
            self.project_longitude_var.set(item_values[2] if len(item_values) > 2 else '')
            self.project_width_var.set(item_values[3] if len(item_values) > 3 else '')
            self.project_length_var.set(item_values[4] if len(item_values) > 4 else '')
            self.project_units_var.set(item_values[5] if len(item_values) > 5 else 'feet')

        elif item_type == 'region':
            # Show region properties form
            self.region_props_frame.pack(fill=tk.BOTH, expand=True)

            # Load region properties
            self.region_name_var.set(item_text)
            self.region_type_var.set(item_values[1] if len(item_values) > 1 else 'meadow')
            self.soil_moisture_var.set(item_values[2] if len(item_values) > 2 else 'medium')
            self.soil_type_var.set(item_values[3] if len(item_values) > 3 else 'loam')
            self.sun_var.set(item_values[4] if len(item_values) > 4 else 'full-sun')

        self._updating_properties = False

        # Update workspace canvas
        before_workspace = time.time()
        self._update_workspace(item_text, item_type)
        after_workspace = time.time()

        self._log_info(f"_update_workspace took {(after_workspace - before_workspace)*1000:.0f}ms")

        total_elapsed = time.time() - start_time
        self._log_info(f"=== Tree select COMPLETE: {total_elapsed*1000:.0f}ms ===")

    def _apply_property_change(self):
        """Apply property changes to the selected tree item."""
        if not self.selected_item or self._updating_properties:
            return

        try:
            # Get current item type
            item_values = self.tree.item(self.selected_item, 'values')
            item_type = item_values[0] if item_values and len(item_values) > 0 else 'project'

            if item_type == 'project':
                # Update project properties
                name = self.project_name_var.get().strip()
                latitude = self.project_latitude_var.get().strip()
                longitude = self.project_longitude_var.get().strip()
                width = self.project_width_var.get().strip()
                length = self.project_length_var.get().strip()
                units = self.project_units_var.get()

                # Update tree item
                if name:
                    self.tree.item(self.selected_item, text=name)
                self.tree.item(self.selected_item, values=('project', latitude, longitude, width, length, units))

            elif item_type == 'region':
                # Update region properties
                name = self.region_name_var.get().strip()
                region_type = self.region_type_var.get()
                soil_moisture = self.soil_moisture_var.get()
                soil_type = self.soil_type_var.get()
                sun = self.sun_var.get()

                # Update tree item
                if name:
                    self.tree.item(self.selected_item, text=name)
                self.tree.item(self.selected_item, values=('region', region_type, soil_moisture, soil_type, sun))

            # Update workspace
            item_text = self.tree.item(self.selected_item, 'text')
            self._update_workspace(item_text, item_type)

        except Exception as e:
            self._log_error(f"Failed to apply property change: {e}")

    def _update_workspace(self, name, item_type, retry_count=0):
        """Update the workspace canvas to display the selected item."""
        import time
        ws_start = time.time()

        # Clear canvas
        self.canvas.delete('all')

        # Get canvas dimensions
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Check if canvas is properly sized, if not skip this update
        if width < 10 or height < 10:
            if retry_count < 50:  # Limit retries to prevent infinite loop
                # Try again in 100ms
                self.root.after(100, lambda: self._update_workspace(name, item_type, retry_count + 1))
            else:
                self._log_error(f"Canvas failed to size properly after {retry_count} retries")
            return

        center_x = width / 2
        center_y = height / 2

        # STEP 1: Always find and draw the project rectangle
        project_item = self._find_project_root()
        if project_item:
            # Check if we switched to a different project
            if project_item != self._current_project_item:
                self._current_project_item = project_item
                self._has_auto_zoomed = False  # Reset auto-zoom flag for new project

            self._draw_project_rectangle(project_item, width, height, center_x, center_y)

        # STEP 2: Always draw ALL saved region polygons (not editable, just display)
        self._draw_all_region_polygons()

        # STEP 3: Always draw origin marker and rulers on top
        self._draw_origin_marker()
        self._update_rulers()

        # STEP 4: If viewing a region, enable drawing mode for THAT region (makes it editable)
        if item_type == 'region':
            if self.selected_item in self.region_polygons:
                # Restore the saved polygon and enable drawing mode for editing
                self.drawing_mode = True
                saved_vertices = self.region_polygons[self.selected_item]
                self.polygon_vertices = list(saved_vertices)
                self._redraw_polygon()
                # Show and enable the Clear Shape button (only if not already visible)
                if not self._clear_button_visible:
                    self.clear_polygon_button.pack(side=tk.LEFT, padx=5)
                    self._clear_button_visible = True
                self.clear_polygon_button.config(state=tk.NORMAL)
                self._log_info(f"Enabled editing for polygon with {len(self.polygon_vertices)} vertices")
            else:
                # No saved polygon, start drawing mode automatically
                self.drawing_mode = True
                self._create_default_rectangle()
                self._log_info("Drawing mode enabled - rectangle created for region")

        ws_elapsed = time.time() - ws_start
        self._log_info(f"Update workspace completed in {ws_elapsed*1000:.1f}ms")

    def _start_tree_rename(self, event):
        """Start in-tree renaming (double-click on item)."""
        # Note: Tkinter Treeview doesn't support native in-line editing
        # So we'll select the name field in Properties instead
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.name_entry.focus_set()
            self.name_entry.select_range(0, tk.END)

    def _show_context_menu(self, event):
        """Show right-click context menu."""
        # Identify the item that was clicked
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.selected_item = item

            # Create context menu
            menu = tk.Menu(self.root, tearoff=0)
            menu.add_command(label="Add Child Region", command=self._add_child_region)
            menu.add_separator()
            menu.add_command(label="Delete", command=self._delete_item)

            # Show menu at cursor position
            menu.post(event.x_root, event.y_root)

    def _add_child_region(self):
        """Add a new child region to the selected item."""
        if not self.selected_item:
            return

        # Insert a new region with default values
        # Region values: (type, region_type, soil_moisture, soil_type, sun)
        new_region = self.tree.insert(self.selected_item, 'end', text='New Region',
                                     values=('region', 'meadow', 'medium', 'loam', 'full-sun'),
                                     tags=('region',))
        self.tree.item(self.selected_item, open=True)  # Expand parent
        self.tree.selection_set(new_region)
        self.tree.see(new_region)
        self._log_info("Added new region to tree")

    def _delete_item(self):
        """Delete the selected item with confirmation."""
        if not self.selected_item:
            return

        # Check if this is the root project
        if not self.tree.parent(self.selected_item):
            messagebox.showwarning("Cannot Delete", "Cannot delete the root project.")
            return

        # Check if item has children
        children = self.tree.get_children(self.selected_item)
        item_text = self.tree.item(self.selected_item, 'text')

        if children:
            # Item has children
            message = f"Warning: '{item_text}' and all its child regions will be removed."
            title = "Confirm Delete"
        else:
            # Empty item
            message = f"Warning: '{item_text}' will be removed from your project."
            title = "Confirm Delete"

        # Create custom dialog with Proceed and Cancel buttons
        if self._show_delete_confirmation(title, message):
            # User clicked Proceed
            parent = self.tree.parent(self.selected_item)
            self.tree.delete(self.selected_item)
            self._log_warning(f"Deleted item: {item_text}")
            self.selected_item = None
            # Select parent if it exists
            if parent:
                self.tree.selection_set(parent)

    def _show_delete_confirmation(self, title, message):
        """Show custom delete confirmation dialog with Proceed and Cancel buttons."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("450x180")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 450) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"450x180+{x}+{y}")

        result = {'proceed': False}

        # Main frame with padding
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Message
        ttk.Label(main_frame, text=message, wraplength=400, font=("Helvetica", 11)).pack(pady=(0, 20))

        # Button frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        # Proceed button (danger style)
        proceed_btn = ttk.Button(
            btn_frame,
            text="Proceed",
            width=12,
            bootstyle="danger",
            command=lambda: [result.update({'proceed': True}), dialog.destroy()]
        )
        proceed_btn.pack(side=tk.LEFT, padx=10)

        # Cancel button
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            width=12,
            bootstyle="secondary",
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

        dialog.wait_window()
        return result['proceed']

    def _on_drag_start(self, event):
        """Handle start of drag operation."""
        # Record the starting position
        self._drag_start_x = event.x
        self._drag_start_y = event.y
        self._has_moved = False

        item = self.tree.identify_row(event.y)
        if item:
            # Don't allow dragging the root node
            if not self.tree.parent(item):
                self._drag_item = None
                return
            self._drag_item = item

    def _on_drag_motion(self, event):
        """Handle drag motion - visual feedback."""
        if not self._drag_item:
            return

        # Check if the mouse has moved enough to be considered a drag
        # Use a 5-pixel threshold to distinguish from clicks
        dx = abs(event.x - self._drag_start_x)
        dy = abs(event.y - self._drag_start_y)
        if dx > 5 or dy > 5:
            self._has_moved = True

        # Only show drag feedback if we've actually moved
        if not self._has_moved:
            return

        # Get the item under the cursor
        target = self.tree.identify_row(event.y)
        if not target:
            self._drop_target = None
            self._drop_position = None
            self.tree.config(cursor='')
            # Clear any previous visual feedback
            self.tree.selection_set(self._drag_item)
            return

        # Don't allow dropping on itself or descendants
        if target == self._drag_item or self._is_descendant(self._drag_item, target):
            self._drop_target = None
            self._drop_position = None
            self.tree.config(cursor='X_cursor')  # Cross-platform "not allowed" cursor
            return

        # Get the bounding box of the target item
        bbox = self.tree.bbox(target)
        if not bbox:
            return

        _, item_y, _, item_height = bbox
        relative_y = event.y - item_y

        # Get drag and target types
        drag_values = self.tree.item(self._drag_item, 'values')
        drag_type = drag_values[0] if drag_values else None
        target_values = self.tree.item(target, 'values')
        target_type = target_values[0] if target_values else None

        # Determine drop position based on cursor position within the item
        # Top quarter = above, bottom quarter = below, middle = inside (if applicable)
        quarter = item_height / 4

        if relative_y < quarter:
            # Top quarter - drop above
            self._drop_position = 'above'
            self._drop_target = target
            self.tree.selection_set(target)
            self.tree.config(cursor='based_arrow_up')
        elif relative_y > 3 * quarter:
            # Bottom quarter - drop below
            self._drop_position = 'below'
            self._drop_target = target
            self.tree.selection_set(target)
            self.tree.config(cursor='based_arrow_down')
        else:
            # Middle half - drop inside (only for regions and projects)
            if drag_type == 'region' and target_type in ('project', 'region'):
                self._drop_position = 'inside'
                self._drop_target = target
                self.tree.selection_set(target)
                self.tree.config(cursor='hand2')
            else:
                # Can't drop inside, default to below
                self._drop_position = 'below'
                self._drop_target = target
                self.tree.selection_set(target)
                self.tree.config(cursor='based_arrow_down')

    def _on_drag_release(self, event):
        """Handle drop operation."""
        if not self._drag_item:
            return

        # If the user didn't actually drag (just clicked), let tree selection happen
        if not self._has_moved:
            # Reset drag state
            self._drag_item = None
            self._drop_target = None
            self._drop_position = None
            self._has_moved = False
            # The click will trigger TreeviewSelect normally
            return

        # Use the drop target and position determined during drag motion
        if self._drop_target and self._drop_position:
            target = self._drop_target
            position = self._drop_position

            # Don't allow dropping root project
            if not self.tree.parent(self._drag_item):
                self._drag_item = None
                self._drop_target = None
                self._drop_position = None
                return

            # Perform the drop based on position
            if position == 'above':
                # Insert above target (as sibling before target)
                target_parent = self.tree.parent(target)
                target_index = self.tree.index(target)
                new_item = self._clone_subtree(self._drag_item, target_parent, target_index)
            elif position == 'below':
                # Insert below target (as sibling after target)
                target_parent = self.tree.parent(target)
                target_index = self.tree.index(target)
                new_item = self._clone_subtree(self._drag_item, target_parent, target_index + 1)
            elif position == 'inside':
                # Insert inside target (as last child)
                new_item = self._clone_subtree(self._drag_item, target, 'end')
                self.tree.item(target, open=True)  # Expand target
            else:
                # Shouldn't happen, but fallback
                self._drag_item = None
                self._drop_target = None
                self._drop_position = None
                return

            # Delete the old item
            self.tree.delete(self._drag_item)

            # Select the new item
            self.tree.selection_set(new_item)
            self.tree.see(new_item)
            self.selected_item = new_item

        # Reset cursor
        self.tree.config(cursor='')

        # Reset drag state
        self._drag_item = None
        self._drop_target = None
        self._drop_position = None
        self._has_moved = False

    def _is_descendant(self, parent_item, child_item):
        """Check if child_item is a descendant of parent_item."""
        current = child_item
        while current:
            if current == parent_item:
                return True
            current = self.tree.parent(current)
        return False

    def _clone_subtree(self, item, new_parent, index):
        """Clone an item and all its children to a new location."""
        # Get item data
        text = self.tree.item(item, 'text')
        values = self.tree.item(item, 'values')
        open_state = self.tree.item(item, 'open')
        tags = self.tree.item(item, 'tags')

        # Insert the new item
        new_item = self.tree.insert(new_parent, index, text=text, values=values, open=open_state, tags=tags)

        # Clone all children recursively
        for child in self.tree.get_children(item):
            self._clone_subtree(child, new_item, 'end')

        return new_item

    def _save_tree_to_file(self, filepath):
        """Save the tree structure to a JSON file."""
        import json

        def serialize_item(item_id):
            """Recursively serialize a tree item and its children."""
            item_data = {
                'text': self.tree.item(item_id, 'text'),
                'values': list(self.tree.item(item_id, 'values')),
                'tags': list(self.tree.item(item_id, 'tags')),
                'children': []
            }
            for child_id in self.tree.get_children(item_id):
                item_data['children'].append(serialize_item(child_id))
            return item_data

        # Get the root items (should be just the project)
        root_items = []
        for item_id in self.tree.get_children(''):
            root_items.append(serialize_item(item_id))

        # Save to file
        project_data = {'tree': root_items}
        with open(filepath, 'w') as f:
            json.dump(project_data, f, indent=2)

    def _load_tree_from_file(self, filepath):
        """Load the tree structure from a JSON file."""
        import json

        def deserialize_item(item_data, parent=''):
            """Recursively deserialize a tree item and its children."""
            # Insert the item
            item_id = self.tree.insert(
                parent,
                'end',
                text=item_data['text'],
                values=tuple(item_data['values']),
                tags=tuple(item_data['tags']),
                open=True
            )
            # Insert children
            for child_data in item_data.get('children', []):
                deserialize_item(child_data, item_id)
            return item_id

        # Load from file
        with open(filepath, 'r') as f:
            project_data = json.load(f)

        # Clear existing tree
        for item in self.tree.get_children(''):
            self.tree.delete(item)

        # Load tree items
        for item_data in project_data.get('tree', []):
            deserialize_item(item_data)

    def _log_info(self, message):
        """Log an info message to the console."""
        self._log_message(message, 'info', '[INFO] ')

    def _log_warning(self, message):
        """Log a warning message to the console."""
        self._log_message(message, 'warning', '[WARNING] ')

    def _log_error(self, message):
        """Log an error message to the console."""
        self._log_message(message, 'error', '[ERROR] ')

    def _log_message(self, message, tag, prefix=''):
        """Internal method to log a message to the console with formatting."""
        from datetime import datetime

        # Enable editing
        self.console.config(state=tk.NORMAL)

        # Get current time
        timestamp = datetime.now().strftime('%H:%M:%S')

        # Insert timestamp
        self.console.insert(tk.END, f"[{timestamp}] ", 'info')

        # Insert prefix and message with appropriate tag
        self.console.insert(tk.END, f"{prefix}{message}\n", tag)

        # Auto-scroll to the end
        self.console.see(tk.END)

        # Disable editing
        self.console.config(state=tk.DISABLED)

    def _copy_console_text(self):
        """Copy all console text to clipboard."""
        console_text = self.console.get('1.0', tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(console_text)
        self._log_info("Console text copied to clipboard")

    def _clear_console(self):
        """Clear all console text."""
        self.console.config(state=tk.NORMAL)
        self.console.delete('1.0', tk.END)
        self.console.config(state=tk.DISABLED)
        self._log_info("Console cleared")

    def _create_tooltip(self, widget, text):
        """Create a tooltip for a widget."""
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            label = tk.Label(tooltip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
            label.pack()
            widget._tooltip = tooltip

        def on_leave(event):
            if hasattr(widget, '_tooltip'):
                widget._tooltip.destroy()
                del widget._tooltip

        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)

    # Canvas Pan/Zoom Methods

    def _on_canvas_resize(self):
        """Handle canvas resize - update rulers and reposition project items."""
        # Update rulers (which also redraws origin marker)
        self._update_rulers()

        # If we're viewing a project with a rectangle, redraw it at the new canvas center
        if self.selected_item and not self.drawing_mode:
            item_values = self.tree.item(self.selected_item, 'values')
            if item_values and len(item_values) > 0 and item_values[0] == 'project':
                # Check if project has dimensions (rectangle should be shown)
                if len(item_values) > 4:
                    project_width_str = item_values[3]
                    project_length_str = item_values[4]
                    if project_width_str and project_length_str:
                        try:
                            project_width = float(project_width_str)
                            project_length = float(project_length_str)

                            if project_width > 0 and project_length > 0:
                                # Redraw the rectangle at the new canvas center
                                self._redraw_project_rectangle(project_width, project_length)
                        except (ValueError, IndexError):
                            pass

    def _find_project_root(self):
        """Find the root project item in the tree."""
        if not self.selected_item:
            return None

        # Walk up the tree to find the root project
        current = self.selected_item
        while self.tree.parent(current):
            current = self.tree.parent(current)

        return current

    def _draw_project_rectangle(self, project_item, width, height, center_x, center_y):
        """Draw the project boundary rectangle. Returns True if drawn, False otherwise."""
        item_values = self.tree.item(project_item, 'values')
        self._log_info(f"Drawing project rectangle: item_values={item_values}")

        if not item_values or len(item_values) < 5:
            self._log_warning(f"Cannot draw rectangle: insufficient values (got {len(item_values) if item_values else 0}, need 5)")
            return False

        try:
            project_width_str = item_values[3]
            project_length_str = item_values[4]

            if not project_width_str or not project_length_str:
                self._log_warning(f"Cannot draw rectangle: width or length is empty")
                return False

            project_width = float(project_width_str)
            project_length = float(project_length_str)

            self._log_info(f"Project dimensions: {project_width} x {project_length}")

            if project_width <= 0 or project_length <= 0:
                return False

            # Convert to pixels (50 pixels = 1 unit at zoom 1.0, scaled by current zoom)
            pixels_per_unit = 50 * self.canvas_zoom
            rect_width = project_width * pixels_per_unit
            rect_height = project_length * pixels_per_unit

            # Center rectangle around canvas center (which represents 0,0 in project coords)
            origin_x = center_x + self.canvas_pan_x
            origin_y = center_y + self.canvas_pan_y

            x1 = origin_x - rect_width / 2
            y1 = origin_y - rect_height / 2
            x2 = origin_x + rect_width / 2
            y2 = origin_y + rect_height / 2

            # Auto-zoom to fit rectangle if it's too large for canvas (only once per project)
            if not self._has_auto_zoomed:
                # Add 20% margin
                required_width = rect_width * 1.2
                required_height = rect_height * 1.2

                # Calculate zoom needed to fit
                zoom_for_width = width / required_width
                zoom_for_height = height / required_height
                auto_zoom = min(zoom_for_width, zoom_for_height)

                # Respect zoom limits (0.01 to 10.0)
                auto_zoom = max(0.01, min(10.0, auto_zoom))

                # Only auto-zoom if rectangle is too large
                if auto_zoom < self.canvas_zoom:
                    self.canvas_zoom = auto_zoom
                    self._log_info(f"Auto-zoomed to {auto_zoom:.3f} to fit rectangle")

                    # Recalculate rectangle with new zoom
                    pixels_per_unit = 50 * self.canvas_zoom
                    rect_width = project_width * pixels_per_unit
                    rect_height = project_length * pixels_per_unit

                    x1 = origin_x - rect_width / 2
                    y1 = origin_y - rect_height / 2
                    x2 = origin_x + rect_width / 2
                    y2 = origin_y + rect_height / 2

                self._has_auto_zoomed = True

            # Draw unfilled rectangle outline
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                outline='#3498db',
                width=2,
                dash=(5, 3),
                tags='project_boundary'
            )

            return True

        except (ValueError, IndexError) as e:
            self._log_error(f"Error drawing project rectangle: {e}")
            return False

    def _draw_all_region_polygons(self):
        """Draw all saved region polygons (non-editable display)."""
        for region_item, vertices in self.region_polygons.items():
            # Skip the currently selected region if in drawing mode (it will be drawn editable)
            if self.drawing_mode and region_item == self.selected_item:
                continue

            if len(vertices) < 3:
                continue

            # Draw the filled polygon
            flat_coords = [coord for vertex in vertices for coord in vertex]
            self.canvas.create_polygon(
                flat_coords,
                fill='#2ecc71',
                outline='#27ae60',
                width=2,
                stipple='gray25',
                tags=f'region_polygon_{region_item}'
            )

            # Draw vertices (small circles, max 10 pixels, scale down with zoom)
            vertex_radius = min(10, max(3, 10 * self.canvas_zoom))
            for vx, vy in vertices:
                self.canvas.create_oval(
                    vx - vertex_radius, vy - vertex_radius,
                    vx + vertex_radius, vy + vertex_radius,
                    fill='#27ae60',
                    outline='#1e8449',
                    width=1,
                    tags=f'region_polygon_{region_item}'
                )

    def _redraw_project_rectangle(self, project_width, project_length):
        """Redraw the project rectangle centered at the origin."""
        # Get current canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width / 2
        center_y = height / 2

        # Calculate rectangle dimensions with current zoom
        pixels_per_unit = 50 * self.canvas_zoom
        rect_width = project_width * pixels_per_unit
        rect_height = project_length * pixels_per_unit

        # Calculate position centered at origin
        origin_x = center_x + self.canvas_pan_x
        origin_y = center_y + self.canvas_pan_y

        x1 = origin_x - rect_width / 2
        y1 = origin_y - rect_height / 2
        x2 = origin_x + rect_width / 2
        y2 = origin_y + rect_height / 2

        # Delete old rectangle and redraw
        self.canvas.delete('project_boundary')
        self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline='#3498db',
            width=2,
            dash=(5, 3),
            tags='project_boundary'
        )

    def _space_pressed(self, _event):
        """Handle space key press for panning mode."""
        self._space_is_pressed = True
        self.canvas.config(cursor='hand2')

    def _space_released(self, _event):
        """Handle space key release."""
        self._space_is_pressed = False
        if not self._is_panning:
            self.canvas.config(cursor='')

    def _start_pan(self, event):
        """Start panning the canvas."""
        self._is_panning = True
        self._pan_start_x = event.x
        self._pan_start_y = event.y
        self.canvas.config(cursor='fleur')

    def _pan_canvas(self, event):
        """Pan the canvas based on mouse movement."""
        if self._is_panning:
            # Calculate delta
            dx = event.x - self._pan_start_x
            dy = event.y - self._pan_start_y

            # Update pan offset
            self.canvas_pan_x += dx
            self.canvas_pan_y += dy

            # Move all canvas items
            self.canvas.move('all', dx, dy)

            # Update start position for next movement
            self._pan_start_x = event.x
            self._pan_start_y = event.y

            # Update rulers
            self._update_rulers()

    def _end_pan(self, _event):
        """End panning the canvas."""
        self._is_panning = False
        if not self._space_is_pressed:
            self.canvas.config(cursor='')

    def _zoom_canvas(self, event):
        """Zoom the canvas based on mouse wheel."""
        # Determine zoom direction
        if event.num == 5 or event.delta < 0:  # Scroll down / zoom out
            factor = 0.9
            direction = "out"
        elif event.num == 4 or event.delta > 0:  # Scroll up / zoom in
            factor = 1.1
            direction = "in"
        else:
            return

        # Limit zoom range
        new_zoom = self.canvas_zoom * factor
        if new_zoom < 0.01 or new_zoom > 10.0:
            self._log_info(f"Zoom {direction} blocked - would exceed limits (new: {new_zoom:.3f})")
            return

        self._log_info(f"Zooming {direction}: {self.canvas_zoom:.3f} -> {new_zoom:.3f}")

        # Get mouse position on canvas
        mouse_x = event.x
        mouse_y = event.y

        # Get canvas dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        center_x = canvas_width / 2
        center_y = canvas_height / 2

        # Calculate the world position under the mouse before zoom
        # world_pos = (screen_pos - center - pan) / pixels_per_unit
        old_pixels_per_unit = 50 * self.canvas_zoom
        world_x = (mouse_x - center_x - self.canvas_pan_x) / old_pixels_per_unit
        world_y = (mouse_y - center_y - self.canvas_pan_y) / old_pixels_per_unit

        # Scale all items (for polygons)
        x = self.canvas.canvasx(mouse_x)
        y = self.canvas.canvasy(mouse_y)
        self.canvas.scale('all', x, y, factor, factor)

        # Update zoom level
        self.canvas_zoom = new_zoom

        # Calculate new pan offset to keep the world position under the mouse
        # screen_pos = (world_pos * new_pixels_per_unit) + center + new_pan
        # mouse = (world * new_pixels) + center + new_pan
        # new_pan = mouse - center - (world * new_pixels)
        new_pixels_per_unit = 50 * self.canvas_zoom
        self.canvas_pan_x = mouse_x - center_x - (world_x * new_pixels_per_unit)
        self.canvas_pan_y = mouse_y - center_y - (world_y * new_pixels_per_unit)

        # Update rulers (which will redraw origin marker and project rectangle)
        self._update_rulers()

    def _fit_to_project_rectangle(self, project_width, project_length):
        """Fit the canvas view to show the project rectangle."""
        # Get canvas dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate required dimensions with 20% margin
        required_width_units = project_width * 1.2
        required_height_units = project_length * 1.2

        # Calculate zoom needed to fit (pixels per unit at zoom 1.0 = 50)
        zoom_for_width = canvas_width / (required_width_units * 50)
        zoom_for_height = canvas_height / (required_height_units * 50)
        target_zoom = min(zoom_for_width, zoom_for_height)

        # Respect zoom limits
        target_zoom = max(0.01, min(10.0, target_zoom))

        # Reset pan to center
        self.canvas_pan_x = 0
        self.canvas_pan_y = 0
        self.canvas_zoom = target_zoom

        # Redraw everything at new zoom
        self._update_rulers()

        self._log_info(f"Fitted view to project rectangle at zoom {target_zoom:.3f}")

    def _fit_to_design_extents(self):
        """Fit the canvas view to show all project regions."""
        if not self.polygon_vertices:
            # Check if we're viewing a project with dimensions
            if self.selected_item:
                item_values = self.tree.item(self.selected_item, 'values')
                if item_values and len(item_values) > 0 and item_values[0] == 'project':
                    if len(item_values) > 4:
                        project_width_str = item_values[3]
                        project_length_str = item_values[4]
                        if project_width_str and project_length_str:
                            try:
                                project_width = float(project_width_str)
                                project_length = float(project_length_str)
                                if project_width > 0 and project_length > 0:
                                    # Fit to project rectangle
                                    self._fit_to_project_rectangle(project_width, project_length)
                                    return
                            except (ValueError, IndexError):
                                pass

            # No polygon or project rectangle to fit
            self._reset_view()
            self._log_info("No polygon to fit - reset to default view")
            return

        # Store original vertices before any transformations
        original_vertices = list(self.polygon_vertices)

        # Calculate bounding box of all vertices (leftmost, rightmost, topmost, bottommost)
        min_x = min(v[0] for v in original_vertices)
        max_x = max(v[0] for v in original_vertices)
        min_y = min(v[1] for v in original_vertices)
        max_y = max(v[1] for v in original_vertices)

        # Calculate center of the polygon bounding box
        poly_center_x = (min_x + max_x) / 2
        poly_center_y = (min_y + max_y) / 2

        # Get canvas dimensions
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        canvas_center_x = canvas_width / 2
        canvas_center_y = canvas_height / 2

        # Reset current view first
        self._reset_view()

        # After reset, polygon is back at original position
        # Calculate dimensions with padding
        width = max_x - min_x
        height = max_y - min_y

        # Add padding (20% on each side)
        padding_factor = 0.2
        padded_width = width * (1 + 2 * padding_factor)
        padded_height = height * (1 + 2 * padding_factor)

        # Calculate required zoom to fit the bounding box with padding
        if padded_width > 0 and padded_height > 0:
            zoom_x = canvas_width / padded_width
            zoom_y = canvas_height / padded_height
            target_zoom = min(zoom_x, zoom_y)

            # Limit zoom range
            target_zoom = max(0.01, min(10.0, target_zoom))
        else:
            target_zoom = 1.0

        # Apply zoom centered on the polygon's center
        if target_zoom != 1.0:
            self.canvas.scale('all', poly_center_x, poly_center_y, target_zoom, target_zoom)
            self.canvas_zoom = target_zoom

        # After zooming, the polygon center has moved to: poly_center_x * target_zoom, poly_center_y * target_zoom
        # But we zoomed around poly_center_x, poly_center_y, so it stays at poly_center_x, poly_center_y

        # Now pan to center the polygon in the canvas
        pan_x = canvas_center_x - poly_center_x
        pan_y = canvas_center_y - poly_center_y

        self.canvas.move('all', pan_x, pan_y)
        self.canvas_pan_x = pan_x
        self.canvas_pan_y = pan_y

        # Update rulers
        self._update_rulers()

        self._log_info("Fitted view to design extents")

    def _fit_to_region(self):
        """Fit the canvas view to the currently selected region."""
        if not self.selected_item:
            self._log_warning("No region selected")
            return

        # Get the selected region name
        item_text = self.tree.item(self.selected_item, 'text')

        # Reset to default view for now
        # In the future, this will fit to the region's polygon bounds
        self._reset_view()
        self._log_info(f"Fitted view to region: {item_text}")

    def _reset_view(self):
        """Reset canvas to default zoom and pan."""
        # Calculate how much to move everything back
        dx = -self.canvas_pan_x
        dy = -self.canvas_pan_y

        # Reset pan
        self.canvas.move('all', dx, dy)
        self.canvas_pan_x = 0
        self.canvas_pan_y = 0

        # Reset zoom (scale back to 1.0)
        if self.canvas_zoom != 1.0:
            center_x = self.canvas.winfo_width() / 2
            center_y = self.canvas.winfo_height() / 2
            scale_factor = 1.0 / self.canvas_zoom
            self.canvas.scale('all', center_x, center_y, scale_factor, scale_factor)
            self.canvas_zoom = 1.0

    def _zoom_in(self):
        """Zoom in by simulating a mouse wheel event."""
        # Create a synthetic event for zoom in
        event = type('Event', (), {
            'num': 4,
            'delta': 120,
            'x': self.canvas.winfo_width() // 2,
            'y': self.canvas.winfo_height() // 2
        })()
        self._zoom_canvas(event)

    def _zoom_out(self):
        """Zoom out by simulating a mouse wheel event."""
        # Create a synthetic event for zoom out
        event = type('Event', (), {
            'num': 5,
            'delta': -120,
            'x': self.canvas.winfo_width() // 2,
            'y': self.canvas.winfo_height() // 2
        })()
        self._zoom_canvas(event)

    def _toggle_grid(self):
        """Toggle grid display on the canvas."""
        if not hasattr(self, '_grid_visible'):
            self._grid_visible = False

        if self._grid_visible:
            # Hide grid
            self.canvas.delete('grid')
            self._grid_visible = False
            self._log_info("Grid hidden")
        else:
            # Show grid
            self._draw_grid()
            self._grid_visible = True
            self._log_info("Grid shown")

    # Canvas Drawing Methods

    # _toggle_drawing_mode removed - drawing mode now starts automatically when viewing a region
    # and exits automatically when switching nodes

    def _create_default_rectangle(self):
        """Create a default rectangle in the center of the canvas."""
        # Get canvas center
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width / 2
        center_y = height / 2

        # Try to get project dimensions
        rect_width = 200  # Default in pixels
        rect_height = 150  # Default in pixels

        # Check if we have a project selected with dimensions
        if self.selected_item:
            item_values = self.tree.item(self.selected_item, 'values')
            item_type = item_values[0] if item_values and len(item_values) > 0 else None

            if item_type == 'project':
                # Get width and length from project properties
                try:
                    project_width_str = item_values[3] if len(item_values) > 3 else ''
                    project_length_str = item_values[4] if len(item_values) > 4 else ''

                    if project_width_str and project_length_str:
                        project_width = float(project_width_str)
                        project_length = float(project_length_str)

                        # Convert to pixels (50 pixels = 1 unit)
                        rect_width = project_width * 50
                        rect_height = project_length * 50
                        self._log_info(f"Creating rectangle from project dimensions: {project_width} x {project_length}")
                except (ValueError, IndexError):
                    # If conversion fails, use defaults
                    pass

        x1 = center_x - rect_width / 2
        y1 = center_y - rect_height / 2
        x2 = center_x + rect_width / 2
        y2 = center_y + rect_height / 2

        # Clear any existing polygon
        self._clear_polygon()

        # Create vertices (clockwise from top-left)
        self.polygon_vertices = [
            (x1, y1),  # Top-left
            (x2, y1),  # Top-right
            (x2, y2),  # Bottom-right
            (x1, y2)   # Bottom-left
        ]

        # Draw the polygon
        self._redraw_polygon()
        # Show and enable the Clear Shape button when in drawing mode (only if not already visible)
        if not self._clear_button_visible:
            self.clear_polygon_button.pack(side=tk.LEFT, padx=5)
            self._clear_button_visible = True
        self.clear_polygon_button.config(state=tk.NORMAL)

    def _clear_polygon(self):
        """Clear the current polygon and vertices."""
        if self.current_polygon:
            self.canvas.delete(self.current_polygon)
            self.current_polygon = None

        for handle in self.vertex_handles:
            self.canvas.delete(handle)
        self.vertex_handles = []

        self.polygon_vertices = []
        self.selected_vertex = None
        self._dragging_vertex = False
        self.clear_polygon_button.config(state=tk.DISABLED)
        self._log_info("Polygon cleared")

    def _redraw_polygon(self):
        """Redraw the polygon and vertex handles."""
        # Delete old polygon and handles
        if self.current_polygon:
            self.canvas.delete(self.current_polygon)
        for handle in self.vertex_handles:
            self.canvas.delete(handle)
        self.vertex_handles = []

        if len(self.polygon_vertices) < 3:
            return

        # Create polygon
        flat_coords = []
        for x, y in self.polygon_vertices:
            flat_coords.extend([x, y])

        self.current_polygon = self.canvas.create_polygon(
            flat_coords,
            fill='lightblue',
            outline='blue',
            width=2,
            tags='polygon'
        )

        # Create vertex handles
        for i, (x, y) in enumerate(self.polygon_vertices):
            handle = self.canvas.create_oval(
                x - 5, y - 5, x + 5, y + 5,
                fill='red' if i == self.selected_vertex else 'white',
                outline='black',
                width=2,
                tags=('vertex', f'vertex_{i}')
            )
            self.vertex_handles.append(handle)

        # Bring handles to front
        for handle in self.vertex_handles:
            self.canvas.tag_raise(handle)

    def _on_canvas_click(self, event):
        """Handle canvas click for vertex selection or edge insertion."""
        if not self.drawing_mode:
            return

        x, y = event.x, event.y

        # Check if clicking on a vertex
        vertex_idx = self._find_vertex_at(x, y)
        if vertex_idx is not None:
            # Select vertex for dragging
            self.selected_vertex = vertex_idx
            self._dragging_vertex = True
            self._redraw_polygon()
            return

        # Check if clicking on an edge to insert a new vertex
        edge_idx = self._find_edge_at(x, y)
        if edge_idx is not None:
            # Insert a new vertex on this edge
            self._insert_vertex_on_edge(edge_idx, x, y)
            return

    def _on_canvas_drag(self, event):
        """Handle canvas drag for moving vertices."""
        if not self.drawing_mode or not self._dragging_vertex:
            return

        if self.selected_vertex is not None:
            # Update vertex position
            self.polygon_vertices[self.selected_vertex] = (event.x, event.y)
            self._redraw_polygon()

    def _on_canvas_release(self, _event):
        """Handle canvas release to stop dragging."""
        if self._dragging_vertex:
            self._dragging_vertex = False

    def _on_canvas_right_click(self, event):
        """Handle right-click (Ctrl+click) to delete a vertex."""
        if not self.drawing_mode:
            return

        x, y = event.x, event.y
        vertex_idx = self._find_vertex_at(x, y)

        if vertex_idx is not None:
            # Don't allow deleting if we'd have fewer than 3 vertices
            if len(self.polygon_vertices) <= 3:
                self._log_warning("Cannot delete vertex - minimum 3 vertices required")
                return

            # Delete the vertex
            del self.polygon_vertices[vertex_idx]
            if self.selected_vertex == vertex_idx:
                self.selected_vertex = None
            elif self.selected_vertex is not None and self.selected_vertex > vertex_idx:
                self.selected_vertex -= 1

            self._redraw_polygon()
            self._log_info(f"Deleted vertex {vertex_idx + 1}")

    def _find_vertex_at(self, x, y, threshold=10):
        """Find if there's a vertex near the given coordinates."""
        for i, (vx, vy) in enumerate(self.polygon_vertices):
            dist = ((x - vx) ** 2 + (y - vy) ** 2) ** 0.5
            if dist <= threshold:
                return i
        return None

    def _find_edge_at(self, x, y, threshold=10):
        """Find if clicking near an edge (for inserting vertices)."""
        if len(self.polygon_vertices) < 2:
            return None

        for i in range(len(self.polygon_vertices)):
            p1 = self.polygon_vertices[i]
            p2 = self.polygon_vertices[(i + 1) % len(self.polygon_vertices)]

            # Calculate distance from point to line segment
            dist = self._point_to_segment_distance(x, y, p1[0], p1[1], p2[0], p2[1])
            if dist <= threshold:
                return i

        return None

    def _point_to_segment_distance(self, px, py, x1, y1, x2, y2):
        """Calculate the distance from a point to a line segment."""
        # Vector from p1 to p2
        dx = x2 - x1
        dy = y2 - y1

        if dx == 0 and dy == 0:
            # Segment is a point
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5

        # Parameter t of the projection of point onto the line
        t = max(0, min(1, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))

        # Closest point on the segment
        closest_x = x1 + t * dx
        closest_y = y1 + t * dy

        # Distance from point to closest point
        return ((px - closest_x) ** 2 + (py - closest_y) ** 2) ** 0.5

    def _insert_vertex_on_edge(self, edge_idx, x, y):
        """Insert a new vertex on the specified edge."""
        # Maximum vertex limit
        if len(self.polygon_vertices) >= 15:
            self._log_warning("Maximum 15 vertices allowed")
            return

        # Insert the new vertex after edge_idx
        self.polygon_vertices.insert(edge_idx + 1, (x, y))
        self.selected_vertex = edge_idx + 1
        self._redraw_polygon()
        self._log_info(f"Added vertex at edge {edge_idx + 1}")

    def _draw_grid(self):
        """Draw a grid on the canvas based on project units."""
        # Get canvas dimensions
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        # Grid spacing in pixels (e.g., 50 pixels per unit)
        # This will be configurable based on project units in the future
        grid_spacing = 50 * self.canvas_zoom

        # Don't draw grid if too zoomed out (would be too dense)
        if grid_spacing < 10:
            return

        # Draw vertical lines
        x = 0
        while x < width:
            self.canvas.create_line(
                x, 0, x, height,
                fill='#cccccc',
                tags='grid'
            )
            x += grid_spacing

        # Draw horizontal lines
        y = 0
        while y < height:
            self.canvas.create_line(
                0, y, width, y,
                fill='#cccccc',
                tags='grid'
            )
            y += grid_spacing

        # Send grid to back
        self.canvas.tag_lower('grid')

        # Update rulers
        self._update_rulers()

    def _calculate_tick_interval(self, visible_range):
        """Calculate an appropriate tick interval to show ~15 ticks.

        Args:
            visible_range: The visible range in units (feet or meters)

        Returns:
            A nice round number for tick spacing
        """
        # Target around 15 ticks
        target_ticks = 15
        raw_interval = visible_range / target_ticks

        # Nice intervals to choose from
        nice_intervals = [
            0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000
        ]

        # Find the closest nice interval
        best_interval = nice_intervals[0]
        for interval in nice_intervals:
            if interval >= raw_interval:
                best_interval = interval
                break
        else:
            best_interval = nice_intervals[-1]

        return best_interval

    def _draw_origin_marker(self):
        """Draw a fixed-size origin marker at (0,0) that doesn't scale with zoom."""
        # Get canvas center (which represents 0,0 in project coordinates)
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width / 2
        center_y = height / 2

        # Calculate the screen position of origin accounting for pan
        origin_screen_x = center_x + self.canvas_pan_x
        origin_screen_y = center_y + self.canvas_pan_y

        # Fixed marker size in pixels (doesn't change with zoom)
        marker_size = 10

        # Delete old origin marker
        self.canvas.delete('origin_marker')

        # Draw new origin marker
        self.canvas.create_line(
            origin_screen_x - marker_size, origin_screen_y,
            origin_screen_x + marker_size, origin_screen_y,
            fill='#e74c3c', width=2, tags='origin_marker'
        )
        self.canvas.create_line(
            origin_screen_x, origin_screen_y - marker_size,
            origin_screen_x, origin_screen_y + marker_size,
            fill='#e74c3c', width=2, tags='origin_marker'
        )

    def _update_rulers(self):
        """Update the ruler markings based on current zoom and pan."""
        # Clear existing rulers
        self.ruler_top.delete('all')
        self.ruler_left.delete('all')

        # Redraw origin marker with updated position
        self._draw_origin_marker()

        # Redraw project rectangle if we're viewing a project
        if self.selected_item and not self.drawing_mode:
            item_values = self.tree.item(self.selected_item, 'values')
            if item_values and len(item_values) > 0 and item_values[0] == 'project':
                if len(item_values) > 4:
                    project_width_str = item_values[3]
                    project_length_str = item_values[4]
                    if project_width_str and project_length_str:
                        try:
                            project_width = float(project_width_str)
                            project_length = float(project_length_str)
                            if project_width > 0 and project_length > 0:
                                self._redraw_project_rectangle(project_width, project_length)
                        except (ValueError, IndexError):
                            pass

        # Get dimensions
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        ruler_top_width = self.ruler_top.winfo_width()
        ruler_left_height = self.ruler_left.winfo_height()

        # Pixels per unit (50 pixels = 1 unit at zoom 1.0)
        pixels_per_unit = 50 * self.canvas_zoom

        # Calculate visible range in units
        visible_width_units = canvas_width / pixels_per_unit
        visible_height_units = canvas_height / pixels_per_unit

        # Calculate appropriate tick intervals
        h_interval = self._calculate_tick_interval(visible_width_units)
        v_interval = self._calculate_tick_interval(visible_height_units)

        # Draw top ruler (horizontal)
        # Draw background
        self.ruler_top.create_rectangle(0, 0, ruler_top_width, 25, fill='#e8e8e8', outline='#999999')

        # Canvas center represents (0,0) in project coordinates
        canvas_center_x = canvas_width / 2

        # Ruler top includes 40px offset for the left ruler
        ruler_offset_x = 40

        # Calculate starting position accounting for pan
        # Position 0 should be at canvas_center + pan_x
        start_unit = -(canvas_center_x + self.canvas_pan_x) / pixels_per_unit

        # Round down to nearest interval
        first_tick = int(start_unit / h_interval) * h_interval

        # Draw ticks
        current_tick = first_tick
        while True:
            # Calculate screen position for this tick on the ruler (offset by 40px)
            x_pos = (current_tick * pixels_per_unit) + canvas_center_x + self.canvas_pan_x + ruler_offset_x
            if x_pos > ruler_top_width:
                break
            if x_pos >= ruler_offset_x:  # Don't draw in the corner reserved for ruler_left
                # Draw tick mark
                self.ruler_top.create_line(x_pos, 20, x_pos, 25, fill='#333333', width=2)
                # Format label based on interval (avoid unnecessary decimals)
                if h_interval >= 1:
                    label = str(int(current_tick))
                else:
                    label = f"{current_tick:.1f}"
                self.ruler_top.create_text(x_pos, 10, text=label, font=("Arial", 8), fill='#333333')
            current_tick += h_interval

        # Draw left ruler (vertical)
        # Draw background
        self.ruler_left.create_rectangle(0, 0, 40, ruler_left_height, fill='#e8e8e8', outline='#999999')

        # Canvas center represents (0,0) in project coordinates
        canvas_center_y = canvas_height / 2

        # Ruler left is vertically aligned with canvas (no offset needed)
        # Both start below the top ruler

        # Calculate starting position accounting for pan
        # Position 0 should be at canvas_center + pan_y
        start_unit = -(canvas_center_y + self.canvas_pan_y) / pixels_per_unit

        # Round down to nearest interval
        first_tick = int(start_unit / v_interval) * v_interval

        # Draw ticks
        current_tick = first_tick
        while True:
            # Calculate screen position for this tick on the ruler
            y_pos = (current_tick * pixels_per_unit) + canvas_center_y + self.canvas_pan_y
            if y_pos > ruler_left_height:
                break
            if y_pos >= 0:
                # Draw tick mark
                self.ruler_left.create_line(35, y_pos, 40, y_pos, fill='#333333', width=2)
                # Format label based on interval (avoid unnecessary decimals)
                if v_interval >= 1:
                    label = str(int(current_tick))
                else:
                    label = f"{current_tick:.1f}"
                self.ruler_left.create_text(18, y_pos, text=label, font=("Arial", 8), fill='#333333')
            current_tick += v_interval

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
