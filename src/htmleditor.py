#!/usr/bin/env python3
import sys
import gi
import re
import os

# Hardware Acclerated Rendering (0); Software Rendering (1)
os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '0'

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gdk, WebKit, GLib, Gio

class HTMLEditorWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
        self.set_default_size(900, 700)
        self.set_title("Untitled - HTML Editor")
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_vexpand(True)  # Ensure main_box expands vertically
        self.main_box.set_hexpand(True)
        self.create_header_bar()
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        #content_box.set_vexpand(True)
        #content_box.set_hexpand(True) 
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True) 
        self.webview.load_html(self.get_editor_html(), None)
        settings = self.webview.get_settings()
        try:
            settings.set_enable_developer_extras(True)
        except:
            pass
        
        try:
            user_content_manager = self.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("contentChanged")
            user_content_manager.connect("script-message-received::contentChanged", 
                                        self.on_content_changed)
        except:
            print("Warning: Could not set up JavaScript message handlers")
            
        self.webview.load_html(self.get_initial_html(), None)
        
        self.statusbar = Gtk.Label(label="Ready")
        self.statusbar.set_halign(Gtk.Align.START)
        self.statusbar.set_margin_start(10)
        self.statusbar.set_margin_end(10)
        self.statusbar.set_margin_top(5)
        self.statusbar.set_margin_bottom(5)
        
        self.bottom_toolbar = self.create_bottom_toolbar()
        self.bottom_toolbar.set_visible(False)
        
        content_box.append(self.webview)
        content_box.append(self.bottom_toolbar)
        content_box.append(self.statusbar)
        
        self.main_box.append(content_box)
        self.set_content(self.main_box)
        
        self.setup_toolbar_animation()

        self.setup_keyboard_shortcuts()
        self.connect("close-request", self.on_close_request)
    
    def on_close_request(self, *args):
        app = self.get_application()
        if app:
            # Before removing this window, store its index
            window_index = app.windows.index(self) if self in app.windows else -1
            
            # Remove window from tracking list
            if self in app.windows:
                app.windows.remove(self)
                
            # Update all window menus
            app.update_window_menu()
            
            # If there are remaining windows, present the next one
            if app.windows and window_index >= 0:
                # Present the next window in sequence, or the last one if this was the last
                next_index = min(window_index, len(app.windows) - 1)
                app.windows[next_index].present()
                
        return False
        
    def get_menu_title(self):
        if self.current_file:
            # Get the path as a string
            if hasattr(self.current_file, 'get_path'):
                path = self.current_file.get_path()
            else:
                path = self.current_file
            # Extract filename without extension and show modified marker
            filename = os.path.splitext(os.path.basename(path))[0]
            return f"{filename}{'*' if self.modified else ''}"
        else:
            return f"Untitled{'*' if self.modified else ''}"
        
    def create_header_bar(self):
        # Create a header bar
        header = Adw.HeaderBar()
        
        # Create buttons for header bar
        new_button = Gtk.Button(icon_name="document-new-symbolic")
        new_button.set_tooltip_text("New Document in New Window")
        new_button.connect("clicked", self.on_new_clicked)
        
        open_button = Gtk.Button(icon_name="document-open-symbolic")
        open_button.set_tooltip_text("Open File in New Window")
        open_button.connect("clicked", self.on_open_clicked)
        
        save_button = Gtk.Button(icon_name="document-save-symbolic")
        save_button.set_tooltip_text("Save File")
        save_button.connect("clicked", self.on_save_clicked)
        
        # Create undo/redo buttons
        self.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        self.undo_button.set_tooltip_text("Undo")
        self.undo_button.connect("clicked", self.on_undo_clicked)
        self.undo_button.set_sensitive(False)  # Initially disabled
        
        self.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        self.redo_button.set_tooltip_text("Redo")
        self.redo_button.connect("clicked", self.on_redo_clicked)
        self.redo_button.set_sensitive(False)  # Initially disabled
        
        # Create menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("Preferences", "app.preferences")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        
        menu_button.set_menu_model(menu)
        
        # Add buttons to header bar
        header.pack_start(new_button)
        header.pack_start(open_button)
        header.pack_start(save_button)
        header.pack_start(self.undo_button)
        header.pack_start(self.redo_button)
        header.pack_end(menu_button)
        
        self.main_box.append(header)

    
    def create_bottom_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
        # Add some HTML editing buttons
        bold_button = Gtk.Button(icon_name="format-text-bold-symbolic")
        bold_button.set_tooltip_text("Bold")
        bold_button.connect("clicked", self.on_bold_clicked)
        
        italic_button = Gtk.Button(icon_name="format-text-italic-symbolic")
        italic_button.set_tooltip_text("Italic")
        italic_button.connect("clicked", self.on_italic_clicked)
        
        underline_button = Gtk.Button(icon_name="format-text-underline-symbolic")
        underline_button.set_tooltip_text("Underline")
        underline_button.connect("clicked", self.on_underline_clicked)
        
        # Add a spacer (expanding box)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        
        # Add a close button
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_toolbar_clicked)
        
        # Add all widgets to the toolbar
        toolbar.append(bold_button)
        toolbar.append(italic_button)
        toolbar.append(underline_button)
        toolbar.append(spacer)
        toolbar.append(close_button)
        
        return toolbar
        
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the window"""
        # Create a shortcut controller
        controller = Gtk.ShortcutController()
        
        # Create Ctrl+T shortcut for toggling the toolbar
        trigger = Gtk.ShortcutTrigger.parse_string("<Control>t")
        action = Gtk.CallbackAction.new(self.toggle_toolbar)
        shortcut = Gtk.Shortcut.new(trigger, action)
        controller.add_shortcut(shortcut)
        
        # Create Ctrl+Z shortcut for undo
        trigger_undo = Gtk.ShortcutTrigger.parse_string("<Control>z")
        action_undo = Gtk.CallbackAction.new(self.on_undo_shortcut)
        shortcut_undo = Gtk.Shortcut.new(trigger_undo, action_undo)
        controller.add_shortcut(shortcut_undo)
        
        # Create Ctrl+Y shortcut for redo
        trigger_redo = Gtk.ShortcutTrigger.parse_string("<Control>y")
        action_redo = Gtk.CallbackAction.new(self.on_redo_shortcut)
        shortcut_redo = Gtk.Shortcut.new(trigger_redo, action_redo)
        controller.add_shortcut(shortcut_redo)
        
        # Create Ctrl+W shortcut for closing current window
        trigger_close = Gtk.ShortcutTrigger.parse_string("<Control>w")
        action_close = Gtk.CallbackAction.new(self.on_close_shortcut)
        shortcut_close = Gtk.Shortcut.new(trigger_close, action_close)
        controller.add_shortcut(shortcut_close)
        
        # Create Ctrl+Shift+W shortcut for closing other windows
        trigger_close_others = Gtk.ShortcutTrigger.parse_string("<Control><Shift>w")
        action_close_others = Gtk.CallbackAction.new(self.on_close_others_shortcut)
        shortcut_close_others = Gtk.Shortcut.new(trigger_close_others, action_close_others)
        controller.add_shortcut(shortcut_close_others)
        
        # Add controller to the window (not the webview)
        self.add_controller(controller)
        
        # Make it capture events at the capture phase
        controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        
        # Make shortcut work regardless of who has focus
        controller.set_scope(Gtk.ShortcutScope.GLOBAL)

    def on_close_shortcut(self, *args):
        """Handle Ctrl+W shortcut to close current window"""
        self.close()
        return True

    def on_close_others_shortcut(self, *args):
        """Handle Ctrl+Shift+W shortcut to close other windows"""
        app = self.get_application()
        if app and hasattr(app, 'on_close_other_windows'):
            app.on_close_other_windows(None, None)
        return True
    
    def setup_toolbar_animation(self):
        if hasattr(self, 'overlay_setup_done') and self.overlay_setup_done:
            return
        
        # Create an overlay
        self.overlay = Gtk.Overlay()
        self.overlay.set_vexpand(True)  # Ensure overlay expands vertically
        self.overlay.set_hexpand(True)  # Ensure overlay expands horizontally
        
        # Get the content box and remove the webview from its current parent
        content_box = self.webview.get_parent()
        if self.webview.get_parent():
            self.webview.get_parent().remove(self.webview)
        
        # Create a box to hold the webview
        webview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        webview_box.set_vexpand(True)  # Ensure webview_box expands vertically
        webview_box.set_hexpand(True)  # Ensure webview_box expands horizontally
        webview_box.append(self.webview)
        
        # Set webview_box as the main child of the overlay
        self.overlay.set_child(webview_box)
        
        # Create the toolbar box
        self.toolbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toolbar_box.set_halign(Gtk.Align.FILL)
        self.toolbar_box.set_valign(Gtk.Align.END)
        self.toolbar_box.set_margin_start(0)
        self.toolbar_box.set_margin_end(0)
        self.toolbar_box.set_margin_bottom(0)
        self.toolbar_box.add_css_class("toolbar-overlay")
        
        # Create and populate the overlay toolbar
        self.overlay_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.overlay_toolbar.set_margin_start(0)
        self.overlay_toolbar.set_margin_end(0)
        self.overlay_toolbar.set_margin_top(0)
        self.overlay_toolbar.set_margin_bottom(0)
        
        bold_button = Gtk.Button(icon_name="format-text-bold-symbolic")
        bold_button.set_tooltip_text("Bold")
        bold_button.connect("clicked", self.on_bold_clicked)
        
        italic_button = Gtk.Button(icon_name="format-text-italic-symbolic")
        italic_button.set_tooltip_text("Italic")
        italic_button.connect("clicked", self.on_italic_clicked)
        
        underline_button = Gtk.Button(icon_name="format-text-underline-symbolic")
        underline_button.set_tooltip_text("Underline")
        underline_button.connect("clicked", self.on_underline_clicked)
        
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", self.on_close_toolbar_clicked)
        
        self.overlay_toolbar.append(bold_button)
        self.overlay_toolbar.append(italic_button)
        self.overlay_toolbar.append(underline_button)
        self.overlay_toolbar.append(spacer)
        self.overlay_toolbar.append(close_button)
        
        self.toolbar_box.append(self.overlay_toolbar)
        
        # Add toolbar_box as an overlay child
        self.overlay.add_overlay(self.toolbar_box)
        
        # Remove existing children from content_box and add the overlay
        if content_box:
            child = content_box.get_first_child()
            while child:
                next_child = child.get_next_sibling()
                if child != self.statusbar and child != self.bottom_toolbar:
                    content_box.remove(child)
                child = next_child
            content_box.append(self.overlay)
        
        # Ensure statusbar is at the bottom
        if self.statusbar.get_parent():
            self.statusbar.get_parent().remove(self.statusbar)
        content_box.append(self.statusbar)
        
        # Set initial state: hidden with zero opacity
        self.toolbar_box.set_opacity(0.0)  # Start fully transparent
        self.toolbar_box.set_visible(True)  # Keep visible but transparent
        
        # Add CSS for toolbar styling and fade animation
        css_provider = Gtk.CssProvider()
        css_data = """
            .toolbar-overlay {
                background-color: @theme_bg_color;
                border-radius: 0px;
                min-height: 36px;
        }
        """
        css_provider.load_from_data(css_data.encode('utf-8'))
        display = self.get_display()
        Gtk.StyleContext.add_provider_for_display(
            display,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        self.overlay_setup_done = True
        print("Overlay toolbar setup complete with fade animation")
    def toggle_toolbar(self, *args):
        """Toggle the visibility of the toolbar overlay with a fade effect"""
        if hasattr(self, 'toolbar_box'):
            current_opacity = self.toolbar_box.get_opacity()
            
            if current_opacity > 0.0:  # Currently visible, fade out
                self.toolbar_box.set_opacity(0.0)
                self.statusbar.set_text("Toolbar hidden")
                print("Toolbar faded out")
            else:  # Currently hidden, fade in
                self.toolbar_box.set_opacity(1.0)
                self.statusbar.set_text("Toolbar shown")
                print("Toolbar faded in")
        else:
            print("Toolbar box not initialized")
        
        return True
    def on_close_toolbar_clicked(self, button):
        """Handle the close button click with fade-out"""
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.set_opacity(0.0)
            self.statusbar.set_text("Toolbar hidden")
        else:
            self.bottom_toolbar.set_visible(False)  # Fallback for old toolbar

    def get_editor_html(self, content=""):
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
    <!DOCTYPE html>
    <html style="height: 100%;">
    <head>
        <title>HTML Editor</title>
        <style>
            html, body {{
                height: 100%;
                margin: 40px; /*Change this for page border*/
                padding: 0;
                font-family: Arial, sans-serif;
            }}
            #editor {{
                border: 1px solid #ccc;
                padding: 10px;
                outline: none;
                min-height: 200px; /* Reduced fallback minimum height */
                height: 100%; /* Allow it to expand fully */
                box-sizing: border-box; /* Include padding/border in height */
            }}
            #editor div {{
                margin: 0;
                padding: 0;
            }}
            #editor:empty:not(:focus):before {{
                content: "Type here to start editing...";
                color: #aaa;
                font-style: italic;
                position: absolute;
                pointer-events: none;
                top: 10px;
                left: 10px;
            }}
        </style>
        <script>
            window.initialContent = "{content or '<div><br></div>'}";
            {self.get_editor_js()}
        </script>
    </head>
    <body>
        <div id="editor" contenteditable="true"></div>
    </body>
    </html>
    """

    def get_editor_js(self):
        """Return the combined JavaScript logic for the editor."""
        return f"""
        // Global scope for persistence
        window.undoStack = [];
        window.redoStack = [];
        window.isUndoRedo = false;
        window.lastContent = "";

        {self.save_state_js()}
        {self.perform_undo_js()}
        {self.perform_redo_js()}
        {self.find_last_text_node_js()}
        {self.get_stack_sizes_js()}
        {self.set_content_js()}
        {self.init_editor_js()}
        """

    def save_state_js(self):
        """JavaScript to save the editor state to the undo stack."""
        return """
        function saveState() {
            window.undoStack.push(document.getElementById('editor').innerHTML);
            if (window.undoStack.length > 100) {
                window.undoStack.shift();
            }
        }
        """

    def perform_undo_js(self):
        """JavaScript to perform an undo operation."""
        return """
        function performUndo() {
            const editor = document.getElementById('editor');
            if (window.undoStack.length > 1) {
                let selection = window.getSelection();
                let range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
                let cursorNode = range ? range.startContainer : null;
                let cursorOffset = range ? range.startOffset : 0;

                window.redoStack.push(window.undoStack.pop());
                window.isUndoRedo = true;
                editor.innerHTML = window.undoStack[window.undoStack.length - 1];
                window.lastContent = editor.innerHTML;
                window.isUndoRedo = false;

                editor.focus();
                try {
                    const newRange = document.createRange();
                    const sel = window.getSelection();
                    const textNode = findLastTextNode(editor) || editor;
                    const offset = textNode.nodeType === 3 ? textNode.length : 0;
                    newRange.setStart(textNode, offset);
                    newRange.setEnd(textNode, offset);
                    sel.removeAllRanges();
                    sel.addRange(newRange);
                } catch (e) {
                    console.log("Could not restore cursor position:", e);
                }
                return { success: true, isInitialState: window.undoStack.length === 1 };
            }
            return { success: false, isInitialState: window.undoStack.length === 1 };
        }
        """

    def perform_redo_js(self):
        """JavaScript to perform a redo operation."""
        return """
        function performRedo() {
            const editor = document.getElementById('editor');
            if (window.redoStack.length > 0) {
                let selection = window.getSelection();
                let range = selection.rangeCount > 0 ? selection.getRangeAt(0) : null;
                let cursorNode = range ? range.startContainer : null;
                let cursorOffset = range ? range.startOffset : 0;

                const state = window.redoStack.pop();
                window.undoStack.push(state);
                window.isUndoRedo = true;
                editor.innerHTML = state;
                window.lastContent = editor.innerHTML;
                window.isUndoRedo = false;

                editor.focus();
                try {
                    const newRange = document.createRange();
                    const sel = window.getSelection();
                    const textNode = findLastTextNode(editor) || editor;
                    const offset = textNode.nodeType === 3 ? textNode.length : 0;
                    newRange.setStart(textNode, offset);
                    newRange.setEnd(textNode, offset);
                    sel.removeAllRanges();
                    sel.addRange(newRange);
                } catch (e) {
                    console.log("Could not restore cursor position:", e);
                }
                return { success: true, isInitialState: window.undoStack.length === 1 };
            }
            return { success: false, isInitialState: window.undoStack.length === 1 };
        }
        """

    def find_last_text_node_js(self):
        """JavaScript to find the last text node for cursor restoration."""
        return """
        function findLastTextNode(node) {
            if (node.nodeType === 3) return node;
            for (let i = node.childNodes.length - 1; i >= 0; i--) {
                const found = findLastTextNode(node.childNodes[i]);
                if (found) return found;
            }
            return null;
        }
        """

    def get_stack_sizes_js(self):
        """JavaScript to get the sizes of undo and redo stacks."""
        return """
        function getStackSizes() {
            return {
                undoSize: window.undoStack.length,
                redoSize: window.redoStack.length
            };
        }
        """

    def set_content_js(self):
        """JavaScript to set the editor content and reset stacks."""
        return """
        function setContent(html) {
            const editor = document.getElementById('editor');
            if (!html || html.trim() === '') {
                editor.innerHTML = '<div><br></div>';
            } else if (!html.trim().match(/^<(div|p|h[1-6]|ul|ol|table)/i)) {
                editor.innerHTML = '<div>' + html + '</div>';
            } else {
                editor.innerHTML = html;
            }
            window.lastContent = editor.innerHTML;
            window.undoStack = [window.lastContent];
            window.redoStack = [];
            editor.focus();
        }
        """

    def init_editor_js(self):
        """JavaScript to initialize the editor and set up event listeners."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            editor.addEventListener('focus', function onFirstFocus(e) {
                if (!editor.textContent.trim() && editor.innerHTML === '') {
                    editor.innerHTML = '<div><br></div>';
                    const range = document.createRange();
                    const sel = window.getSelection();
                    const firstDiv = editor.querySelector('div');
                    if (firstDiv) {
                        range.setStart(firstDiv, 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                    editor.removeEventListener('focus', onFirstFocus);
                }
            });

            window.lastContent = editor.innerHTML;
            saveState();
            editor.focus();

            editor.addEventListener('input', function(e) {
                if (document.getSelection().anchorNode === editor) {
                    document.execCommand('formatBlock', false, 'div');
                }
                if (!window.isUndoRedo) {
                    const currentContent = editor.innerHTML;
                    if (currentContent !== window.lastContent) {
                        saveState();
                        window.lastContent = currentContent;
                        window.redoStack = [];
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage("changed");
                        } catch(e) {
                            console.log("Could not notify about changes:", e);
                        }
                    }
                }
            });

            if (window.initialContent) {
                setContent(window.initialContent);
            }
        });
        """
        
    def get_initial_html(self):
        return self.get_editor_html()
    
    def execute_js(self, script):
        """Execute JavaScript in the WebView"""
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)
    
    def extract_body_content(self, html):
        """Extract content from the body or just return the HTML if parsing fails"""
        try:
            # Simple regex to extract content between body tags
            import re
            body_match = re.search(r'<body[^>]*>([\s\S]*)<\/body>', html)
            if body_match:
                return body_match.group(1)
            return html
        except Exception:
            # In case of any error, return the original HTML
            return html
    
    # Undo/Redo related methods
    def on_content_changed(self, manager, result):
        self.modified = True
        self.update_window_title()
        self.update_undo_redo_state()
        
    def update_undo_redo_state(self):
        try:
            # Get stack sizes to update button states
            self.webview.evaluate_javascript(
                "JSON.stringify(getStackSizes());",  # Ensure we get a proper JSON string
                -1, None, None, None,
                self._on_get_stack_sizes, 
                None
            )
        except Exception as e:
            print(f"Error updating undo/redo state: {e}")
            # Fallback - enable buttons
            self.undo_button.set_sensitive(True)
            self.redo_button.set_sensitive(False)
        
    def _on_get_stack_sizes(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                # Try different approaches to get the result based on WebKit version
                try:
                    # Newer WebKit APIs
                    if hasattr(js_result, 'get_js_value'):
                        stack_sizes = js_result.get_js_value().to_string()
                    # Direct value access - works in some WebKit versions
                    elif hasattr(js_result, 'to_string'):
                        stack_sizes = js_result.to_string()
                    elif hasattr(js_result, 'get_string'):
                        stack_sizes = js_result.get_string()
                    else:
                        # Fallback - try converting to string directly
                        stack_sizes = str(js_result)
                    
                    # Parse the JSON result
                    import json
                    try:
                        # Remove any surrounding quotes if present
                        if stack_sizes.startswith('"') and stack_sizes.endswith('"'):
                            stack_sizes = stack_sizes[1:-1]
                        
                        # Try to parse as JSON
                        sizes = json.loads(stack_sizes)
                        # Update button states
                        self.undo_button.set_sensitive(sizes.get('undoSize', 0) > 1)
                        self.redo_button.set_sensitive(sizes.get('redoSize', 0) > 0)
                    except json.JSONDecodeError as je:
                        print(f"Error parsing JSON: {je}, value was: {stack_sizes}")
                        # Set reasonable defaults
                        self.undo_button.set_sensitive(True)
                        self.redo_button.set_sensitive(False)
                except Exception as inner_e:
                    print(f"Inner error processing JS result: {inner_e}")
                    # Set reasonable defaults
                    self.undo_button.set_sensitive(True)
                    self.redo_button.set_sensitive(False)
        except Exception as e:
            print(f"Error getting stack sizes: {e}")
            # Set reasonable defaults in case of error
            self.undo_button.set_sensitive(True)
            self.redo_button.set_sensitive(False)
            
    def on_undo_clicked(self, button):
        self.perform_undo()
        
    def on_redo_clicked(self, button):
        self.perform_redo()
        
    def on_undo_shortcut(self, *args):
        self.perform_undo()
        return True
        
    def on_redo_shortcut(self, *args):
        self.perform_redo()
        return True
        
    def perform_undo(self):
        try:
            self.webview.evaluate_javascript(
                "JSON.stringify(performUndo());",
                -1, None, None, None,
                self._on_undo_redo_performed,
                "undo"
            )
            self.statusbar.set_text("Undo performed")
        except Exception as e:
            print(f"Error during undo: {e}")
            self.statusbar.set_text("Undo failed")
        
    def perform_redo(self):
        try:
            self.webview.evaluate_javascript(
                "JSON.stringify(performRedo());",
                -1, None, None, None,
                self._on_undo_redo_performed,
                "redo"
            )
            self.statusbar.set_text("Redo performed")
        except Exception as e:
            print(f"Error during redo: {e}")
            self.statusbar.set_text("Redo failed")

    def _on_undo_redo_performed(self, webview, result, operation):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                result_str = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                              js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                import json
                result_data = json.loads(result_str)
                success = result_data.get('success', False)
                is_initial_state = result_data.get('isInitialState', False)

                if success:
                    self.statusbar.set_text(f"{operation.capitalize()} performed")
                    if operation == "undo" and is_initial_state:
                        self.modified = False  # Reset when fully undone
                    else:
                        self.modified = True  # Set for redo or partial undo
                    self.update_window_title()
                    self.update_undo_redo_state()
                else:
                    self.statusbar.set_text(f"No more {operation} actions available")
        except Exception as e:
            print(f"Error during {operation}: {e}")
            self.statusbar.set_text(f"{operation.capitalize()} failed")
    
    # Auto-save related methods
    def on_auto_save_toggled(self, switch, gparam):
        active = switch.get_active()
        self.auto_save_enabled = active
        
        # Update status bar
        self.statusbar.set_text(f"Auto-save {'enabled' if active else 'disabled'}")
        
        # Start or stop auto-save timer
        if active:
            self.start_auto_save_timer()
        else:
            self.stop_auto_save_timer()
    
    def on_auto_save_interval_changed(self, spinner):
        self.auto_save_interval = spinner.get_value_as_int()
        self.statusbar.set_text(f"Auto-save interval set to {self.auto_save_interval} seconds")
        
        # Restart timer if enabled
        if self.auto_save_enabled:
            self.stop_auto_save_timer()
            self.start_auto_save_timer()
    
    def start_auto_save_timer(self):
        # Stop any existing timer
        self.stop_auto_save_timer()
        
        # Only start if we have a file to save to
        if self.current_file:
            # Create a new timer
            self.auto_save_source_id = GLib.timeout_add_seconds(
                self.auto_save_interval,
                self.perform_auto_save
            )
        else:
            # Prompt for save location if we don't have one
            dialog = Gtk.FileDialog()
            dialog.set_title("Auto-Save Location")
            
            filter = Gtk.FileFilter()
            filter.set_name("HTML files")
            filter.add_pattern("*.html")
            filter.add_pattern("*.htm")
            
            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(filter)
            
            dialog.set_filters(filters)
            dialog.save(self, None, self._on_auto_save_location_set)
    
    def _on_auto_save_location_set(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                self.current_file = file
                # Now start the timer
                self.auto_save_source_id = GLib.timeout_add_seconds(
                    self.auto_save_interval,
                    self.perform_auto_save
                )
                self.statusbar.set_text(f"Auto-save will save to: {file.get_path()}")
            else:
                # User cancelled, disable auto-save
                self.auto_save_enabled = False
                self.statusbar.set_text("Auto-save disabled (no location selected)")
        except GLib.Error as error:
            print(f"Error setting auto-save location: {error.message}")
            self.auto_save_enabled = False
            self.statusbar.set_text("Auto-save disabled due to error")
    
    def stop_auto_save_timer(self):
        if self.auto_save_source_id:
            GLib.source_remove(self.auto_save_source_id)
            self.auto_save_source_id = None
    
    def perform_auto_save(self):
        if not self.current_file or not self.auto_save_enabled:
            return False  # Stop the timer
        
        # Get only the editor content from WebView using JavaScript
        self.webview.evaluate_javascript(
            "document.getElementById('editor').innerHTML;",
            -1, None, None,
            None,
            self._on_auto_save_content, 
            None
        )
        
        return True  # Continue the timer

    def _on_auto_save_content(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result and self.current_file:
                try:
                    if hasattr(js_result, 'get_js_value'):
                        editor_content = js_result.get_js_value().to_string()
                    elif hasattr(js_result, 'to_string'):
                        editor_content = js_result.to_string()
                    else:
                        editor_content = str(js_result)
                    self.save_html_content(editor_content, self.current_file, self._on_auto_save_completed)
                except Exception as e:
                    print(f"Error processing auto-save content: {e}")
        except Exception as e:
            print(f"Error during auto-save: {e}")
    
    def _on_auto_save_completed(self, file, result):
        try:
            success, _ = file.replace_contents_finish(result)
            if success:
                current_time = GLib.DateTime.new_now_local().format("%H:%M:%S")
                self.statusbar.set_text(f"Auto-saved at {current_time}")
        except GLib.Error as error:
            print(f"Error completing auto-save: {error.message}")
            self.statusbar.set_text("Auto-save failed")
    
    # Event handlers
    def on_new_clicked(self, button):
        app = self.get_application()
        if app:
            # Create a new window with a blank document
            new_win = HTMLEditorWindow(application=app)
            app.windows.append(new_win)
            app.setup_header_bar(new_win)
            new_win.present()
            app.update_window_menu()
            new_win.statusbar.set_text("New document created")
    
    def on_open_clicked(self, button):
        """Show open file dialog and decide whether to open in current or new window"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open Document")
        
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_pattern("*.html")
        filter_html.add_pattern("*.htm")
        
        filter_txt = Gtk.FileFilter()
        filter_txt.set_name("Text files")
        filter_txt.add_pattern("*.txt")
        
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        
        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        filter_list.append(filter_html)
        filter_list.append(filter_txt)
        filter_list.append(filter_all)
        
        dialog.set_filters(filter_list)
        
        # If no changes made and no file is open, open in current window, otherwise open in new window
        if self.modified or self.current_file:
            dialog.open(self, None, self.on_open_new_window_response)
        else:
            dialog.open(self, None, self.on_open_current_window_response)

    def on_open_new_window_response(self, dialog, result):
        """Handle open file dialog response to open in a new window"""
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                app = self.get_application()
                if app:
                    # Create a new window for the file
                    new_win = HTMLEditorWindow(application=app)
                    app.windows.append(new_win)
                    app.setup_header_bar(new_win)
                    new_win.load_file(filepath)
                    new_win.present()
                    app.update_window_menu()
        except GLib.Error as e:
            if e.domain != 'gtk-dialog-error-quark' or e.code != 2:  # Ignore cancel
                app = self.get_application()
                if app and hasattr(app, 'show_error_dialog'):
                    app.show_error_dialog(f"Error opening file: {e}")

    def on_open_current_window_response(self, dialog, result):
        """Handle open file dialog response to open in current window"""
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                self.load_file(filepath)
                self.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
        except GLib.Error as e:
            if e.domain != 'gtk-dialog-error-quark' or e.code != 2:  # Ignore cancel
                app = self.get_application()
                if app and hasattr(app, 'show_error_dialog'):
                    app.show_error_dialog(f"Error opening file: {e}")

    def load_file(self, filepath):
        """Load file content into editor"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            is_html = content.strip().startswith("<") and (
                "<html" in content.lower() or 
                "<body" in content.lower() or 
                "<div" in content.lower()
            )
            if is_html:
                body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
                if body_match:
                    content = body_match.group(1).strip()
            else:
                content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                content = content.replace("\n", "<br>")
            
            # Escape for JavaScript
            content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            js_code = f'setContent("{content}");'
            
            # Check WebView load status and execute JS accordingly
            def execute_when_ready():
                # Get the current load status
                load_status = self.webview.get_estimated_load_progress()
                
                if load_status == 1.0:  # Fully loaded
                    # Execute directly
                    self.execute_js(js_code)
                    return False  # Stop the timeout
                else:
                    # Set up a handler for when loading finishes
                    def on_load_changed(webview, event):
                        if event == WebKit.LoadEvent.FINISHED:
                            self.execute_js(js_code)
                            webview.disconnect_by_func(on_load_changed)
                    
                    self.webview.connect("load-changed", on_load_changed)
                    return False  # Stop the timeout
            
            # Use GLib timeout to ensure we're not in the middle of another operation
            GLib.timeout_add(50, execute_when_ready)
            
            # Update file information
            self.current_file = Gio.File.new_for_path(filepath)
            self.modified = False
            self.update_window_title()
            self.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            self.statusbar.set_text(f"Error loading file: {str(e)}")
            # Call show_error_dialog if it exists
            if hasattr(self, 'show_error_dialog'):
                self.show_error_dialog(f"Error loading file: {e}")

    def update_window_title(self):
        """Update window title to show document name (without extension) and modified status"""
        if self.current_file:
            # Get the path as a string
            if hasattr(self.current_file, 'get_path'):
                path = self.current_file.get_path()
            else:
                path = self.current_file
            # Extract filename without extension
            filename = os.path.splitext(os.path.basename(path))[0]
            title = f"{filename} - HTML Editor{' *' if self.modified else ''}"
        else:
            title = f"Untitled - HTML Editor{' *' if self.modified else ''}"
        self.set_title(title)

    
    def on_save_clicked(self, button):
        dialog = Gtk.FileDialog()
        dialog.set_title("Save HTML File")
        
        filter = Gtk.FileFilter()
        filter.set_name("HTML files")
        filter.add_pattern("*.html")
        filter.add_pattern("*.htm")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter)
        
        dialog.set_filters(filters)
        dialog.save(self, None, self._on_save_response)
    
    def _on_save_response(self, dialog, result):
        try:
            file = dialog.save_finish(result)
            if file:
                self.current_file = file  # Already a Gio.File
                self.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    self._on_get_html_content, 
                    file
                )
        except GLib.Error as error:
            print(f"Error saving file: {error.message}")
    
    def _on_snapshot_ready(self, webview, result, file):
        try:
            # Get just the editor content using JavaScript instead of the whole document
            self.webview.evaluate_javascript(
                "document.getElementById('editor').innerHTML;",
                -1, None, None,
                None,
                self._on_get_html_content, 
                file
            )
        except Exception as e:
            print(f"Error preparing content: {e}")
            
    def save_html_content(self, editor_content, file, callback):
            try:
                if editor_content.strip() == "" or editor_content == "<br>":
                    editor_content = "<div><br></div>"
                elif not (editor_content.startswith('<div') and editor_content.endswith('</div>')):
                    editor_content = f"<div>{editor_content.strip()}</div>"
                html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>HTML Document</title>
    <meta charset="utf-8">
</head>
<body>
{editor_content}
</body>
</html>
"""
                file_bytes = html_content.encode('utf-8')
                file.replace_contents_async(file_bytes, None, False, Gio.FileCreateFlags.NONE, None, callback)
            except Exception as e:
                print(f"Error saving content: {e}")

    def _on_get_html_content(self, webview, result, file):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                                 js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                self.save_html_content(editor_content, file, self._on_file_saved)
            else:
                print("Failed to get HTML content from webview")
        except Exception as e:
            print(f"Error getting HTML content: {e}")
    
    def _on_file_saved(self, file, result):
        try:
            success, _ = file.replace_contents_finish(result)
            if success:
                self.current_file = file  # Ensure consistency by updating self.current_file
                self.statusbar.set_text(f"Saved: {file.get_path()}")
                self.update_window_title()
                self.modified = False  # Reset modified flag after save
        except GLib.Error as error:
            print(f"Error writing file: {error.message}")
    
    def on_bold_clicked(self, button):
        self.execute_js("document.execCommand('bold', false, null);")
    
    def on_italic_clicked(self, button):
        self.execute_js("document.execCommand('italic', false, null);")
    
    def on_underline_clicked(self, button):
        self.execute_js("document.execCommand('underline', false, null);")
    
    def on_close_toolbar_clicked(self, button):
        self.bottom_toolbar.set_visible(False)
        
    def on_close_request(self, *args):
        """Handle window close request"""
        app = self.get_application()
        if app:
            # Use the app's method to properly remove this window
            app.remove_window(self)
        return False

class HTMLEditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='io.github.fastrizwaan.htmleditor',
                        flags=Gio.ApplicationFlags.HANDLES_OPEN,
                        **kwargs)
        self.windows = []  # Track all open windows
        self.window_buttons = {}  # Track window menu buttons {window_id: button}
        self.connect('activate', self.on_activate)
        self.connect("open", self.on_open)

    def create_window_menu(self):
        """Create a fresh window menu"""
        menu = Gio.Menu()
        actions_section = Gio.Menu()
        window_section = Gio.Menu()
        
        # Add "Close Other Windows" option at the top if there's more than one window
        if len(self.windows) > 1:
            actions_section.append("Close Other Windows", "app.close-other-windows")
            menu.append_section("Actions", actions_section)
        
        # Add all windows to the menu
        for i, win in enumerate(self.windows):
            title = win.get_menu_title()
            action_string = f"app.switch-window({i})"
            window_section.append(title, action_string)
        
        menu.append_section("Windows", window_section)
        return menu

    def update_window_menu(self):
        """Force update all window menu buttons"""
        fresh_menu = self.create_window_menu()
        
        # Should we show the window menu button?
        show_button = len(self.windows) > 1
        
        # Create a set of windows that still need a button
        windows_needing_buttons = set(self.windows)
        
        # First, update existing buttons
        buttons_to_remove = []
        for window_id, button in self.window_buttons.items():
            # Check if the window still exists
            window_exists = False
            for win in self.windows:
                if id(win) == window_id:
                    window_exists = True
                    windows_needing_buttons.remove(win)
                    break
            
            if window_exists:
                # Update existing button with fresh menu and visibility
                button.set_menu_model(fresh_menu)
                button.set_visible(show_button)
            else:
                # Window no longer exists, mark button for removal
                buttons_to_remove.append(window_id)
        
        # Remove buttons for closed windows
        for window_id in buttons_to_remove:
            del self.window_buttons[window_id]
        
        # Add buttons for new windows
        for win in windows_needing_buttons:
            self.add_window_menu_button(win, fresh_menu)
    
    def add_window_menu_button(self, win, menu_model=None):
        """Add a window menu button to a window or update an existing one"""
        header = win.main_box.get_first_child()
        if not header or not isinstance(header, Adw.HeaderBar):
            return
        
        # Look for existing window menu button
        child = header.get_first_child()
        window_button = None
        while child:
            if (isinstance(child, Gtk.MenuButton) and 
                child.get_icon_name() == "window-new-symbolic"):
                window_button = child
                break
            child = child.get_next_sibling()
        
        # Create a new menu model if not provided
        if menu_model is None:
            menu_model = self.create_window_menu()
        
        # Only show the window menu button if there's more than one window
        show_button = len(self.windows) > 1
        
        if window_button:
            # Update existing button's menu and visibility
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
        elif show_button:
            # Only create a new button if we need to show it
            window_button = Gtk.MenuButton()
            window_button.set_icon_name("window-new-symbolic")
            window_button.set_tooltip_text("Window List")
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
            header.pack_end(window_button)
            
            # Store reference to the button
            self.window_buttons[id(win)] = window_button
        
        # Make sure we keep the reference if button exists
        if window_button:
            self.window_buttons[id(win)] = window_button


    def setup_header_bar(self, win):
        """Initialize the header bar for a window"""
        header = win.main_box.get_first_child()
        if not header:
            win.create_header_bar()
        
        # Add window menu button (uses cached menu if available)
        self.add_window_menu_button(win)

    def on_switch_window(self, action, param):
        """Handle window switching action"""
        index = param.get_int32()
        if 0 <= index < len(self.windows):
            self.windows[index].present()
            
    def on_new_window(self, action, param):
        """Create a new empty window"""
        win = HTMLEditorWindow(application=self)
        self.windows.append(win)
        self.setup_header_bar(win)
        win.present()
        # Update all window menus
        self.update_window_menu()

    def create_actions(self):
        """Set up application actions"""
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)
        
        # New window action
        new_window_action = Gio.SimpleAction.new("new-window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)
        
        # Close other windows action
        close_other_windows_action = Gio.SimpleAction.new("close-other-windows", None)
        close_other_windows_action.connect("activate", self.on_close_other_windows)
        self.add_action(close_other_windows_action)

        # Window switching action
        switch_window_action = Gio.SimpleAction.new(
            "switch-window", 
            GLib.VariantType.new("i")
        )
        switch_window_action.connect("activate", self.on_switch_window)
        self.add_action(switch_window_action)
        
    def on_close_other_windows(self, action, param):
        """Close all windows except the active one with confirmation"""
        if len(self.windows) <= 1:
            return
            
        # Find the active window (the one that was most recently focused)
        active_window = None
        for win in self.windows:
            if win.is_active():
                active_window = win
                break
                
        # If no active window found, use the first one
        if not active_window and self.windows:
            active_window = self.windows[0]
            
        if not active_window:
            return
            
        # The number of windows that will be closed
        windows_to_close_count = len(self.windows) - 1
        
        # Create confirmation dialog using non-deprecated methods
        dialog = Adw.Dialog.new()
        dialog.set_title(f"Close {windows_to_close_count} Other Window{'s' if windows_to_close_count > 1 else ''}?")
        dialog.set_content_width(350)
        
        # Create dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Message label
        message_label = Gtk.Label()
        message_label.set_text(f"Are you sure you want to close {windows_to_close_count} other window{'s' if windows_to_close_count > 1 else ''}?")
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        # Close button (destructive)
        close_button = Gtk.Button(label="Close Windows")
        close_button.add_css_class("destructive-action")
        close_button.connect("clicked", lambda btn: self._on_close_others_response(dialog, active_window))
        button_box.append(close_button)
        
        content_box.append(button_box)
        
        # Set the dialog content and present
        dialog.set_child(content_box)
        dialog.present(active_window)

    def _on_close_others_response(self, dialog, active_window):
        """Handle the close action from the dialog"""
        # Close dialog
        dialog.close()
        
        # Get windows to close (all except active_window)
        windows_to_close = [win for win in self.windows if win != active_window]
        
        # Close each window
        for win in windows_to_close[:]:  # Use a copy of the list since we'll modify it
            win.close()
            
        # Make sure active window is still presented
        if active_window in self.windows:
            active_window.present()
            
        # Update window menu
        self.update_window_menu()
                
    def do_startup(self):
        Adw.Application.do_startup(self)
        self.create_actions()

    def on_activate(self, app):
        """Handle application activation (new window)"""
        win = HTMLEditorWindow(application=self)
        self.windows.append(win)
        self.setup_header_bar(win)
        win.present()
        self.update_window_menu()

    def on_open(self, app, files, n_files, hint):
        """Handle file opening"""
        windows_added = False
        
        for file in files:
            file_path = file.get_path()
            existing_win = None
            for win in self.windows:
                if win.current_file and win.current_file.get_path() == file_path:
                    existing_win = win
                    break
            
            if existing_win:
                existing_win.present()
            else:
                win = HTMLEditorWindow(application=self)
                self.windows.append(win)
                self.setup_header_bar(win)
                win.load_file(file_path)
                win.present()
                windows_added = True
                
        if windows_added:
            self.update_window_menu()

    def remove_window(self, window):
        """Properly remove a window and update menus"""
        if window in self.windows:
            # Remove window from list
            self.windows.remove(window)
            # Clean up button reference
            if id(window) in self.window_buttons:
                del self.window_buttons[id(window)]
            # Update menus in all remaining windows
            self.update_window_menu()
            
            # Focus the next window if available
            if self.windows:
                self.windows[0].present()

    def on_quit(self, action, param):
        """Quit the application"""
        for win in self.windows[:]:  # Use a copy to avoid modification during iteration
            win.close()
        self.quit()
    
    def on_about(self, action, param):
        """Show about dialog"""
        parent_window = self.windows[0] if self.windows else None
        about = Adw.AboutWindow(
            transient_for=parent_window,
            application_name="HTML Editor",
            application_icon="text-editor",
            developer_name="Developer",
            version="1.0",
            developers=["Your Name"],
            copyright="© 2025"
        )
        about.present()
    
    def on_preferences(self, action, param):
        """Show preferences dialog"""
        if not self.windows:
            return
            
        self.win = self.windows[0]  # Use first window for preferences
        
        # Create dialog
        dialog = Adw.Dialog.new()
        dialog.set_title("Preferences")
        dialog.set_content_width(450)
        
        # Create content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Add settings UI
        header = Gtk.Label()
        header.set_markup("<b>Editor Settings</b>")
        header.set_halign(Gtk.Align.START)
        header.set_margin_bottom(12)
        content_box.append(header)
        
        # Auto-save toggle
        auto_save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_save_box.set_margin_start(12)
        
        auto_save_label = Gtk.Label(label="Auto Save:")
        auto_save_label.set_halign(Gtk.Align.START)
        auto_save_label.set_hexpand(True)
        
        auto_save_switch = Gtk.Switch()
        auto_save_switch.set_active(self.win.auto_save_enabled)
        auto_save_switch.set_valign(Gtk.Align.CENTER)
        
        auto_save_box.append(auto_save_label)
        auto_save_box.append(auto_save_switch)
        content_box.append(auto_save_box)
        
        # Interval settings
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        interval_box.set_margin_start(12)
        interval_box.set_margin_top(12)
        
        interval_label = Gtk.Label(label="Auto-save Interval (seconds):")
        interval_label.set_halign(Gtk.Align.START)
        interval_label.set_hexpand(True)
        
        adjustment = Gtk.Adjustment(
            value=self.win.auto_save_interval,
            lower=10,
            upper=600,
            step_increment=10
        )
        
        spinner = Gtk.SpinButton()
        spinner.set_adjustment(adjustment)
        spinner.set_valign(Gtk.Align.CENTER)
        
        interval_box.append(interval_label)
        interval_box.append(spinner)
        content_box.append(interval_box)
        
        # Dialog buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", lambda btn: self.save_preferences(
            dialog, auto_save_switch.get_active(), spinner.get_value_as_int()
        ))
        button_box.append(ok_button)
        
        content_box.append(button_box)
        
        # Set dialog content and show
        dialog.set_child(content_box)
        dialog.present(self.win)

    def save_preferences(self, dialog, auto_save_enabled, auto_save_interval):
        """Save preferences settings"""
        previous_auto_save = self.win.auto_save_enabled
        
        self.win.auto_save_enabled = auto_save_enabled
        self.win.auto_save_interval = auto_save_interval
        
        # Update auto-save timer if needed
        if auto_save_enabled != previous_auto_save:
            if auto_save_enabled:
                self.win.start_auto_save_timer()
                self.win.statusbar.set_text("Auto-save enabled")
            else:
                self.win.stop_auto_save_timer()
                self.win.statusbar.set_text("Auto-save disabled")
        elif auto_save_enabled:
            # Restart timer with new interval
            self.win.stop_auto_save_timer()
            self.win.start_auto_save_timer()
            self.win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
        
        dialog.close()

    def show_error_dialog(self, message):
        """Show error message dialog"""
        if not self.windows:
            print(f"Error: {message}")
            return
            
        parent_window = self.windows[0]
        
        dialog = Adw.Dialog.new()
        dialog.set_title("Error")
        dialog.set_content_width(350)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        error_icon = Gtk.Image.new_from_icon_name("dialog-error-symbolic")
        error_icon.set_pixel_size(48)
        error_icon.set_margin_bottom(12)
        content_box.append(error_icon)
        
        message_label = Gtk.Label(label=message)
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.CENTER)
        button_box.set_margin_top(12)
        
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(ok_button)
        
        content_box.append(button_box)
        
        dialog.set_child(content_box)
        dialog.present(parent_window)

def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
