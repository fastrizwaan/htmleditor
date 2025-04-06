#!/usr/bin/env python3
import sys
import gi
import re
import os
import json

# Hardware Accelerated Rendering (0); Software Rendering (1)
os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '0'

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gdk, WebKit, GLib, Gio
from methods import *

class HTMLEditor(Adw.ApplicationWindow):
    def __init__(self, *args, application=None, **kwargs):
        super().__init__(application=application, *args, **kwargs)
        
        # Application-level attributes
        self.windows = [self]  # Track all open windows (starting with self)
        self.window_buttons = {}  # Track window menu buttons {window_id: button}
        
        # Window-specific attributes
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
        self.set_default_size(900, 700)
        self.set_title("Untitled - HTML Editor")
        
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.main_box.set_vexpand(True)
        self.main_box.set_hexpand(True)
        self.create_header_bar()
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
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
        self.create_actions()
        self.connect("close-request", self.on_close_request)

    setup_keyboard_shortcuts = setup_keyboard_shortcuts
    
        
    # Header bar creation
    def create_header_bar(self):
        header = Adw.HeaderBar()
        
        new_button = Gtk.Button(icon_name="document-new-symbolic")
        new_button.set_tooltip_text("New Document in New Window")
        new_button.connect("clicked", self.on_new_clicked)
        
        open_button = Gtk.Button(icon_name="document-open-symbolic")
        open_button.set_tooltip_text("Open File in New Window")
        open_button.connect("clicked", self.on_open_clicked)
        
        save_button = Gtk.Button(icon_name="document-save-symbolic")
        save_button.set_tooltip_text("Save File")
        save_button.connect("clicked", self.on_save_clicked)
        
        self.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        self.undo_button.set_tooltip_text("Undo")
        self.undo_button.connect("clicked", self.on_undo_clicked)
        self.undo_button.set_sensitive(False)
        
        self.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        self.redo_button.set_tooltip_text("Redo")
        self.redo_button.connect("clicked", self.on_redo_clicked)
        self.redo_button.set_sensitive(False)
        
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("Preferences", "win.preferences")
        menu.append("About", "win.about")
        menu.append("Quit", "win.quit")
        menu_button.set_menu_model(menu)
        
        header.pack_start(new_button)
        header.pack_start(open_button)
        header.pack_start(save_button)
        header.pack_start(self.undo_button)
        header.pack_start(self.redo_button)
        header.pack_end(menu_button)
        
        self.main_box.append(header)
        self.add_window_menu_button(self)

    # Window menu management
    def create_window_menu(self):
        menu = Gio.Menu()
        actions_section = Gio.Menu()
        window_section = Gio.Menu()
        
        if len(self.windows) > 1:
            actions_section.append("Close Other Windows", "win.close-other-windows")
            menu.append_section("Actions", actions_section)
        
        for i, win in enumerate(self.windows):
            title = win.get_menu_title()
            action_string = f"win.switch-window({i})"
            window_section.append(title, action_string)
        
        menu.append_section("Windows", window_section)
        return menu

    def update_window_menu(self):
        fresh_menu = self.create_window_menu()
        show_button = len(self.windows) > 1
        
        windows_needing_buttons = set(self.windows)
        buttons_to_remove = []
        
        for window_id, button in self.window_buttons.items():
            window_exists = False
            for win in self.windows:
                if id(win) ==植物window_id:
                    window_exists = True
                    windows_needing_buttons.remove(win)
                    break
            
            if window_exists:
                button.set_menu_model(fresh_menu)
                button.set_visible(show_button)
            else:
                buttons_to_remove.append(window_id)
        
        for window_id in buttons_to_remove:
            del self.window_buttons[window_id]
        
        for win in windows_needing_buttons:
            self.add_window_menu_button(win, fresh_menu)

    def add_window_menu_button(self, win, menu_model=None):
        header = win.main_box.get_first_child()
        if not header or not isinstance(header, Adw.HeaderBar):
            return
        
        window_button = None
        child = header.get_first_child()
        while child:
            if isinstance(child, Gtk.MenuButton) and child.get_icon_name() == "window-new-symbolic":
                window_button = child
                break
            child = child.get_next_sibling()
        
        if menu_model is None:
            menu_model = self.create_window_menu()
        
        show_button = len(self.windows) > 1
        
        if window_button:
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
        elif show_button:
            window_button = Gtk.MenuButton()
            window_button.set_icon_name("window-new-symbolic")
            window_button.set_tooltip_text("Window List")
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
            header.pack_end(window_button)
            self.window_buttons[id(win)] = window_button
        
        if window_button:
            self.window_buttons[id(win)] = window_button

    # Actions setup
    def create_actions(self):
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self.on_quit)
        self.add_action(quit_action)
        
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self.on_about)
        self.add_action(about_action)
        
        preferences_action = Gio.SimpleAction.new("preferences", None)
        preferences_action.connect("activate", self.on_preferences)
        self.add_action(preferences_action)
        
        new_window_action = Gio.SimpleAction.new("new-window", None)
        new_window_action.connect("activate", self.on_new_window)
        self.add_action(new_window_action)
        
        close_other_windows_action = Gio.SimpleAction.new("close-other-windows", None)
        close_other_windows_action.connect("activate", self.on_close_other_windows)
        self.add_action(close_other_windows_action)
        
        switch_window_action = Gio.SimpleAction.new("switch-window", GLib.VariantType.new("i"))
        switch_window_action.connect("activate", self.on_switch_window)
        self.add_action(switch_window_action)

    # Event handlers for actions
    def on_new_window(self, action, param):
        win = HTMLEditor(application=self.get_application())
        self.windows.append(win)
        win.present()
        self.update_window_menu()

    def on_switch_window(self, action, param):
        index = param.get_int32()
        if 0 <= index < len(self.windows):
            self.windows[index].present()

    def on_close_other_windows(self, action, param):
        if len(self.windows) <= 1:
            return
        
        active_window = self if self.is_active() else self.windows[0]
        windows_to_close_count = len(self.windows) - 1
        
        dialog = Adw.Dialog.new()
        dialog.set_title(f"Close {windows_to_close_count} Other Window{'s' if windows_to_close_count > 1 else ''}?")
        dialog.set_content_width(350)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        message_label = Gtk.Label()
        message_label.set_text(f"Are you sure you want to close {windows_to_close_count} other window{'s' if windows_to_close_count > 1 else ''}?")
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        close_button = Gtk.Button(label="Close Windows")
        close_button.add_css_class("destructive-action")
        close_button.connect("clicked", lambda btn: self._on_close_others_response(dialog, active_window))
        button_box.append(close_button)
        
        content_box.append(button_box)
        dialog.set_child(content_box)
        dialog.present(active_window)

    def _on_close_others_response(self, dialog, active_window):
        dialog.close()
        windows_to_close = [win for win in self.windows if win != active_window]
        for win in windows_to_close[:]:
            win.close()
        if active_window in self.windows:
            active_window.present()
        self.update_window_menu()

    on_quit = on_quit

    def on_close_request(self, *args):
        if self in self.windows:
            self.windows.remove(self)
            if id(self) in self.window_buttons:
                del self.window_buttons[id(self)]
            self.update_window_menu()
            if self.windows:
                self.windows[0].present()
        return False

    # Remaining methods (unchanged from HTMLEditorWindow)
    def get_menu_title(self):
        if self.current_file:
            path = self.current_file.get_path() if hasattr(self.current_file, 'get_path') else self.current_file
            filename = os.path.splitext(os.path.basename(path))[0]
            return f"{filename}{'*' if self.modified else ''}"
        else:
            return f"Untitled{'*' if self.modified else ''}"

    def create_bottom_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
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
        
        toolbar.append(bold_button)
        toolbar.append(italic_button)
        toolbar.append(underline_button)
        toolbar.append(spacer)
        toolbar.append(close_button)
        
        return toolbar

    def setup_toolbar_animation(self):
        if hasattr(self, 'overlay_setup_done') and self.overlay_setup_done:
            return
        
        self.overlay = Gtk.Overlay()
        self.overlay.set_vexpand(True)
        self.overlay.set_hexpand(True)
        
        content_box = self.webview.get_parent()
        if self.webview.get_parent():
            self.webview.get_parent().remove(self.webview)
        
        webview_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        webview_box.set_vexpand(True)
        webview_box.set_hexpand(True)
        webview_box.append(self.webview)
        
        self.overlay.set_child(webview_box)
        
        self.toolbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.toolbar_box.set_halign(Gtk.Align.FILL)
        self.toolbar_box.set_valign(Gtk.Align.END)
        self.toolbar_box.set_margin_start(0)
        self.toolbar_box.set_margin_end(0)
        self.toolbar_box.set_margin_bottom(0)
        self.toolbar_box.add_css_class("toolbar-overlay")
        
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
        
        self.overlay.add_overlay(self.toolbar_box)
        
        if content_box:
            child = content_box.get_first_child()
            while child:
                next_child = child.get_next_sibling()
                if child != self.statusbar and child != self.bottom_toolbar:
                    content_box.remove(child)
                child = next_child
            content_box.append(self.overlay)
        
        if self.statusbar.get_parent():
            self.statusbar.get_parent().remove(self.statusbar)
        content_box.append(self.statusbar)
        
        self.toolbar_box.set_opacity(0.0)
        self.toolbar_box.set_visible(True)
        
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

    def toggle_toolbar(self, *args):
        if hasattr(self, 'toolbar_box'):
            current_opacity = self.toolbar_box.get_opacity()
            if current_opacity > 0.0:
                self.toolbar_box.set_opacity(0.0)
                self.statusbar.set_text("Toolbar hidden")
            else:
                self.toolbar_box.set_opacity(1.0)
                self.statusbar.set_text("Toolbar shown")
        return True

    def on_close_toolbar_clicked(self, button):
        if hasattr(self, 'toolbar_box'):
            self.toolbar_box.set_opacity(0.0)
            self.statusbar.set_text("Toolbar hidden")
        else:
            self.bottom_toolbar.set_visible(False)

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
                margin: 40px;
                padding: 0;
                font-family: Arial, sans-serif;
            }}
            #editor {{
                border: 1px solid #ccc;
                padding: 10px;
                outline: none;
                min-height: 200px;
                height: 100%;
                box-sizing: border-box;
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
        return f"""
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
        return """
        function saveState() {
            window.undoStack.push(document.getElementById('editor').innerHTML);
            if (window.undoStack.length > 100) {
                window.undoStack.shift();
            }
        }
        """

    def perform_undo_js(self):
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
        return """
        function getStackSizes() {
            return {
                undoSize: window.undoStack.length,
                redoSize: window.redoStack.length
            };
        }
        """

    def set_content_js(self):
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
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)

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

    def on_new_clicked(self, button):
        win = HTMLEditor(application=self.get_application())
        self.windows.append(win)
        win.present()
        self.update_window_menu()
        win.statusbar.set_text("New document created")

    def on_open_clicked(self, button):
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
        
        if self.modified or self.current_file:
            dialog.open(self, None, self.on_open_new_window_response)
        else:
            dialog.open(self, None, self.on_open_current_window_response)

    def on_open_new_window_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                win = HTMLEditor(application=self.get_application())
                self.windows.append(win)
                win.load_file(filepath)
                win.present()
                self.update_window_menu()
        except GLib.Error as e:
            if e.domain != 'gtk-dialog-error-quark' or e.code != 2:
                self.show_error_dialog(f"Error opening file: {e}")

    def on_open_current_window_response(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                filepath = file.get_path()
                self.load_file(filepath)
                self.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
        except GLib.Error as e:
            if e.domain != 'gtk-dialog-error-quark' or e.code != 2:
                self.show_error_dialog(f"Error opening file: {e}")

    def load_file(self, filepath):
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
            
            content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            js_code = f'setContent("{content}");'
            
            def execute_when_ready():
                load_status = self.webview.get_estimated_load_progress()
                if load_status == 1.0:
                    self.execute_js(js_code)
                    return False
                else:
                    def on_load_changed(webview, event):
                        if event == WebKit.LoadEvent.FINISHED:
                            self.execute_js(js_code)
                            webview.disconnect_by_func(on_load_changed)
                    self.webview.connect("load-changed", on_load_changed)
                    return False
            
            GLib.timeout_add(50, execute_when_ready)
            
            self.current_file = Gio.File.new_for_path(filepath)
            self.modified = False
            self.update_window_title()
            self.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
        except Exception as e:
            print(f"Error loading file: {str(e)}")
            self.statusbar.set_text(f"Error loading file: {str(e)}")
            self.show_error_dialog(f"Error loading file: {e}")

    def update_window_title(self):
        if self.current_file:
            path = self.current_file.get_path() if hasattr(self.current_file, 'get_path') else self.current_file
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
                self.current_file = file
                self.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    self._on_get_html_content,
                    file
                )
        except GLib.Error as error:
            print(f"Error saving file: {error.message}")

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
                editor_content = js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else str(js_result)
                self.save_html_content(editor_content, file, self._on_file_saved)
        except Exception as e:
            print(f"Error getting HTML content: {e}")

    def _on_file_saved(self, file, result):
        try:
            success, _ = file.replace_contents_finish(result)
            if success:
                self.current_file = file
                self.statusbar.set_text(f"Saved: {file.get_path()}")
                self.update_window_title()
                self.modified = False
        except GLib.Error as error:
            print(f"Error writing file: {error.message}")

    def on_bold_clicked(self, button):
        self.execute_js("document.execCommand('bold', false, null);")

    def on_italic_clicked(self, button):
        self.execute_js("document.execCommand('italic', false, null);")

    def on_underline_clicked(self, button):
        self.execute_js("document.execCommand('underline', false, null);")

    def on_auto_save_toggled(self, switch, gparam):
        active = switch.get_active()
        self.auto_save_enabled = active
        self.statusbar.set_text(f"Auto-save {'enabled' if active else 'disabled'}")
        if active:
            self.start_auto_save_timer()
        else:
            self.stop_auto_save_timer()

    def on_auto_save_interval_changed(self, spinner):
        self.auto_save_interval = spinner.get_value_as_int()
        self.statusbar.set_text(f"Auto-save interval set to {self.auto_save_interval} seconds")
        if self.auto_save_enabled:
            self.stop_auto_save_timer()
            self.start_auto_save_timer()

    def start_auto_save_timer(self):
        self.stop_auto_save_timer()
        if self.current_file:
            self.auto_save_source_id = GLib.timeout_add_seconds(
                self.auto_save_interval,
                self.perform_auto_save
            )
        else:
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
                self.auto_save_source_id = GLib.timeout_add_seconds(
                    self.auto_save_interval,
                    self.perform_auto_save
                )
                self.statusbar.set_text(f"Auto-save will save to: {file.get_path()}")
            else:
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
            return False
        self.webview.evaluate_javascript(
            "document.getElementById('editor').innerHTML;",
            -1, None, None,
            None,
            self._on_auto_save_content,
            None
        )
        return True

    def _on_auto_save_content(self, webview, result, user_data):
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result and self.current_file:
                editor_content = js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else str(js_result)
                self.save_html_content(editor_content, self.current_file, self._on_auto_save_completed)
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

    def on_about(self, action, param):
        about = Adw.AboutWindow(
            transient_for=self,
            application_name="HTML Editor",
            application_icon="text-editor",
            developer_name="Developer",
            version="1.0",
            developers=["Your Name"],
            copyright="© 2025"
        )
        about.present()

    def on_preferences(self, action, param):
        dialog = Adw.Dialog.new()
        dialog.set_title("Preferences")
        dialog.set_content_width(450)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        header = Gtk.Label()
        header.set_markup("<b>Editor Settings</b>")
        header.set_halign(Gtk.Align.START)
        header.set_margin_bottom(12)
        content_box.append(header)
        
        auto_save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_save_box.set_margin_start(12)
        auto_save_label = Gtk.Label(label="Auto Save:")
        auto_save_label.set_halign(Gtk.Align.START)
        auto_save_label.set_hexpand(True)
        auto_save_switch = Gtk.Switch()
        auto_save_switch.set_active(self.auto_save_enabled)
        auto_save_switch.set_valign(Gtk.Align.CENTER)
        auto_save_box.append(auto_save_label)
        auto_save_box.append(auto_save_switch)
        content_box.append(auto_save_box)
        
        interval_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        interval_box.set_margin_start(12)
        interval_box.set_margin_top(12)
        interval_label = Gtk.Label(label="Auto-save Interval (seconds):")
        interval_label.set_halign(Gtk.Align.START)
        interval_label.set_hexpand(True)
        adjustment = Gtk.Adjustment(value=self.auto_save_interval, lower=10, upper=600, step_increment=10)
        spinner = Gtk.SpinButton()
        spinner.set_adjustment(adjustment)
        spinner.set_valign(Gtk.Align.CENTER)
        interval_box.append(interval_label)
        interval_box.append(spinner)
        content_box.append(interval_box)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        ok_button = Gtk.Button(label="OK")
        ok_button.add_css_class("suggested-action")
        ok_button.connect("clicked", lambda btn: self.save_preferences(dialog, auto_save_switch.get_active(), spinner.get_value_as_int()))
        button_box.append(ok_button)
        
        content_box.append(button_box)
        dialog.set_child(content_box)
        dialog.present(self)

    def save_preferences(self, dialog, auto_save_enabled, interval):
        self.auto_save_enabled = auto_save_enabled
        self.auto_save_interval = interval
        if self.auto_save_enabled:
            self.start_auto_save_timer()
        else:
            self.stop_auto_save_timer()
        dialog.close()

    def show_error_dialog(self, message):
        dialog = Adw.MessageDialog.new(self, "Error", message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda d, r: d.close())
        dialog.present()

    def on_close_shortcut(self, *args):
        self.close()
        return True

    def on_close_others_shortcut(self, *args):
        self.on_close_other_windows(None, None)
        return True

    def on_undo_shortcut(self, *args):
        self.perform_undo()
        return True

    def on_redo_shortcut(self, *args):
        self.perform_redo()
        return True

def main():
    app = Gtk.Application(application_id='io.github.fastrizwaan.htmleditor')
    app.connect('activate', lambda app: HTMLEditor(application=app).present())
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
