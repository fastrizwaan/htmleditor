#!/usr/bin/env python3
import sys
import gi
import re
import os

# Hardware Acclerated Rendering (0); Software Rendering (1)
os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '1'

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gdk, WebKit, GLib, Gio, Pango, PangoCairo, Gdk

# Import file operation functions directly
import file_operations # open, save, save as
import find
import formatting_operations

class HTMLEditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='io.github.fastrizwaan.htmleditor',
                        flags=Gio.ApplicationFlags.HANDLES_OPEN,
                        **kwargs)
        self.windows = []  # Track all open windows
        self.window_buttons = {}  # Track window menu buttons {window_id: button}
        self.connect('activate', self.on_activate)
        self.connect("open", self.on_open)
        
        # Window properties (migrated from HTMLEditorWindow)
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None
        
        # Import methods from file_operations module
        file_operation_methods = [
            # File opening methods
            'on_open_clicked', 'on_open_new_window_response',
            'on_open_current_window_response', 'load_file',
            '_process_image_references', '_get_mime_type', 'cleanup_temp_files',
            'convert_with_libreoffice', 'show_loading_dialog',
            
            # File saving methods
            'on_save_clicked', 'show_format_selection_dialog', 'on_save_as_clicked', 'show_custom_save_dialog',
            '_create_custom_save_dialog', '_get_shortened_path',
            '_on_browse_clicked','_on_dialog_response', '_on_format_selection_response',
            '_on_folder_selected', 'show_save_as_warning_dialog', '_on_save_warning_response',
            '_get_file_path_from_dialog', 'show_conversion_notification', 
            'update_save_sensitivity', 
            
            
            # Format-specific save methods
            'save_as_mhtml', 'save_webkit_callback', 'save_as_html',
            'save_as_text','save_as_markdown', '_simple_markdown_to_html',

            # Save as PDF
            'save_as_pdf', '_save_pdf_step1', '_save_pdf_step2', '_pdf_save_success',
            '_pdf_save_cleanup', '_cleanup_temp_dir', 'set_secondary_text'
            # Callback handlers
            'save_html_callback', 'save_text_callback',
            'save_markdown_callback', 'save_completion_callback',
            
            # Legacy methods for backward compatibility
            '_on_save_response', '_on_save_as_response', '_on_get_html_content',
            '_on_file_saved',
            
            # webkit
            '_on_editor_ready_for_mhtml', '_check_mhtml_load_status', 
            '_handle_mhtml_load_check', '_check_mhtml_load_error',
            'load_mhtml_with_webkit', '_load_mhtml_file', '_process_mhtml_resources',
            '_extract_mhtml_content', '_on_mhtml_content_extracted',
        ]
        
        # Import methods from file_operations
        for method_name in file_operation_methods:
            if hasattr(file_operations, method_name):
                setattr(self, method_name, getattr(file_operations, method_name).__get__(self, HTMLEditorApp))
                
        # Import methods from find module
        find_methods = [
            'create_find_bar', 'on_find_shortcut', 'on_find_clicked',
            'on_close_find_clicked', 'on_case_sensitive_toggled',
            'on_find_text_changed', 'on_search_result', 'on_find_next_clicked',
            'on_find_previous_clicked', 'on_replace_clicked', 
            'on_replace_all_clicked', 'on_replace_all_result', 
            'on_find_key_pressed', 'on_find_button_toggled',
            'populate_find_field_from_selection', '_on_get_selection_for_find',
            'search_functions_js'
        ]
        
        # Import methods from find module
        for method_name in find_methods:
            if hasattr(find, method_name):
                setattr(self, method_name, getattr(find, method_name).__get__(self, HTMLEditorApp))

        # Import methods from formatting_toolbar module
        formatting_toolbar_methods = [
            'on_select_all_clicked', 'on_bold_shortcut', 'on_italic_shortcut',
            'on_underline_shortcut', 'on_strikeout_shortcut', 'on_subscript_shortcut',
            'on_superscript_shortcut', 'on_bold_toggled', 'on_italic_toggled',
            'on_underline_toggled', 'on_strikeout_toggled', 'on_subscript_toggled',
            'on_superscript_toggled', 'on_formatting_changed', 'on_indent_clicked',
            'on_outdent_clicked', 'on_bullet_list_toggled', 'on_numbered_list_toggled',
            '_update_alignment_buttons', 'on_align_left_toggled', 'on_align_center_toggled',
            'on_align_right_toggled', 'on_align_justify_toggled', '_update_alignment_buttons',
            'selection_change_js', 'on_paragraph_style_changed', 'on_font_changed',
            'on_font_size_changed', 'cleanup_editor_tags', 'create_color_button',
            'on_font_color_button_clicked', 'on_font_color_selected', 'on_font_color_automatic_clicked',
            'on_more_font_colors_clicked', 'on_font_color_dialog_response', 'apply_font_color',
            'on_bg_color_button_clicked', 'on_bg_color_selected', 'on_bg_color_automatic_clicked',
            'on_more_bg_colors_clicked', 'on_bg_color_dialog_response', 'apply_bg_color',
            'set_box_color', 'on_clear_formatting_clicked', 'on_change_case',
            'on_drop_cap_clicked', '_handle_drop_cap_result', 'on_show_formatting_marks_toggled',
            
        ]

        # Import methods from formatting_toolbar module
        for method_name in formatting_toolbar_methods:
            if hasattr(formatting_operations, method_name):
                setattr(self, method_name, getattr(formatting_operations, method_name).__get__(self, HTMLEditorApp))
        
    def do_startup(self):
        """Initialize application and set up CSS provider"""
        Adw.Application.do_startup(self)
        
        # Set up CSS provider
        self.setup_css_provider()
        
        # Create actions
        self.create_actions()


    def setup_css_provider(self):
        """Set up CSS provider for custom styling"""
        self.css_provider = Gtk.CssProvider()
        
        css_data = b"""
.toolbar-container { padding: 0px 0px; background-color: rgba(127, 127, 127, 0.05); }
.flat { background: none; }
.flat:hover { background: rgba(127, 127, 127, 0.25); }
.flat:checked { background: rgba(127, 127, 127, 0.25); }
colorbutton.flat, colorbutton.flat button { background: none; }
colorbutton.flat:hover, colorbutton.flat button:hover { background: rgba(127, 127, 127, 0.25); }
dropdown.flat, dropdown.flat button { background: none; border-radius: 5px; }
dropdown.flat:hover { background: rgba(127, 127, 127, 0.25); }
.flat-header { background: rgba(127, 127, 127, 0.05); border: none; box-shadow: none; padding: 0px; }
.button-box button { min-width: 80px; min-height: 36px; }
.highlighted { background-color: rgba(127, 127, 127, 0.15); }
.toolbar-group { margin: 0px 3px; }
.toolbar-separator { min-height: 0px; min-width: 1px; background-color: alpha(currentColor, 0.15); margin: 0px 0px; }
.color-indicator { min-height: 2px; min-width: 16px; margin-top: 1px; margin-bottom: 0px; border-radius: 2px; }
.color-box { padding: 0px; }




.linked button               {background-color: rgba(127, 127, 127, 0.10); border: solid 1px rgba(127, 127, 127, 0.00); }
.linked button:hover         {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}
.linked button:active        {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked       {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked:hover {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}

/* Corrected menubutton selectors - removed space after colon */
.linked menubutton:first-child  {
    border-top-left-radius: 5px; 
    border-bottom-left-radius: 5px; 
    border-top-right-radius: 0px; 
    border-bottom-right-radius: 0px;
}

.linked menubutton:last-child {
    border-top-left-radius: 0px; 
    border-bottom-left-radius: 0px; 
    border-top-right-radius: 5px; 
    border-bottom-right-radius: 5px; 
} 

/* Additional recommended fixes for consistent styling */
.linked menubutton button {
    background-color: rgba(127, 127, 127, 0.10);
    border: solid 1px rgba(127, 127, 127, 0.00);
}

.linked menubutton button:hover {
    background-color: rgba(127, 127, 127, 0.35);
    border: solid 1px rgba(127, 127, 127, 0.30);
}

.linked menubutton button:active, 
.linked menubutton button:checked {
    background-color: rgba(127, 127, 127, 0.35);
    border: solid 1px rgba(127, 127, 127, 0.00);
}

.linked menubutton button:checked:hover {
    background-color: rgba(127, 127, 127, 0.35);
    border: solid 1px rgba(127, 127, 127, 0.30);
}

.linked splitbutton > menubutton > button.toggle {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px; padding: 0px 2px 0px 2px; }
.linked splitbutton > button  {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton:first-child > button  {
    border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton:last-child > button  {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton:last-child > menubutton > button.toggle   {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 5px; border-bottom-right-radius: 5px;}

"""
        
        # Load the CSS data
        try:
            self.css_provider.load_from_data(css_data)
        except Exception as e:
            print(f"Error loading CSS data: {e}")
            return
        
        # Apply the CSS provider using the appropriate method based on GTK version
        try:
            # GTK4 method (modern approach)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except (AttributeError, TypeError) as e:
            # Fallback for GTK3 if the application is using an older version
            try:
                screen = Gdk.Screen.get_default()
                Gtk.StyleContext.add_provider_for_screen(
                    screen,
                    self.css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            except Exception as e2:
                print(f"Error applying CSS provider: {e2}")
        
    def on_activate(self, app):
        """Handle application activation (new window)"""
        win = self.create_window()
        win.present()
        
        # Set focus after window is shown - this is crucial
        GLib.timeout_add(500, lambda: self.set_initial_focus(win))
        
        self.update_window_menu()


    def on_open(self, app, files, n_files, hint):
        """Handle file opening"""
        windows_added = False
        
        for file in files:
            file_path = file.get_path()
            existing_win = None
            for win in self.windows:
                if hasattr(win, 'current_file') and win.current_file and win.current_file.get_path() == file_path:
                    existing_win = win
                    break
            
            if existing_win:
                existing_win.present()
            else:
                win = self.create_window()
                self.load_file(win, file_path)
                win.present()
                windows_added = True
                
        if windows_added:
            self.update_window_menu()
                
    def setup_headerbar_content(self, win):
        """Create simplified headerbar content (menu and window buttons)"""
        win.headerbar.set_margin_top(0)
        win.headerbar.set_margin_bottom(0)
        # Create menu
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        menu_button.add_css_class("flat")  # Add flat style
        
        menu = Gio.Menu()
        
        # File menu section
        file_section = Gio.Menu()
        file_section.append("New Window", "app.new-window")
        file_section.append("Open", "app.open") # You'll need to add this action
        file_section.append("Save", "app.save") # You'll need to add this action
        file_section.append("Save As", "app.save-as") # You'll need to add this action
        menu.append_section("File", file_section)
        
        # View menu section
        view_section = Gio.Menu()
        view_section.append("Show/Hide File Toolbar", "app.toggle-file-toolbar") # You'll need to add this action
        view_section.append("Show/Hide Format Toolbar", "app.toggle-format-toolbar") # You'll need to add this action
        view_section.append("Show/Hide Statusbar", "app.toggle-statusbar") # You'll need to add this action
        menu.append_section("View", view_section)
        
        # App menu section
        app_section = Gio.Menu()
        app_section.append("Preferences", "app.preferences")
        app_section.append("About", "app.about")
        app_section.append("Quit", "app.quit")
        menu.append_section("Application", app_section)
        
        menu_button.set_menu_model(menu)
        
        # Set up the window title widget (can be customized further)
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Untitled  - HTML Editor")
        win.title_widget = title_widget  # Store for later updates
        
        # Save reference to update title 
        win.headerbar.set_title_widget(title_widget)
        
        # Add buttons to header bar
        win.headerbar.pack_start(menu_button)
        
        # Create window menu button on the right side
        self.add_window_menu_button(win)
            
## Insert related code


    def insert_text_box_js(self):
        return """ """

    def insert_image_js(self):
        """JavaScript for insert image and related functionality"""
        return """ """

    def insert_link_js(self):
        """JavaScript for insert link and related functionality"""
        return """ """

    # Python handler for table insertion
    def on_insert_table_clicked(self, win, btn):
        """Handle table insertion button click"""
        return

    def on_insert_text_box_clicked(self, win, btn):
        """Handle text box insertion button click, textbox"""
        return
        
    def on_insert_image_clicked(self, win, btn):
        """Handle image insertion button click"""
        return

    def on_insert_link_clicked(self, win, btn):
        """show a dialog with URL and Text """
        return 
      
## /Insert related code

    def on_cut_clicked(self, win, btn):
        """Handle cut button click"""
        self.execute_js(win, """
            (function() {
                let sel = window.getSelection();
                if (sel.rangeCount) {
                    document.execCommand('cut');
                    return true;
                }
                return false;
            })();
        """)
        win.statusbar.set_text("Cut to clipboard")

    def on_copy_clicked(self, win, btn):
        """Handle copy button click"""
        self.execute_js(win, """
            (function() {
                let sel = window.getSelection();
                if (sel.rangeCount) {
                    document.execCommand('copy');
                    return true;
                }
                return false;
            })();
        """)
        win.statusbar.set_text("Copied to clipboard")

    def on_paste_clicked(self, win, btn):
        """Handle paste button click"""
        # Try to get text from clipboard
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.read_text_async(None, self.on_text_received, win)
        win.statusbar.set_text("Pasting from clipboard...")

    def on_text_received(self, clipboard, result, win):
        """Handle clipboard text retrieval"""
        try:
            text = clipboard.read_text_finish(result)
            if text:
                # Escape text for JavaScript
                import json
                text_json = json.dumps(text)
                # Insert the text at cursor position
                self.execute_js(win, f"""
                    (function() {{
                        document.execCommand('insertText', false, {text_json});
                        return true;
                    }})();
                """)
                win.statusbar.set_text("Pasted from clipboard")
            else:
                win.statusbar.set_text("No text in clipboard")
        except GLib.Error as e:
            print("Paste error:", e.message)
            win.statusbar.set_text(f"Paste failed: {e.message}")
            
    def on_zoom_changed(self, win, scale, zoom_button):
        """Handle zoom scale change"""
        zoom_level = int(scale.get_value())
        zoom_button.set_label(f"{zoom_level}%")
        win.zoom_level = zoom_level
        
        # Apply zoom to the editor
        self.apply_zoom(win, zoom_level)

    def on_zoom_preset_clicked(self, win, preset, scale, zoom_button, popover):
        """Handle zoom preset button click"""
        scale.set_value(preset)
        zoom_button.set_label(f"{preset}%")
        win.zoom_level = preset
        
        # Apply zoom to the editor
        self.apply_zoom(win, preset)
        
        # Close the popover
        popover.popdown()

    def apply_zoom(self, win, zoom_level):
        """Apply zoom level to the editor"""
        # Convert percentage to scale factor (1.0 = 100%)
        scale_factor = zoom_level / 100.0
        
        # Apply zoom using JavaScript
        js_code = f"""
        (function() {{
            document.body.style.zoom = "{scale_factor}";
            document.getElementById('editor').style.zoom = "{scale_factor}";
            return true;
        }})();
        """
        
        self.execute_js(win, js_code)
        #win.statusbar.set_text(f"Zoom level: {zoom_level}%")    
        



        
    def setup_keyboard_shortcuts(self, win):
        """Setup keyboard shortcuts for the window"""
        # Create a shortcut controller
        controller = Gtk.ShortcutController()
        
        # Create Ctrl+Shift+F shortcut for toggling the file toolbar
        trigger_file_toolbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>f")
        action_file_toolbar = Gtk.CallbackAction.new(lambda *args: self.toggle_file_toolbar(win, *args))
        shortcut_file_toolbar = Gtk.Shortcut.new(trigger_file_toolbar, action_file_toolbar)
        controller.add_shortcut(shortcut_file_toolbar)

        # Create Ctrl+P shortcut for print
        trigger_print = Gtk.ShortcutTrigger.parse_string("<Control>p")
        action_print = Gtk.CallbackAction.new(lambda *args: self.on_print_clicked(win, None))
        shortcut_print = Gtk.Shortcut.new(trigger_print, action_print)
        controller.add_shortcut(shortcut_print)
        
        # Create Ctrl+F shortcut for find
        trigger_find = Gtk.ShortcutTrigger.parse_string("<Control>f")
        action_find = Gtk.CallbackAction.new(lambda *args: self.on_find_shortcut(win, *args))
        shortcut_find = Gtk.Shortcut.new(trigger_find, action_find)
        controller.add_shortcut(shortcut_find)
        
        # Create Ctrl+Shift+S shortcut for toggling the statusbar
        trigger_statusbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>s")
        action_statusbar = Gtk.CallbackAction.new(lambda *args: self.toggle_statusbar(win, *args))
        shortcut_statusbar = Gtk.Shortcut.new(trigger_statusbar, action_statusbar)
        controller.add_shortcut(shortcut_statusbar)
        
        # Create Ctrl+Shift+H shortcut for toggling the headerbar
        trigger_headerbar = Gtk.ShortcutTrigger.parse_string("<Control><Shift>h")
        action_headerbar = Gtk.CallbackAction.new(lambda *args: self.toggle_headerbar(win, *args))
        shortcut_headerbar = Gtk.Shortcut.new(trigger_headerbar, action_headerbar)
        controller.add_shortcut(shortcut_headerbar)
        
        # Create Ctrl+Z shortcut for undo
        trigger_undo = Gtk.ShortcutTrigger.parse_string("<Control>z")
        action_undo = Gtk.CallbackAction.new(lambda *args: self.on_undo_shortcut(win, *args))
        shortcut_undo = Gtk.Shortcut.new(trigger_undo, action_undo)
        controller.add_shortcut(shortcut_undo)
        
        # Create Ctrl+Y shortcut for redo
        trigger_redo = Gtk.ShortcutTrigger.parse_string("<Control>y")
        action_redo = Gtk.CallbackAction.new(lambda *args: self.on_redo_shortcut(win, *args))
        shortcut_redo = Gtk.Shortcut.new(trigger_redo, action_redo)
        controller.add_shortcut(shortcut_redo)
        
        # Create Ctrl+W shortcut for closing current window
        trigger_close = Gtk.ShortcutTrigger.parse_string("<Control>w")
        action_close = Gtk.CallbackAction.new(lambda *args: self.on_close_shortcut(win, *args))
        shortcut_close = Gtk.Shortcut.new(trigger_close, action_close)
        controller.add_shortcut(shortcut_close)
        
        # Create Ctrl+Shift+W shortcut for closing other windows
        trigger_close_others = Gtk.ShortcutTrigger.parse_string("<Control><Shift>w")
        action_close_others = Gtk.CallbackAction.new(lambda *args: self.on_close_others_shortcut(win, *args))
        shortcut_close_others = Gtk.Shortcut.new(trigger_close_others, action_close_others)
        controller.add_shortcut(shortcut_close_others)
        
        # FORMATTING SHORTCUTS
        
        # Ctrl+B for Bold
        trigger_bold = Gtk.ShortcutTrigger.parse_string("<Control>b")
        action_bold = Gtk.CallbackAction.new(lambda *args: self.on_bold_shortcut(win, *args))
        shortcut_bold = Gtk.Shortcut.new(trigger_bold, action_bold)
        controller.add_shortcut(shortcut_bold)
        
        # Ctrl+I for Italic
        trigger_italic = Gtk.ShortcutTrigger.parse_string("<Control>i")
        action_italic = Gtk.CallbackAction.new(lambda *args: self.on_italic_shortcut(win, *args))
        shortcut_italic = Gtk.Shortcut.new(trigger_italic, action_italic)
        controller.add_shortcut(shortcut_italic)
        
        # Ctrl+U for Underline
        trigger_underline = Gtk.ShortcutTrigger.parse_string("<Control>u")
        action_underline = Gtk.CallbackAction.new(lambda *args: self.on_underline_shortcut(win, *args))
        shortcut_underline = Gtk.Shortcut.new(trigger_underline, action_underline)
        controller.add_shortcut(shortcut_underline)       
        
        # Ctrl+Shift+X for Strikeout
        trigger_strikeout = Gtk.ShortcutTrigger.parse_string("<Control><Shift>x")
        action_strikeout = Gtk.CallbackAction.new(lambda *args: self.on_strikeout_shortcut(win, *args))
        shortcut_strikeout = Gtk.Shortcut.new(trigger_strikeout, action_strikeout)
        controller.add_shortcut(shortcut_strikeout)

        # Create Ctrl+= shortcut for subscript (standard shortcut)
        trigger_subscript = Gtk.ShortcutTrigger.parse_string("<Control>equal")
        action_subscript = Gtk.CallbackAction.new(lambda *args: self.on_subscript_shortcut(win, *args))
        shortcut_subscript = Gtk.Shortcut.new(trigger_subscript, action_subscript)
        controller.add_shortcut(shortcut_subscript)
        
        # Create Ctrl++ (or Ctrl+Shift+=) shortcut for superscript (standard shortcut)
        # We'll add both variants to ensure compatibility across different keyboard layouts
        
        # Variant 1: Ctrl++
        trigger_superscript1 = Gtk.ShortcutTrigger.parse_string("<Control>plus")
        action_superscript1 = Gtk.CallbackAction.new(lambda *args: self.on_superscript_shortcut(win, *args))
        shortcut_superscript1 = Gtk.Shortcut.new(trigger_superscript1, action_superscript1)
        controller.add_shortcut(shortcut_superscript1)
        
        # Variant 2: Ctrl+Shift+=
        trigger_superscript2 = Gtk.ShortcutTrigger.parse_string("<Control><Shift>equal")
        action_superscript2 = Gtk.CallbackAction.new(lambda *args: self.on_superscript_shortcut(win, *args))
        shortcut_superscript2 = Gtk.Shortcut.new(trigger_superscript2, action_superscript2)
        controller.add_shortcut(shortcut_superscript2)
        
                
        # Add controller to the window
        win.add_controller(controller)
        
        # Make it capture events at the capture phase
        controller.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        
        # Make shortcut work regardless of who has focus
        controller.set_scope(Gtk.ShortcutScope.GLOBAL)


                        
    def toggle_file_toolbar(self, win, *args):
        """Toggle the visibility of the file toolbar with animation"""
        is_revealed = win.toolbar_revealer.get_reveal_child()
        win.toolbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"File Toolbar {status}")
        return True         
             

    def toggle_statusbar(self, win, *args):
        """Toggle the visibility of the statusbar with animation"""
        is_revealed = win.statusbar_revealer.get_reveal_child()
        win.statusbar_revealer.set_reveal_child(not is_revealed)
        if not is_revealed:
            win.statusbar.set_text("Statusbar shown")
        return True
    
    def toggle_headerbar(self, win, *args):
        """Toggle the visibility of the headerbar with animation"""
        is_revealed = win.headerbar_revealer.get_reveal_child()
        win.headerbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"Headerbar {status}")
        return True

    def on_close_shortcut(self, win, *args):
        """Handle Ctrl+W shortcut to close current window"""
        win.close()
        return True

    def on_close_others_shortcut(self, win, *args):
        """Handle Ctrl+Shift+W shortcut to close other windows"""
        self.on_close_other_windows(None, None)
        return True

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
                /*margin: 40px; */ /*Change this for page border*/
                padding: 0;
                font-family: Sans;
            }}
            #editor {{
                /*border: 1px solid #ccc;*/
                padding: 0px;
                outline: none;
                /*min-height: 200px; */ /* Reduced fallback minimum height */
                height: 100%; /* Allow it to expand fully */
                /*box-sizing: border-box; */ /* Include padding/border in height */
                font-family: Sans;
                font-size: 11pt;
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
            @media (prefers-color-scheme: dark) {{
                html, body {{
                    background-color: #1e1e1e;
                    color: #c0c0c0;
                }}
            }}
            @media (prefers-color-scheme: light) {{
                html, body {{
                    background-color: #ffffff;
                    color: #000000;
                }}
            }}
        </style>
        <script>
            window.initialContent = "{content or '<div><font face=\"Sans\" style=\"font-size: 11pt;\"><br></font></div>'}";
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
        
        // Search variables
        var searchResults = [];
        var searchIndex = -1;
        var currentSearchText = "";

        {self.save_state_js()}
        {self.perform_undo_js()}
        {self.perform_redo_js()}
        {self.find_last_text_node_js()}
        {self.get_stack_sizes_js()}
        {self.set_content_js()}
        {self.selection_change_js()}
        {self.search_functions_js()}
        {self.paragraph_and_line_spacing_js()}
        {self.insert_table_js()}
        {self.table_border_style_js()}
        {self.table_color_js()}
        {self.insert_text_box_js()}
        {self.insert_image_js()}
        {self.insert_link_js()}
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

    def selection_change_js(self):
        """JavaScript to track selection changes and update formatting buttons"""
        return """
        function updateFormattingState() {
            try {
                // Get basic formatting states
                const isBold = document.queryCommandState('bold');
                const isItalic = document.queryCommandState('italic');
                const isUnderline = document.queryCommandState('underline');
                const isStrikeThrough = document.queryCommandState('strikeThrough');
                const isSubscript = document.queryCommandState('subscript');
                const isSuperscript = document.queryCommandState('superscript');
                
                // Get the current paragraph formatting
                let paragraphStyle = 'Normal'; // Default
                const selection = window.getSelection();
                let fontFamily = '';
                let fontSize = '';
                
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    const node = range.commonAncestorContainer;
                    
                    // Find the closest block element
                    const getNodeName = (node) => {
                        return node.nodeType === 1 ? node.nodeName.toLowerCase() : null;
                    };
                    
                    const getParentBlockElement = (node) => {
                        if (node.nodeType === 3) { // Text node
                            return getParentBlockElement(node.parentNode);
                        }
                        const tagName = getNodeName(node);
                        if (['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div'].includes(tagName)) {
                            return node;
                        }
                        if (node.parentNode && node.parentNode.id !== 'editor') {
                            return getParentBlockElement(node.parentNode);
                        }
                        return null;
                    };
                    
                    const blockElement = getParentBlockElement(node);
                    if (blockElement) {
                        const tagName = getNodeName(blockElement);
                        switch (tagName) {
                            case 'h1': paragraphStyle = 'Heading 1'; break;
                            case 'h2': paragraphStyle = 'Heading 2'; break;
                            case 'h3': paragraphStyle = 'Heading 3'; break;
                            case 'h4': paragraphStyle = 'Heading 4'; break;
                            case 'h5': paragraphStyle = 'Heading 5'; break;
                            case 'h6': paragraphStyle = 'Heading 6'; break;
                            default: paragraphStyle = 'Normal'; break;
                        }
                    }
                    
                    // Enhanced font size detection
                    // Start with the deepest element at cursor/selection
                    let currentElement = node;
                    if (currentElement.nodeType === 3) { // Text node
                        currentElement = currentElement.parentNode;
                    }
                    
                    // Work our way up the DOM tree to find font-size styles
                    while (currentElement && currentElement !== editor) {
                        // Check for inline font size
                        if (currentElement.style && currentElement.style.fontSize) {
                            fontSize = currentElement.style.fontSize;
                            break;
                        }
                        
                        // Check for font elements with size attribute
                        if (currentElement.tagName && currentElement.tagName.toLowerCase() === 'font' && currentElement.hasAttribute('size')) {
                            // This is a rough conversion from HTML font size (1-7) to points
                            const htmlSize = parseInt(currentElement.getAttribute('size'));
                            const sizeMap = {1: '8', 2: '10', 3: '12', 4: '14', 5: '18', 6: '24', 7: '36'};
                            fontSize = sizeMap[htmlSize] || '12';
                            break;
                        }
                        
                        // If we haven't found a font size yet, move up to parent
                        currentElement = currentElement.parentNode;
                    }
                    
                    // If we still don't have a font size, get it from computed style
                    if (!fontSize) {
                        // Use computed style as a fallback
                        const computedStyle = window.getComputedStyle(node.nodeType === 3 ? node.parentNode : node);
                        fontSize = computedStyle.fontSize;
                    }
                    
                    // Convert pixel sizes to points (approximate)
                    if (fontSize.endsWith('px')) {
                        const pxValue = parseFloat(fontSize);
                        fontSize = Math.round(pxValue * 0.75).toString();
                    } else if (fontSize.endsWith('pt')) {
                        fontSize = fontSize.replace('pt', '');
                    } else {
                        // For other units or no units, try to extract just the number
                        fontSize = fontSize.replace(/[^0-9.]/g, '');
                    }
                    
                    // Get font family using a similar approach
                    currentElement = node;
                    if (currentElement.nodeType === 3) {
                        currentElement = currentElement.parentNode;
                    }
                    
                    while (currentElement && currentElement !== editor) {
                        if (currentElement.style && currentElement.style.fontFamily) {
                            fontFamily = currentElement.style.fontFamily;
                            // Clean up quotes and fallbacks
                            fontFamily = fontFamily.split(',')[0].replace(/["']/g, '');
                            break;
                        }
                        
                        // Check for font elements with face attribute
                        if (currentElement.tagName && currentElement.tagName.toLowerCase() === 'font' && currentElement.hasAttribute('face')) {
                            fontFamily = currentElement.getAttribute('face');
                            break;
                        }
                        
                        currentElement = currentElement.parentNode;
                    }
                    
                    // If we still don't have a font family, get it from computed style
                    if (!fontFamily) {
                        const computedStyle = window.getComputedStyle(node.nodeType === 3 ? node.parentNode : node);
                        fontFamily = computedStyle.fontFamily.split(',')[0].replace(/["']/g, '');
                    }
                }
                
                // Send the state to Python - MAKE SURE subscript and superscript are included here
                window.webkit.messageHandlers.formattingChanged.postMessage(
                    JSON.stringify({
                        bold: isBold, 
                        italic: isItalic, 
                        underline: isUnderline,
                        strikeThrough: isStrikeThrough,
                        subscript: isSubscript,
                        superscript: isSuperscript,
                        paragraphStyle: paragraphStyle,
                        fontFamily: fontFamily,
                        fontSize: fontSize
                    })
                );
            } catch(e) {
                console.log("Error updating formatting state:", e);
            }
        }
        
        document.addEventListener('selectionchange', function() {
            // Only update if the selection is in our editor
            const selection = window.getSelection();
            if (selection.rangeCount > 0) {
                const range = selection.getRangeAt(0);
                const editor = document.getElementById('editor');
                
                // Check if the selection is within our editor
                if (editor.contains(range.commonAncestorContainer)) {
                    updateFormattingState();
                }
            }
        });
        """

    def init_editor_js(self):
        """JavaScript to initialize the editor and set up event listeners."""
        return f"""
        {self.setup_tab_key_handler_js()}
        {self.setup_first_focus_handler_js()}
        {self.setup_input_handler_js()}
        {self.dom_content_loaded_handler_js()}
        """

    def setup_tab_key_handler_js(self):
        """JavaScript to handle tab key behavior in the editor."""
        return """
        function setupTabKeyHandler(editor) {
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    // Check if we're inside a table cell
                    const selection = window.getSelection();
                    if (selection.rangeCount > 0) {
                        let node = selection.anchorNode;
                        
                        // Find parent cell (TD or TH)
                        while (node && node !== editor) {
                            if (node.tagName === 'TD' || node.tagName === 'TH') {
                                // We're in a table cell
                                e.preventDefault();
                                
                                if (e.shiftKey) {
                                    // Shift+Tab: Navigate to previous cell
                                    navigateToPreviousCell(node);
                                } else {
                                    // Tab: Navigate to next cell
                                    navigateToNextCell(node);
                                }
                                
                                return; // Don't insert a tab character
                            }
                            node = node.parentNode;
                        }
                    }
                    
                    // Not in a table cell - insert tab as normal
                    e.preventDefault();
                    document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    
                    // Trigger input event to register the change for undo/redo
                    const event = new Event('input', {
                        bubbles: true,
                        cancelable: true
                    });
                    editor.dispatchEvent(event);
                }
            });
        }
        
        // Function to navigate to the next table cell
        function navigateToNextCell(currentCell) {
            const currentRow = currentCell.parentNode;
            const currentTable = currentRow.closest('table');
            
            // Find next cell in the same row
            const nextCell = currentCell.nextElementSibling;
            
            if (nextCell) {
                // Move to next cell in same row
                focusCell(nextCell);
            } else {
                // End of row - move to first cell of next row
                const nextRow = currentRow.nextElementSibling;
                if (nextRow) {
                    const firstCell = nextRow.firstElementChild;
                    if (firstCell) {
                        focusCell(firstCell);
                    }
                } else {
                    // End of table - create a new row
                    const newRow = currentTable.insertRow(-1);
                    
                    // Create cells based on the current row's cell count
                    for (let i = 0; i < currentRow.cells.length; i++) {
                        const newCell = newRow.insertCell(i);
                        newCell.innerHTML = '&nbsp;';
                        
                        // Copy styles from the current row
                        const currentRowCell = currentRow.cells[i];
                        if (currentRowCell) {
                            // Copy border style
                            if (currentRowCell.style.border) {
                                newCell.style.border = currentRowCell.style.border;
                            } else {
                                newCell.style.border = '1px solid ' + getBorderColor();
                            }
                            // Copy padding style
                            if (currentRowCell.style.padding) {
                                newCell.style.padding = currentRowCell.style.padding;
                            } else {
                                newCell.style.padding = '5px';
                            }
                            // Copy background color if any
                            if (currentRowCell.style.backgroundColor) {
                                newCell.style.backgroundColor = currentRowCell.style.backgroundColor;
                            }
                        }
                    }
                    
                    // Focus the first cell of the new row
                    if (newRow.firstElementChild) {
                        focusCell(newRow.firstElementChild);
                    }
                    
                    // Notify that content changed
                    try {
                        window.webkit.messageHandlers.contentChanged.postMessage('changed');
                    } catch(e) {
                        console.log("Could not notify about content change:", e);
                    }
                }
            }
        }
        
        // Function to navigate to the previous table cell
        function navigateToPreviousCell(currentCell) {
            const currentRow = currentCell.parentNode;
            const currentTable = currentRow.closest('table');
            
            // Find previous cell in the same row
            const previousCell = currentCell.previousElementSibling;
            
            if (previousCell) {
                // Move to previous cell in same row
                focusCell(previousCell);
            } else {
                // Beginning of row - move to last cell of previous row
                const previousRow = currentRow.previousElementSibling;
                if (previousRow) {
                    const lastCell = previousRow.lastElementChild;
                    if (lastCell) {
                        focusCell(lastCell);
                    }
                } else {
                    // Beginning of table - stay in current cell
                    focusCell(currentCell);
                }
            }
        }
        
        // Function to focus a table cell and position cursor at beginning
        function focusCell(cell) {
            // Create a range at the beginning of the cell
            const range = document.createRange();
            const selection = window.getSelection();
            
            // Try to find the first text node in the cell
            let firstNode = cell;
            let firstTextNode = null;
            
            function findFirstTextNode(node) {
                if (node.nodeType === Node.TEXT_NODE && node.textContent.trim().length > 0) {
                    return node;
                }
                for (let child of node.childNodes) {
                    const result = findFirstTextNode(child);
                    if (result) return result;
                }
                return null;
            }
            
            firstTextNode = findFirstTextNode(cell);
            
            if (firstTextNode) {
                // Place cursor at the beginning of the text
                range.setStart(firstTextNode, 0);
                range.setEnd(firstTextNode, 0);
            } else {
                // No text node found - place cursor at the beginning of the cell
                range.setStart(cell, 0);
                range.setEnd(cell, 0);
            }
            
            // Clear any existing selection and apply the new range
            selection.removeAllRanges();
            selection.addRange(range);
            
            // Scroll the cell into view if needed
            cell.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
            
            // Ensure the cell has focus
            cell.focus();
        }
        """

    def setup_first_focus_handler_js(self):
        """JavaScript to handle the first focus event."""
        return """
        function setupFirstFocusHandler(editor) {
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
        }
        """

    def setup_input_handler_js(self):
        """JavaScript to handle input events and content changes."""
        return """
        function setupInputHandler(editor) {
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
        }
        """
        
    def dom_content_loaded_handler_js(self):
        """JavaScript to handle DOMContentLoaded event and initialize the editor."""
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Give the editor a proper tabindex to ensure it can capture keyboard focus
            editor.setAttribute('tabindex', '0');
            
            // Set up event handlers
            setupTabKeyHandler(editor);
            setupFirstFocusHandler(editor);
            setupInputHandler(editor);
            
            // Initialize content state
            window.lastContent = editor.innerHTML;
            saveState();
            editor.focus();
            
            // Load initial content if available
            if (window.initialContent) {
                setContent(window.initialContent);
            }
        });
        """
        
    def get_initial_html(self):
        return self.get_editor_html('<div><font face="Sans" style="font-size: 11pt;"><br></font></div>')
    
    def execute_js(self, win, script):
        """Execute JavaScript in the WebView"""
        win.webview.evaluate_javascript(script, -1, None, None, None, None, None)
    
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
    def on_content_changed(self, win, manager, result):
        # Check current modified state before changing it
        was_modified = win.modified
        
        # Set new state and update window title
        win.modified = True
        self.update_window_title(win)
        self.update_undo_redo_state(win)
        
        # Only update window menu if the modified state changed
        if not was_modified:  # If it wasn't modified before but now is
            self.update_window_menu()
        
    def update_undo_redo_state(self, win):
        try:
            # Get stack sizes to update button states
            win.webview.evaluate_javascript(
                "JSON.stringify(getStackSizes());",  # Ensure we get a proper JSON string
                -1, None, None, None,
                lambda webview, result, data: self._on_get_stack_sizes(win, webview, result, data), 
                None
            )
        except Exception as e:
            print(f"Error updating undo/redo state: {e}")
            # Fallback - enable buttons
            win.undo_button.set_sensitive(True)
            win.redo_button.set_sensitive(False)
        
    def _on_get_stack_sizes(self, win, webview, result, user_data):
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
                        win.undo_button.set_sensitive(sizes.get('undoSize', 0) > 1)
                        win.redo_button.set_sensitive(sizes.get('redoSize', 0) > 0)
                    except json.JSONDecodeError as je:
                        print(f"Error parsing JSON: {je}, value was: {stack_sizes}")
                        # Set reasonable defaults
                        win.undo_button.set_sensitive(True)
                        win.redo_button.set_sensitive(False)
                except Exception as inner_e:
                    print(f"Inner error processing JS result: {inner_e}")
                    # Set reasonable defaults
                    win.undo_button.set_sensitive(True)
                    win.redo_button.set_sensitive(False)
        except Exception as e:
            print(f"Error getting stack sizes: {e}")
            # Set reasonable defaults in case of error
            win.undo_button.set_sensitive(True)
            win.redo_button.set_sensitive(False)
            
    def on_undo_clicked(self, win, button):
        self.perform_undo(win)
        
    def on_redo_clicked(self, win, button):
        self.perform_redo(win)
        
    def on_undo_shortcut(self, win, *args):
        self.perform_undo(win)
        return True
        
    def on_redo_shortcut(self, win, *args):
        self.perform_redo(win)
        return True
        
    def perform_undo(self, win):
        try:
            win.webview.evaluate_javascript(
                "JSON.stringify(performUndo());",
                -1, None, None, None,
                lambda webview, result, data: self._on_undo_redo_performed(win, webview, result, data),
                "undo"
            )
            win.statusbar.set_text("Undo performed")
        except Exception as e:
            print(f"Error during undo: {e}")
            win.statusbar.set_text("Undo failed")
        
    def perform_redo(self, win):
        try:
            win.webview.evaluate_javascript(
                "JSON.stringify(performRedo());",
                -1, None, None, None,
                lambda webview, result, data: self._on_undo_redo_performed(win, webview, result, data),
                "redo"
            )
            win.statusbar.set_text("Redo performed")
        except Exception as e:
            print(f"Error during redo: {e}")
            win.statusbar.set_text("Redo failed")

    def _on_undo_redo_performed(self, win, webview, result, operation):
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
                    win.statusbar.set_text(f"{operation.capitalize()} performed")
                    
                    # Check current modified state before changing it
                    was_modified = win.modified
                    
                    # Determine new state based on operation and result
                    new_modified_state = not (operation == "undo" and is_initial_state)
                    
                    # Set new state if it's different
                    if win.modified != new_modified_state:
                        win.modified = new_modified_state
                        self.update_window_title(win)
                        
                        # Only update window menu if modified state changed
                        self.update_window_menu()
                    
                    self.update_undo_redo_state(win)
                else:
                    win.statusbar.set_text(f"No more {operation} actions available")
        except Exception as e:
            print(f"Error during {operation}: {e}")
            win.statusbar.set_text(f"{operation.capitalize()} failed")
            
    # Event handlers
    def on_new_clicked(self, win, button):
        # Create a new window with a blank document
        new_win = self.create_window()
        new_win.present()
        GLib.timeout_add(500, lambda: self.set_initial_focus(new_win))
        self.update_window_menu()
        new_win.statusbar.set_text("New document created")
    
    def get_menu_title(self, win):
        if win.current_file:
            # Get the path as a string
            if hasattr(win.current_file, 'get_path'):
                path = win.current_file.get_path()
            else:
                path = win.current_file
            # Extract filename without extension and show modified marker
            filename = os.path.splitext(os.path.basename(path))[0]
            return f"{'  ⃰' if win.modified else ''}{filename}"
        else:
            return f"{'  ⃰' if win.modified else ''}Untitled"

    def update_window_title(self, win):
        """Update window title to show document name (without extension) and modified status"""
        if win.current_file:
            # Get the path as a string
            if hasattr(win.current_file, 'get_path'):
                path = win.current_file.get_path()
            else:
                path = win.current_file
            # Extract filename without extension
            filename = os.path.splitext(os.path.basename(path))[0]
            title = f"{'  ⃰' if win.modified else ''}{filename}"
            win.set_title(f"{title} - HTML Editor")
            
            # Update the title widget if it exists
            if hasattr(win, 'title_widget'):
                win.title_widget.set_title(f"{'  ⃰' if win.modified else ''}{filename} - HTML Editor")
        else:
            title = f"{'  ⃰' if win.modified else ''}Untitled"
            win.set_title(f"{title} - HTML Editor")
            
            # Update the title widget if it exists
            if hasattr(win, 'title_widget'):
                win.title_widget.set_title(f"{'  ⃰' if win.modified else ''}Untitled  - HTML Editor")


    # Window Close Request
    def on_window_close_request(self, win, *args):
        """Handle window close request with save confirmation if needed"""
        if win.modified:
            # Show confirmation dialog
            self.show_save_confirmation_dialog(win, lambda response: self._handle_close_confirmation(win, response))
            # Return True to stop the default close handler
            return True
        else:
            # No unsaved changes, proceed with closing
            self.remove_window(win)
            return False

    def _handle_close_confirmation(self, win, response):
        """Handle the response from the save confirmation dialog"""
        if response == "save":
            # Save and then close
            if win.current_file:
                # We have a file path, save directly
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_before_close(win, webview, result, data),
                    None
                )
            else:
                # No file path, show save dialog
                dialog = Gtk.FileDialog()
                dialog.set_title("Save Before Closing")
                
                filter = Gtk.FileFilter()
                filter.set_name("HTML files")
                filter.add_pattern("*.html")
                filter.add_pattern("*.htm")
                
                filters = Gio.ListStore.new(Gtk.FileFilter)
                filters.append(filter)
                
                dialog.set_filters(filters)
                dialog.save(win, None, lambda dialog, result: self._on_save_response_before_close(win, dialog, result))
        elif response == "discard":
            # Mark as unmodified before closing
            win.modified = False
            
            # Close without saving
            self.remove_window(win)
            win.close()
        # If response is "cancel", do nothing and keep the window open

    def _on_save_before_close(self, win, webview, result, data):
        """Save the content and then close the window"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                               js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                # Define a callback that will close the window after saving
                def after_save(file, result):
                    try:
                        success, _ = file.replace_contents_finish(result)
                        if success:
                            win.modified = False  # Mark as unmodified
                            self.update_window_title(win)
                            # Now close the window
                            self.remove_window(win)
                            win.close()
                    except Exception as e:
                        print(f"Error during save before close: {e}")
                        # Close anyway in case of error
                        self.remove_window(win)
                        win.close()
                
                self.save_html_content(win, editor_content, win.current_file, after_save)
        except Exception as e:
            print(f"Error getting HTML content: {e}")
            # Close anyway in case of error
            self.remove_window(win)
            win.close()

    def _on_saved_close_window(self, file, result):
        """After saving, close the window"""
        try:
            success, _ = file.replace_contents_finish(result)
            # Find the window with this file
            for win in self.windows:
                if win.current_file and win.current_file.equal(file):
                    self.remove_window(win)
                    win.close()
                    break
        except Exception as e:
            print(f"Error saving before close: {e}")

    def _on_save_response_before_close(self, win, dialog, result):
        """Handle save dialog response before closing"""
        try:
            file = dialog.save_finish(result)
            if file:
                win.current_file = file
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_before_close(win, webview, result, data),
                    None
                )
            else:
                # User cancelled save dialog, keep window open
                pass
        except GLib.Error as error:
            if error.domain != 'gtk-dialog-error-quark' or error.code != 2:  # Ignore cancel
                print(f"Error saving file: {error.message}")
            # Keep window open

    def show_save_confirmation_dialog(self, win, callback):
        """Show dialog asking if user wants to save changes before closing"""
        dialog = Adw.Dialog.new()
        dialog.set_title("Unsaved Changes")
        dialog.set_content_width(400)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Warning icon
        warning_icon = Gtk.Image.new_from_icon_name("dialog-warning-symbolic")
        warning_icon.set_pixel_size(48)
        warning_icon.set_margin_bottom(12)
        content_box.append(warning_icon)
        
        # Message
        document_name = "Untitled"
        if win.current_file:
            path = win.current_file.get_path() if hasattr(win.current_file, 'get_path') else win.current_file
            document_name = os.path.splitext(os.path.basename(path))[0]
            
        message_label = Gtk.Label()
        message_label.set_markup(f"<b>Save changes to \"{document_name}\" before closing?</b>")
        message_label.set_wrap(True)
        message_label.set_max_width_chars(40)
        content_box.append(message_label)
        
        description_label = Gtk.Label(label="If you don't save, your changes will be lost.")
        description_label.set_wrap(True)
        description_label.set_max_width_chars(40)
        content_box.append(description_label)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(12)
        
        # Discard button
        discard_button = Gtk.Button(label="Discard")
        discard_button.add_css_class("destructive-action")
        discard_button.connect("clicked", lambda btn: [dialog.close(), callback("discard")])
        button_box.append(discard_button)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: [dialog.close(), callback("cancel")])
        button_box.append(cancel_button)
        
        # Save button
        save_button = Gtk.Button(label="Save")
        save_button.add_css_class("suggested-action")
        save_button.connect("clicked", lambda btn: [dialog.close(), callback("save")])
        button_box.append(save_button)
        
        content_box.append(button_box)
        
        # Present the dialog
        dialog.set_child(content_box)
        dialog.present(win)

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
            title = self.get_menu_title(win)
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
        # Look for existing window menu button
        window_button = None
        child = win.headerbar.get_first_child()
        while child:
            if (isinstance(child, Gtk.MenuButton) and 
                child.get_icon_name() == "multi-window-symbolic"):
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
            window_button.set_icon_name("multi-window-symbolic")
            window_button.set_tooltip_text("Window List")
            window_button.set_menu_model(menu_model)
            window_button.set_visible(show_button)
            window_button.add_css_class("flat")
            win.headerbar.pack_end(window_button)
            
            # Store reference to the button
            self.window_buttons[id(win)] = window_button
        
        # Make sure we keep the reference if button exists
        if window_button:
            self.window_buttons[id(win)] = window_button
            
    def on_switch_window(self, action, param):
        """Handle window switching action"""
        index = param.get_int32()
        if 0 <= index < len(self.windows):
            self.windows[index].present()
            
    def on_new_window(self, action, param):
        """Create a new empty window"""
        win = self.create_window()
        win.present()
        # Update all window menus
        self.update_window_menu()

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
    
    # On Quit
    def on_quit(self, action, param):
        """Quit the application with save confirmation if needed"""
        # Check if any window has unsaved changes
        windows_with_changes = [win for win in self.windows if win.modified]
        
        if windows_with_changes:
            # Prioritize the active window if it has unsaved changes
            active_window = None
            for win in self.windows:
                if win.is_active() and win.modified:
                    active_window = win
                    break
                    
            # If no active window with changes, use the first window with changes
            if not active_window and windows_with_changes:
                active_window = windows_with_changes[0]
            
            # Move the active window to the front of the list
            if active_window in windows_with_changes:
                windows_with_changes.remove(active_window)
                windows_with_changes.insert(0, active_window)
            
            # Start handling windows one by one
            self._handle_quit_with_unsaved_changes(windows_with_changes)
        else:
            # No unsaved changes, quit directly
            self.quit()

    def _handle_quit_with_unsaved_changes(self, windows_with_changes):
        """Handle unsaved changes during quit, one window at a time"""
        if not windows_with_changes:
            # All windows handled, check if we should quit
            if not self.windows:
                self.quit()
            return
            
        win = windows_with_changes[0]
        # Make sure the window is presented to the user
        win.present()
        # Show the confirmation dialog
        self.show_save_confirmation_dialog(win, lambda response: self._handle_quit_confirmation(
            response, windows_with_changes, win))

    def _handle_quit_confirmation(self, response, windows_with_changes, win):
        """Handle the response from the save confirmation dialog during quit"""
        if response == "save":
            # Save and then close this window
            if win.current_file:
                # We have a file path, save directly
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_continue_quit(
                        win, webview, result, windows_with_changes),
                    None
                )
            else:
                # No file path, show save dialog
                dialog = Gtk.FileDialog()
                dialog.set_title("Save Before Quitting")
                
                filter = Gtk.FileFilter()
                filter.set_name("HTML files")
                filter.add_pattern("*.html")
                filter.add_pattern("*.htm")
                
                filters = Gio.ListStore.new(Gtk.FileFilter)
                filters.append(filter)
                
                dialog.set_filters(filters)
                dialog.save(win, None, lambda dialog, result: self._on_save_response_during_quit(
                    win, dialog, result, windows_with_changes))
        elif response == "discard":
            # Explicitly mark as unmodified before closing
            win.modified = False
            
            # Close this window without saving and continue with the next
            self.remove_window(win)
            win.close()
            
            # Continue with remaining windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
            elif not self.windows:
                # If all windows are closed, quit the application
                self.quit()
        elif response == "cancel":
            # Cancel the entire quit operation
            # Continue with other windows that might be open but not modified
            pass

    def _on_save_continue_quit(self, win, webview, result, windows_with_changes):
        """Save the content, close this window, and continue with the quit process"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                               js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                # Define a callback for after saving
                def after_save(file, result):
                    try:
                        success, _ = file.replace_contents_finish(result)
                        if success:
                            win.modified = False  # Mark as unmodified
                            self.update_window_title(win)
                        
                        # Close this window
                        self.remove_window(win)
                        win.close()
                        
                        # Continue with remaining windows
                        remaining_windows = windows_with_changes[1:]
                        if remaining_windows:
                            GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
                        elif not self.windows:
                            # If all windows are closed, quit the application
                            self.quit()
                    except Exception as e:
                        print(f"Error saving during quit: {e}")
                        # Close anyway and continue
                        self.remove_window(win)
                        win.close()
                        
                        # Continue with remaining windows
                        remaining_windows = windows_with_changes[1:]
                        if remaining_windows:
                            GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
                        elif not self.windows:
                            # If all windows are closed, quit the application
                            self.quit()
                
                # Save with our callback
                self.save_html_content(win, editor_content, win.current_file, after_save)
        except Exception as e:
            print(f"Error getting HTML content during quit: {e}")
            # Close anyway and continue
            self.remove_window(win)
            win.close()
            
            # Continue with remaining windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
            elif not self.windows:
                # If all windows are closed, quit the application
                self.quit()

    def _on_save_response_during_quit(self, win, dialog, result, windows_with_changes):
        """Handle save dialog response during quit"""
        try:
            file = dialog.save_finish(result)
            if file:
                win.current_file = file
                win.webview.evaluate_javascript(
                    "document.getElementById('editor').innerHTML;",
                    -1, None, None, None,
                    lambda webview, result, data: self._on_save_continue_quit(
                        win, webview, result, windows_with_changes),
                    None
                )
            else:
                # User cancelled save dialog, cancel quit for this window
                # but continue with other windows that might need attention
                remaining_windows = windows_with_changes[1:]
                if remaining_windows:
                    GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
        except GLib.Error as error:
            if error.domain != 'gtk-dialog-error-quark' or error.code != 2:  # Ignore cancel
                print(f"Error saving file during quit: {error.message}")
            # Continue with other windows
            remaining_windows = windows_with_changes[1:]
            if remaining_windows:
                GLib.idle_add(lambda: self._handle_quit_with_unsaved_changes(remaining_windows))
    
    def on_about(self, action, param):
        """Show about dialog"""
        parent_window = self.windows[0] if self.windows else None
        about = Adw.AboutWindow(
            transient_for=parent_window,
            application_name="HTML Editor",
            application_icon="text-editor",
            copyright="GNU General Public License (GPLv3+)",
            comments="rich text editor using webkit",
            website="https://github.com/fastrizwaan/htmleditor",
            developer_name="Mohammed Asif Ali Rizvan",
            license_type=Gtk.License.GPL_3_0,
            issue_url="https://github.com/fastrizwaan/htmleditor/issues"
        )
        about.present()

            
    def on_preferences(self, action, param):
        """Show preferences dialog"""
        if not self.windows:
            return
                
        # Find the active window instead of just using the first window
        active_win = None
        for win in self.windows:
            if win.is_active():
                active_win = win
                break
        
        # If no active window found, use the first one as fallback
        if not active_win:
            active_win = self.windows[0]
                
        # Create dialog
        dialog = Adw.Dialog.new()
        dialog.set_title("Preferences")
        dialog.set_content_width(450)
        
        # Create content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
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
        
        # Show/Hide UI elements section
        ui_header = Gtk.Label()
        ui_header.set_markup("<b>User Interface</b>")
        ui_header.set_halign(Gtk.Align.START)
        ui_header.set_margin_bottom(12)
        ui_header.set_margin_top(24)
        content_box.append(ui_header)
        
        # Show Toolbar option
        formatting_toolbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        formatting_toolbar_box.set_margin_start(12)
        
        formatting_toolbar_label = Gtk.Label(label="Show Toolbar:")
        formatting_toolbar_label.set_halign(Gtk.Align.START)
        formatting_toolbar_label.set_hexpand(True)
        
        formatting_toolbar_switch = Gtk.Switch()
        formatting_toolbar_switch.set_active(active_win.formatting_toolbar_revealer.get_reveal_child())
        formatting_toolbar_switch.set_valign(Gtk.Align.CENTER)
        formatting_toolbar_switch.connect("state-set", lambda sw, state: active_win.formatting_toolbar_revealer.set_reveal_child(state))
        
        formatting_toolbar_box.append(formatting_toolbar_label)
        formatting_toolbar_box.append(formatting_toolbar_switch)
        content_box.append(formatting_toolbar_box)
        
        # Show Statusbar option
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        statusbar_box.set_margin_start(12)
        statusbar_box.set_margin_top(12)
        
        statusbar_label = Gtk.Label(label="Show Statusbar:")
        statusbar_label.set_halign(Gtk.Align.START)
        statusbar_label.set_hexpand(True)
        
        statusbar_switch = Gtk.Switch()
        statusbar_switch.set_active(active_win.statusbar_revealer.get_reveal_child())
        statusbar_switch.set_valign(Gtk.Align.CENTER)
        statusbar_switch.connect("state-set", lambda sw, state: active_win.statusbar_revealer.set_reveal_child(state))
        
        statusbar_box.append(statusbar_label)
        statusbar_box.append(statusbar_switch)
        content_box.append(statusbar_box)
        
        # Show Headerbar option
        headerbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        headerbar_box.set_margin_start(12)
        headerbar_box.set_margin_top(12)
        
        headerbar_label = Gtk.Label(label="Show Headerbar:")
        headerbar_label.set_halign(Gtk.Align.START)
        headerbar_label.set_hexpand(True)
        
        headerbar_switch = Gtk.Switch()
        headerbar_switch.set_active(active_win.headerbar_revealer.get_reveal_child())
        headerbar_switch.set_valign(Gtk.Align.CENTER)
        headerbar_switch.connect("state-set", lambda sw, state: active_win.headerbar_revealer.set_reveal_child(state))
        
        headerbar_box.append(headerbar_label)
        headerbar_box.append(headerbar_switch)
        content_box.append(headerbar_box)
        
        # Auto-save toggle
        auto_save_section = Gtk.Label()
        auto_save_section.set_markup("<b>Auto Save</b>")
        auto_save_section.set_halign(Gtk.Align.START)
        auto_save_section.set_margin_bottom(12)
        auto_save_section.set_margin_top(24)
        content_box.append(auto_save_section)
        
        auto_save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        auto_save_box.set_margin_start(12)
        
        auto_save_label = Gtk.Label(label="Auto Save:")
        auto_save_label.set_halign(Gtk.Align.START)
        auto_save_label.set_hexpand(True)
        
        auto_save_switch = Gtk.Switch()
        auto_save_switch.set_active(active_win.auto_save_enabled)
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
            value=active_win.auto_save_interval,
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
            dialog, active_win, auto_save_switch.get_active(), spinner.get_value_as_int()
        ))
        button_box.append(ok_button)
        
        content_box.append(button_box)
        
        # Important: Store a reference to the dialog in the window
        active_win.preferences_dialog = dialog
        
        # Connect to the closed signal to clean up the reference
        dialog.connect("closed", lambda d: self.on_preferences_dialog_closed(active_win))
        
        # Set dialog content and show
        dialog.set_child(content_box)
        dialog.present(active_win)

    def on_preferences_dialog_closed(self, win):
        """Handle preferences dialog closed event"""
        # Remove the reference to allow proper cleanup
        if hasattr(win, 'preferences_dialog'):
            win.preferences_dialog = None

    def save_preferences(self, dialog, win, auto_save_enabled, auto_save_interval):
        """Save preferences settings"""
        previous_auto_save = win.auto_save_enabled
        
        win.auto_save_enabled = auto_save_enabled
        win.auto_save_interval = auto_save_interval
        
        # Update auto-save timer if needed
        if auto_save_enabled != previous_auto_save:
            if auto_save_enabled:
                self.start_auto_save_timer(win)
                win.statusbar.set_text("Auto-save enabled")
            else:
                self.stop_auto_save_timer(win)
                win.statusbar.set_text("Auto-save disabled")
        elif auto_save_enabled:
            # Restart timer with new interval
            self.stop_auto_save_timer(win)
            self.start_auto_save_timer(win)
            win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
        
        dialog.close()

    def save_preferences(self, dialog, win, auto_save_enabled, auto_save_interval):
        """Save preferences settings"""
        previous_auto_save = win.auto_save_enabled
        
        win.auto_save_enabled = auto_save_enabled
        win.auto_save_interval = auto_save_interval
        
        # Update auto-save timer if needed
        if auto_save_enabled != previous_auto_save:
            if auto_save_enabled:
                self.start_auto_save_timer(win)
                win.statusbar.set_text("Auto-save enabled")
            else:
                self.stop_auto_save_timer(win)
                win.statusbar.set_text("Auto-save disabled")
        elif auto_save_enabled:
            # Restart timer with new interval
            self.stop_auto_save_timer(win)
            self.start_auto_save_timer(win)
            win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
        
        dialog.close()

    def start_auto_save_timer(self, win):
        """Start auto-save timer for a window"""
        if win.auto_save_source_id:
            GLib.source_remove(win.auto_save_source_id)
            
        # Set up auto-save timer
        win.auto_save_source_id = GLib.timeout_add_seconds(
            win.auto_save_interval,
            lambda: self.auto_save(win)
        )

    def stop_auto_save_timer(self, win):
        """Stop auto-save timer for a window"""
        if win.auto_save_source_id:
            GLib.source_remove(win.auto_save_source_id)
            win.auto_save_source_id = None

    def auto_save(self, win):
        """Perform auto-save if needed"""
        if win.modified and win.current_file:
            win.statusbar.set_text("Auto-saving...")
            win.webview.evaluate_javascript(
                "document.getElementById('editor').innerHTML;",
                -1, None, None, None,
                lambda webview, result, file: self._on_get_html_content_auto_save(win, webview, result, win.current_file),
                None
            )
        return win.auto_save_enabled  # Continue timer if enabled

    def _on_get_html_content_auto_save(self, win, webview, result, file):
        """Handle auto-save content retrieval"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                editor_content = (js_result.get_js_value().to_string() if hasattr(js_result, 'get_js_value') else
                                js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result))
                
                self.save_html_content(win, editor_content, file, 
                                      lambda file, result: self._on_auto_save_completed(win, file, result))
        except Exception as e:
            print(f"Error getting HTML content for auto-save: {e}")
            win.statusbar.set_text(f"Auto-save failed: {e}")

    def _on_auto_save_completed(self, win, file, result):
        """Handle auto-save completion"""
        try:
            success, _ = file.replace_contents_finish(result)
            if success:
                win.modified = False  # Reset modified flag after save
                self.update_window_title(win)
                win.statusbar.set_text(f"Auto-saved at {GLib.DateTime.new_now_local().format('%H:%M:%S')}")
            else:
                win.statusbar.set_text("Auto-save failed")
        except GLib.Error as error:
            print(f"Error during auto-save: {error.message}")
            win.statusbar.set_text(f"Auto-save failed: {error.message}")

    def show_error_dialog(self, message):
        """Show error message dialog"""
        if not self.windows:
            print(f"Error: {message}")
            return
            
        # Find the active window
        active_window = None
        for win in self.windows:
            if win.is_active():
                active_window = win
                break
                
        # Fallback to first window if none is active
        if not active_window:
            active_window = self.windows[0]
        
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
        dialog.present(active_window)

    # Show Caret in the window (for new and fresh start)
    def set_initial_focus(self, win):
        """Set focus to the WebView and its editor element after window is shown"""
        try:
            # First grab focus on the WebView widget itself
            win.webview.grab_focus()
            
            # Then focus the editor element inside the WebView
            js_code = """
            (function() {
                const editor = document.getElementById('editor');
                if (!editor) return false;
                
                editor.focus();
                
                // Set cursor position
                try {
                    const range = document.createRange();
                    const sel = window.getSelection();
                    
                    // Find or create a text node to place cursor
                    let textNode = null;
                    let firstDiv = editor.querySelector('div');
                    
                    if (!firstDiv) {
                        editor.innerHTML = '<div><br></div>';
                        firstDiv = editor.querySelector('div');
                    }
                    
                    if (firstDiv) {
                        range.setStart(firstDiv, 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                } catch (e) {
                    console.log("Error setting cursor position:", e);
                }
                
                return true;
            })();
            """
            
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            return False  # Don't call again
        except Exception as e:
            print(f"Error setting initial focus: {e}")
            return False  # Don't call again

    def on_print_clicked(self, win, btn):
        """Handle print button click using WebKit's print operation"""
        win.statusbar.set_text("Preparing to print...")
        
        # Create a print operation with WebKit
        print_op = WebKit.PrintOperation.new(win.webview)
        
        # Run the print dialog
        print_op.run_dialog(win)
######################


#### Zoom statusbar
    def on_zoom_changed_statusbar(self, win, scale):
        """Handle zoom scale change with snapping to common values"""
        # Get the current value from the scale
        raw_value = scale.get_value()
        
        # Define common zoom levels to snap to
        common_zoom_levels = [50, 75, 100, 125, 150, 175, 200, 250, 300, 350, 400]
        
        # Find the closest common zoom level
        closest_zoom = min(common_zoom_levels, key=lambda x: abs(x - raw_value))
        
        # Check if we're close enough to snap
        snap_threshold = 5  # Snap if within 5% of a common value
        if abs(raw_value - closest_zoom) <= snap_threshold:
            # We're close to a common value, snap to it
            if raw_value != closest_zoom:  # Only set if different to avoid infinite recursion
                scale.set_value(closest_zoom)
            zoom_level = closest_zoom
        else:
            # Not close to a common value, use the rounded value
            zoom_level = int(raw_value)
        
        # Update the label and apply zoom
        win.zoom_label.set_text(f"{zoom_level}%")
        win.zoom_level = zoom_level
        
        # Apply zoom to the editor
        self.apply_zoom(win, zoom_level)
        
    # Add these new methods for zoom control in the statusbar
    def on_zoom_toggle_clicked(self, win, button):
        """Handle zoom toggle button click"""
        is_active = button.get_active()
        win.zoom_revealer.set_reveal_child(is_active)
        
        # Update status text
        if is_active:
            win.statusbar.set_text("Zoom")
        else:
            # Restore previous status message or show 'Ready'
            win.statusbar.set_text("Ready")

    def on_zoom_in_clicked(self, win):
        """Handle zoom in button click"""
        current_value = win.zoom_scale.get_value()
        new_value = min(current_value + 10, 400)  # Increase by 10%, max 400%
        win.zoom_scale.set_value(new_value)

    def on_zoom_out_clicked(self, win):
        """Handle zoom out button click"""
        current_value = win.zoom_scale.get_value()
        new_value = max(current_value - 10, 50)  # Decrease by 10%, min 50%
        win.zoom_scale.set_value(new_value)

########################### line spacing and column
    def setup_spacing_actions(self, win):
        """Setup actions for paragraph and line spacing"""
        # Line spacing actions
        line_spacing_action = Gio.SimpleAction.new("line-spacing", GLib.VariantType.new("s"))
        line_spacing_action.connect("activate", lambda action, param: self.apply_quick_line_spacing(win, float(param.get_string())))
        win.add_action(line_spacing_action)
        
        line_spacing_dialog_action = Gio.SimpleAction.new("line-spacing-dialog", None)
        line_spacing_dialog_action.connect("activate", lambda action, param: self.on_line_spacing_clicked(win, action, param))
        win.add_action(line_spacing_dialog_action)
        
        # Paragraph spacing actions
        para_spacing_action = Gio.SimpleAction.new("paragraph-spacing", GLib.VariantType.new("s"))
        para_spacing_action.connect("activate", lambda action, param: self.apply_quick_paragraph_spacing(win, int(param.get_string())))
        win.add_action(para_spacing_action)
        
        para_spacing_dialog_action = Gio.SimpleAction.new("paragraph-spacing-dialog", None)
        para_spacing_dialog_action.connect("activate", lambda action, param: self.on_paragraph_spacing_clicked(win, action, param))
        win.add_action(para_spacing_dialog_action)

    def on_paragraph_spacing_clicked(self, win, action, param):
        """Show dialog to adjust paragraph spacing for individual or all paragraphs"""
        dialog = Adw.Dialog()
        dialog.set_title("Paragraph Spacing")
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create spacing selection
        header = Gtk.Label()
        header.set_markup("<b>Paragraph Spacing Options:</b>")
        header.set_halign(Gtk.Align.START)
        content_box.append(header)
        
        # Radio buttons for scope selection
        scope_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scope_box.set_margin_top(12)
        scope_box.set_margin_bottom(12)
        
        scope_label = Gtk.Label(label="Apply to:")
        scope_label.set_halign(Gtk.Align.START)
        scope_box.append(scope_label)
        
        # Create radio buttons
        current_radio = Gtk.CheckButton(label="Current paragraph only")
        current_radio.set_active(True)
        scope_box.append(current_radio)
        
        all_radio = Gtk.CheckButton(label="All paragraphs")
        all_radio.set_group(current_radio)
        scope_box.append(all_radio)
        
        content_box.append(scope_box)
        
        # Spacing slider
        spacing_label = Gtk.Label(label="Spacing value:")
        spacing_label.set_halign(Gtk.Align.START)
        content_box.append(spacing_label)
        
        adjustment = Gtk.Adjustment.new(10, 0, 50, 1, 5, 0)
        spacing_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        spacing_scale.set_hexpand(True)
        spacing_scale.set_digits(0)
        spacing_scale.set_draw_value(True)
        spacing_scale.add_mark(0, Gtk.PositionType.BOTTOM, "None")
        spacing_scale.add_mark(10, Gtk.PositionType.BOTTOM, "Default")
        spacing_scale.add_mark(30, Gtk.PositionType.BOTTOM, "Wide")
        content_box.append(spacing_scale)
        
        # Preset buttons
        presets_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        presets_box.set_homogeneous(True)
        presets_box.set_margin_top(12)
        
        none_button = Gtk.Button(label="None")
        none_button.connect("clicked", lambda btn: spacing_scale.set_value(0))
        presets_box.append(none_button)
        
        small_button = Gtk.Button(label="Small")
        small_button.connect("clicked", lambda btn: spacing_scale.set_value(5))
        presets_box.append(small_button)
        
        medium_button = Gtk.Button(label="Medium") 
        medium_button.connect("clicked", lambda btn: spacing_scale.set_value(15))
        presets_box.append(medium_button)
        
        large_button = Gtk.Button(label="Large")
        large_button.connect("clicked", lambda btn: spacing_scale.set_value(30))
        presets_box.append(large_button)
        
        content_box.append(presets_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        # Apply button
        apply_button = Gtk.Button(label="Apply")
        apply_button.add_css_class("suggested-action")
        apply_button.connect("clicked", lambda btn: self.apply_paragraph_spacing(
            win, dialog, spacing_scale.get_value(), current_radio.get_active()))
        button_box.append(apply_button)
        
        content_box.append(button_box)
        
        # Set up the dialog content
        dialog.set_child(content_box)
        
        # Present the dialog
        dialog.present(win)

    def apply_paragraph_spacing(self, win, dialog, spacing, current_only):
        """Apply paragraph spacing to the current paragraph or all paragraphs"""
        if current_only:
            # Apply spacing to just the selected paragraphs
            js_code = f"""
            (function() {{
                return setParagraphSpacing({int(spacing)});
            }})();
            """
            self.execute_js(win, js_code)
        else:
            # Apply spacing to all paragraphs
            js_code = f"""
            (function() {{
                // First ensure all direct text content is wrapped
                wrapUnwrappedText(document.getElementById('editor'));
                
                // Target both p tags and div tags as paragraphs
                let paragraphs = document.getElementById('editor').querySelectorAll('p, div');
                
                // Apply to all paragraphs
                for (let i = 0; i < paragraphs.length; i++) {{
                    paragraphs[i].style.marginBottom = '{int(spacing)}px';
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
        
        win.statusbar.set_text(f"Paragraph spacing set to {int(spacing)}px")
        dialog.close()

    def apply_quick_paragraph_spacing(self, win, spacing):
        """Apply spacing to the selected paragraphs through menu action"""
        js_code = f"""
        (function() {{
            return setParagraphSpacing({spacing});
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Paragraph spacing set to {spacing}px")

    def on_line_spacing_clicked(self, win, action, param):
        """Show dialog to adjust line spacing for individual or all paragraphs"""
        dialog = Adw.Dialog()
        dialog.set_title("Line Spacing")
        
        # Create main content box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=20)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Create spacing selection
        header = Gtk.Label()
        header.set_markup("<b>Line Spacing Options:</b>")
        header.set_halign(Gtk.Align.START)
        content_box.append(header)
        
        # Radio buttons for scope selection
        scope_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        scope_box.set_margin_top(12)
        scope_box.set_margin_bottom(12)
        
        scope_label = Gtk.Label(label="Apply to:")
        scope_label.set_halign(Gtk.Align.START)
        scope_box.append(scope_label)
        
        # Create radio buttons
        current_radio = Gtk.CheckButton(label="Current paragraph only")
        current_radio.set_active(True)
        scope_box.append(current_radio)
        
        all_radio = Gtk.CheckButton(label="All paragraphs")
        all_radio.set_group(current_radio)
        scope_box.append(all_radio)
        
        content_box.append(scope_box)
        
        # Preset buttons
        presets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        presets_label = Gtk.Label(label="Common spacing:")
        presets_label.set_halign(Gtk.Align.START)
        presets_box.append(presets_label)
        
        buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        buttons_box.set_homogeneous(True)
        
        single_button = Gtk.Button(label="Single (1.0)")
        single_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 1.0, current_radio.get_active()))
        buttons_box.append(single_button)
        
        one_half_button = Gtk.Button(label="1.5 lines")
        one_half_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 1.5, current_radio.get_active()))
        buttons_box.append(one_half_button)
        
        double_button = Gtk.Button(label="Double (2.0)")
        double_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, 2.0, current_radio.get_active()))
        buttons_box.append(double_button)
        
        presets_box.append(buttons_box)
        content_box.append(presets_box)
        
        # Custom spacing section
        custom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        custom_box.set_margin_top(8)
        
        custom_label = Gtk.Label(label="Custom spacing:")
        custom_label.set_halign(Gtk.Align.START)
        custom_box.append(custom_label)
        
        # Add slider for custom spacing
        adjustment = Gtk.Adjustment.new(1.0, 0.8, 3.0, 0.1, 0.2, 0)
        spacing_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        spacing_scale.set_hexpand(True)
        spacing_scale.set_digits(1)
        spacing_scale.set_draw_value(True)
        spacing_scale.add_mark(1.0, Gtk.PositionType.BOTTOM, "1.0")
        spacing_scale.add_mark(1.5, Gtk.PositionType.BOTTOM, "1.5")
        spacing_scale.add_mark(2.0, Gtk.PositionType.BOTTOM, "2.0")
        custom_box.append(spacing_scale)
        
        # Apply custom button
        custom_apply_button = Gtk.Button(label="Apply Custom Value")
        custom_apply_button.connect("clicked", lambda btn: self.apply_line_spacing(
            win, dialog, spacing_scale.get_value(), current_radio.get_active()))
        custom_apply_button.set_margin_top(8)
        custom_box.append(custom_apply_button)
        
        content_box.append(custom_box)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(24)
        
        # Cancel button
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        button_box.append(cancel_button)
        
        content_box.append(button_box)
        
        # Set up the dialog content
        dialog.set_child(content_box)
        
        # Present the dialog
        dialog.present(win)

    def apply_line_spacing(self, win, dialog, spacing, current_only):
        """Apply line spacing to the current paragraph or all paragraphs"""
        if current_only:
            # Apply spacing to just the selected paragraphs
            js_code = f"""
            (function() {{
                return setLineSpacing({spacing});
            }})();
            """
            self.execute_js(win, js_code)
        else:
            # Apply spacing to all paragraphs
            js_code = f"""
            (function() {{
                // First ensure all direct text content is wrapped
                wrapUnwrappedText(document.getElementById('editor'));
                
                // Target both p tags and div tags as paragraphs
                let paragraphs = document.getElementById('editor').querySelectorAll('p, div');
                
                // Apply to all paragraphs
                for (let i = 0; i < paragraphs.length; i++) {{
                    paragraphs[i].style.lineHeight = '{spacing}';
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
        
        win.statusbar.set_text(f"Line spacing set to {spacing}")
        dialog.close()
    def apply_quick_line_spacing(self, win, spacing):
        """Apply line spacing to the selected paragraphs through menu action"""
        js_code = f"""
        (function() {{
            return setLineSpacing({spacing});
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Line spacing set to {spacing}")


    def paragraph_and_line_spacing_js(self):
        """JavaScript for paragraph and line spacing functions"""
        return """
        // Function to set paragraph spacing
        function setParagraphSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy: Get all paragraphs in the selection range
            const range = selection.getRangeAt(0);
            const startNode = findContainerParagraph(range.startContainer);
            const endNode = findContainerParagraph(range.endContainer);
            
            // If we couldn't find containers, try a different approach
            if (!startNode || !endNode) {
                return setSimpleParagraphSpacing(spacing);
            }
            
            // Get all paragraphs in the selection range
            const paragraphs = getAllParagraphsInRange(startNode, endNode);
            
            // Apply spacing to all found paragraphs
            paragraphs.forEach(para => {
                para.style.marginBottom = spacing + 'px';
            });
            
            return true;
        }
        
        // Function to set line spacing
        function setLineSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy: Get all paragraphs in the selection range
            const range = selection.getRangeAt(0);
            const startNode = findContainerParagraph(range.startContainer);
            const endNode = findContainerParagraph(range.endContainer);
            
            // If we couldn't find containers, try a different approach
            if (!startNode || !endNode) {
                return setSimpleLineSpacing(spacing);
            }
            
            // Get all paragraphs in the selection range
            const paragraphs = getAllParagraphsInRange(startNode, endNode);
            
            // Apply spacing to all found paragraphs
            paragraphs.forEach(para => {
                para.style.lineHeight = spacing;
            });
            
            return true;
        }
        
        // Helper function to find the container paragraph of a node
        function findContainerParagraph(node) {
            while (node && node.id !== 'editor') {
                if (node.nodeType === 1 && 
                    (node.nodeName.toLowerCase() === 'p' || 
                     node.nodeName.toLowerCase() === 'div')) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        }
        
        // Get all paragraphs between start and end node (inclusive)
        function getAllParagraphsInRange(startNode, endNode) {
            // If start and end are the same, just return that node
            if (startNode === endNode) {
                return [startNode];
            }
            
            // Get all paragraphs in the editor
            const allParagraphs = Array.from(document.getElementById('editor').querySelectorAll('p, div'));
            
            // Find the indices of our start and end nodes
            const startIndex = allParagraphs.indexOf(startNode);
            const endIndex = allParagraphs.indexOf(endNode);
            
            // Handle case where we can't find one of the nodes
            if (startIndex === -1 || endIndex === -1) {
                // Fall back to just the nodes we have
                return [startNode, endNode].filter(node => node !== null);
            }
            
            // Return all paragraphs between start and end (inclusive)
            return allParagraphs.slice(
                Math.min(startIndex, endIndex), 
                Math.max(startIndex, endIndex) + 1
            );
        }
        
        // Fallback method for paragraph spacing when selection is unusual
        function setSimpleParagraphSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            let node = selection.getRangeAt(0).commonAncestorContainer;
            
            // Navigate up to find the paragraph node
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            
            // Find the containing paragraph or div
            while (node && node.id !== 'editor' && 
                  (node.nodeName.toLowerCase() !== 'p' && 
                   node.nodeName.toLowerCase() !== 'div')) {
                node = node.parentNode;
            }
            
            if (node && node.id !== 'editor') {
                node.style.marginBottom = spacing + 'px';
                return true;
            }
            return false;
        }
        
        // Fallback method for line spacing when selection is unusual
        function setSimpleLineSpacing(spacing) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            let node = selection.getRangeAt(0).commonAncestorContainer;
            
            // Navigate up to find the paragraph node
            while (node && node.nodeType !== 1) {
                node = node.parentNode;
            }
            
            // Find the containing paragraph or div
            while (node && node.id !== 'editor' && 
                  (node.nodeName.toLowerCase() !== 'p' && 
                   node.nodeName.toLowerCase() !== 'div')) {
                node = node.parentNode;
            }
            
            if (node && node.id !== 'editor') {
                node.style.lineHeight = spacing;
                return true;
            }
            return false;
        }
        
        // Function to wrap unwrapped text
        function wrapUnwrappedText(container) {
            let childNodes = Array.from(container.childNodes);
            for (let i = 0; i < childNodes.length; i++) {
                let node = childNodes[i];
                if (node.nodeType === 3 && node.nodeValue.trim() !== '') {
                    // It's a text node with content, wrap it
                    let wrapper = document.createElement('div');
                    node.parentNode.insertBefore(wrapper, node);
                    wrapper.appendChild(node);
                }
            }
        }
        // Function to apply column layout to a container
        function setColumnLayout(container, columns) {
            if (columns <= 1) {
                // Remove column styling
                container.style.columnCount = '';
                container.style.columnGap = '';
                container.style.columnRule = '';
            } else {
                // Apply column styling
                container.style.columnCount = columns;
                container.style.columnGap = '20px';
                container.style.columnRule = '1px solid #ccc';
            }
        }
        """      
        
############ column
    def setup_spacing_actions(self, win):
        """Setup actions for paragraph and line spacing"""
        # Line spacing actions
        line_spacing_action = Gio.SimpleAction.new("line-spacing", GLib.VariantType.new("s"))
        line_spacing_action.connect("activate", lambda action, param: self.apply_quick_line_spacing(win, float(param.get_string())))
        win.add_action(line_spacing_action)
        
        line_spacing_dialog_action = Gio.SimpleAction.new("line-spacing-dialog", None)
        line_spacing_dialog_action.connect("activate", lambda action, param: self.on_line_spacing_clicked(win, action, param))
        win.add_action(line_spacing_dialog_action)
        
        # Paragraph spacing actions
        para_spacing_action = Gio.SimpleAction.new("paragraph-spacing", GLib.VariantType.new("s"))
        para_spacing_action.connect("activate", lambda action, param: self.apply_quick_paragraph_spacing(win, int(param.get_string())))
        win.add_action(para_spacing_action)
        
        para_spacing_dialog_action = Gio.SimpleAction.new("paragraph-spacing-dialog", None)
        para_spacing_dialog_action.connect("activate", lambda action, param: self.on_paragraph_spacing_clicked(win, action, param))
        win.add_action(para_spacing_dialog_action)
        
        # Column layout actions
        column_action = Gio.SimpleAction.new("set-columns", GLib.VariantType.new("s"))
        column_action.connect("activate", lambda action, param: self.apply_column_layout(win, int(param.get_string())))
        win.add_action(column_action)        

    def apply_column_layout(self, win, columns):
        """Apply column layout to the selected content"""
        js_code = f"""
        (function() {{
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Strategy similar to paragraph spacing
            const range = selection.getRangeAt(0);
            
            // First, try to get a structured element like div or p
            let container = null;
            
            // Check if selection is within a paragraph or div
            let node = range.commonAncestorContainer;
            if (node.nodeType === 3) {{ // Text node
                node = node.parentNode;
            }}
            
            // Find a suitable container or create one
            while (node && node.id !== 'editor') {{
                if (node.nodeName.toLowerCase() === 'div' || 
                    node.nodeName.toLowerCase() === 'p') {{
                    container = node;
                    break;
                }}
                node = node.parentNode;
            }}
            
            // If we didn't find a container, we'll need to create a wrapper
            if (!container || container.id === 'editor') {{
                // Create a wrapper around the selection
                document.execCommand('formatBlock', false, 'div');
                
                // Get the newly created div
                const newRange = selection.getRangeAt(0);
                node = newRange.commonAncestorContainer;
                if (node.nodeType === 3) {{
                    node = node.parentNode;
                }}
                
                // Find our new container
                while (node && node.id !== 'editor') {{
                    if (node.nodeName.toLowerCase() === 'div') {{
                        container = node;
                        break;
                    }}
                    node = node.parentNode;
                }}
            }}
            
            if (container) {{
                if ({columns} <= 1) {{
                    // Remove column styling
                    container.style.columnCount = '';
                    container.style.columnGap = '';
                    container.style.columnRule = '';
                    return true;
                }} else {{
                    // Apply column styling
                    container.style.columnCount = {columns};
                    container.style.columnGap = '20px';
                    container.style.columnRule = '1px solid #ccc';
                    return true;
                }}
            }}
            
            return false;
        }})();
        """
        self.execute_js(win, js_code)
        
        status_text = "Column layout removed" if columns <= 1 else f"Applied {columns}-column layout"
        win.statusbar.set_text(status_text)
        
    def create_window(self):
        """Create a new window with all initialization"""
        win = Adw.ApplicationWindow(application=self)
        
        # Set window properties
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        
        win.set_default_size(676, 480)
        win.set_title("Untitled - HTML Editor")
        
        # Create main box to contain all UI elements
        win.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.main_box.set_vexpand(True)
        win.main_box.set_hexpand(True)
        
        # Create master headerbar revealer
        win.headerbar_revealer = Gtk.Revealer()
        win.headerbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.headerbar_revealer.set_margin_start(0)
        win.headerbar_revealer.set_margin_end(0)
        win.headerbar_revealer.set_margin_top(0)
        win.headerbar_revealer.set_margin_bottom(0)
        win.headerbar_revealer.set_transition_duration(250)
        win.headerbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create the main headerbar
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")  # Add flat-header style
        self.setup_headerbar_content(win)
        
        # Create a vertical box to contain headerbar and unified toolbar
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.headerbar_box.append(win.headerbar)
        
        # Create toolbar revealer for smooth show/hide
        win.toolbar_revealer = Gtk.Revealer()
        win.toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.toolbar_revealer.set_transition_duration(250)
        win.toolbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create WrapBox for flexible toolbar layout
        win.toolbars_wrapbox = Adw.WrapBox()
        win.toolbars_wrapbox.set_margin_start(4)
        win.toolbars_wrapbox.set_margin_end(4)
        win.toolbars_wrapbox.set_margin_top(4)
        win.toolbars_wrapbox.set_margin_bottom(4)
        win.toolbars_wrapbox.set_child_spacing(4)
        win.toolbars_wrapbox.set_line_spacing(4)
        
        # --- File operations group (New, Open, Save, Save As) ---
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        file_group.add_css_class("linked")  # Apply linked styling
        file_group.set_margin_start(0)

        # New button
        new_button = Gtk.Button(icon_name="document-new-symbolic")
        new_button.set_tooltip_text("New Document in New Window")
        new_button.connect("clicked", lambda btn: self.on_new_clicked(win, btn))
        # Set size request to match formatting toolbar buttons
        new_button.set_size_request(40, 36)

        # Open button
        open_button = Gtk.Button(icon_name="document-open-symbolic")
        open_button.set_tooltip_text("Open File in New Window")
        open_button.connect("clicked", lambda btn: self.on_open_clicked(win, btn))
        open_button.set_size_request(40, 36)

        # Save button
        save_button = Gtk.Button(icon_name="document-save-symbolic")
        save_button.set_tooltip_text("Save File")
        save_button.connect("clicked", lambda btn: self.on_save_clicked(win, btn))
        save_button.set_size_request(40, 36)

        # Save As button
        save_as_button = Gtk.Button(icon_name="document-save-as-symbolic")
        save_as_button.set_tooltip_text("Save File As")
        save_as_button.connect("clicked", lambda btn: self.on_save_as_clicked(win, btn))
        save_as_button.set_size_request(40, 36)

        # Add buttons to file group
        file_group.append(new_button)
        file_group.append(open_button)
        file_group.append(save_button)
        file_group.append(save_as_button)
        
        # Add file group to toolbar
        win.toolbars_wrapbox.append(file_group)
        

        
        # Select All button
        # --- Edit operations group (Cut, Copy, Paste, Select All) ---
        select_all_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        select_all_group.add_css_class("linked")  # Apply linked styling
        select_all_group.set_margin_start(0)
        
        select_all_button = Gtk.Button(icon_name="edit-select-all-symbolic")
        select_all_button.set_tooltip_text("Select All")
        select_all_button.connect("clicked", lambda btn: self.on_select_all_clicked(win, btn))
        select_all_button.set_size_request(40, 36)

        select_all_group.append(select_all_button)
        win.toolbars_wrapbox.append(select_all_group)
        # --- Edit operations group (Cut, Copy, Paste, Select All) ---
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        edit_group.add_css_class("linked")  # Apply linked styling
        edit_group.set_margin_start(0)
                
        # Cut button
        cut_button = Gtk.Button(icon_name="edit-cut-symbolic")
        cut_button.set_tooltip_text("Cut")
        cut_button.connect("clicked", lambda btn: self.on_cut_clicked(win, btn))
        cut_button.set_size_request(40, 36)

        # Copy button
        copy_button = Gtk.Button(icon_name="edit-copy-symbolic")
        copy_button.set_tooltip_text("Copy")
        copy_button.connect("clicked", lambda btn: self.on_copy_clicked(win, btn))
        copy_button.set_size_request(40, 36)

        # Paste button
        paste_button = Gtk.Button(icon_name="edit-paste-symbolic")
        paste_button.set_tooltip_text("Paste")
        paste_button.connect("clicked", lambda btn: self.on_paste_clicked(win, btn))
        paste_button.set_size_request(40, 36)
        
        # Add buttons to edit group
        edit_group.append(cut_button)
        edit_group.append(copy_button)
        edit_group.append(paste_button)
        
        # Add edit group to toolbar
        win.toolbars_wrapbox.append(edit_group)
        
        # --- Undo/Redo group ---
        undo_redo_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        undo_redo_group.add_css_class("linked")  # Apply linked styling
        undo_redo_group.set_margin_start(0)
        
        # Undo button
        win.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        win.undo_button.set_tooltip_text("Undo")
        win.undo_button.connect("clicked", lambda btn: self.on_undo_clicked(win, btn))
        win.undo_button.set_sensitive(False)  # Initially disabled
        win.undo_button.set_size_request(40, 36)
        
        # Redo button
        win.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        win.redo_button.set_tooltip_text("Redo")
        win.redo_button.connect("clicked", lambda btn: self.on_redo_clicked(win, btn))
        win.redo_button.set_sensitive(False)  # Initially disabled
        win.redo_button.set_size_request(40, 36)
        
        # Add buttons to undo group
        undo_redo_group.append(win.undo_button)
        undo_redo_group.append(win.redo_button)

        # Add undo group to toolbar
        win.toolbars_wrapbox.append(undo_redo_group)
        
        # Print button
        print_find_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        print_find_group.add_css_class("linked")  # Apply linked styling
        print_find_group.set_margin_start(0)
        print_button = Gtk.Button(icon_name="document-print-symbolic")
        print_button.set_tooltip_text("Print Document")
        print_button.connect("clicked", lambda btn: self.on_print_clicked(win, btn) if hasattr(self, "on_print_clicked") else None)
        print_button.set_size_request(40, 36)
        
        # Find-Replace toggle button
        win.find_button = Gtk.ToggleButton(icon_name="edit-find-replace-symbolic")
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))
        win.find_button.set_size_request(40, 36)

        print_find_group.append(print_button)
        print_find_group.append(win.find_button)

        # Add print find group to toolbar
        win.toolbars_wrapbox.append(print_find_group)
        
        # --- Spacing operations group (Line Spacing, Paragraph Spacing) ---
        spacing_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        spacing_group.add_css_class("linked")  # Apply linked styling
        spacing_group.set_margin_start(0)
        
        # Line spacing button menu
        line_spacing_button = Gtk.MenuButton(icon_name="line_space_new")
        line_spacing_button.set_size_request(40, 36)
        line_spacing_button.set_tooltip_text("Line Spacing")

        
        # Create line spacing menu
        line_spacing_menu = Gio.Menu()
        
        # Add line spacing options
        line_spacing_menu.append("Single (1.0)", "win.line-spacing('1.0')")
        line_spacing_menu.append("1.5 Lines", "win.line-spacing('1.5')")
        line_spacing_menu.append("Double (2.0)", "win.line-spacing('2.0')")
        line_spacing_menu.append("Custom...", "win.line-spacing-dialog")
        
        line_spacing_button.set_menu_model(line_spacing_menu)
        
        # Paragraph spacing button menu
        para_spacing_button = Gtk.MenuButton(icon_name="paragraph_line_spacing")
        para_spacing_button.set_size_request(40, 36)
        para_spacing_button.set_tooltip_text("Paragraph Spacing")

        
        # Create paragraph spacing menu
        para_spacing_menu = Gio.Menu()
        
        # Add paragraph spacing options
        para_spacing_menu.append("None", "win.paragraph-spacing('0')")
        para_spacing_menu.append("Small (5px)", "win.paragraph-spacing('5')")
        para_spacing_menu.append("Medium (15px)", "win.paragraph-spacing('15')")
        para_spacing_menu.append("Large (30px)", "win.paragraph-spacing('30')")
        para_spacing_menu.append("Custom...", "win.paragraph-spacing-dialog")
        
        para_spacing_button.set_menu_model(para_spacing_menu)
        
        # Add buttons to spacing group
        spacing_group.append(line_spacing_button)
        spacing_group.append(para_spacing_button)

        # Add spacing group to toolbar
        win.toolbars_wrapbox.append(spacing_group)        
                
        # Column layout button menu
        column_case_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        column_case_group.add_css_class("linked")  # Apply linked styling
        column_case_group.set_margin_start(0)
        
        column_button = Gtk.MenuButton(icon_name="columns-symbolic")
        column_button.set_size_request(40, 36)
        column_button.set_tooltip_text("Column Layout")

        
        # Create column menu
        column_menu = Gio.Menu()
        
        # Add column options
        column_menu.append("Single Column", "win.set-columns('1')")
        column_menu.append("Two Columns", "win.set-columns('2')")
        column_menu.append("Three Columns", "win.set-columns('3')")
        column_menu.append("Four Columns", "win.set-columns('4')")
        column_menu.append("Remove Columns", "win.set-columns('0')")
        
        column_button.set_menu_model(column_menu)
        
        # Case change menu button
        case_menu_button = Gtk.MenuButton(icon_name="uppercase-symbolic")
        case_menu_button.set_tooltip_text("Change Case")
        case_menu_button.set_size_request(40, 36)

        # Create case change menu
        case_menu = Gio.Menu()
        case_menu.append("Sentence case.", "win.change-case::sentence")
        case_menu.append("lowercase", "win.change-case::lower")
        case_menu.append("UPPERCASE", "win.change-case::upper")
        case_menu.append("Capitalize Each Word", "win.change-case::title")
        case_menu.append("tOGGLE cASE", "win.change-case::toggle")

        # Set the menu model for the button
        case_menu_button.set_menu_model(case_menu)

        # Add buttons to column case group
        column_case_group.append(column_button)
        column_case_group.append(case_menu_button)        
        
        # Add spacing group to toolbar
        win.toolbars_wrapbox.append(column_case_group)        
            





        # Create formatting toolbar
        # Paragraph, font family, font size box        
        para_font_size_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        para_font_size_box.add_css_class("linked")
        #pfs_box.set_margin_start(2)
        #pfs_box.set_margin_end(6)
        
        # Store the handlers for blocking
        win.bold_handler_id = None
        win.italic_handler_id = None
        win.underline_handler_id = None
        win.strikeout_handler_id = None
        win.subscript_handler_id = None
        win.superscript_handler_id = None
        win.paragraph_style_handler_id = None
        win.font_handler_id = None
        win.font_size_handler_id = None

        # ---- PARAGRAPH STYLES DROPDOWN ----
        # Create paragraph styles dropdown
        win.paragraph_style_dropdown = Gtk.DropDown()
        win.paragraph_style_dropdown.set_tooltip_text("Paragraph Style")
        win.paragraph_style_dropdown.set_focus_on_click(False)
        
        # Create string list for paragraph styles
        paragraph_styles = Gtk.StringList()
        paragraph_styles.append("Normal")
        paragraph_styles.append("Heading 1")
        paragraph_styles.append("Heading 2")
        paragraph_styles.append("Heading 3")
        paragraph_styles.append("Heading 4")
        paragraph_styles.append("Heading 5")
        paragraph_styles.append("Heading 6")
        win.paragraph_style_dropdown.set_model(paragraph_styles)
        win.paragraph_style_dropdown.set_selected(0)  # Default to Normal
        
        # Connect signal handler
        win.paragraph_style_handler_id = win.paragraph_style_dropdown.connect(
            "notify::selected", lambda dd, param: self.on_paragraph_style_changed(win, dd))
        win.paragraph_style_dropdown.set_size_request(64, -1)
        
        # ---- FONT FAMILY DROPDOWN ----
        # Get available fonts from Pango
        font_map = PangoCairo.FontMap.get_default()
        font_families = font_map.list_families()
        
        # Create string list and sort alphabetically
        font_names = Gtk.StringList()
        sorted_families = sorted([family.get_name() for family in font_families])
        
        # Add all fonts in alphabetical order
        for family in sorted_families:
            font_names.append(family)
        
        # Create dropdown with fixed width
        win.font_dropdown = Gtk.DropDown()
        win.font_dropdown.set_tooltip_text("Font Family")
        win.font_dropdown.set_focus_on_click(False)
        win.font_dropdown.set_model(font_names)

        # Set fixed width and prevent expansion
        win.font_dropdown.set_size_request(163, -1)  # Reduced width in flat layout
        win.font_dropdown.set_hexpand(False)
        
        # Create a factory only for the BUTTON part of the dropdown
        button_factory = Gtk.SignalListItemFactory()
        
        def setup_button_label(factory, list_item):
            label = Gtk.Label()
            label.set_ellipsize(Pango.EllipsizeMode.END)  # Ellipsize button text
            label.set_xalign(0)
            label.set_margin_start(0)
            label.set_margin_end(0)
            # Set maximum width for the text
            label.set_max_width_chars(10)  # Limit to approximately 10 characters
            label.set_width_chars(10)      # Try to keep consistent width
            list_item.set_child(label)
        
        def bind_button_label(factory, list_item):
            position = list_item.get_position()
            label = list_item.get_child()
            label.set_text(font_names.get_string(position))
        
        button_factory.connect("setup", setup_button_label)
        button_factory.connect("bind", bind_button_label)
        
        # Apply the factory only to the dropdown display (not the list)
        win.font_dropdown.set_factory(button_factory)
        
        # For the popup list, create a standard factory without ellipsization
        list_factory = Gtk.SignalListItemFactory()
        
        def setup_list_label(factory, list_item):
            label = Gtk.Label()
            label.set_xalign(0)
            label.set_margin_start(2)
            label.set_margin_end(2)
            list_item.set_child(label)
        
        def bind_list_label(factory, list_item):
            position = list_item.get_position()
            label = list_item.get_child()
            label.set_text(font_names.get_string(position))
        
        list_factory.connect("setup", setup_list_label)
        list_factory.connect("bind", bind_list_label)
        
        # Apply the list factory to the dropdown list only
        win.font_dropdown.set_list_factory(list_factory)
        
        # Set initial font (first in list)
        win.font_dropdown.set_selected(0)
        
        # Connect signal handler
        win.font_handler_id = win.font_dropdown.connect(
            "notify::selected", lambda dd, param: self.on_font_changed(win, dd))
        
        # ---- FONT SIZE DROPDOWN ----
        # Create string list for font sizes
        font_sizes = Gtk.StringList()
        for size in [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 18, 20, 21, 22, 24, 26, 28, 32, 36, 40, 42, 44, 48, 54, 60, 66, 72, 80, 88, 96]:
            font_sizes.append(str(size))
        
        # Create dropdown
        win.font_size_dropdown = Gtk.DropDown()
        win.font_size_dropdown.set_tooltip_text("Font Size")
        win.font_size_dropdown.set_focus_on_click(False)
        win.font_size_dropdown.set_model(font_sizes)
        
        # Set a reasonable width
        win.font_size_dropdown.set_size_request(65, -1)
        
        # Set initial size (12pt)
        initial_size = 6  # Index of size 12 in our list
        win.font_size_dropdown.set_selected(initial_size)
        
        # Connect signal handler
        win.font_size_handler_id = win.font_size_dropdown.connect(
            "notify::selected", lambda dd, param: self.on_font_size_changed(win, dd))
        
        # Add Paragraph, font, size linked button group
        para_font_size_box.append(win.paragraph_style_dropdown)
        para_font_size_box.append(win.font_dropdown)
        para_font_size_box.append(win.font_size_dropdown)    
                    
        win.toolbars_wrapbox.append(para_font_size_box)        

        
        # Create first button group (basic formatting - Bold, Italics, Underline, Strikethrough)
        bius_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        bius_group.set_margin_start(0)
        bius_group.set_margin_end(0)
        
        # Bold button
        win.bold_button = Gtk.ToggleButton(icon_name="format-text-bold-symbolic")
        win.bold_button.set_tooltip_text("Bold")
        win.bold_button.set_focus_on_click(False)
        win.bold_button.set_size_request(40, 36)
        win.bold_handler_id = win.bold_button.connect("toggled", lambda btn: self.on_bold_toggled(win, btn))
        bius_group.append(win.bold_button)
        
        # Italic button
        win.italic_button = Gtk.ToggleButton(icon_name="format-text-italic-symbolic")
        win.italic_button.set_tooltip_text("Italic")
        win.italic_button.set_focus_on_click(False)
        win.italic_button.set_size_request(40, 36)
        win.italic_handler_id = win.italic_button.connect("toggled", lambda btn: self.on_italic_toggled(win, btn))
        bius_group.append(win.italic_button)
        
        # Underline button
        win.underline_button = Gtk.ToggleButton(icon_name="format-text-underline-symbolic")
        win.underline_button.set_tooltip_text("Underline")
        win.underline_button.set_focus_on_click(False)
        win.underline_button.set_size_request(40, 36)
        win.underline_handler_id = win.underline_button.connect("toggled", lambda btn: self.on_underline_toggled(win, btn))
        bius_group.append(win.underline_button)
        
        
        # Strikeout button
        win.strikeout_button = Gtk.ToggleButton(icon_name="format-text-strikethrough-symbolic")
        win.strikeout_button.set_tooltip_text("Strikeout")
        win.strikeout_button.set_focus_on_click(False)
        win.strikeout_button.set_size_request(40, 36)
        win.strikeout_handler_id = win.strikeout_button.connect("toggled", lambda btn: self.on_strikeout_toggled(win, btn))
        bius_group.append(win.strikeout_button)        

        win.toolbars_wrapbox.append(bius_group)

        # Subscript, Superscript, Paragraph, Font style shadow, color )
        subscript_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        subscript_group.set_margin_start(0)
        subscript_group.set_margin_end(0)
        # Add subscript and superscript buttons if your handlers exist
        if hasattr(self, 'on_subscript_toggled'):
            win.subscript_button = Gtk.ToggleButton(icon_name="format-text-subscript-symbolic")
            win.subscript_button.set_tooltip_text("Subscript")
            win.subscript_button.add_css_class("flat")
            win.subscript_button.set_size_request(40, 36)
            win.subscript_handler_id = win.subscript_button.connect("toggled", 
                lambda btn: self.on_subscript_toggled(win, btn))
            subscript_group.append(win.subscript_button)
        
        if hasattr(self, 'on_superscript_toggled'):
            win.superscript_button = Gtk.ToggleButton(icon_name="format-text-superscript-symbolic")
            win.superscript_button.set_tooltip_text("Superscript")
            win.superscript_button.add_css_class("flat")
            win.superscript_button.set_size_request(40, 36)
            win.superscript_handler_id = win.superscript_button.connect("toggled", 
                lambda btn: self.on_superscript_toggled(win, btn))
            subscript_group.append(win.superscript_button)

        win.toolbars_wrapbox.append(subscript_group)
        
        # Show formatting marks toggle button
        dropcap_formatting_marks_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        dropcap_formatting_marks_group.set_margin_start(0)
        dropcap_formatting_marks_group.set_margin_end(0)
        win.format_marks_button = Gtk.ToggleButton(icon_name="format-show-marks-symbolic")
        win.format_marks_button.set_tooltip_text("Show Formatting Marks")
        win.format_marks_button.set_size_request(40, 36)
        win.format_marks_button.connect("toggled", lambda btn: self.on_show_formatting_marks_toggled(win, btn))
        dropcap_formatting_marks_group.append(win.format_marks_button)

        # Drop cap button
        win.drop_cap_button = Gtk.Button(icon_name="format-drop-cap-symbolic")
        win.drop_cap_button.set_tooltip_text("Drop Cap")
        win.drop_cap_button.set_size_request(40, 36)
        win.drop_cap_button.connect("clicked", lambda btn: self.on_drop_cap_clicked(win, btn))
        dropcap_formatting_marks_group.append(win.drop_cap_button)
        
        win.toolbars_wrapbox.append(dropcap_formatting_marks_group)

        # Create linked button group for list/indent controls
        indent_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # Indent button
        indent_button = Gtk.Button(icon_name="format-indent-more-symbolic")
        indent_button.set_tooltip_text("Increase Indent")
        indent_button.set_focus_on_click(False)
        indent_button.set_size_request(40, 36)
        indent_button.connect("clicked", lambda btn: self.on_indent_clicked(win, btn))
        indent_group.append(indent_button)
        
        # Outdent button
        outdent_button = Gtk.Button(icon_name="format-indent-less-symbolic")
        outdent_button.set_tooltip_text("Decrease Indent")
        outdent_button.set_focus_on_click(False)
        outdent_button.set_size_request(40, 36)
        outdent_button.connect("clicked", lambda btn: self.on_outdent_clicked(win, btn))
        indent_group.append(outdent_button)
        
        win.toolbars_wrapbox.append(indent_group)
        # Bullet List button
        list_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        win.bullet_list_button = Gtk.ToggleButton(icon_name="view-list-bullet-symbolic")
        win.bullet_list_button.set_tooltip_text("Bullet List")
        win.bullet_list_button.set_focus_on_click(False)
        win.bullet_list_button.set_size_request(40, 36)
        # Store the handler ID directly on the button
        win.bullet_list_button.handler_id = win.bullet_list_button.connect("toggled", 
            lambda btn: self.on_bullet_list_toggled(win, btn))
        list_group.append(win.bullet_list_button)

        # Numbered List button
        win.numbered_list_button = Gtk.ToggleButton(icon_name="view-list-ordered-symbolic")
        win.numbered_list_button.set_tooltip_text("Numbered List")
        win.numbered_list_button.set_focus_on_click(False)
        win.numbered_list_button.set_size_request(40, 36)
        # Store the handler ID directly on the button
        win.numbered_list_button.handler_id = win.numbered_list_button.connect("toggled", 
            lambda btn: self.on_numbered_list_toggled(win, btn))
        list_group.append(win.numbered_list_button)

        win.toolbars_wrapbox.append(list_group)



        # Create second button group for colors and other formatting
        color_bg_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)        
        color_bg_group.set_margin_start(0)
        color_bg_group.set_margin_end(0)

        # --- Text Color SplitButton ---
        # Create the main button part with icon and color indicator
        font_color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Icon
        font_color_icon = Gtk.Image.new_from_icon_name("draw-text-symbolic")
        font_color_icon.set_margin_top(4)
        font_color_icon.set_margin_bottom(0)
        font_color_box.append(font_color_icon)

        # Color indicator
        win.font_color_indicator = Gtk.Box()
        win.font_color_indicator.add_css_class("color-indicator")
        win.font_color_indicator.set_size_request(16, 2)
        color = Gdk.RGBA()
        color.parse("transparent")
        self.set_box_color(win.font_color_indicator, color)
        font_color_box.append(win.font_color_indicator)

        # Create font color popover for the dropdown part
        font_color_popover = Gtk.Popover()
        font_color_popover.set_autohide(True)
        font_color_popover.set_has_arrow(False)

        font_color_box_menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        font_color_box_menu.set_margin_start(6)
        font_color_box_menu.set_margin_end(6)
        font_color_box_menu.set_margin_top(6)
        font_color_box_menu.set_margin_bottom(6)

        # Add "Automatic" option at the top
        automatic_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        automatic_row.set_margin_bottom(0)
        automatic_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic")
        automatic_label = Gtk.Label(label="Automatic")
        automatic_row.append(automatic_icon)
        automatic_row.append(automatic_label)

        automatic_button = Gtk.Button()
        automatic_button.set_child(automatic_row)
        automatic_button.connect("clicked", lambda btn: self.on_font_color_automatic_clicked(win, font_color_popover))
        font_color_box_menu.append(automatic_button)

        # Create color grid
        font_color_grid = Gtk.Grid()
        font_color_grid.set_row_spacing(2)
        font_color_grid.set_column_spacing(2)
        font_color_grid.set_row_homogeneous(True)
        font_color_grid.set_column_homogeneous(True)
        font_color_grid.add_css_class("color-grid")

        # Basic colors for text
        text_colors = [
            "#000000", "#434343", "#666666", "#999999", "#b7b7b7", "#cccccc", "#d9d9d9", "#efefef", "#f3f3f3", "#ffffff",
            "#980000", "#ff0000", "#ff9900", "#ffff00", "#00ff00", "#00ffff", "#4a86e8", "#0000ff", "#9900ff", "#ff00ff",
            "#e6b8af", "#f4cccc", "#fce5cd", "#fff2cc", "#d9ead3", "#d0e0e3", "#c9daf8", "#cfe2f3", "#d9d2e9", "#ead1dc",
            "#dd7e6b", "#ea9999", "#f9cb9c", "#ffe599", "#b6d7a8", "#a2c4c9", "#a4c2f4", "#9fc5e8", "#b4a7d6", "#d5a6bd",
            "#cc4125", "#e06666", "#f6b26b", "#ffd966", "#93c47d", "#76a5af", "#6d9eeb", "#6fa8dc", "#8e7cc3", "#c27ba0",
            "#a61c00", "#cc0000", "#e69138", "#f1c232", "#6aa84f", "#45818e", "#3c78d8", "#3d85c6", "#674ea7", "#a64d79",
            "#85200c", "#990000", "#b45f06", "#bf9000", "#38761d", "#134f5c", "#1155cc", "#0b5394", "#351c75", "#741b47",
            "#5b0f00", "#660000", "#783f04", "#7f6000", "#274e13", "#0c343d", "#1c4587", "#073763", "#20124d", "#4c1130"
        ]

        # Create color buttons and add to grid
        row, col = 0, 0
        for color_hex in text_colors:
            color_button = self.create_color_button(color_hex)
            color_button.connect("clicked", lambda btn, c=color_hex: self.on_font_color_selected(win, c, font_color_popover))
            font_color_grid.attach(color_button, col, row, 1, 1)
            col += 1
            if col >= 10:  # 10 columns
                col = 0
                row += 1

        font_color_box_menu.append(font_color_grid)

        # Add "More Colors..." button
        more_colors_button = Gtk.Button(label="More Colors...")
        more_colors_button.set_margin_top(6)
        more_colors_button.connect("clicked", lambda btn: self.on_more_font_colors_clicked(win, font_color_popover))
        font_color_box_menu.append(more_colors_button)

        # Set content for popover
        font_color_popover.set_child(font_color_box_menu)

        # Create the SplitButton
        win.font_color_button = Adw.SplitButton()
        win.font_color_button.set_tooltip_text("Text Color")
        win.font_color_button.set_focus_on_click(False)
        win.font_color_button.set_size_request(40, 36)
        win.font_color_button.set_child(font_color_box)
        win.font_color_button.set_popover(font_color_popover)

        # Connect the click handler to apply the current color
        win.font_color_button.connect("clicked", lambda btn: self.on_font_color_button_clicked(win))
        color_bg_group.append(win.font_color_button)
        
        # --- Background Color SplitButton ---
        # Create the main button part with icon and color indicator
        bg_color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)

        # Icon
        bg_color_icon = Gtk.Image.new_from_icon_name("marker-symbolic")
        bg_color_icon.set_margin_top(4)
        bg_color_icon.set_margin_bottom(0)
        bg_color_box.append(bg_color_icon)

        # Color indicator
        win.bg_color_indicator = Gtk.Box()
        win.bg_color_indicator.add_css_class("color-indicator")
        win.bg_color_indicator.set_size_request(16, 2)
        bg_color = Gdk.RGBA()
        bg_color.parse("transparent")
        self.set_box_color(win.bg_color_indicator, bg_color)
        bg_color_box.append(win.bg_color_indicator)

        # Create Background Color popover for the dropdown
        bg_color_popover = Gtk.Popover()
        bg_color_popover.set_autohide(True)
        bg_color_popover.set_has_arrow(False)
        bg_color_box_menu = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        bg_color_box_menu.set_margin_start(6)
        bg_color_box_menu.set_margin_end(6)
        bg_color_box_menu.set_margin_top(6)
        bg_color_box_menu.set_margin_bottom(6)

        # Add "Automatic" option at the top
        bg_automatic_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        bg_automatic_row.set_margin_bottom(0)
        bg_automatic_icon = Gtk.Image.new_from_icon_name("edit-undo-symbolic")
        bg_automatic_label = Gtk.Label(label="Automatic")
        bg_automatic_row.append(bg_automatic_icon)
        bg_automatic_row.append(bg_automatic_label)

        bg_automatic_button = Gtk.Button()
        bg_automatic_button.set_child(bg_automatic_row)
        bg_automatic_button.connect("clicked", lambda btn: self.on_bg_color_automatic_clicked(win, bg_color_popover))
        bg_color_box_menu.append(bg_automatic_button)

        # Add separator
        bg_separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        bg_separator.set_margin_bottom(6)
        bg_color_box_menu.append(bg_separator)

        # Create color grid
        bg_color_grid = Gtk.Grid()
        bg_color_grid.set_row_spacing(2)
        bg_color_grid.set_column_spacing(2)
        bg_color_grid.set_row_homogeneous(True)
        bg_color_grid.set_column_homogeneous(True)
        bg_color_grid.add_css_class("color-grid")

        # Basic colors for background (same palette as text)
        bg_colors = text_colors

        # Create color buttons and add to grid
        row, col = 0, 0
        for color_hex in bg_colors:
            color_button = self.create_color_button(color_hex)
            color_button.connect("clicked", lambda btn, c=color_hex: self.on_bg_color_selected(win, c, bg_color_popover))
            bg_color_grid.attach(color_button, col, row, 1, 1)
            col += 1
            if col >= 10:  # 10 columns
                col = 0
                row += 1

        bg_color_box_menu.append(bg_color_grid)

        # Add "More Colors..." button
        bg_more_colors_button = Gtk.Button(label="More Colors...")
        bg_more_colors_button.set_margin_top(6)
        bg_more_colors_button.connect("clicked", lambda btn: self.on_more_bg_colors_clicked(win, bg_color_popover))
        bg_color_box_menu.append(bg_more_colors_button)

        # Set content for popover
        bg_color_popover.set_child(bg_color_box_menu)

        # Create the SplitButton
        win.bg_color_button = Adw.SplitButton()
        win.bg_color_button.set_tooltip_text("Background Color")
        win.bg_color_button.set_focus_on_click(False)
        win.bg_color_button.set_size_request(40, 36)
        win.bg_color_button.set_child(bg_color_box)
        win.bg_color_button.set_popover(bg_color_popover)

        # Connect the click handler to apply the current color
        win.bg_color_button.connect("clicked", lambda btn: self.on_bg_color_button_clicked(win))
        color_bg_group.append(win.bg_color_button)
        
        win.toolbars_wrapbox.append(color_bg_group)
        # Clear formatting button
        clear_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)        
        clear_group.set_margin_start(0)
        clear_group.set_margin_end(0)
        
        clear_formatting_button = Gtk.Button(icon_name="eraser-symbolic")
        clear_formatting_button.set_tooltip_text("Remove Text Formatting")
        clear_formatting_button.set_size_request(42, 36)
        clear_formatting_button.connect("clicked", lambda btn: self.on_clear_formatting_clicked(win, btn))
        clear_group.append(clear_formatting_button)

        win.toolbars_wrapbox.append(clear_group)

        # Create linked button group for alignment controls
        alignment_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        
        # Align Left button
        align_left_button = Gtk.ToggleButton(icon_name="format-justify-left-symbolic")
        align_left_button.set_tooltip_text("Align Left")
        align_left_button.set_focus_on_click(False)
        align_left_button.set_size_request(40, 36)
        # Store the handler ID when connecting
        align_left_button.handler_id = align_left_button.connect("toggled", 
            lambda btn: self.on_align_left_toggled(win, btn))
        alignment_group.append(align_left_button)

        # Align Center button
        align_center_button = Gtk.ToggleButton(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Align Center")
        align_center_button.set_focus_on_click(False)
        align_center_button.set_size_request(40, 36)
        # Store the handler ID when connecting
        align_center_button.handler_id = align_center_button.connect("toggled", 
            lambda btn: self.on_align_center_toggled(win, btn))
        alignment_group.append(align_center_button)

        # Align Right button
        align_right_button = Gtk.ToggleButton(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right")
        align_right_button.set_focus_on_click(False)
        align_right_button.set_size_request(40, 36)
        # Store the handler ID when connecting
        align_right_button.handler_id = align_right_button.connect("toggled", 
            lambda btn: self.on_align_right_toggled(win, btn))
        alignment_group.append(align_right_button)

        # Justify button
        align_justify_button = Gtk.ToggleButton(icon_name="format-justify-fill-symbolic")
        align_justify_button.set_tooltip_text("Justify")
        align_justify_button.set_focus_on_click(False)
        align_justify_button.set_size_request(40, 36)
        # Store the handler ID when connecting
        align_justify_button.handler_id = align_justify_button.connect("toggled", 
            lambda btn: self.on_align_justify_toggled(win, btn))
        alignment_group.append(align_justify_button)

        
        # Store references to alignment buttons for toggling
        win.alignment_buttons = {
            'left': align_left_button,
            'center': align_center_button, 
            'right': align_right_button,
            'justify': align_justify_button
        }

        win.toolbars_wrapbox.append(alignment_group)


        # --- Insert operations group (Table, Text Box, Image) ---
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        insert_group.add_css_class("linked")  # Apply linked styling
        insert_group.set_margin_start(0)

        # Insert table button
        table_button = Gtk.Button(icon_name="table-symbolic")  # Use a standard table icon
        table_button.set_size_request(40, 36)
        table_button.set_tooltip_text("Insert Table")
        table_button.connect("clicked", lambda btn: self.on_insert_table_clicked(win, btn))

        # Insert text box button
        text_box_button = Gtk.Button(icon_name="insert-text-symbolic")
        text_box_button.set_size_request(40, 36)
        text_box_button.set_tooltip_text("Insert Text Box")
        text_box_button.connect("clicked", lambda btn: self.on_insert_text_box_clicked(win, btn))

        # Insert image button
        image_button = Gtk.Button(icon_name="insert-image-symbolic")
        image_button.set_size_request(40, 36)
        image_button.set_tooltip_text("Insert Image")
        image_button.connect("clicked", lambda btn: self.on_insert_image_clicked(win, btn))

        # Insert link button
        link_button = Gtk.Button(icon_name="insert-link-symbolic")
        link_button.set_size_request(40, 36)
        link_button.set_tooltip_text("Insert link")
        link_button.connect("clicked", lambda btn: self.on_insert_link_clicked(win, btn))

        # Add buttons to insert group
        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        insert_group.append(link_button)
        # Add insert group to toolbar
        win.toolbars_wrapbox.append(insert_group)


        # --- Add the Show HTML button ---
        show_html_button = Gtk.Button(icon_name="text-x-generic-symbolic")
        show_html_button.set_tooltip_text("Show HTML")
        show_html_button.set_margin_start(10)
        show_html_button.connect("clicked", lambda btn: self.on_show_html_clicked(win, btn))
        win.toolbars_wrapbox.append(show_html_button)













        # Set toolbar WrapBox as the child of toolbar revealer
        win.toolbar_revealer.set_child(win.toolbars_wrapbox)
        
        # Add toolbar revealer to headerbar box
        win.headerbar_box.append(win.toolbar_revealer)
        
        # Set the headerbar box as child of headerbar revealer
        win.headerbar_revealer.set_child(win.headerbar_box)
        
        # Add headerbar revealer to main box
        win.main_box.append(win.headerbar_revealer)
        
        # Create content box (for webview and toolbars)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        # Create webview
        win.webview = WebKit.WebView()
        win.webview.set_vexpand(True)
        win.webview.set_hexpand(True) 
        win.webview.load_html(self.get_editor_html(), None)
        settings = win.webview.get_settings()
        try:
            settings.set_enable_developer_extras(True)
        except:
            pass
        
        try:
            user_content_manager = win.webview.get_user_content_manager()
            user_content_manager.register_script_message_handler("contentChanged")
            user_content_manager.connect("script-message-received::contentChanged", 
                                        lambda mgr, res: self.on_content_changed(win, mgr, res))
            
            # Add handler for formatting changes
            user_content_manager.register_script_message_handler("formattingChanged")
            user_content_manager.connect("script-message-received::formattingChanged", 
                                        lambda mgr, res: self.on_formatting_changed(win, mgr, res))
            
            # ADD THESE TABLE-RELATED MESSAGE HANDLERS
            user_content_manager.register_script_message_handler("tableClicked")
            user_content_manager.register_script_message_handler("tableDeleted")
            user_content_manager.register_script_message_handler("tablesDeactivated")
            
            user_content_manager.connect("script-message-received::tableClicked", 
                                        lambda mgr, res: self.on_table_clicked(win, mgr, res))
            user_content_manager.connect("script-message-received::tableDeleted", 
                                        lambda mgr, res: self.on_table_deleted(win, mgr, res))
            user_content_manager.connect("script-message-received::tablesDeactivated", 
                                        lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
        except:
            print("Warning: Could not set up JavaScript message handlers")
        
        # ADD THIS: Key event controller for table navigation
        win.key_controller = Gtk.EventControllerKey()
        win.key_controller.connect("key-pressed", self.on_webview_key_pressed)
        win.webview.add_controller(win.key_controller)
        
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        # Find bar with revealer - kept at the bottom above statusbar
        win.find_bar = self.create_find_bar(win)
        content_box.append(win.find_bar)

        # Create table toolbar with revealer (hidden by default)
        win.table_toolbar_revealer = Gtk.Revealer()
        win.table_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.table_toolbar_revealer.set_transition_duration(250)
        win.table_toolbar_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create and add table toolbar
        win.table_toolbar = self.create_table_toolbar(win)
        win.table_toolbar_revealer.set_child(win.table_toolbar)
        content_box.append(win.table_toolbar_revealer)
        
        # Create statusbar with revealer
        win.statusbar_revealer = Gtk.Revealer()
        win.statusbar_revealer.add_css_class("flat-header")
        win.statusbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.statusbar_revealer.set_transition_duration(250)
        win.statusbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create a box for the statusbar 
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        statusbar_box.set_margin_start(10)
        statusbar_box.set_margin_end(10)
        statusbar_box.set_margin_top(0)
        statusbar_box.set_margin_bottom(4)
        
        # Create the text label
        win.statusbar = Gtk.Label(label="Ready")
        win.statusbar.set_halign(Gtk.Align.START)
        win.statusbar.set_hexpand(True)
        statusbar_box.append(win.statusbar)
        
        # Add zoom toggle button at the right side of the statusbar
        win.zoom_toggle_button = Gtk.ToggleButton()
        win.zoom_toggle_button.set_icon_name("org.gnome.Settings-accessibility-zoom-symbolic")
        win.zoom_toggle_button.set_tooltip_text("Toggle Zoom Controls")
        win.zoom_toggle_button.add_css_class("flat")
        win.zoom_toggle_button.connect("toggled", lambda btn: self.on_zoom_toggle_clicked(win, btn))
        statusbar_box.append(win.zoom_toggle_button)
        
        # Create zoom revealer for toggle functionality
        win.zoom_revealer = Gtk.Revealer()
        win.zoom_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_LEFT)
        win.zoom_revealer.set_transition_duration(300)
        win.zoom_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create zoom control element inside the revealer
        zoom_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_control_box.add_css_class("linked")  # Use linked styling for cleaner appearance
        zoom_control_box.set_halign(Gtk.Align.END)
        
        # Create zoom level label
        win.zoom_label = Gtk.Label(label="100%")
        win.zoom_label.set_width_chars(4)  # Set a fixed width for the label
        win.zoom_label.set_margin_start(0)
        zoom_control_box.append(win.zoom_label)
        
        # Add zoom out button
        zoom_out_button = Gtk.Button.new_from_icon_name("zoom-out-symbolic")
        zoom_out_button.set_tooltip_text("Zoom Out")
        zoom_out_button.connect("clicked", lambda btn: self.on_zoom_out_clicked(win))
        zoom_control_box.append(zoom_out_button)
        
        # Create the slider for zoom with just marks, no text
        adjustment = Gtk.Adjustment(
            value=100,     # Default value
            lower=50,      # Minimum value
            upper=400,     # Maximum value
            step_increment=10,  # Step size
            page_increment=50   # Page step size
        )

        win.zoom_scale = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        win.zoom_scale.set_draw_value(False)  # Don't show the value on the scale
        win.zoom_scale.set_size_request(100, -1)  # Set a reasonable width
        win.zoom_scale.set_round_digits(0)  # Round to integer values

        # Add only marks without any text
        for mark_value in [50, 100, 200, 300]:
            win.zoom_scale.add_mark(mark_value, Gtk.PositionType.BOTTOM, None)

        # Connect to our zoom handler
        win.zoom_scale.connect("value-changed", lambda s: self.on_zoom_changed_statusbar(win, s))
        zoom_control_box.append(win.zoom_scale)

        # Enable snapping to the marks
        win.zoom_scale.set_has_origin(False)  # Disable highlighting from origin to current value

        # Add zoom in button
        zoom_in_button = Gtk.Button.new_from_icon_name("zoom-in-symbolic")
        zoom_in_button.set_tooltip_text("Zoom In")
        zoom_in_button.connect("clicked", lambda btn: self.on_zoom_in_clicked(win))
        zoom_control_box.append(zoom_in_button)

        # Set the zoom control box as the child of the revealer
        win.zoom_revealer.set_child(zoom_control_box)

        # Add the zoom revealer to the statusbar, before the toggle button
        statusbar_box.insert_child_after(win.zoom_revealer, win.statusbar)

        # Set the statusbar box as the child of the revealer
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        self.setup_keyboard_shortcuts(win)
        
        # Add case change action to the window
        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        win.connect("close-request", self.on_window_close_request)

        # Add to windows list
        self.windows.append(win)
        self.setup_spacing_actions(win)
        
        return win

##########################  show html
    def on_show_html_clicked(self, win, btn):
        """Handle Show HTML button click"""
        win.statusbar.set_text("Getting HTML content...")
        
        # Execute JavaScript to get the full HTML content
        js_code = """
        (function() {
            // Get the complete HTML content of the editor
            const editorContent = document.getElementById('editor').innerHTML;
            return editorContent;
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self.show_html_dialog(win, webview, result),
            None
        )

    # 3. Function to display the HTML in a dialog

    def show_html_dialog(self, win, webview, result):
        """Show the HTML content in a dialog"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            html_content = ""
            
            if js_result:
                # Get the HTML content
                if hasattr(js_result, 'get_js_value'):
                    html_content = js_result.get_js_value().to_string()
                else:
                    html_content = js_result.to_string()
                
                # Create a dialog with resizable text view
                dialog = Adw.Dialog()
                dialog.set_title("HTML Source")
                dialog.set_content_width(600)
                dialog.set_content_height(400)
                
                # Create content box
                content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
                content_box.set_margin_top(24)
                content_box.set_margin_bottom(24)
                content_box.set_margin_start(24)
                content_box.set_margin_end(24)
                
                # Add explanation label
                explanation = Gtk.Label()
                explanation.set_markup("<b>HTML Source Code:</b>")
                explanation.set_halign(Gtk.Align.START)
                content_box.append(explanation)
                
                # Create scrolled window for text view
                scrolled_window = Gtk.ScrolledWindow()
                scrolled_window.set_vexpand(True)
                scrolled_window.set_hexpand(True)
                
                # Create text view for HTML content
                text_view = Gtk.TextView()
                text_view.set_editable(True)  # Allow editing
                text_view.set_monospace(True)  # Use monospace font for code
                text_view.set_wrap_mode(Gtk.WrapMode.WORD)
                
                # Create text buffer and set content
                text_buffer = text_view.get_buffer()
                text_buffer.set_text(html_content)
                
                scrolled_window.set_child(text_view)
                content_box.append(scrolled_window)
                
                # Add buttons box
                buttons_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
                buttons_box.set_halign(Gtk.Align.END)
                buttons_box.set_margin_top(12)
                
                # Copy button - left aligned with spacer to separate from other buttons
                copy_button = Gtk.Button(label="Copy to Clipboard")
                copy_button.connect("clicked", lambda btn: self.copy_html_to_clipboard(win, text_buffer))
                copy_button.set_halign(Gtk.Align.START)
                
                # Button spacer to push close/apply buttons to the right
                button_spacer = Gtk.Box()
                button_spacer.set_hexpand(True)
                
                # Apply changes button
                apply_button = Gtk.Button(label="Apply Changes")
                apply_button.add_css_class("suggested-action")
                apply_button.connect("clicked", lambda btn: self.apply_html_changes(win, dialog, text_buffer))
                
                # Close button
                close_button = Gtk.Button(label="Close")
                close_button.connect("clicked", lambda btn: dialog.close())
                
                buttons_box.append(copy_button)
                buttons_box.append(button_spacer)
                buttons_box.append(close_button)
                buttons_box.append(apply_button)
                content_box.append(buttons_box)
                
                # Set dialog content and present
                dialog.set_child(content_box)
                dialog.present(win)
                
                # Update status
                win.statusbar.set_text("HTML content displayed")
            else:
                win.statusbar.set_text("Failed to get HTML content")
                
        except Exception as e:
            print(f"Error displaying HTML: {e}")
            win.statusbar.set_text(f"Error displaying HTML: {e}")

    # 4. Function to apply HTML changes

    def apply_html_changes(self, win, dialog, text_buffer):
        """Apply the edited HTML content back to the editor"""
        try:
            # Get the text from the buffer
            start_iter = text_buffer.get_start_iter()
            end_iter = text_buffer.get_end_iter()
            html_content = text_buffer.get_text(start_iter, end_iter, True)
            
            # Escape for JavaScript
            js_content = html_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            
            # Set the content in the editor
            js_code = f'setContent("{js_content}");'
            self.execute_js(win, js_code)
            
            # Close the dialog
            dialog.close()
            
            # Update status
            win.statusbar.set_text("HTML changes applied")
            
            # Mark document as modified
            win.modified = True
            self.update_window_title(win)
            
        except Exception as e:
            print(f"Error applying HTML changes: {e}")
            win.statusbar.set_text(f"Error applying HTML changes: {e}")

    def copy_html_to_clipboard(self, win, text_buffer):
        """Copy the HTML content to clipboard"""
        try:
            # Get the text from the buffer
            start_iter = text_buffer.get_start_iter()
            end_iter = text_buffer.get_end_iter()
            html_content = text_buffer.get_text(start_iter, end_iter, True)
            
            # Get the clipboard
            clipboard = Gdk.Display.get_default().get_clipboard()
            
            # Set the text to the clipboard
            clipboard.set(html_content)
            
            # Update status
            win.statusbar.set_text("HTML copied to clipboard")
            
        except Exception as e:
            print(f"Error copying to clipboard: {e}")
            win.statusbar.set_text(f"Error copying to clipboard: {e}")
##########################  /show html           

###################### Table related HTMLEDITOR METHODS

    def _parse_color_string(self, color_str):
        """Parse a color string (hex, rgb, or rgba) into a Gdk.RGBA object"""
        try:
            rgba = Gdk.RGBA()
            
            if color_str.startswith('#'):
                # Hex color
                rgba.parse(color_str)
                return rgba
            elif color_str.startswith('rgb'):
                # RGB(A) color
                import re
                match = re.search(r'rgba?\(([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)(?:[,\s]+([\d.]+))?\)', color_str)
                if match:
                    r, g, b = float(match.group(1)), float(match.group(2)), float(match.group(3))
                    a = float(match.group(4)) if match.group(4) else 1.0
                    
                    # Convert 0-255 range to 0-1 range if necessary
                    if r > 1 or g > 1 or b > 1:
                        r, g, b = r/255, g/255, b/255
                    
                    rgba.red, rgba.green, rgba.blue, rgba.alpha = r, g, b, a
                    return rgba
            
            return None
        except Exception as e:
            print(f"Error parsing color string '{color_str}': {e}")
            return None

    def _is_dark_theme(self):
        """Check if the system is using dark theme"""
        try:
            style_manager = Adw.StyleManager.get_default()
            return style_manager.get_dark()
        except:
            # Fallback method
            settings = Gtk.Settings.get_default()
            return settings.get_property("gtk-application-prefer-dark-theme")

    def _rgba_to_color(self, rgba):
        """Convert Gdk.RGBA to Gdk.Color for compatibility"""
        color = Gdk.Color()
        color.red = int(rgba.red * 65535)
        color.green = int(rgba.green * 65535)
        color.blue = int(rgba.blue * 65535)
        return color

    def _update_margin_controls(self, win, webview, result):
        """Update margin spin buttons with current table margins"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            result_str = None
            
            if hasattr(js_result, 'get_js_value'):
                result_str = js_result.get_js_value().to_string()
            else:
                result_str = js_result.to_string()
            
            if result_str:
                import json
                margins = json.loads(result_str)
                
                if hasattr(win, 'margin_controls') and isinstance(margins, dict):
                    for side in ['top', 'right', 'bottom', 'left']:
                        if side in win.margin_controls and side in margins:
                            win.margin_controls[side].set_value(margins[side])
        except Exception as e:
            print(f"Error updating margin controls: {e}")

    def on_margin_changed(self, win, side, value):
        """Apply margin change to the active table"""
        js_code = f"""
        (function() {{
            // Pass all four sides with the updated value for the specified side
            const margins = getTableMargins() || {{ top: 0, right: 0, bottom: 0, left: 0 }};
            margins.{side} = {value};
            setTableMargins(margins.top, margins.right, margins.bottom, margins.left);
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Applied {side} margin: {value}px")   
                 
    def get_editor_html(self, content=""):
        """Return HTML for the editor with improved table and text box styles"""
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
        <!DOCTYPE html>
        <html style="height: 100%;">
        <head>
            <title>HTML Editor</title>
            <style>
                html, body {{
                    height: 100%;
                    padding: 0;
                    font-family: Sans;
                }}
                #editor {{
                    padding: 0px;
                    outline: none;
                    height: 100%;
                    font-family: Sans;
                    font-size: 11pt;
                    position: relative; /* Important for absolute positioning of floating tables */
                    min-height: 300px;  /* Ensure there's space to drag tables */
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
                /* Table styles */
                table {{
                    border-collapse: collapse;
                    margin: 0 0 10px 0;  /* Changed from margin: 10px 0 */
                    position: relative;  /* Important for internal handles */
                    resize: both;
                    overflow: visible;   /* Changed from auto to visible to ensure handles are not clipped */
                    min-width: 30px;
                    min-height: 30px;
                }}
                table.left-align {{
                    float: left;
                    margin-right: 10px;
                    margin-top: 0;  /* Ensure no top margin for floated tables */
                    clear: none;
                }}
                table.right-align {{
                    float: right;
                    margin-left: 10px;
                    margin-top: 0;  /* Ensure no top margin for floated tables */
                    clear: none;
                }}
                table.center-align {{
                    display: table;  /* Ensure block behavior is correct */
                    margin-left: auto !important;
                    margin-right: auto !important;
                    margin-top: 0;
                    float: none !important;
                    clear: both;
                    position: relative;
                }}
                table.no-wrap {{
                    float: none;
                    clear: both;
                    width: 100%;
                    margin-top: 0;
                }}
                table td {{
                    padding: 5px;
                    min-width: 30px;
                    position: relative;
                }}
                table th {{
                    padding: 5px;
                    min-width: 30px;
                    background-color: #f0f0f0;
                }}
                
                /* Floating table styles - border removed from CSS and applied conditionally via JS */
                table.floating-table {{
                    position: absolute !important;
                    z-index: 50;
                    box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                    background-color: rgba(255, 255, 255, 0.95);
                    cursor: grab;
                }}
                
                table.floating-table:active {{
                    cursor: grabbing;
                }}
                
                table.floating-table .table-drag-handle {{
                    width: 20px !important;
                    height: 20px !important;
                    border-radius: 3px;
                    opacity: 0.9;
                }}
                
                /* Table handles are now defined in JavaScript for better control */
                
                /* Text box styles (enhanced table) */
                table.text-box-table {{
                    border: 1px solid #ccc !important;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    background-color: #fff;
                    width: 80px;  /* Initial width */
                    height: 80px; /* Initial height */
                    min-width: 80px;
                    min-height: 80px;
                    resize: both !important; /* Ensure resizability */
                }}
                
                table.text-box-table td {{
                    vertical-align: top;
                }}
                
                /* Ensure text boxes handle selection properly */
                #editor ::selection {{
                    background-color: #b5d7ff;
                    color: inherit;
                }}
                
                @media (prefers-color-scheme: dark) {{
                    html, body {{
                        background-color: #1e1e1e;
                        color: #c0c0c0;
                    }}
                    table th {{
                        background-color: #2a2a2a;
                    }}
                    table.text-box-table {{
                        border-color: #444 !important;
                        background-color: #2d2d2d;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                    }}
                    table.floating-table {{
                        background-color: rgba(45, 45, 45, 0.95);
                        box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                    }}
                    #editor ::selection {{
                        background-color: #264f78;
                        color: inherit;
                    }}
                }}
                @media (prefers-color-scheme: light) {{
                    html, body {{
                        background-color: #ffffff;
                        color: #000000;
                    }}
                }}
            </style>
            <script>
                window.initialContent = "{content or '<div><font face=\"Sans\" style=\"font-size: 11pt;\"><br></font></div>'}";
                {self.get_editor_js()}
            </script>
        </head>
        <body>
            <div id="editor" contenteditable="true"></div>
        </body>
        </html>
        """
############################# /TABLE RELATED HTMLEDITOR METHODS

#################### DIRECT COPY PASTE from TABLE52
    def insert_table_js(self):
        """JavaScript for insert table and related functionality"""
        return f"""
        {self.table_theme_helpers_js()}
        {self.table_handles_css_js()}
        {self.table_insert_functions_js()}
        {self.table_activation_js()}
        {self.table_drag_resize_js()}
        {self.table_row_column_js()}
        {self.table_alignment_js()}
        {self.table_floating_js()}
        {self.table_event_handlers_js()}
        """

    def table_theme_helpers_js(self):
        """JavaScript helper functions for theme detection and colors"""
        return """
        // Function to check if we're in dark mode
        function isDarkMode() {
            return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        }
        
        // Function to get appropriate border color based on current theme
        function getBorderColor() {
            return isDarkMode() ? '#444' : '#ccc';
        }
        
        // Function to get appropriate header background color based on current theme
        function getHeaderBgColor() {
            return isDarkMode() ? '#2a2a2a' : '#f0f0f0';
        }
        """

    def table_handles_css_js(self):
        """JavaScript that defines CSS for table handles with proper display properties"""
        return """
            // CSS for table handles
            const tableHandlesCSS = `
            /* Table drag handle - positioned inside the table */
            .table-drag-handle {
                position: absolute;
                top: 0;
                left: 0;
                width: 16px;
                height: 16px;
                background-color: #4e9eff;
                cursor: move;
                z-index: 1000;
                display: flex;  /* Changed from static display to allow proper show/hide */
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 10px;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
            }

            /* Table resize handle - triangular shape in bottom right */
            .table-handle {
                position: absolute;
                bottom: 0;
                right: 0;
                width: 0;
                height: 0;
                border-style: solid;
                border-width: 0 0 16px 16px;
                border-color: transparent transparent #4e9eff transparent;
                cursor: nwse-resize;
                z-index: 1000;
                pointer-events: all;
                user-select: none;
                -webkit-user-select: none;
                -moz-user-select: none;
                -ms-user-select: none;
                display: block;  /* Added to allow proper show/hide */
            }
            
            /* Floating table styles */
            .floating-table {
                position: absolute !important;
                z-index: 50;
                box-shadow: 0 3px 10px rgba(0,0,0,0.2);
                background-color: rgba(255, 255, 255, 0.95);
                cursor: grab;
            }
            
            .floating-table:active {
                cursor: grabbing;
            }
            
            .floating-table .table-drag-handle {
                width: 20px !important;
                height: 20px !important;
                border-radius: 3px;
                opacity: 0.9;
            }

            @media (prefers-color-scheme: dark) {
                .table-drag-handle {
                    background-color: #0078d7;
                }
                .table-handle {
                    border-color: transparent transparent #0078d7 transparent;
                }
                .floating-table {
                    background-color: rgba(45, 45, 45, 0.95);
                    box-shadow: 0 3px 10px rgba(0,0,0,0.5);
                }
                .floating-table .table-drag-handle {
                    background-color: #0078d7;
                }
            }`;
            
            // Function to add the table handle styles to the document
            function addTableHandleStyles() {
                // Check if our style element already exists
                let styleElement = document.getElementById('table-handle-styles');
                
                // If not, create and append it
                if (!styleElement) {
                    styleElement = document.createElement('style');
                    styleElement.id = 'table-handle-styles';
                    styleElement.textContent = tableHandlesCSS;
                    document.head.appendChild(styleElement);
                } else {
                    // If it exists, update the content
                    styleElement.textContent = tableHandlesCSS;
                }
            }
            """
            
    def table_insert_functions_js(self):
        """JavaScript for inserting tables with default margins"""
        return """
        // Function to insert a table at the current cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth, isFloating) {
            // Get theme-appropriate colors
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Create table HTML
            let tableHTML = '<table cellspacing="0" cellpadding="5" ';
            
            // Add class and style attributes (including default margins)
            tableHTML += 'class="editor-table no-wrap" style="border-collapse: collapse; width: ' + tableWidth + '; margin: 6px 6px 0 0;">';
            
            // Create header row if requested
            if (hasHeader) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<th style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; background-color: ' + headerBgColor + ';">Header ' + (j+1) + '</th>';
                }
                tableHTML += '</tr>';
                rows--; // Reduce regular rows by one since we added a header
            }
            
            // Create regular rows and cells
            for (let i = 0; i < rows; i++) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<td style="border: ' + borderWidth + 'px solid ' + borderColor + '; padding: 5px; min-width: 30px;">Cell</td>';
                }
                tableHTML += '</tr>';
            }
            
            tableHTML += '</table><p></p>';
            
            // Insert the table at the current cursor position
            document.execCommand('insertHTML', false, tableHTML);
            
            // Activate the newly inserted table
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editor-table');
                const newTable = tables[tables.length - 1] || document.querySelector('table:last-of-type');
                if (newTable) {
                    // Ensure the editor-table class is present
                    if (!newTable.classList.contains('editor-table')) {
                        newTable.classList.add('editor-table');
                    }
                    
                    // Set default margins
                    newTable.style.marginTop = '6px';
                    newTable.style.marginRight = '6px';
                    newTable.style.marginBottom = '0px';
                    newTable.style.marginLeft = '0px';
                    
                    // Store margin values as attributes
                    newTable.setAttribute('data-margin-top', '6');
                    newTable.setAttribute('data-margin-right', '6');
                    newTable.setAttribute('data-margin-bottom', '0');
                    newTable.setAttribute('data-margin-left', '0');
                    
                    // Make table floating if requested
                    if (isFloating) {
                        newTable.classList.add('floating-table');
                        setTableFloating(newTable);
                    }
                    
                    activateTable(newTable);
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                }
            }, 10);
        }
        """

    def table_activation_js(self):
        """JavaScript for table activation and deactivation"""
        return """
        // Variables for table handling
        var activeTable = null;
        var isDragging = false;
        var isResizing = false;
        var dragStartX = 0;
        var dragStartY = 0;
        var tableStartX = 0;
        var tableStartY = 0;
        
        // Function to find parent table element
        function findParentTable(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'TABLE') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Function to activate a table (add handles)
        function activateTable(tableElement) {
            if (activeTable === tableElement) return; // Already active
            
            // Deactivate any previously active tables
            if (activeTable && activeTable !== tableElement) {
                deactivateTable(activeTable);
            }
            
            activeTable = tableElement;
            
            // Store original styles and apply selection styling
            storeAndApplyTableStyles(tableElement);
            
            // Determine current table alignment class
            const currentClasses = tableElement.className;
            const alignmentClasses = ['left-align', 'right-align', 'center-align', 'no-wrap'];
            let currentAlignment = 'no-wrap';
            
            alignmentClasses.forEach(cls => {
                if (currentClasses.includes(cls)) {
                    currentAlignment = cls;
                }
            });
            
            // Reset and apply the appropriate alignment class
            alignmentClasses.forEach(cls => tableElement.classList.remove(cls));
            tableElement.classList.add(currentAlignment);
            
            // Add resize handle if needed
            if (!tableElement.querySelector('.table-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'table-handle';
                
                // Make handle non-selectable and prevent focus
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.setAttribute('tabindex', '-1');
                
                // Add event listener to prevent propagation of mousedown events
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableResize(e, tableElement);
                }, true);
                
                tableElement.appendChild(resizeHandle);
            }
            
            // Add drag handle if needed
            if (!tableElement.querySelector('.table-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'table-drag-handle';
                dragHandle.innerHTML = '↕';
                
                // Set title based on whether it's a floating table or not
                if (tableElement.classList.contains('floating-table')) {
                    dragHandle.title = 'Drag to move table freely';
                } else {
                    dragHandle.title = 'Drag to reposition table between paragraphs';
                }
                
                // Make handle non-selectable and prevent focus
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.setAttribute('tabindex', '-1');
                
                // Add event listener to prevent propagation of mousedown events
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableDrag(e, tableElement);
                }, true);
                
                tableElement.appendChild(dragHandle);
            }
            
            // Special styling for floating tables
            if (tableElement.classList.contains('floating-table')) {
                enhanceTableDragHandles(tableElement);
            }
        }
        
        // Store original table styles and apply selection styling
        function storeAndApplyTableStyles(tableElement) {
            // Add selected class for CSS styling
            tableElement.classList.add('table-selected');
            
            // Ensure table has editor-table class
            if (!tableElement.classList.contains('editor-table')) {
                tableElement.classList.add('editor-table');
            }
            
            // Ensure the table has position: relative for proper handle positioning
            // Only set relative position if not already a floating table
            if (!tableElement.classList.contains('floating-table')) {
                tableElement.style.position = 'relative';
            }
        }
        
        // Function to deactivate a specific table
        function deactivateTable(tableElement) {
            if (!tableElement) return;
            
            // Remove selected class
            tableElement.classList.remove('table-selected');
            
            // Remove handles
            const resizeHandle = tableElement.querySelector('.table-handle');
            if (resizeHandle) resizeHandle.remove();
            
            const dragHandle = tableElement.querySelector('.table-drag-handle');
            if (dragHandle) dragHandle.remove();
            
            if (tableElement === activeTable) {
                activeTable = null;
            }
        }
        
        // Function to deactivate all tables
        function deactivateAllTables() {
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {
                deactivateTable(table);
            });
            
            // Always notify that tables are deactivated, regardless of whether activeTable was set
            activeTable = null;
            try {
                window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
            } catch(e) {
                console.log("Could not notify about table deactivation:", e);
            }
        }
        
        // Function to update table colors based on current theme
        function updateTableThemeColors(tableElement) {
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Update all headers
            const headers = tableElement.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = headerBgColor;
                header.style.borderColor = borderColor;
            });
            
            // Update all cells
            const cells = tableElement.querySelectorAll('td');
            cells.forEach(cell => {
                cell.style.borderColor = borderColor;
            });
        }
        """

    def table_drag_resize_js(self):
        """JavaScript for table dragging and resizing"""
        return """
        // Function to start table drag
        function startTableDrag(e, tableElement) {
            e.preventDefault();
            if (!tableElement) return;
            
            isDragging = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            
            // Set cursor based on whether the table is floating or not
            if (tableElement.classList.contains('floating-table')) {
                document.body.style.cursor = 'grabbing';
            } else {
                document.body.style.cursor = 'move';
            }
        }
        
        // Function to move table
        function moveTable(e) {
            if (!isDragging || !activeTable) return;
            
            // Check if the table is a floating table
            if (activeTable.classList.contains('floating-table')) {
                // For floating tables, just move it to the mouse position with offset
                const deltaX = e.clientX - dragStartX;
                const deltaY = e.clientY - dragStartY;
                
                // Get current position from style
                const currentTop = parseInt(activeTable.style.top) || 0;
                const currentLeft = parseInt(activeTable.style.left) || 0;
                
                // Update position
                activeTable.style.top = `${currentTop + deltaY}px`;
                activeTable.style.left = `${currentLeft + deltaX}px`;
                
                // Update starting points for next movement
                dragStartX = e.clientX;
                dragStartY = e.clientY;
                
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
            } else {
                const currentY = e.clientY;
                const deltaY = currentY - dragStartY;
                
                if (Math.abs(deltaY) > 30) {
                    const editor = document.getElementById('editor');
                    const blocks = Array.from(editor.children).filter(node => {
                        const style = window.getComputedStyle(node);
                        return style.display.includes('block') || node.tagName === 'TABLE';
                    });
                    
                    const tableIndex = blocks.indexOf(activeTable);
                    
                    if (deltaY < 0 && tableIndex > 0) {
                        const targetElement = blocks[tableIndex - 1];
                        editor.insertBefore(activeTable, targetElement);
                        dragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    } 
                    else if (deltaY > 0 && tableIndex < blocks.length - 1) {
                        const targetElement = blocks[tableIndex + 1];
                        if (targetElement.nextSibling) {
                            editor.insertBefore(activeTable, targetElement.nextSibling);
                        } else {
                            editor.appendChild(activeTable);
                        }
                        dragStartY = currentY;
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            }
        }
        
        // Function to start table resize
        function startTableResize(e, tableElement) {
            e.preventDefault();
            isResizing = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            const style = window.getComputedStyle(tableElement);
            tableStartX = parseInt(style.width) || tableElement.offsetWidth;
            tableStartY = parseInt(style.height) || tableElement.offsetHeight;
        }
        
        // Function to resize table
        function resizeTable(e) {
            if (!isResizing || !activeTable) return;
            
            const deltaX = e.clientX - dragStartX;
            
            // Only adjust width, not height - this prevents the horizontal line artifact
            activeTable.style.width = (tableStartX + deltaX) + 'px';
        }
        """

    def table_row_column_js(self):
        """JavaScript for table row and column operations"""
        return """
        // Function to add a row to the table
        function addTableRow(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const rows = tableElement.rows;
            if (rows.length > 0) {
                // If position is provided, use it, otherwise append at the end
                const rowIndex = (position !== undefined) ? position : rows.length;
                const newRow = tableElement.insertRow(rowIndex);
                
                for (let i = 0; i < rows[0].cells.length; i++) {
                    const cell = newRow.insertCell(i);
                    cell.innerHTML = '&nbsp;';
                    // Copy border style from other cells
                    if (rows[0].cells[i].style.border) {
                        cell.style.border = rows[0].cells[i].style.border;
                    } else {
                        cell.style.border = '1px solid ' + borderColor;
                    }
                    // Copy padding style from other cells
                    if (rows[0].cells[i].style.padding) {
                        cell.style.padding = rows[0].cells[i].style.padding;
                    } else {
                        cell.style.padding = '5px';
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to add a column to the table
        function addTableColumn(tableElement, position) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            const rows = tableElement.rows;
            for (let i = 0; i < rows.length; i++) {
                // If position is provided, use it, otherwise append at the end
                const cellIndex = (position !== undefined) ? position : rows[i].cells.length;
                const cell = rows[i].insertCell(cellIndex);
                cell.innerHTML = '&nbsp;';
                
                // Default styles based on theme
                let cellStyle = {
                    border: '1px solid ' + borderColor,
                    padding: '5px'
                };
                
                // Copy styles from adjacent cells if available
                if (rows[i].cells.length > 1) {
                    const refCell = cellIndex > 0 ? 
                                    rows[i].cells[cellIndex - 1] : 
                                    rows[i].cells[cellIndex + 1];
                                    
                    if (refCell) {
                        if (refCell.style.border) {
                            cellStyle.border = refCell.style.border;
                        }
                        if (refCell.style.padding) {
                            cellStyle.padding = refCell.style.padding;
                        }
                        
                        // If it's a header cell, make new cell a header too
                        if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            
                            // Apply all styles
                            Object.assign(headerCell.style, cellStyle);
                            headerCell.style.backgroundColor = headerBgColor;
                            
                            cell.parentNode.replaceChild(headerCell, cell);
                        } else {
                            // Apply styles to normal cell
                            Object.assign(cell.style, cellStyle);
                        }
                    }
                } else {
                    // Apply default styles if no reference cells
                    Object.assign(cell.style, cellStyle);
                    
                    // If this is the first row, it might be a header
                    if (i === 0 && rows[0].cells[0].tagName === 'TH') {
                        const headerCell = document.createElement('th');
                        headerCell.innerHTML = cell.innerHTML;
                        Object.assign(headerCell.style, cellStyle);
                        headerCell.style.backgroundColor = headerBgColor;
                        cell.parentNode.replaceChild(headerCell, cell);
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a row from the table
        function deleteTableRow(tableElement, rowIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 1) {
                // If rowIndex is provided, delete that row, otherwise delete the last row
                const indexToDelete = (rowIndex !== undefined) ? rowIndex : rows.length - 1;
                if (indexToDelete >= 0 && indexToDelete < rows.length) {
                    tableElement.deleteRow(indexToDelete);
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a column from the table
        function deleteTableColumn(tableElement, colIndex) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            const rows = tableElement.rows;
            if (rows.length > 0 && rows[0].cells.length > 1) {
                // If colIndex is provided, delete that column, otherwise delete the last column
                const indexToDelete = (colIndex !== undefined) ? colIndex : rows[0].cells.length - 1;
                
                for (let i = 0; i < rows.length; i++) {
                    if (indexToDelete >= 0 && indexToDelete < rows[i].cells.length) {
                        rows[i].deleteCell(indexToDelete);
                    }
                }
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        
        // Function to delete a table
        function deleteTable(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // Remove the table from the DOM
            tableElement.parentNode.removeChild(tableElement);
            
            // Reset activeTable reference
            activeTable = null;
            
            // Notify the app
            try {
                window.webkit.messageHandlers.tableDeleted.postMessage('table-deleted');
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about table deletion:", e);
            }
        }
        """

    def table_alignment_js(self):
        """JavaScript for table alignment"""
        return """
        // Function to set table alignment
        function setTableAlignment(alignClass) {
            if (!activeTable) return;
            
            // Remove all alignment classes
            activeTable.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap', 'floating-table');
            
            // Add the requested alignment class
            activeTable.classList.add(alignClass);
            
            // Reset positioning if it was previously floating
            if (activeTable.style.position === 'absolute') {
                activeTable.style.position = 'relative';
                activeTable.style.top = '';
                activeTable.style.left = '';
                activeTable.style.zIndex = '';
            }
            
            // Set width to auto except for full-width
            if (alignClass === 'no-wrap') {
                activeTable.style.width = '100%';
            } else {
                activeTable.style.width = 'auto';
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        }
        """
        
    def table_floating_js(self):
        """JavaScript for floating table functionality"""
        return """
        // Function to make a table floating (freely positionable)
        function setTableFloating(tableElement) {
            if (!tableElement && activeTable) {
                tableElement = activeTable;
            }
            
            if (!tableElement) return;
            
            // First, remove any alignment classes
            tableElement.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            
            // Add floating class for special styling
            tableElement.classList.add('floating-table');
            
            // Set positioning to absolute
            tableElement.style.position = 'absolute';
            
            // Calculate initial position - center in the visible editor area
            const editorRect = document.getElementById('editor').getBoundingClientRect();
            const tableRect = tableElement.getBoundingClientRect();
            
            // Set initial position
            const editorScrollTop = document.getElementById('editor').scrollTop;
            
            // Position in the middle of the visible editor area
            const topPos = (editorRect.height / 2) - (tableRect.height / 2) + editorScrollTop;
            const leftPos = (editorRect.width / 2) - (tableRect.width / 2);
            
            tableElement.style.top = `${Math.max(topPos, editorScrollTop)}px`;
            tableElement.style.left = `${Math.max(leftPos, 0)}px`;
            
            // Enhance the drag handle for position control
            enhanceTableDragHandles(tableElement);
            
            // Ensure proper z-index to be above regular content
            tableElement.style.zIndex = "50";
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            // Activate the table to show handles
            if (tableElement !== activeTable) {
                activateTable(tableElement);
            }
        }
        
        // Add enhanced drag handling for floating tables
        function enhanceTableDragHandles(tableElement) {
            if (!tableElement) return;
            
            // Find or create the drag handle
            let dragHandle = tableElement.querySelector('.table-drag-handle');
            if (!dragHandle) {
                // If it doesn't exist, we might need to activate the table first
                activateTable(tableElement);
                dragHandle = tableElement.querySelector('.table-drag-handle');
            }
            
            if (dragHandle) {
                // Update tooltip to reflect new functionality
                dragHandle.title = "Drag to move table freely";
                
                // Make the drag handle more visible for floating tables
                dragHandle.style.width = "20px";
                dragHandle.style.height = "20px";
                dragHandle.style.backgroundColor = "#4e9eff";
                dragHandle.style.borderRadius = "3px";
                dragHandle.style.opacity = "0.9";
            }
        }
        """

    def table_event_handlers_js(self):
        """JavaScript for table event handlers with handle hiding during editing and tab navigation"""
        return """
        // Function to save editor state
        function saveState() {
            const editor = document.getElementById('editor');
            if (!editor) return;
            
            window.undoStack.push(editor.innerHTML);
            if (window.undoStack.length > 100) {
                window.undoStack.shift();
            }
        }
        
        // Function to handle dark mode changes
        function handleColorSchemeChange(e) {
            const tables = document.querySelectorAll('table');
            tables.forEach(updateTableThemeColors);
        }
        
        // Function to hide table handles
        function hideTableHandles() {
            if (activeTable) {
                const dragHandle = activeTable.querySelector('.table-drag-handle');
                const resizeHandle = activeTable.querySelector('.table-handle');
                
                if (dragHandle) dragHandle.style.display = 'none';
                if (resizeHandle) resizeHandle.style.display = 'none';
            }
        }
        
        // Function to show table handles
        function showTableHandles() {
            if (activeTable) {
                const dragHandle = activeTable.querySelector('.table-drag-handle');
                const resizeHandle = activeTable.querySelector('.table-handle');
                
                if (dragHandle) dragHandle.style.display = 'flex';
                if (resizeHandle) resizeHandle.style.display = 'block';
            }
        }
        
        // Check if element is a table cell
        function isTableCell(element) {
            return element && (element.tagName === 'TD' || element.tagName === 'TH');
        }
        
        // Find parent cell element
        function findParentCell(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'TD' || element.tagName === 'TH') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
        
        // Add event handlers for table interactions
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Add the custom style for table handles
            addTableHandleStyles();
            
            // Handle mouse down events
            editor.addEventListener('mousedown', function(e) {
                // Prevent selection of table handles
                if (e.target.classList.contains('table-handle') || 
                    e.target.classList.contains('table-drag-handle')) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                
                let tableElement = findParentTable(e.target);
                
                if (e.target.classList.contains('table-drag-handle')) {
                    if (e.button === 0) { // Left mouse button
                        startTableDrag(e, findParentTable(e.target));
                    }
                }
                
                if (e.target.classList.contains('table-handle')) {
                    startTableResize(e, findParentTable(e.target));
                }
            });
            
            // Handle focus events on cells to hide handles when editing
            editor.addEventListener('focusin', function(e) {
                const cell = findParentCell(e.target);
                if (cell && activeTable && activeTable.contains(cell)) {
                    hideTableHandles();
                }
            });
            
            // Handle when user starts typing in a cell
            editor.addEventListener('keydown', function(e) {
                const cell = findParentCell(e.target);
                if (cell && activeTable && activeTable.contains(cell)) {
                    // Hide handles when typing in cells (except for navigation keys and Tab)
                    if (!['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Tab', 'Escape', 'Shift'].includes(e.key)) {
                        hideTableHandles();
                    }
                }
            });
            
            // Handle mouse move events
            document.addEventListener('mousemove', function(e) {
                if (isDragging && activeTable) {
                    moveTable(e);
                }
                if (isResizing && activeTable) {
                    resizeTable(e);
                }
            });
            
            // Handle mouse up events
            document.addEventListener('mouseup', function() {
                if (isDragging || isResizing) {
                    isDragging = false;
                    isResizing = false;
                    document.body.style.cursor = '';
                    
                    if (activeTable) {
                        try {
                            window.webkit.messageHandlers.contentChanged.postMessage('changed');
                        } catch(e) {
                            console.log("Could not notify about content change:", e);
                        }
                    }
                }
            });
            
            // Handle click events for table selection
            editor.addEventListener('click', function(e) {
                let tableElement = findParentTable(e.target);
                
                if (!tableElement) {
                    // We clicked outside any table
                    if (activeTable) {
                        // If there was a previously active table, deactivate it
                        deactivateAllTables();
                    } else {
                        // Even if there was no active table, still send the deactivation message
                        try {
                            window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
                        } catch(e) {
                            console.log("Could not notify about table deactivation:", e);
                        }
                    }
                } else if (tableElement !== activeTable) {
                    // We clicked on a different table than the currently active one
                    deactivateAllTables();
                    activateTable(tableElement);
                    
                    // Show handles unless we clicked inside a cell for editing
                    const cell = findParentCell(e.target);
                    if (!cell || !isTableCell(e.target)) {
                        showTableHandles();
                    }
                    
                    try {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    } catch(e) {
                        console.log("Could not notify about table click:", e);
                    }
                } else {
                    // Clicking on the same table
                    const cell = findParentCell(e.target);
                    if (cell) {
                        // If clicking on a cell, hide handles for editing
                        hideTableHandles();
                    } else if (!e.target.classList.contains('table-handle') && 
                              !e.target.classList.contains('table-drag-handle')) {
                        // If clicking elsewhere on the table (not handles), show handles
                        showTableHandles();
                    }
                }
            });
            
            // Add a focusout handler to show handles again when leaving a cell
            editor.addEventListener('focusout', function(e) {
                if (activeTable) {
                    // Check if the focus is moving outside the table
                    setTimeout(() => {
                        const newFocusElement = document.activeElement;
                        if (!activeTable.contains(newFocusElement)) {
                            showTableHandles();
                        } else {
                            // If focus moved to another cell in the same table, keep handles hidden
                            const newCell = findParentCell(newFocusElement);
                            if (!newCell) {
                                showTableHandles();
                            }
                        }
                    }, 0);
                }
            });

            // Add a document-level click handler that will deactivate tables when clicking outside the editor
            document.addEventListener('click', function(e) {
                // Check if the click is outside the editor
                if (!editor.contains(e.target) && activeTable) {
                    deactivateAllTables();
                }
            });

            // Listen for color scheme changes
            if (window.matchMedia) {
                const colorSchemeQuery = window.matchMedia('(prefers-color-scheme: dark)');
                // Modern approach (newer browsers)
                if (colorSchemeQuery.addEventListener) {
                    colorSchemeQuery.addEventListener('change', handleColorSchemeChange);
                } 
                // Legacy approach (older browsers)
                else if (colorSchemeQuery.addListener) {
                    colorSchemeQuery.addListener(handleColorSchemeChange);
                }
            }
        });
        """    
        
    def table_color_js(self):
        """JavaScript for table color operations with theme preservation"""
        return """
        // Function to set table background color
        function setTableBackgroundColor(color) {
            if (!activeTable) return false;
            
            activeTable.style.backgroundColor = color;
            
            // Store the background color
            activeTable.setAttribute('data-bg-color', color);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set header background color
        function setHeaderBackgroundColor(color) {
            if (!activeTable) return false;
            
            const headers = activeTable.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = color;
            });
            
            // Store the header color
            activeTable.setAttribute('data-header-color', color);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set cell background color (only for the active cell)
        function setCellBackgroundColor(color) {
            if (!activeTable) return false;
            
            // Get the current selection
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Find the active cell
            let activeCell = selection.anchorNode;
            
            // If the selection is in a text node, get the parent element
            if (activeCell.nodeType === Node.TEXT_NODE) {
                activeCell = activeCell.parentElement;
            }
            
            // Find the closest td or th element
            while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                activeCell = activeCell.parentElement;
            }
            
            // If we found a cell and it belongs to our active table
            if (activeCell && activeTable.contains(activeCell)) {
                activeCell.style.backgroundColor = color;
                
                // Store the color on the cell itself
                activeCell.setAttribute('data-cell-color', color);
                
                // Notify that content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
                
                return true;
            }
            
            return false;
        }
        
        // Function to set row background color
        function setRowBackgroundColor(color) {
            if (!activeTable) return false;
            
            // Get the current selection
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Find the active cell
            let activeCell = selection.anchorNode;
            
            // If the selection is in a text node, get the parent element
            if (activeCell.nodeType === Node.TEXT_NODE) {
                activeCell = activeCell.parentElement;
            }
            
            // Find the closest td or th element
            while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                activeCell = activeCell.parentElement;
            }
            
            // If we found a cell and it belongs to our active table
            if (activeCell && activeTable.contains(activeCell)) {
                // Find the parent row
                const row = activeCell.parentElement;
                if (row && row.tagName === 'TR') {
                    // Apply color to all cells in the row
                    const cells = row.querySelectorAll('td, th');
                    cells.forEach(cell => {
                        cell.style.backgroundColor = color;
                        cell.setAttribute('data-cell-color', color);
                    });
                    
                    // Store the row color
                    row.setAttribute('data-row-color', color);
                    
                    // Notify that content changed
                    try {
                        window.webkit.messageHandlers.contentChanged.postMessage('changed');
                    } catch(e) {
                        console.log("Could not notify about content change:", e);
                    }
                    
                    return true;
                }
            }
            
            return false;
        }
        
        // Function to set column background color
        function setColumnBackgroundColor(color) {
            if (!activeTable) return false;
            
            // Get the current selection
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Find the active cell
            let activeCell = selection.anchorNode;
            
            // If the selection is in a text node, get the parent element
            if (activeCell.nodeType === Node.TEXT_NODE) {
                activeCell = activeCell.parentElement;
            }
            
            // Find the closest td or th element
            while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                activeCell = activeCell.parentElement;
            }
            
            // If we found a cell and it belongs to our active table
            if (activeCell && activeTable.contains(activeCell)) {
                // Get the column index
                const cellIndex = activeCell.cellIndex;
                
                // Apply color to all cells in the same column
                const rows = activeTable.rows;
                for (let i = 0; i < rows.length; i++) {
                    const cell = rows[i].cells[cellIndex];
                    if (cell) {
                        cell.style.backgroundColor = color;
                        cell.setAttribute('data-cell-color', color);
                    }
                }
                
                // Store the column color
                activeTable.setAttribute(`data-col-${cellIndex}-color`, color);
                
                // Notify that content changed
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } catch(e) {
                    console.log("Could not notify about content change:", e);
                }
                
                return true;
            }
            
            return false;
        }
        
        // Function to get current table colors
        function getTableColors() {
            if (!activeTable) return null;
            
            // Get stored values
            const bgColor = activeTable.getAttribute('data-bg-color') || activeTable.style.backgroundColor || '';
            const headerColor = activeTable.getAttribute('data-header-color') || '';
            const borderColor = activeTable.getAttribute('data-border-color') || '';
            
            // Get active cell color if there's a selection
            let cellColor = '';
            const selection = window.getSelection();
            if (selection.rangeCount) {
                let activeCell = selection.anchorNode;
                if (activeCell.nodeType === Node.TEXT_NODE) {
                    activeCell = activeCell.parentElement;
                }
                while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {
                    activeCell = activeCell.parentElement;
                }
                if (activeCell && activeTable.contains(activeCell)) {
                    cellColor = activeCell.getAttribute('data-cell-color') || activeCell.style.backgroundColor || '';
                }
            }
            
            return {
                background: bgColor,
                header: headerColor,
                cell: cellColor,
                border: borderColor
            };
        }
        
        // Function to preserve table colors during theme changes
        function preserveTableColors() {
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                // Preserve background color
                const bgColor = table.getAttribute('data-bg-color');
                if (bgColor) {
                    table.style.backgroundColor = bgColor;
                }
                
                // Preserve header colors
                const headerColor = table.getAttribute('data-header-color');
                const headers = table.querySelectorAll('th');
                headers.forEach(header => {
                    if (headerColor) {
                        header.style.backgroundColor = headerColor;
                    } else if (!header.getAttribute('data-cell-color')) {
                        // Set default header color based on theme
                        header.style.backgroundColor = getHeaderBgColor();
                    }
                });
                
                // Preserve cell colors
                const cells = table.querySelectorAll('td, th');
                cells.forEach(cell => {
                    const cellColor = cell.getAttribute('data-cell-color');
                    if (cellColor) {
                        cell.style.backgroundColor = cellColor;
                    }
                });
                
                // Preserve border colors
                const borderColor = table.getAttribute('data-border-color');
                if (borderColor) {
                    cells.forEach(cell => {
                        cell.style.borderColor = borderColor;
                    });
                }
            });
        }
        """
        
    def table_border_style_js(self):
        """JavaScript for table border style manipulation with combined borders"""
        return """
        // Function to set table border style
        function setTableBorderStyle(style, width, color) {
            if (!activeTable) return false;
            
            // Get all cells in the table
            const cells = activeTable.querySelectorAll('th, td');
            
            // Get current values from table attributes
            let currentStyle = activeTable.getAttribute('data-border-style');
            let currentWidth = activeTable.getAttribute('data-border-width');
            let currentColor = activeTable.getAttribute('data-border-color');
            
            // If attributes don't exist, try to get from the first cell
            if (!currentStyle || !currentWidth || !currentColor) {
                if (cells.length > 0) {
                    const firstCell = cells[0];
                    const computedStyle = window.getComputedStyle(firstCell);
                    
                    // Try to get current style from computed style
                    currentStyle = currentStyle || firstCell.style.borderStyle || computedStyle.borderStyle || 'solid';
                    
                    // Get current width
                    if (!currentWidth) {
                        currentWidth = parseInt(firstCell.style.borderWidth) || 
                                      parseInt(computedStyle.borderWidth) || 1;
                    }
                    
                    // Get current color
                    currentColor = currentColor || firstCell.style.borderColor || 
                                  computedStyle.borderColor || getBorderColor();
                } else {
                    // Default values if no cells exist
                    currentStyle = currentStyle || 'solid';
                    currentWidth = currentWidth || 1;
                    currentColor = currentColor || getBorderColor();
                }
            }
            
            // Use provided values or fall back to current/default values
            const newStyle = (style !== null && style !== undefined && style !== '') ? style : currentStyle;
            const newWidth = (width !== null && width !== undefined && width !== '') ? width : currentWidth;
            const newColor = (color !== null && color !== undefined && color !== '') ? color : currentColor;
            
            // Update all cells while preserving which borders are visible
            cells.forEach(cell => {
                // Check which borders are currently visible
                const hasTopBorder = cell.style.borderTopStyle !== 'none' && cell.style.borderTopWidth !== '0px';
                const hasRightBorder = cell.style.borderRightStyle !== 'none' && cell.style.borderRightWidth !== '0px';
                const hasBottomBorder = cell.style.borderBottomStyle !== 'none' && cell.style.borderBottomWidth !== '0px';
                const hasLeftBorder = cell.style.borderLeftStyle !== 'none' && cell.style.borderLeftWidth !== '0px';
                
                // Apply new properties only to existing borders
                if (hasTopBorder || cell.style.borderTopStyle) {
                    cell.style.borderTopStyle = newStyle;
                    cell.style.borderTopWidth = newWidth + 'px';
                    cell.style.borderTopColor = newColor;
                }
                
                if (hasRightBorder || cell.style.borderRightStyle) {
                    cell.style.borderRightStyle = newStyle;
                    cell.style.borderRightWidth = newWidth + 'px';
                    cell.style.borderRightColor = newColor;
                }
                
                if (hasBottomBorder || cell.style.borderBottomStyle) {
                    cell.style.borderBottomStyle = newStyle;
                    cell.style.borderBottomWidth = newWidth + 'px';
                    cell.style.borderBottomColor = newColor;
                }
                
                if (hasLeftBorder || cell.style.borderLeftStyle) {
                    cell.style.borderLeftStyle = newStyle;
                    cell.style.borderLeftWidth = newWidth + 'px';
                    cell.style.borderLeftColor = newColor;
                }
                
                // If cell has a generic border property, update it too
                if (cell.style.border || cell.getAttribute('style')?.includes('border:')) {
                    // Check if the cell has any borders at all
                    if (hasTopBorder || hasRightBorder || hasBottomBorder || hasLeftBorder) {
                        // Keep the border but update its properties
                        cell.style.borderStyle = newStyle;
                        cell.style.borderWidth = newWidth + 'px';
                        cell.style.borderColor = newColor;
                    }
                }
            });
            
            // Store the current border settings on the table
            activeTable.setAttribute('data-border-style', newStyle);
            activeTable.setAttribute('data-border-width', newWidth);
            activeTable.setAttribute('data-border-color', newColor);
            
            // Also update the table's own border if it has one
            if (activeTable.style.border) {
                activeTable.style.borderStyle = newStyle;
                activeTable.style.borderWidth = newWidth + 'px';
                activeTable.style.borderColor = newColor;
            }
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to set table border color
        function setTableBorderColor(color) {
            return setTableBorderStyle(null, null, color);
        }
        
        // Function to set table border width
        function setTableBorderWidth(width) {
            return setTableBorderStyle(null, width, null);
        }
        
        // Function to get current table border style
        function getTableBorderStyle() {
            if (!activeTable) return null;
            
            // First try to get from stored data attributes
            const storedStyle = activeTable.getAttribute('data-border-style');
            const storedWidth = activeTable.getAttribute('data-border-width');
            const storedColor = activeTable.getAttribute('data-border-color');
            
            if (storedStyle && storedWidth && storedColor) {
                return {
                    style: storedStyle,
                    width: parseInt(storedWidth),
                    color: storedColor
                };
            }
            
            // If not stored, get from the first cell
            const firstCell = activeTable.querySelector('td, th');
            if (!firstCell) return {
                style: 'solid',
                width: 1,
                color: getBorderColor()
            };
            
            // Get computed style to ensure we get actual values
            const computedStyle = window.getComputedStyle(firstCell);
            
            const result = {
                style: firstCell.style.borderStyle || computedStyle.borderStyle || 'solid',
                width: parseInt(firstCell.style.borderWidth) || parseInt(computedStyle.borderWidth) || 1,
                color: firstCell.style.borderColor || computedStyle.borderColor || getBorderColor()
            };
            
            // Store these values for future use
            activeTable.setAttribute('data-border-style', result.style);
            activeTable.setAttribute('data-border-width', result.width);
            activeTable.setAttribute('data-border-color', result.color);
            
            return result;
        }
        
        // Function to get current table border properties (including shadow)
        function getTableBorderProperties() {
            if (!activeTable) return null;
            
            const borderStyle = getTableBorderStyle();
            const hasShadow = activeTable.getAttribute('data-border-shadow') === 'true' || 
                             (window.getComputedStyle(activeTable).boxShadow !== 'none' && 
                              window.getComputedStyle(activeTable).boxShadow !== '');
            
            return {
                ...borderStyle,
                shadow: hasShadow
            };
        }
        
        // Function to set table margins
        function setTableMargins(top, right, bottom, left) {
            if (!activeTable) return false;
            
            // Set margins individually if provided
            if (top !== undefined && top !== null) {
                activeTable.style.marginTop = top + 'px';
            }
            if (right !== undefined && right !== null) {
                activeTable.style.marginRight = right + 'px';
            }
            if (bottom !== undefined && bottom !== null) {
                activeTable.style.marginBottom = bottom + 'px';
            }
            if (left !== undefined && left !== null) {
                activeTable.style.marginLeft = left + 'px';
            }
            
            // Store margin values as attributes for later reference
            activeTable.setAttribute('data-margin-top', parseInt(activeTable.style.marginTop) || 0);
            activeTable.setAttribute('data-margin-right', parseInt(activeTable.style.marginRight) || 0);
            activeTable.setAttribute('data-margin-bottom', parseInt(activeTable.style.marginBottom) || 0);
            activeTable.setAttribute('data-margin-left', parseInt(activeTable.style.marginLeft) || 0);
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        
        // Function to get current table margins
        function getTableMargins() {
            if (!activeTable) return null;
            
            // Try to get from stored attributes first
            const storedTop = activeTable.getAttribute('data-margin-top');
            const storedRight = activeTable.getAttribute('data-margin-right');
            const storedBottom = activeTable.getAttribute('data-margin-bottom');
            const storedLeft = activeTable.getAttribute('data-margin-left');
            
            if (storedTop !== null || storedRight !== null || storedBottom !== null || storedLeft !== null) {
                return {
                    top: parseInt(storedTop) || 0,
                    right: parseInt(storedRight) || 0,
                    bottom: parseInt(storedBottom) || 0,
                    left: parseInt(storedLeft) || 0
                };
            }
            
            // Otherwise get from computed style
            const computedStyle = window.getComputedStyle(activeTable);
            
            return {
                top: parseInt(computedStyle.marginTop) || 0,
                right: parseInt(computedStyle.marginRight) || 0,
                bottom: parseInt(computedStyle.marginBottom) || 0,
                left: parseInt(computedStyle.marginLeft) || 0
            };
        }
        
        // Enhanced function to apply border to specific sides of the table
        // Now supports combined options like 'outer' + 'horizontal'
        function applyTableBorderSides(sides) {
            if (!activeTable) return false;
            
            const cells = activeTable.querySelectorAll('td, th');
            const currentStyle = getTableBorderStyle();
            
            if (!currentStyle) return false;
            
            // Create the border string with preserved style, width and color
            const borderValue = `${currentStyle.width}px ${currentStyle.style} ${currentStyle.color}`;
            
            // Check for special combined cases
            const hasOuter = sides.includes('outer');
            const hasInner = sides.includes('inner');
            const hasHorizontal = sides.includes('horizontal');
            const hasVertical = sides.includes('vertical');
            
            // Apply borders based on selected sides
            cells.forEach(cell => {
                // Get row and column position
                const row = cell.parentElement;
                const rowIndex = row.rowIndex;
                const cellIndex = cell.cellIndex;
                const isFirstRow = rowIndex === 0;
                const isLastRow = rowIndex === activeTable.rows.length - 1;
                const isFirstColumn = cellIndex === 0;
                const isLastColumn = cellIndex === row.cells.length - 1;
                
                // Reset all borders first
                cell.style.borderTop = 'none';
                cell.style.borderRight = 'none';
                cell.style.borderBottom = 'none';
                cell.style.borderLeft = 'none';
                
                // Apply borders based on sides parameter and cell position
                if (sides.includes('all')) {
                    cell.style.border = borderValue;
                } else if (sides.includes('none')) {
                    cell.style.border = 'none';
                } else {
                    // Outer + Inner Horizontal: Apply outer borders on all 4 sides PLUS inner horizontal borders
                    if (hasOuter && hasInner && hasHorizontal && !hasVertical) {
                        // Apply outer borders (all 4 sides)
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // Plus inner horizontal borders
                        if (!isLastRow) cell.style.borderBottom = borderValue;
                    }
                    // Outer + Inner Vertical: Apply outer borders on all 4 sides PLUS inner vertical borders
                    else if (hasOuter && hasInner && hasVertical && !hasHorizontal) {
                        // Apply outer borders (all 4 sides)
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // Plus inner vertical borders
                        if (!isLastColumn) cell.style.borderRight = borderValue;
                    }
                    // Handle outer borders
                    else if (hasOuter) {
                        if (isFirstRow) cell.style.borderTop = borderValue;
                        if (isLastRow) cell.style.borderBottom = borderValue;
                        if (isFirstColumn) cell.style.borderLeft = borderValue;
                        if (isLastColumn) cell.style.borderRight = borderValue;
                        
                        // If outer + horizontal, add only top and bottom outer borders
                        if (hasHorizontal && !hasVertical) {
                            if (isFirstRow) cell.style.borderTop = borderValue;
                            if (isLastRow) cell.style.borderBottom = borderValue;
                            cell.style.borderLeft = 'none';
                            cell.style.borderRight = 'none';
                        }
                        
                        // If outer + vertical, add only left and right outer borders
                        if (hasVertical && !hasHorizontal) {
                            cell.style.borderTop = 'none';
                            cell.style.borderBottom = 'none';
                            if (isFirstColumn) cell.style.borderLeft = borderValue;
                            if (isLastColumn) cell.style.borderRight = borderValue;
                        }
                    }
                    
                    // Handle inner borders
                    else if (hasInner) {
                        if (!isLastRow) cell.style.borderBottom = borderValue;
                        if (!isLastColumn) cell.style.borderRight = borderValue;
                        
                        // If inner + horizontal, add only horizontal inner borders
                        if (hasHorizontal && !hasVertical) {
                            if (!isLastRow) cell.style.borderBottom = borderValue;
                            cell.style.borderRight = 'none';
                        }
                        
                        // If inner + vertical, add only vertical inner borders
                        if (hasVertical && !hasHorizontal) {
                            cell.style.borderBottom = 'none';
                            if (!isLastColumn) cell.style.borderRight = borderValue;
                        }
                    }
                    
                    // Handle standalone horizontal/vertical if not combined with outer/inner
                    else {
                        if (hasHorizontal) {
                            cell.style.borderTop = borderValue;
                            cell.style.borderBottom = borderValue;
                        }
                        
                        if (hasVertical) {
                            cell.style.borderLeft = borderValue;
                            cell.style.borderRight = borderValue;
                        }
                    }
                }
            });
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return true;
        }
        """

    def create_table_toolbar(self, win):
        """Create a toolbar for table editing"""
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        
        # Table operations label
        table_label = Gtk.Label(label="Table:")
        table_label.set_margin_end(10)
        toolbar.append(table_label)
        
        # Create a group for row operations
        row_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        row_group.add_css_class("linked")
        
        # Add Row Above button
        add_row_above_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_above_button.set_tooltip_text("Add row above")
        add_row_above_button.connect("clicked", lambda btn: self.on_add_row_above_clicked(win))
        row_group.append(add_row_above_button)
        
        # Add Row Below button
        add_row_below_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_below_button.set_tooltip_text("Add row below")
        add_row_below_button.connect("clicked", lambda btn: self.on_add_row_below_clicked(win))
        row_group.append(add_row_below_button)
        
        # Add row group to toolbar
        toolbar.append(row_group)
        
        # Create a group for column operations
        col_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        col_group.add_css_class("linked")
        col_group.set_margin_start(5)
        
        # Add Column Before button
        add_col_before_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_before_button.set_tooltip_text("Add column before")
        add_col_before_button.connect("clicked", lambda btn: self.on_add_column_before_clicked(win))
        col_group.append(add_col_before_button)
        
        # Add Column After button
        add_col_after_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_after_button.set_tooltip_text("Add column after")
        add_col_after_button.connect("clicked", lambda btn: self.on_add_column_after_clicked(win))
        col_group.append(add_col_after_button)
        
        # Add column group to toolbar
        toolbar.append(col_group)
        
        # Small separator
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator1.set_margin_start(5)
        separator1.set_margin_end(5)
        toolbar.append(separator1)
        
        # Create a group for delete operations
        delete_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        delete_group.add_css_class("linked")
        
        # Delete Row button
        del_row_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_row_button.set_tooltip_text("Delete row")
        del_row_button.connect("clicked", lambda btn: self.on_delete_row_clicked(win))
        delete_group.append(del_row_button)
        
        # Delete Column button
        del_col_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_col_button.set_tooltip_text("Delete column")
        del_col_button.connect("clicked", lambda btn: self.on_delete_column_clicked(win))
        delete_group.append(del_col_button)
        
        # Delete Table button
        del_table_button = Gtk.Button(icon_name="edit-delete-symbolic")
        del_table_button.set_tooltip_text("Delete table")
        del_table_button.connect("clicked", lambda btn: self.on_delete_table_clicked(win))
        delete_group.append(del_table_button)
        
        # Add delete group to toolbar
        toolbar.append(delete_group)
        
        # Separator
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator2.set_margin_start(10)
        separator2.set_margin_end(10)
        toolbar.append(separator2)
        
        # Table properties button (combines border, margin, and color)
        table_props_button = Gtk.Button(icon_name="document-properties-symbolic")
        table_props_button.set_tooltip_text("Table Properties")
        table_props_button.connect("clicked", lambda btn: self.on_table_button_clicked(win, btn))
        toolbar.append(table_props_button)
        
        # Separator
        separator3 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator3.set_margin_start(10)
        separator3.set_margin_end(10)
        toolbar.append(separator3)
        
        # Alignment options
        align_label = Gtk.Label(label="Align:")
        align_label.set_margin_end(5)
        toolbar.append(align_label)
        
        # Create a group for alignment buttons
        align_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        align_group.add_css_class("linked")
        
        # Left alignment
        align_left_button = Gtk.Button(icon_name="format-justify-left-symbolic")
        align_left_button.set_tooltip_text("Align Left (text wraps around right)")
        align_left_button.connect("clicked", lambda btn: self.on_table_align_left(win))
        align_group.append(align_left_button)
        
        # Center alignment
        align_center_button = Gtk.Button(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Center (no text wrap)")
        align_center_button.connect("clicked", lambda btn: self.on_table_align_center(win))
        align_group.append(align_center_button)
        
        # Right alignment
        align_right_button = Gtk.Button(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right (text wraps around left)")
        align_right_button.connect("clicked", lambda btn: self.on_table_align_right(win))
        align_group.append(align_right_button)
        
        # Full width (no wrap)
        full_width_button = Gtk.Button(icon_name="format-justify-fill-symbolic")
        full_width_button.set_tooltip_text("Full Width (no text wrap)")
        full_width_button.connect("clicked", lambda btn: self.on_table_full_width(win))
        align_group.append(full_width_button)
        
        # Add alignment group to toolbar
        toolbar.append(align_group)
        
        # Float button
        float_button = Gtk.Button(icon_name="move-tool-symbolic")
        float_button.set_tooltip_text("Make table float freely in editor")
        float_button.set_margin_start(5)
        float_button.connect("clicked", lambda btn: self.on_table_float_clicked(win))
        toolbar.append(float_button)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        
        # Close button
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close table toolbar")
        close_button.connect("clicked", lambda btn: self.on_close_table_toolbar_clicked(win))
        toolbar.append(close_button)
        
        return toolbar

    def on_insert_table_clicked(self, win, btn):
        """Handle table insertion button click"""
        win.statusbar.set_text("Inserting table...")
        
        # Create a dialog to configure the table
        dialog = Adw.Dialog()
        dialog.set_title("Insert Table")
        dialog.set_content_width(350)
        
        # Create layout for dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Rows input
        rows_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rows_label = Gtk.Label(label="Rows:")
        rows_label.set_halign(Gtk.Align.START)
        rows_label.set_hexpand(True)
        
        rows_adjustment = Gtk.Adjustment(value=3, lower=1, upper=20, step_increment=1)
        rows_spin = Gtk.SpinButton()
        rows_spin.set_adjustment(rows_adjustment)
        
        rows_box.append(rows_label)
        rows_box.append(rows_spin)
        content_box.append(rows_box)
        
        # Columns input
        cols_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cols_label = Gtk.Label(label="Columns:")
        cols_label.set_halign(Gtk.Align.START)
        cols_label.set_hexpand(True)
        
        cols_adjustment = Gtk.Adjustment(value=3, lower=1, upper=10, step_increment=1)
        cols_spin = Gtk.SpinButton()
        cols_spin.set_adjustment(cols_adjustment)
        
        cols_box.append(cols_label)
        cols_box.append(cols_spin)
        content_box.append(cols_box)
        
        # Header row checkbox
        header_check = Gtk.CheckButton(label="Include header row")
        header_check.set_active(True)
        content_box.append(header_check)
        
        # Border options
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        border_label = Gtk.Label(label="Border width:")
        border_label.set_halign(Gtk.Align.START)
        border_label.set_hexpand(True)
        
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=5, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_adjustment(border_adjustment)
        
        border_box.append(border_label)
        border_box.append(border_spin)
        content_box.append(border_box)
        
        # Table width options
        width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        width_label = Gtk.Label(label="Table width:")
        width_label.set_halign(Gtk.Align.START)
        width_label.set_hexpand(True)
        
        width_combo = Gtk.DropDown()
        width_options = Gtk.StringList()
        width_options.append("Auto")
        width_options.append("100%")
        width_options.append("75%")
        width_options.append("50%")
        width_combo.set_model(width_options)
        width_combo.set_selected(1)  # Default to 100% (index 1)
        
        width_box.append(width_label)
        width_box.append(width_combo)
        content_box.append(width_box)
        
        # ADDED: Floating option checkbox
        float_check = Gtk.CheckButton(label="Free-floating (text wraps around)")
        float_check.set_active(True)  # Enabled by default
        content_box.append(float_check)
        
        # Set initial width based on floating setting (Auto for floating tables)
        width_combo.set_selected(0)  # Start with Auto since floating is active by default
        
        # Connect change handler for float check to update width combo
        def on_float_check_toggled(check_button):
            if check_button.get_active():  # If float is enabled
                width_combo.set_selected(0)  # Set to "Auto"
            else:  # If float is disabled
                width_combo.set_selected(1)  # Set to "100%"
        
        float_check.connect("toggled", on_float_check_toggled)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(16)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        
        insert_button = Gtk.Button(label="Insert")
        insert_button.add_css_class("suggested-action")
        insert_button.connect("clicked", lambda btn: self.on_table_dialog_response(
            win, dialog, 
            rows_spin.get_value_as_int(), 
            cols_spin.get_value_as_int(),
            header_check.get_active(),
            border_spin.get_value_as_int(),
            width_options.get_string(width_combo.get_selected()),
            float_check.get_active()  # Pass floating state
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Set dialog content and present
        dialog.set_child(content_box)
        dialog.present(win)

    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option, is_floating):
        """Handle response from the table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Execute JavaScript to insert the table
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}", {str(is_floating).lower()});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        
        # Update status message based on table type
        if is_floating:
            win.statusbar.set_text("Floating table inserted")
        else:
            win.statusbar.set_text("Table inserted")        

    def on_table_clicked(self, win, manager, message):
        """Handle table click event from editor"""
        win.table_toolbar_revealer.set_reveal_child(True)
        win.statusbar.set_text("Table selected")
        
        # Update margin controls with current table margins
        js_code = """
        (function() {
            const margins = getTableMargins();
            return JSON.stringify(margins);
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._update_margin_controls(win, webview, result),
            None
        )
        
    def on_table_deleted(self, win, manager, message):
        """Handle table deleted event from editor"""
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("Table deleted")

    def on_tables_deactivated(self, win, manager, message):
        """Handle event when all tables are deactivated"""
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("No table selected")
        
    def on_webview_key_pressed(self, controller, keyval, keycode, state):
        """Handle key press events on the webview"""
        # Check for Shift+Tab
        if keyval == Gdk.KEY_ISO_Left_Tab or (keyval == Gdk.KEY_Tab and (state & Gdk.ModifierType.SHIFT_MASK)):
            # Return True to indicate we've handled the event and prevent default behavior
            return True
        
        # For all other keys, let them pass through normally
        return False        

    # Table operation methods
    def on_add_row_above_clicked(self, win):
        """Add a row above the current row in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) {
                // If no selection, add at the beginning
                addTableRow(activeTable, 0);
                return;
            }
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, add at the beginning
                addTableRow(activeTable, 0);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) {
                addTableRow(activeTable, 0);
                return;
            }
            
            // Find the row index - this is the simple approach
            let rowIndex = Array.from(activeTable.rows).indexOf(row);
            
            // If we're at the first row, we need to insert at position 0
            if (rowIndex === 0) {
                // Create a new row directly at the start of the table
                const newRow = activeTable.insertRow(0);
                
                // Create cells matching the current row's cells
                for (let i = 0; i < row.cells.length; i++) {
                    const cell = row.cells[i];
                    const newCell = newRow.insertCell(i);
                    
                    // Copy cell type (TD or TH)
                    if (cell.tagName === 'TH') {
                        const headerCell = document.createElement('th');
                        headerCell.innerHTML = '&nbsp;';
                        // Copy styles
                        headerCell.style.border = cell.style.border || '1px solid ' + getBorderColor();
                        headerCell.style.padding = cell.style.padding || '5px';
                        headerCell.style.backgroundColor = cell.style.backgroundColor || getHeaderBgColor();
                        newRow.replaceChild(headerCell, newCell);
                    } else {
                        newCell.innerHTML = '&nbsp;';
                        newCell.style.border = cell.style.border || '1px solid ' + getBorderColor();
                        newCell.style.padding = cell.style.padding || '5px';
                    }
                }
            } else {
                // For other rows, use the regular addTableRow function
                addTableRow(activeTable, rowIndex);
            }
            
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
        })();
        """
        self.execute_js(win, js_code)

    def on_add_row_below_clicked(self, win):
        """Add a row below the current row in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the end
                addTableRow(activeTable);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) return;
            
            // Find the row index
            let rowIndex = row.rowIndex;
            
            // Add a row below this one
            addTableRow(activeTable, rowIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_column_before_clicked(self, win):
        """Add a column before the current column in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the start
                addTableColumn(activeTable, 0);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Add a column before the current one
            addTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)     
        
        
    def on_add_column_after_clicked(self, win):
        """Add a column after the current column in the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
    // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just add to the end
                addTableColumn(activeTable);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Add a column after the current one
            addTableColumn(activeTable, cellIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_row_clicked(self, win):
        """Delete the current row from the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current row index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just delete the last row
                deleteTableRow(activeTable);
                return;
            }
            
            // Find the TR parent
            let row = cell;
            while (row && row.tagName !== 'TR') {
                row = row.parentNode;
            }
            
            if (!row) return;
            
            // Find the row index
            let rowIndex = row.rowIndex;
            
            // Delete this row
            deleteTableRow(activeTable, rowIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_column_clicked(self, win):
        """Delete the current column from the active table"""
        js_code = """
        (function() {
            if (!activeTable) return;
            
            // Get the current cell index
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            
            // Find the TD/TH parent
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                // If no cell is selected, just delete the last column
                deleteTableColumn(activeTable);
                return;
            }
            
            // Find the cell index
            let cellIndex = cell.cellIndex;
            
            // Delete this column
            deleteTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_table_clicked(self, win):
        """Delete the entire table"""
        js_code = "deleteTable(activeTable);"
        self.execute_js(win, js_code)

    def on_table_align_left(self, win):
        """Align table to the left with text wrapping around right"""
        js_code = "setTableAlignment('left-align');"
        self.execute_js(win, js_code)

    def on_table_align_center(self, win):
        """Align table to the center with no text wrapping"""
        js_code = "setTableAlignment('center-align');"
        self.execute_js(win, js_code)

    def on_table_align_right(self, win):
        """Align table to the right with text wrapping around left"""
        js_code = "setTableAlignment('right-align');"
        self.execute_js(win, js_code)

    def on_table_full_width(self, win):
        """Make table full width with no text wrapping"""
        js_code = "setTableAlignment('no-wrap');"
        self.execute_js(win, js_code)

    def on_close_table_toolbar_clicked(self, win):
        """Hide the table toolbar and deactivate tables"""
        win.table_toolbar_revealer.set_reveal_child(False)
        js_code = "deactivateAllTables();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table toolbar closed")

    def on_table_button_clicked(self, win, button):
        """Show the table properties popup with tabs"""
        # Create a popover for table properties
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        # Create the content box with reduced margins and spacing
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # Reduced from 8
        content_box.set_margin_start(8)  # Reduced from 12
        content_box.set_margin_end(8)
        content_box.set_margin_top(8)
        content_box.set_margin_bottom(8)
        content_box.set_size_request(320, 230)  # Reduced from 350, 250
        
        # Create header with title and close button
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header_box.set_margin_bottom(6)  # Reduced from 8
        
        # Add title label
        title_label = Gtk.Label(label="<b>Table Properties</b>")
        title_label.set_use_markup(True)
        title_label.set_halign(Gtk.Align.START)
        title_label.set_hexpand(True)
        header_box.append(title_label)
        
        # Add close button [x]
        close_button = Gtk.Button.new_from_icon_name("window-close-symbolic")
        close_button.set_tooltip_text("Close")
        close_button.add_css_class("flat")
        close_button.connect("clicked", lambda btn: popover.popdown())
        header_box.append(close_button)
        
        content_box.append(header_box)
        
        # Create tab view
        tab_view = Gtk.Notebook()
        tab_view.set_vexpand(True)
        
        # Create Border tab
        border_page = self._create_border_tab(win, popover)
        tab_view.append_page(border_page, Gtk.Label(label="Border"))
        
        # Create Margin tab
        margin_page = self._create_margin_tab(win, popover)
        tab_view.append_page(margin_page, Gtk.Label(label="Margin"))
        
        # Create Color tab
        color_page = self._create_color_tab(win, popover)
        tab_view.append_page(color_page, Gtk.Label(label="Color"))
        
        content_box.append(tab_view)
        
        # Set the content and show the popover
        popover.set_child(content_box)
        popover.popup()
        
        # Get current properties to initialize the dialogs
        self._initialize_table_properties(win, popover)

    def _create_border_tab(self, win, popover):
        """Create the border properties tab"""
        border_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        border_box.set_margin_start(12)
        border_box.set_margin_end(12)
        border_box.set_margin_top(12)
        border_box.set_margin_bottom(12)
        
        # Border style and width in a single row
        style_width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Border style dropdown (more compact)
        style_label = Gtk.Label(label="Style:")
        style_label.set_halign(Gtk.Align.START)
        
        style_combo = Gtk.DropDown()
        style_options = Gtk.StringList()
        styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
        for style in styles:
            style_options.append(style)
        style_combo.set_model(style_options)
        style_combo.set_selected(0)  # Default to solid
        
        # Border width spinner (more compact)
        width_label = Gtk.Label(label="Width:")
        width_label.set_halign(Gtk.Align.START)
        
        width_adjustment = Gtk.Adjustment(value=1, lower=0, upper=10, step_increment=1)
        width_spin = Gtk.SpinButton()
        width_spin.set_adjustment(width_adjustment)
        width_spin.set_width_chars(3)  # Make it more compact
        
        # Connect style change
        style_combo.connect("notify::selected", lambda cb, p: self.on_border_style_changed(
            win, styles[cb.get_selected()], width_spin.get_value_as_int()))
        
        # Connect width change
        width_spin.connect("value-changed", lambda spin: self.on_border_width_changed(
            win, styles[style_combo.get_selected()], spin.get_value_as_int()))
        
        # Add all to the row
        style_width_box.append(style_label)
        style_width_box.append(style_combo)
        style_width_box.append(width_label)
        style_width_box.append(width_spin)
        border_box.append(style_width_box)
        
        # Border shadow option
        shadow_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        shadow_label = Gtk.Label(label="Shadow:")
        shadow_label.set_halign(Gtk.Align.START)
        
        shadow_switch = Gtk.Switch()
        shadow_switch.set_active(False)
        shadow_switch.connect("notify::active", lambda sw, _: self.on_border_shadow_changed(win, sw.get_active()))
        
        shadow_box.append(shadow_label)
        shadow_box.append(shadow_switch)
        border_box.append(shadow_box)
        
        # Add a separator
        border_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))
        
        # Border display options title (more compact)
        display_label = Gtk.Label(label="Border Display:")
        display_label.set_halign(Gtk.Align.START)
        display_label.set_margin_top(4)
        border_box.append(display_label)
        
        # Create a horizontal box for all border options
        all_options_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Create a linked box for primary border toggles
        primary_border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        primary_border_box.add_css_class("linked")
        
        # Create the primary border buttons
        border_options = [
            {"icon": "table-border-all-symbolic", "tooltip": "All Borders", "value": "all"},
            {"icon": "table-border-none-symbolic", "tooltip": "No Borders", "value": "none"},
            {"icon": "table-border-outer-symbolic", "tooltip": "Outer Borders", "value": "outer"},
            {"icon": "table-border-inner-symbolic", "tooltip": "Inner Borders", "value": "inner"}
        ]
        
        for option in border_options:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                win, None, width_spin, border_option))
            primary_border_box.append(button)
        
        all_options_box.append(primary_border_box)
        
        # Create a linked box for combo border options
        combo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box.add_css_class("linked")
        
        # Create horizontal/vertical buttons
        combo_options = [
            {"icon": "table-border-horizontal-symbolic", "tooltip": "Horizontal Borders", "value": "horizontal"},
            {"icon": "table-border-vertical-symbolic", "tooltip": "Vertical Borders", "value": "vertical"}
        ]
        
        for option in combo_options:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                win, None, width_spin, border_option))
            combo_box.append(button)
        
        all_options_box.append(combo_box)
        border_box.append(all_options_box)
        
        # Create a second row for combination border options
        combo_row2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        combo_row2.set_margin_top(4)
        
        # First linked box for combined options
        combo_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box2.add_css_class("linked")
        
        combo_options2 = [
            {"icon": "table-border-outer-horizontal-symbolic", "tooltip": "Outer Horizontal", "value": ["outer", "horizontal"]},
            {"icon": "table-border-outer-vertical-symbolic", "tooltip": "Outer Vertical", "value": ["outer", "vertical"]},
            {"icon": "table-border-inner-horizontal-symbolic", "tooltip": "Inner Horizontal", "value": ["inner", "horizontal"]},
            {"icon": "table-border-inner-vertical-symbolic", "tooltip": "Inner Vertical", "value": ["inner", "vertical"]}
        ]
        
        for option in combo_options2:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            if isinstance(option["value"], list):
                button.connect("clicked", lambda btn, border_types=option["value"]: self._apply_combined_borders(
                    win, width_spin, border_types))
            else:
                button.connect("clicked", lambda btn, border_option=option["value"]: self.on_border_display_option_clicked(
                    win, None, width_spin, border_option))
            combo_box2.append(button)
        
        combo_row2.append(combo_box2)
        
        # Second linked box for all combined options
        combo_box3 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        combo_box3.add_css_class("linked")
        
        combo_options3 = [
            {"icon": "table-border-outer-inner-horizontal-symbolic", "tooltip": "Outer + Inner Horizontal", "value": ["outer", "inner", "horizontal"]},
            {"icon": "table-border-outer-inner-vertical-symbolic", "tooltip": "Outer + Inner Vertical", "value": ["outer", "inner", "vertical"]}
        ]
        
        for option in combo_options3:
            button = Gtk.Button.new_from_icon_name(option["icon"])
            button.set_tooltip_text(option["tooltip"])
            button.connect("clicked", lambda btn, border_types=option["value"]: self._apply_combined_borders(
                win, width_spin, border_types))
            combo_box3.append(button)
        
        combo_row2.append(combo_box3)
        border_box.append(combo_row2)
        
        # Store references for later initialization
        border_box.style_combo = style_combo
        border_box.width_spin = width_spin
        border_box.shadow_switch = shadow_switch
        
        return border_box

    def _create_margin_tab(self, win, popover):
        """Create the margin properties tab with default values"""
        margin_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        margin_box.set_margin_start(12)
        margin_box.set_margin_end(12)
        margin_box.set_margin_top(12)
        margin_box.set_margin_bottom(12)
        
        # Create grid for margin controls
        margin_grid = Gtk.Grid()
        margin_grid.set_row_spacing(8)
        margin_grid.set_column_spacing(12)
        margin_grid.set_halign(Gtk.Align.CENTER)
        
        margin_controls = {}
        
        # Define positions for a visual layout with default values
        positions = {
            'top': (0, 1, 6),      # (row, col, default_value)
            'left': (1, 0, 0),
            'right': (1, 2, 6),
            'bottom': (2, 1, 0)
        }
        
        for side, (row, col, default_value) in positions.items():
            # Create a box for label and spin button
            side_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            
            # Add label
            label = Gtk.Label(label=side.capitalize())
            label.set_halign(Gtk.Align.CENTER)
            side_box.append(label)
            
            # Create spin button with appropriate default value
            adjustment = Gtk.Adjustment(value=default_value, lower=0, upper=100, step_increment=1)
            spin = Gtk.SpinButton()
            spin.set_adjustment(adjustment)
            spin.set_width_chars(5)
            
            # Connect change signal
            spin.connect("value-changed", lambda s, sd=side: self.on_margin_changed(win, sd, s.get_value_as_int()))
            
            side_box.append(spin)
            margin_grid.attach(side_box, col, row, 1, 1)
            margin_controls[side] = spin
        
        # Add a visual representation of the table in the center
        table_visual = Gtk.DrawingArea()
        table_visual.set_size_request(80, 60)
        table_visual.set_content_width(80)
        table_visual.set_content_height(60)
        
        def draw_table_visual(area, cr, width, height, data):
            # Draw a simple table representation
            cr.set_source_rgb(0.8, 0.8, 0.8)
            cr.rectangle(10, 10, width - 20, height - 20)
            cr.fill()
            
            cr.set_source_rgb(0.5, 0.5, 0.5)
            cr.rectangle(10, 10, width - 20, height - 20)
            cr.stroke()
        
        table_visual.set_draw_func(draw_table_visual, None)
        margin_grid.attach(table_visual, 1, 1, 1, 1)
        
        margin_box.append(margin_grid)
        
        # Add separator before default button
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(8)
        separator.set_margin_bottom(8)
        margin_box.append(separator)
        
        # Add default button
        default_button = Gtk.Button(label="Reset to Default Margins")
        default_button.connect("clicked", lambda btn: self._reset_default_margins(win, margin_controls))
        margin_box.append(default_button)
        
        # Store margin controls for later reference
        margin_box.margin_controls = margin_controls
        
        return margin_box

    def _create_color_tab(self, win, popover):
        """Create the color properties tab with GTK4 compatible color handling and compact layout"""
        color_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)  # Reduced from 12
        color_box.set_margin_start(8)  # Reduced from 12
        color_box.set_margin_end(8)
        color_box.set_margin_top(8)
        color_box.set_margin_bottom(8)
        
        # Helper function to create color button with custom color picker
        def create_color_button_row(label_text, apply_function):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)  # Reduced from 8
            label = Gtk.Label(label=label_text)
            label.set_halign(Gtk.Align.START)
            label.set_hexpand(True)
            
            # Create a button with color icon instead of ColorButton
            color_button = Gtk.Button()
            color_button.set_size_request(36, 20)  # Reduced from 40, 24
            
            # Create a DrawingArea for color display
            color_display = Gtk.DrawingArea()
            color_display.set_size_request(28, 16)  # Reduced from 30, 18
            color_button.set_child(color_display)
            
            # Default color
            color_button.current_color = "#000000"
            
            # Draw function for color display
            def draw_color(area, cr, width, height, data):
                rgba = self._parse_color_string(color_button.current_color)
                if rgba:
                    cr.set_source_rgba(rgba.red, rgba.green, rgba.blue, rgba.alpha)
                else:
                    cr.set_source_rgba(0, 0, 0, 1)  # Default to black
                cr.rectangle(2, 2, width - 4, height - 4)
                cr.fill()
                
                # Draw border
                cr.set_source_rgba(0.5, 0.5, 0.5, 1)
                cr.rectangle(2, 2, width - 4, height - 4)
                cr.set_line_width(1)
                cr.stroke()
            
            color_display.set_draw_func(draw_color, None)
            
            # Connect click handler to show color dialog
            color_button.connect("clicked", lambda btn: self._show_color_dialog(win, btn, apply_function))
            
            row_box.append(label)
            row_box.append(color_button)
            return row_box, color_button
        
        # Border color row
        border_color_box, border_color_button = create_color_button_row(
            "Border Color:", self._apply_border_color)
        color_box.append(border_color_box)
        
        # Table background color row
        table_color_box, table_color_button = create_color_button_row(
            "Table Color:", self._apply_table_color)
        color_box.append(table_color_box)
        
        # Header color row
        header_color_box, header_color_button = create_color_button_row(
            "Header Color:", self._apply_header_color)
        color_box.append(header_color_box)
        
        # Row color row (NEW)
        row_color_box, row_color_button = create_color_button_row(
            "Row Color:", self._apply_row_color)
        color_box.append(row_color_box)
        
        # Column color row (NEW)
        column_color_box, column_color_button = create_color_button_row(
            "Column Color:", self._apply_column_color)
        color_box.append(column_color_box)
        
        # Cell color row
        cell_color_box, cell_color_button = create_color_button_row(
            "Current Cell Color:", self._apply_cell_color)
        color_box.append(cell_color_box)
        
        # Add separator
        separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator.set_margin_top(6)  # Reduced from 8
        separator.set_margin_bottom(6)
        color_box.append(separator)
        
        # Add default button
        default_button = Gtk.Button(label="Reset to Default Colors")
        default_button.connect("clicked", lambda btn: self._reset_default_colors(win))
        color_box.append(default_button)
        
        # Store color buttons for later initialization
        color_box.border_color_button = border_color_button
        color_box.table_color_button = table_color_button
        color_box.header_color_button = header_color_button
        color_box.row_color_button = row_color_button
        color_box.column_color_button = column_color_button
        color_box.cell_color_button = cell_color_button
        
        return color_box

    def _initialize_table_properties(self, win, popover):
        """Initialize the table properties popup with current values"""
        # Get current table properties
        js_code = """
        (function() {
            const borderProps = getTableBorderProperties();
            const margins = getTableMargins();
            const colors = getTableColors();
            
            return JSON.stringify({
                border: borderProps,
                margins: margins,
                colors: colors
            });
        })();
        """
        
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._on_get_table_properties(win, webview, result, popover),
            None
        )

    def _on_get_table_properties(self, win, webview, result, popover):
        """Handle getting current table properties"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            result_str = None
            
            if hasattr(js_result, 'get_js_value'):
                result_str = js_result.get_js_value().to_string()
            else:
                result_str = js_result.to_string()
            
            if result_str:
                import json
                properties = json.loads(result_str)
                
                # Get references to the tab pages
                content_box = popover.get_child()
                notebook = None
                
                # Find the notebook widget (skip header)
                for child in content_box:
                    if isinstance(child, Gtk.Notebook):
                        notebook = child
                        break
                
                if notebook:
                    border_page = notebook.get_nth_page(0)
                    margin_page = notebook.get_nth_page(1)
                    color_page = notebook.get_nth_page(2)
                    
                    # Initialize border controls
                    if properties.get('border'):
                        border_style = properties['border'].get('style', 'solid')
                        border_width = properties['border'].get('width', 1)
                        has_shadow = properties['border'].get('shadow', False)
                        
                        # Find index of style
                        styles = ["solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset"]
                        try:
                            style_index = styles.index(border_style)
                        except ValueError:
                            style_index = 0  # Default to solid
                        
                        border_page.style_combo.set_selected(style_index)
                        border_page.width_spin.set_value(border_width)
                        border_page.shadow_switch.set_active(has_shadow)
                    
                    # Initialize margin controls
                    if properties.get('margins'):
                        margins = properties['margins']
                        for side in ['top', 'right', 'bottom', 'left']:
                            if side in margin_page.margin_controls and side in margins:
                                margin_page.margin_controls[side].set_value(margins[side])
                    
                    # Initialize color controls
                    if properties.get('colors'):
                        colors = properties['colors']
                        
                        # Set border color
                        if colors.get('border'):
                            color_page.border_color_button.current_color = colors['border']
                            color_display = color_page.border_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set table background color
                        if colors.get('background'):
                            color_page.table_color_button.current_color = colors['background']
                            color_display = color_page.table_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set header color
                        if colors.get('header'):
                            color_page.header_color_button.current_color = colors['header']
                            color_display = color_page.header_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
                        # Set cell color (if selected)
                        if colors.get('cell'):
                            color_page.cell_color_button.current_color = colors['cell']
                            color_display = color_page.cell_color_button.get_child()
                            if color_display:
                                color_display.queue_draw()
                        
        except Exception as e:
            print(f"Error initializing table properties: {e}")     
            
    def on_border_style_changed(self, win, style, width):
        """Apply border style change immediately while preserving other properties"""
        # Execute JavaScript to apply the border style while preserving width
        js_code = f"""
        (function() {{
            // Get current border properties first
            const currentStyle = getTableBorderStyle();
            const currentWidth = currentStyle ? currentStyle.width : {width};
            const currentColor = currentStyle ? currentStyle.color : getBorderColor();
            
            // Apply with preserved values
            setTableBorderStyle('{style}', currentWidth, currentColor);
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {style} border style")

    def on_border_width_changed(self, win, style, width):
        """Apply border width change immediately while preserving other properties"""
        # Execute JavaScript to apply the border width while preserving style
        js_code = f"""
        (function() {{
            // Get current border properties first
            const currentStyle = getTableBorderStyle();
            const currentBorderStyle = currentStyle ? currentStyle.style : 'solid';
            const currentColor = currentStyle ? currentStyle.color : getBorderColor();
            
            // Apply with preserved values
            setTableBorderStyle(currentBorderStyle, {width}, currentColor);
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {width}px border width")       

    def on_border_shadow_changed(self, win, active):
        """Apply or remove border shadow"""
        js_code = f"""
        (function() {{
            if (!activeTable) return false;
            
            if ({str(active).lower()}) {{
                activeTable.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.2)';
            }} else {{
                activeTable.style.boxShadow = 'none';
            }}
            
            // Store shadow state
            activeTable.setAttribute('data-border-shadow', {str(active).lower()});
            
            // Notify that content changed
            try {{
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }} catch(e) {{
                console.log("Could not notify about content change:", e);
            }}
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text(f"Border shadow {'enabled' if active else 'disabled'}")
        


    def _reset_default_margins(self, win, margin_controls):
        """Reset margins to default values"""
        default_margins = {
            'top': 6,
            'right': 6,
            'bottom': 0,
            'left': 0
        }
        
        # Update spin buttons
        for side, value in default_margins.items():
            if side in margin_controls:
                margin_controls[side].set_value(value)
        
        # Apply the margins in JavaScript
        js_code = f"""
        (function() {{
            setTableMargins({default_margins['top']}, {default_margins['right']}, 
                            {default_margins['bottom']}, {default_margins['left']});
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text("Reset to default margins")


    def _get_color_from_button(self, color_button):
        """Get color from button in a safe way that handles deprecation"""
        try:
            # Try the standard method first
            rgba = color_button.get_rgba()
            hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
            return hex_color
        except:
            try:
                # Try alternative methods
                color = color_button.get_color()
                red = (color.red >> 8) / 255.0
                green = (color.green >> 8) / 255.0
                blue = (color.blue >> 8) / 255.0
                hex_color = f"#{int(red * 255):02x}{int(green * 255):02x}{int(blue * 255):02x}"
                return hex_color
            except:
                # Final fallback
                return "#000000"

    def _set_color_on_button(self, color_button, color_string):
        """Set color on button in a safe way that handles deprecation"""
        try:
            rgba = self._parse_color_string(color_string)
            if rgba:
                try:
                    color_button.set_rgba(rgba)
                except:
                    # Try alternative methods
                    color_button.set_color(self._rgba_to_color(rgba))
        except Exception as e:
            print(f"Error setting color on button: {e}")


    def _show_color_dialog(self, win, color_button, apply_function):
        """Show a color dialog compatible with GTK4"""
        try:
            # Try using GTK4 ColorDialog
            try:
                dialog = Gtk.ColorDialog()
                dialog.set_title("Choose Color")
                
                # Set initial color
                initial_rgba = self._parse_color_string(color_button.current_color)
                if not initial_rgba:
                    initial_rgba = Gdk.RGBA()
                    initial_rgba.parse("#000000")
                
                dialog.choose_rgba(
                    win,
                    initial_rgba,
                    None,
                    lambda dlg, result, data: self._on_color_chosen(dlg, result, color_button, apply_function, win),
                    None
                )
                return
            except AttributeError:
                # ColorDialog not available, use ColorChooserDialog
                dialog = Gtk.ColorChooserDialog(
                    title="Choose Color",
                    transient_for=win
                )
                
                # Set initial color
                initial_rgba = self._parse_color_string(color_button.current_color)
                if initial_rgba:
                    try:
                        dialog.set_rgba(initial_rgba)
                    except AttributeError:
                        pass
                
                # Connect response handler
                dialog.connect("response", lambda dlg, response: self._on_color_dialog_response(
                    dlg, response, color_button, apply_function, win))
                
                dialog.show()
        except Exception as e:
            print(f"Error showing color dialog: {e}")
            # Fallback to preset color popover
            self._show_color_preset_popover(win, color_button, apply_function)

    def _on_color_chosen(self, dialog, result, color_button, apply_function, win):
        """Handle color selection from GTK4 ColorDialog"""
        try:
            rgba = dialog.choose_rgba_finish(result)
            if rgba:
                # Convert to hex color
                hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
                color_button.current_color = hex_color
                
                # Update color display
                color_display = color_button.get_child()
                if color_display:
                    color_display.queue_draw()
                
                # Apply the color
                apply_function(win, hex_color)
        except Exception as e:
            print(f"Error choosing color: {e}")

    def _on_color_dialog_response(self, dialog, response, color_button, apply_function, win):
        """Handle response from ColorChooserDialog"""
        if response == Gtk.ResponseType.OK:
            try:
                rgba = dialog.get_rgba()
                hex_color = f"#{int(rgba.red * 255):02x}{int(rgba.green * 255):02x}{int(rgba.blue * 255):02x}"
                color_button.current_color = hex_color
                
                # Update color display
                color_display = color_button.get_child()
                if color_display:
                    color_display.queue_draw()
                
                # Apply the color
                apply_function(win, hex_color)
            except Exception as e:
                print(f"Error getting color: {e}")
        
        dialog.destroy()

    def _apply_border_color(self, win, hex_color):
        """Apply border color"""
        try:
            print(f"Applying border color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color to all cells' borders
                const cells = activeTable.querySelectorAll('td, th');
                cells.forEach(cell => {{
                    cell.style.borderColor = '{hex_color}';
                }});
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-border-color', '{hex_color}');
                
                // Debug output
                console.log('Applied border color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied border color: {hex_color}")
        except Exception as e:
            print(f"Error applying border color: {e}")
            win.statusbar.set_text("Error applying border color")

    def _apply_table_color(self, win, hex_color):
        """Apply table background color"""
        try:
            print(f"Applying table color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color
                activeTable.style.backgroundColor = '{hex_color}';
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-bg-color', '{hex_color}');
                
                // Debug output
                console.log('Applied table color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied table color: {hex_color}")
        except Exception as e:
            print(f"Error applying table color: {e}")
            win.statusbar.set_text("Error applying table color")

    def _apply_header_color(self, win, hex_color):
        """Apply header background color"""
        try:
            print(f"Applying header color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply the color to all header cells
                const headers = activeTable.querySelectorAll('th');
                headers.forEach(header => {{
                    header.style.backgroundColor = '{hex_color}';
                }});
                
                // Store the color for theme preservation
                activeTable.setAttribute('data-header-color', '{hex_color}');
                
                // Debug output
                console.log('Applied header color:', '{hex_color}');
                
                // Notify that content changed
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }} catch(e) {{
                    console.log("Could not notify about content change:", e);
                }}
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied header color: {hex_color}")
        except Exception as e:
            print(f"Error applying header color: {e}")
            win.statusbar.set_text("Error applying header color")

    def _apply_cell_color(self, win, hex_color):
        """Apply cell background color"""
        try:
            print(f"Applying cell color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Get the current selection
                const selection = window.getSelection();
                if (!selection.rangeCount) return false;
                
                // Find the active cell
                let activeCell = selection.anchorNode;
                
                // If the selection is in a text node, get the parent element
                if (activeCell.nodeType === Node.TEXT_NODE) {{
                    activeCell = activeCell.parentElement;
                }}
                
                // Find the closest td or th element
                while (activeCell && activeCell.tagName !== 'TD' && activeCell.tagName !== 'TH') {{
                    activeCell = activeCell.parentElement;
                }}
                
                // If we found a cell and it belongs to our active table
                if (activeCell && activeTable.contains(activeCell)) {{
                    activeCell.style.backgroundColor = '{hex_color}';
                    
                    // Store the color on the cell itself
                    activeCell.setAttribute('data-cell-color', '{hex_color}');
                    
                    // Debug output
                    console.log('Applied cell color:', '{hex_color}');
                    
                    // Notify that content changed
                    try {{
                        window.webkit.messageHandlers.contentChanged.postMessage('changed');
                    }} catch(e) {{
                        console.log("Could not notify about content change:", e);
                    }}
                    
                    return true;
                }}
                
                return false;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied cell color: {hex_color}")
        except Exception as e:
            print(f"Error applying cell color: {e}")
            win.statusbar.set_text("Error applying cell color")

    def _apply_row_color(self, win, hex_color):
        """Apply row background color"""
        try:
            print(f"Applying row color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply row color
                setRowBackgroundColor('{hex_color}');
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied row color: {hex_color}")
        except Exception as e:
            print(f"Error applying row color: {e}")
            win.statusbar.set_text("Error applying row color")

    def _apply_column_color(self, win, hex_color):
        """Apply column background color"""
        try:
            print(f"Applying column color: {hex_color}")  # Debug print
            
            js_code = f"""
            (function() {{
                if (!activeTable) return false;
                
                // Apply column color
                setColumnBackgroundColor('{hex_color}');
                
                return true;
            }})();
            """
            self.execute_js(win, js_code)
            win.statusbar.set_text(f"Applied column color: {hex_color}")
        except Exception as e:
            print(f"Error applying column color: {e}")
            win.statusbar.set_text("Error applying column color")

    def _reset_default_colors(self, win):
        """Reset table colors to default values"""
        js_code = """
        (function() {
            if (!activeTable) return false;
            
            // Get default colors based on theme
            const borderColor = getBorderColor();
            const headerBgColor = getHeaderBgColor();
            
            // Reset border color
            setTableBorderColor(borderColor);
            
            // Reset table background color
            activeTable.style.backgroundColor = '';
            activeTable.removeAttribute('data-bg-color');
            
            // Reset header color
            const headers = activeTable.querySelectorAll('th');
            headers.forEach(header => {
                header.style.backgroundColor = headerBgColor;
            });
            activeTable.setAttribute('data-header-color', headerBgColor);
            
            // Reset all cell colors
            const cells = activeTable.querySelectorAll('td');
            cells.forEach(cell => {
                cell.style.backgroundColor = '';
                cell.removeAttribute('data-cell-color');
            });
            
            // Notify that content changed
            try {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            } catch(e) {
                console.log("Could not notify about content change:", e);
            }
            
            return JSON.stringify({
                border: borderColor,
                header: headerBgColor
            });
        })();
        """
        
        # Execute the reset and update color buttons
        win.webview.evaluate_javascript(
            js_code,
            -1, None, None, None,
            lambda webview, result, data: self._update_color_buttons_after_reset(webview, result, win),
            None
        )
        
        win.statusbar.set_text("Reset to default colors")

    # 2. Helper method to update color buttons after reset
    def _update_color_buttons_after_reset(self, webview, result, win):
        """Update color buttons after resetting to defaults"""
        try:
            js_result = webview.evaluate_javascript_finish(result)
            if js_result:
                result_str = js_result.to_string() if hasattr(js_result, 'to_string') else str(js_result)
                import json
                colors = json.loads(result_str)
                
                # Update color buttons if they exist in the current context
                for child in win.main_box:
                    if isinstance(child, Gtk.Popover):
                        content = child.get_child()
                        if content and isinstance(content, Gtk.Box):
                            for widget in content:
                                if isinstance(widget, Gtk.Notebook):
                                    color_page = widget.get_nth_page(2)  # Color tab
                                    if color_page:
                                        # Update border color button
                                        if hasattr(color_page, 'border_color_button'):
                                            rgba = self._parse_color_string(colors['border'])
                                            if rgba:
                                                color_page.border_color_button.set_rgba(rgba)
                                        
                                        # Clear other color buttons
                                        if hasattr(color_page, 'table_color_button'):
                                            rgba = Gdk.RGBA()
                                            rgba.parse('#ffffff')
                                            color_page.table_color_button.set_rgba(rgba)
                                        
                                        if hasattr(color_page, 'header_color_button'):
                                            rgba = self._parse_color_string(colors['header'])
                                            if rgba:
                                                color_page.header_color_button.set_rgba(rgba)
                                        
                                        if hasattr(color_page, 'cell_color_button'):
                                            rgba = Gdk.RGBA()
                                            rgba.parse('#ffffff')
                                            color_page.cell_color_button.set_rgba(rgba)
        except Exception as e:
            print(f"Error updating color buttons: {e}")


    def on_border_display_option_clicked(self, win, popover, width_spin, option):
        """Apply the selected border display option while preserving style and width"""
        js_code = f"""
        (function() {{
            // Get current border properties
            const currentStyle = getTableBorderStyle();
            let style = currentStyle ? currentStyle.style : 'solid';
            let width = currentStyle ? currentStyle.width : {width_spin.get_value()};
            let color = currentStyle ? currentStyle.color : getBorderColor();
            
            // Ensure we have valid values
            if (!style || style === 'none') {{
                style = 'solid';
            }}
            
            // First apply the current style, width, and color
            setTableBorderStyle(style, width, color);
            
            // Then apply the border option
            applyTableBorderSides(['{option}']);
            
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        win.statusbar.set_text(f"Applied {option} borders")
        
        # Close the popover if provided
        if popover:
            popover.popdown()
            
    def _apply_combined_borders(self, win, width_spin, border_types):
        """Apply combined border options while preserving properties"""
        border_types_js = str(border_types).replace("'", '"')
        
        js_code = f"""
        (function() {{
            // Get current border properties
            const currentStyle = getTableBorderStyle();
            let style = currentStyle ? currentStyle.style : 'solid';
            let width = currentStyle ? currentStyle.width : {width_spin.get_value()};
            let color = currentStyle ? currentStyle.color : getBorderColor();
            
            // Ensure we have valid values
            if (!style || style === 'none') {{
                style = 'solid';
            }}
            
            // First apply the current style, width, and color
            setTableBorderStyle(style, width, color);
            
            // Then apply the combined border options
            applyTableBorderSides({border_types_js});
            
            return true;
        }})();
        """
        win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
        
        # Update status message
        border_text = " + ".join(border_types)
        win.statusbar.set_text(f"Applied {border_text} borders")

############# Additional methods

 
 
 
 
 
 
 
 
def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
