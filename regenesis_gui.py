import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from regenesis import Regenesis


class RegenesisGUI:
    """GUI class for the Regenesis application."""

    def __init__(self):
        import time

        # Create main window first (but hidden)
        self.root = tk.Tk()

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
        self.root.geometry("1000x700")
        self.current_file = None  # Track the currently open file
        self.selected_item = None  # Track selected tree item
        self._updating_properties = False  # Flag to prevent update loops
        self._drag_item = None  # Track item being dragged
        self._drop_target = None  # Track current drop target
        self._drop_position = None  # Track drop position: 'above', 'below', or 'inside'

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
        splash.update_idletasks()
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")

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

        # Design tree section
        tree_label = tk.Label(left_panel, text="Design Structure", font=("Arial", 12, "bold"))
        tree_label.pack(pady=(5, 0))

        # Scrollable tree
        tree_frame = tk.Frame(left_panel)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5)

        tree_scroll = tk.Scrollbar(tree_frame)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(tree_frame, yscrollcommand=tree_scroll.set, height=15)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)


        # Configure tree item styles - make design largest, regions bold
        style = ttk.Style()
        style.configure("Treeview", font=("Arial", 10))
        self.tree.tag_configure('design', font=("Arial", 14, "bold"))
        self.tree.tag_configure('region', font=("Arial", 11, "bold"))

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

        # Populate with sample data
        self._populate_sample_tree()

        # DEFINITIONS PANEL (below tree)
        definitions_frame = tk.LabelFrame(left_panel, text="Properties", relief=tk.GROOVE, borderwidth=2)
        definitions_frame.pack(fill=tk.BOTH, padx=5, pady=5)

        # Name field
        tk.Label(definitions_frame, text="Name:", font=("Arial", 10)).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.name_var = tk.StringVar()
        self.name_entry = tk.Entry(definitions_frame, textvariable=self.name_var, width=20)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_entry.bind('<Return>', lambda _: self._apply_name_change())
        self.name_entry.bind('<FocusOut>', lambda _: self._apply_name_change())

        # Uhab type selector
        tk.Label(definitions_frame, text="Uhab Type:", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.uhab_type_var = tk.StringVar(value="(none)")

        # Use OptionMenu instead of Combobox for better cross-platform behavior
        self.uhab_dropdown = tk.OptionMenu(
            definitions_frame,
            self.uhab_type_var,
            "(none)", "Meadow", "Layered", "Pond", "Stream",
            command=lambda _: self._apply_uhab_type_change()
        )
        self.uhab_dropdown.config(width=15)
        self.uhab_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        # RIGHT PANEL - Workspace
        workspace_frame = tk.Frame(main_container, relief=tk.SUNKEN, borderwidth=1, bg='white')
        main_container.add(workspace_frame, minsize=400)

        # Workspace label
        tk.Label(workspace_frame, text="Workspace", font=("Arial", 14, "bold"), bg='white').pack(pady=10)

        # Canvas for visualization
        self.canvas = tk.Canvas(workspace_frame, bg='#f0f0f0', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Initial message
        self.canvas_text = self.canvas.create_text(
            400, 300,
            text="Select an item from the design tree",
            font=("Arial", 16),
            fill="#999999"
        )

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
                self.app.load_from_file(filepath)
                self.current_file = filepath
                self._update_title()
                messagebox.showinfo("Project Opened", f"Loaded: {os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open project:\n{str(e)}")

    def _save_project(self):
        """Save the current project."""
        if self.current_file:
            try:
                self.app.save_to_file(self.current_file)
                messagebox.showinfo("Project Saved", f"Saved: {os.path.basename(self.current_file)}")
            except Exception as e:
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
                self.app.save_to_file(filepath)
                self.current_file = filepath
                self._update_title()
                messagebox.showinfo("Project Saved", f"Saved as: {os.path.basename(filepath)}")
            except Exception as e:
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
        """Show preferences dialog (placeholder for macOS)."""
        messagebox.showinfo("Preferences", "Preferences dialog not yet implemented.")

    def _populate_sample_tree(self):
        """Populate the tree with sample design structure."""
        # Root node - the design itself
        root = self.tree.insert('', 'end', text='Smith Residence', values=('design',), open=True, tags=('design',))

        # Front yard - meadow uhab
        self.tree.insert(root, 'end', text='Front Yard', values=('Meadow',))

        # Side yard - layered uhab
        self.tree.insert(root, 'end', text='Side Yard', values=('Layered',))

        # Backyard - container region
        backyard = self.tree.insert(root, 'end', text='Backyard', values=('region',), open=True, tags=('region',))

        # Backyard children
        self.tree.insert(backyard, 'end', text='Pond', values=('Pond',))
        self.tree.insert(backyard, 'end', text='Layered Area 1', values=('Layered',))
        self.tree.insert(backyard, 'end', text='Layered Area 2', values=('Layered',))

    def _on_tree_select(self, event):
        """Handle tree selection event."""
        selection = self.tree.selection()
        if not selection:
            return

        item = selection[0]
        self.selected_item = item

        # Get item details
        item_text = self.tree.item(item, 'text')
        item_values = self.tree.item(item, 'values')

        # Update properties panel
        self._updating_properties = True
        self.name_var.set(item_text)

        if item_values:
            uhab_type = item_values[0]
            if uhab_type == 'design':
                self.uhab_type_var.set("(none)")
            elif uhab_type == 'region':
                self.uhab_type_var.set("(none)")
            else:
                self.uhab_type_var.set(uhab_type)
        self._updating_properties = False

        # Update workspace canvas
        self._update_workspace(item_text, item_values[0] if item_values else 'unknown')

    def _apply_uhab_type_change(self):
        """Apply the uhab type change to the selected item."""
        if not self.selected_item:
            return

        new_type = self.uhab_type_var.get()

        # Update the tree item's values
        if new_type == "(none)":
            self.tree.item(self.selected_item, values=('region',), tags=('region',))
            actual_type = 'region'
        else:
            self.tree.item(self.selected_item, values=(new_type,), tags=())
            actual_type = new_type

        # Update the workspace to reflect the change
        item_text = self.tree.item(self.selected_item, 'text')
        self._update_workspace(item_text, actual_type)

    def _update_workspace(self, name, uhab_type):
        """Update the workspace canvas to display the selected item."""
        # Clear canvas
        self.canvas.delete('all')

        # Get canvas dimensions
        self.canvas.update_idletasks()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        center_x = width / 2
        center_y = height / 2

        # Display the uhab name
        if uhab_type == 'design':
            text = f"Design: {name}"
            color = "#2c3e50"
        elif uhab_type == 'region':
            text = f"Region: {name}"
            color = "#7f8c8d"
        else:
            text = f"{uhab_type} Uhab\n{name}"
            color = "#27ae60"

        self.canvas.create_text(
            center_x, center_y,
            text=text,
            font=("Arial", 20, "bold"),
            fill=color,
            justify=tk.CENTER
        )

        # Add uhab type indicator
        if uhab_type not in ['design', 'region', 'unknown']:
            self.canvas.create_text(
                center_x, center_y + 50,
                text=f"Type: {uhab_type}",
                font=("Arial", 12),
                fill="#95a5a6"
            )

    def _apply_name_change(self):
        """Apply the name change to the selected tree item."""
        if not self.selected_item or self._updating_properties:
            return

        new_name = self.name_var.get().strip()
        if new_name:
            self.tree.item(self.selected_item, text=new_name)

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
            menu.add_command(label="Add Child Uhab", command=self._add_child_uhab)
            menu.add_separator()
            menu.add_command(label="Delete", command=self._delete_item)

            # Show menu at cursor position
            menu.post(event.x_root, event.y_root)

    def _add_child_region(self):
        """Add a new child region to the selected item."""
        if not self.selected_item:
            return

        # Insert a new container region
        new_region = self.tree.insert(self.selected_item, 'end', text='New Region', values=('region',), tags=('region',))
        self.tree.item(self.selected_item, open=True)  # Expand parent
        self.tree.selection_set(new_region)
        self.tree.see(new_region)

    def _add_child_uhab(self):
        """Add a new child uhab to the selected item."""
        if not self.selected_item:
            return

        # Check if selected item is a uhab (not 'design' or 'region')
        item_values = self.tree.item(self.selected_item, 'values')
        if item_values and item_values[0] not in ('design', 'region'):
            # Selected item is a uhab - add the new uhab as a sibling instead
            parent = self.tree.parent(self.selected_item)
            if not parent:
                messagebox.showwarning("Cannot Add", "Cannot add uhab here.")
                return
            target_parent = parent
        else:
            # Selected item is design or region - add as child
            target_parent = self.selected_item

        # Show a simple dialog to select uhab type
        uhab_type = self._ask_uhab_type()
        if uhab_type:
            new_uhab = self.tree.insert(target_parent, 'end', text=f'New {uhab_type}', values=(uhab_type,))
            self.tree.item(target_parent, open=True)  # Expand parent
            self.tree.selection_set(new_uhab)
            self.tree.see(new_uhab)

    def _ask_uhab_type(self):
        """Show dialog to select uhab type."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select Uhab Type")
        dialog.geometry("300x320")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 300) // 2
        y = (dialog.winfo_screenheight() - 320) // 2
        dialog.geometry(f"300x320+{x}+{y}")

        result = {'type': None}

        # Handle window close button
        dialog.protocol("WM_DELETE_WINDOW", lambda: dialog.destroy())

        tk.Label(dialog, text="Select Uhab Type:", font=("Arial", 12)).pack(pady=15)

        uhab_types = ["Meadow", "Layered", "Pond", "Stream"]
        for uhab_type in uhab_types:
            btn = tk.Button(
                dialog,
                text=uhab_type,
                width=15,
                command=lambda t=uhab_type: [result.update({'type': t}), dialog.destroy()]
            )
            btn.pack(pady=5)

        # Add Cancel button
        cancel_btn = tk.Button(
            dialog,
            text="Cancel",
            width=15,
            command=dialog.destroy
        )
        cancel_btn.pack(pady=10)

        # Make sure dialog appears and is responsive
        dialog.update()
        dialog.deiconify()
        dialog.wait_window()
        return result['type']

    def _delete_item(self):
        """Delete the selected item with confirmation."""
        if not self.selected_item:
            return

        # Check if this is the root design
        if not self.tree.parent(self.selected_item):
            messagebox.showwarning("Cannot Delete", "Cannot delete the root design.")
            return

        # Check if item has children
        children = self.tree.get_children(self.selected_item)
        item_text = self.tree.item(self.selected_item, 'text')

        if children:
            # Item has children
            message = f"Warning: '{item_text}' will be removed with lower microhabitats and/or regions."
            title = "Confirm Delete"
        else:
            # Empty item
            message = f"Warning: '{item_text}' will be removed from your design."
            title = "Confirm Delete"

        # Create custom dialog with Proceed and Cancel buttons
        if self._show_delete_confirmation(title, message):
            # User clicked Proceed
            parent = self.tree.parent(self.selected_item)
            self.tree.delete(self.selected_item)
            self.selected_item = None
            # Select parent if it exists
            if parent:
                self.tree.selection_set(parent)

    def _show_delete_confirmation(self, title, message):
        """Show custom delete confirmation dialog with Proceed and Cancel buttons."""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.geometry("400x150")
        dialog.transient(self.root)
        dialog.grab_set()

        # Center the dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 150) // 2
        dialog.geometry(f"400x150+{x}+{y}")

        result = {'proceed': False}

        # Message
        tk.Label(dialog, text=message, wraplength=350, font=("Arial", 11)).pack(pady=20)

        # Button frame
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)

        # Proceed button
        proceed_btn = tk.Button(
            btn_frame,
            text="Proceed",
            width=10,
            command=lambda: [result.update({'proceed': True}), dialog.destroy()]
        )
        proceed_btn.pack(side=tk.LEFT, padx=10)

        # Cancel button
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            width=10,
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)

        dialog.wait_window()
        return result['proceed']

    def _on_drag_start(self, event):
        """Handle start of drag operation."""
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
            # Middle half - drop inside (only for regions and design)
            if drag_type == 'region' and target_type in ('design', 'region'):
                self._drop_position = 'inside'
                self._drop_target = target
                self.tree.selection_set(target)
                self.tree.config(cursor='hand2')
            elif drag_type not in ('design', 'region') and target_type in ('design', 'region'):
                # Uhabs can be dropped inside regions/design
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

        # Use the drop target and position determined during drag motion
        if self._drop_target and self._drop_position:
            target = self._drop_target
            position = self._drop_position

            # Don't allow dropping root design
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

    def run(self):
        """Start the GUI application."""
        self.root.mainloop()
