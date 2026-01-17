"""
Overlay window implementation for AicodeX
Creates a transparent overlay that stays on top of other windows
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import platform


class OverlayWindow:
    """Main overlay window for AicodeX"""
    
    def __init__(self, config, hotkey_manager):
        """Initialize the overlay window"""
        self.config = config
        self.hotkey_manager = hotkey_manager
        self.root = tk.Tk()
        self.visible = True
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Configure the main window properties"""
        self.root.title("AicodeX - Code Companion")
        
        # Get window settings from config
        settings = self.config.get('window', {})
        width = settings.get('width', 400)
        height = settings.get('height', 600)
        x_pos = settings.get('x_position', 100)
        y_pos = settings.get('y_position', 100)
        
        self.root.geometry(f"{width}x{height}+{x_pos}+{y_pos}")
        
        # Set window properties for overlay
        opacity = settings.get('opacity', 0.95)
        self.root.attributes('-alpha', opacity)
        self.root.attributes('-topmost', True)
        
        # Set window style (Windows-specific)
        if platform.system() == 'Windows':
            try:
                self.root.attributes('-toolwindow', True)
            except tk.TclError:
                pass
        
        # Bind hotkey manager callbacks
        self.hotkey_manager.set_toggle_callback(self.toggle_visibility)
        
    def create_widgets(self):
        """Create the UI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title label
        title_label = ttk.Label(
            main_frame,
            text="AicodeX Code Companion",
            font=("Arial", 14, "bold")
        )
        title_label.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Code snippets tab
        snippets_frame = ttk.Frame(notebook, padding="5")
        notebook.add(snippets_frame, text="Snippets")
        self.create_snippets_tab(snippets_frame)
        
        # Quick actions tab
        actions_frame = ttk.Frame(notebook, padding="5")
        notebook.add(actions_frame, text="Actions")
        self.create_actions_tab(actions_frame)
        
        # Settings tab
        settings_frame = ttk.Frame(notebook, padding="5")
        notebook.add(settings_frame, text="Settings")
        self.create_settings_tab(settings_frame)
        
        # Configure grid weights for resizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
    def create_snippets_tab(self, parent):
        """Create the code snippets tab"""
        # Snippet list
        list_frame = ttk.Frame(parent)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        snippets = self.config.get('snippets', [])
        
        ttk.Label(list_frame, text="Code Snippets:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 5))
        
        # Scrolled text for displaying snippets
        snippet_text = scrolledtext.ScrolledText(list_frame, height=15, wrap=tk.WORD)
        snippet_text.pack(fill=tk.BOTH, expand=True)
        
        # Add default snippets
        if not snippets:
            snippet_text.insert(tk.END, "# Python Function Template\n")
            snippet_text.insert(tk.END, "def function_name(param):\n")
            snippet_text.insert(tk.END, "    \"\"\"Docstring\"\"\"\n")
            snippet_text.insert(tk.END, "    pass\n\n")
            
            snippet_text.insert(tk.END, "# JavaScript Function Template\n")
            snippet_text.insert(tk.END, "function functionName(param) {\n")
            snippet_text.insert(tk.END, "    // Comment\n")
            snippet_text.insert(tk.END, "    return value;\n")
            snippet_text.insert(tk.END, "}\n")
        else:
            for snippet in snippets:
                snippet_text.insert(tk.END, f"# {snippet.get('name', 'Unnamed')}\n")
                snippet_text.insert(tk.END, f"{snippet.get('code', '')}\n\n")
        
    def create_actions_tab(self, parent):
        """Create the quick actions tab"""
        actions_frame = ttk.Frame(parent)
        actions_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(actions_frame, text="Quick Actions:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Add action buttons
        actions = [
            ("Check HandBrake Version", self.check_handbrake),
            ("Format Code", lambda: self.show_message("Format code action")),
            ("Generate Docstring", lambda: self.show_message("Generate docstring action")),
            ("Refactor Selection", lambda: self.show_message("Refactor action")),
        ]
        
        for action_name, action_func in actions:
            btn = ttk.Button(actions_frame, text=action_name, command=action_func)
            btn.pack(fill=tk.X, pady=2)
            
    def create_settings_tab(self, parent):
        """Create the settings tab"""
        settings_frame = ttk.Frame(parent)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        ttk.Label(settings_frame, text="Settings:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Opacity control
        opacity_frame = ttk.Frame(settings_frame)
        opacity_frame.pack(fill=tk.X, pady=5)
        ttk.Label(opacity_frame, text="Opacity:").pack(side=tk.LEFT)
        
        opacity_var = tk.DoubleVar(value=self.config.get('window', {}).get('opacity', 0.95) * 100)
        opacity_scale = ttk.Scale(
            opacity_frame,
            from_=50,
            to=100,
            variable=opacity_var,
            orient=tk.HORIZONTAL,
            command=lambda v: self.set_opacity(float(v) / 100)
        )
        opacity_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Hotkeys display
        ttk.Label(settings_frame, text="Hotkeys:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        hotkeys = self.config.get('hotkeys', {})
        hotkeys_text = scrolledtext.ScrolledText(settings_frame, height=8, wrap=tk.WORD)
        hotkeys_text.pack(fill=tk.BOTH, expand=True)
        
        for action, hotkey in hotkeys.items():
            hotkeys_text.insert(tk.END, f"{action}: {hotkey}\n")
        
        hotkeys_text.config(state=tk.DISABLED)
        
    def toggle_visibility(self):
        """Toggle overlay visibility"""
        if self.visible:
            self.root.withdraw()
            self.visible = False
        else:
            self.root.deiconify()
            self.visible = True
            
    def set_opacity(self, value):
        """Set window opacity"""
        self.root.attributes('-alpha', value)
        
    def check_handbrake(self):
        """Check HandBrake version"""
        from utils.handbrake_checker import HandBrakeChecker
        checker = HandBrakeChecker()
        result = checker.check_version()
        self.show_message(result)
        
    def show_message(self, message):
        """Show a message dialog"""
        msg_window = tk.Toplevel(self.root)
        msg_window.title("AicodeX")
        msg_window.geometry("300x100")
        msg_window.attributes('-topmost', True)
        
        ttk.Label(msg_window, text=message, wraplength=280).pack(pady=20)
        ttk.Button(msg_window, text="OK", command=msg_window.destroy).pack()
        
    def run(self):
        """Start the overlay application"""
        self.root.mainloop()
