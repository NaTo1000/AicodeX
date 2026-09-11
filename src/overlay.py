"""
Overlay window implementation for AicodeX
Creates a transparent overlay that stays on top of other windows
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
import platform

from assistant import AssistantEngine
from interaction import InteractionController


class OverlayWindow:
    """Main overlay window for AicodeX"""
    
    def __init__(self, config, hotkey_manager):
        """Initialize the overlay window"""
        self.config = config
        self.hotkey_manager = hotkey_manager
        self.assistant_engine = AssistantEngine.from_config(config.settings)
        self.interaction = InteractionController.from_config(
            self.assistant_engine, config.settings
        )
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
        
        # Assistant (persona & analysis) tab
        assistant_frame = ttk.Frame(notebook, padding="5")
        notebook.add(assistant_frame, text="Assistant")
        self.create_assistant_tab(assistant_frame)
        
        # Voice & Chat tab
        interaction_frame = ttk.Frame(notebook, padding="5")
        notebook.add(interaction_frame, text="Voice & Chat")
        self.create_interaction_tab(interaction_frame)
        
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
            
    def create_assistant_tab(self, parent):
        """Create the Assistant Persona & Analysis tab"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        persona = self.assistant_engine.persona
        ttk.Label(
            frame,
            text=f"Assistant: {persona.name} (tone: {persona.tone})",
            font=("Arial", 10, "bold"),
        ).pack(anchor=tk.W, pady=(0, 5))

        # Persona trait (graphical personality) read-out
        traits = ", ".join(
            f"{axis}={value:.2f}" for axis, value in persona.dominant_traits()
        ) or "none"
        ttk.Label(frame, text=f"Persona traits: {traits}", wraplength=360).pack(
            anchor=tk.W, pady=(0, 8)
        )

        ttk.Label(frame, text="Ask the assistant:").pack(anchor=tk.W)
        self.assistant_input = ttk.Entry(frame)
        self.assistant_input.pack(fill=tk.X, pady=(2, 4))
        self.assistant_input.bind("<Return>", lambda _e: self.run_assistant())

        ttk.Button(frame, text="Analyze", command=self.run_assistant).pack(
            fill=tk.X, pady=(0, 6)
        )

        self.assistant_output = scrolledtext.ScrolledText(frame, height=14, wrap=tk.WORD)
        self.assistant_output.pack(fill=tk.BOTH, expand=True)
        self.assistant_output.insert(
            tk.END,
            "Type a question and press Analyze. The engine will profile the "
            "incoming data against graphical personality types, match a "
            "performance solution (or explain why none fits), and show the "
            "TWINBRAIN + CCC.Ai council's justified decision.",
        )
        self.assistant_output.config(state=tk.DISABLED)

    def run_assistant(self):
        """Analyze the input and render the assistant report."""
        question = self.assistant_input.get().strip()
        if not question:
            return
        report = self.assistant_engine.process(question)
        self.assistant_output.config(state=tk.NORMAL)
        self.assistant_output.delete("1.0", tk.END)
        self.assistant_output.insert(tk.END, report.summary())
        self.assistant_output.config(state=tk.DISABLED)

    def create_interaction_tab(self, parent):
        """Create the Voice & Chat tab (chat, voice commands, interludes, sandbox)."""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        ttk.Label(frame, text="Chat & Voice Commands", font=("Arial", 10, "bold")).pack(
            anchor=tk.W, pady=(0, 5)
        )

        # Conversation / output log
        self.interaction_log = scrolledtext.ScrolledText(frame, height=12, wrap=tk.WORD)
        self.interaction_log.pack(fill=tk.BOTH, expand=True)
        self.interaction_log.config(state=tk.DISABLED)
        self._interaction_append(
            "system",
            "Chat with the assistant, or use a voice command. Try 'help', "
            "'analyze <text>', 'preview <code>', 'interlude <topic>'.",
        )

        # Input row
        input_row = ttk.Frame(frame)
        input_row.pack(fill=tk.X, pady=(6, 4))
        self.interaction_input = ttk.Entry(input_row)
        self.interaction_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.interaction_input.bind("<Return>", lambda _e: self.run_chat())

        # Button row
        buttons = ttk.Frame(frame)
        buttons.pack(fill=tk.X)
        ttk.Button(buttons, text="Send", command=self.run_chat).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(buttons, text="Voice Command", command=self.run_voice).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Interlude", command=self.toggle_interlude).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Preview", command=self.run_preview).pack(side=tk.LEFT, padx=4)

    def _interaction_append(self, role, text):
        self.interaction_log.config(state=tk.NORMAL)
        self.interaction_log.insert(tk.END, f"{role}: {text}\n\n")
        self.interaction_log.see(tk.END)
        self.interaction_log.config(state=tk.DISABLED)

    def run_chat(self):
        """Send the typed input as a chat message through the assistant engine."""
        text = self.interaction_input.get().strip()
        if not text:
            return
        self.interaction_input.delete(0, tk.END)
        self._interaction_append("you", text)
        reply = self.interaction.chat(text)
        self._interaction_append("assistant", reply)

    def run_voice(self):
        """Treat the typed input as a spoken voice command."""
        utterance = self.interaction_input.get().strip()
        if not utterance:
            return
        self.interaction_input.delete(0, tk.END)
        self._interaction_append("voice", utterance)
        response = self.interaction.handle_voice(utterance)
        self._interaction_append("assistant", response)

    def toggle_interlude(self):
        """Start a brainstorming interlude, or end the active one."""
        if self.interaction.interludes.active:
            result = self.interaction.end_interlude()
        else:
            topic = self.interaction_input.get().strip() or "brainstorm"
            self.interaction_input.delete(0, tk.END)
            result = self.interaction.start_interlude(topic)
        self._interaction_append("system", result)

    def run_preview(self):
        """Run the typed input as a sandboxed code snippet preview."""
        code = self.interaction_input.get().strip()
        if not code:
            return
        self.interaction_input.delete(0, tk.END)
        self._interaction_append("you", f"[preview] {code}")
        result = self.interaction.preview(code)
        self._interaction_append("sandbox", result.summary())

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
