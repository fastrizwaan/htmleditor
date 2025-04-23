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
            'create_formatting_toolbar', 'on_bold_shortcut', 'on_italic_shortcut',
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
.linked button               {background-color: rgba(127, 127, 127, 0.10); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:hover         {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}
.linked button:active        {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked       {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.00);}
.linked button:checked:hover {background-color: rgba(127, 127, 127, 0.35); border: solid 1px rgba(127, 127, 127, 0.30);}
.linked splitbutton > menubutton > button.toggle {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton > button  {
    border-top-left-radius: 0px; border-bottom-left-radius: 0px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}
.linked splitbutton:first-child > button  {
    border-top-left-radius: 5px; border-bottom-left-radius: 5px; border-top-right-radius: 0px; border-bottom-right-radius: 0px;}

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
                
    def create_window(self):
        """Create a new window with all initialization (former HTMLEditorWindow.__init__)"""
        win = Adw.ApplicationWindow(application=self)
        
        # Set window properties
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        
        win.set_default_size(800, 600)
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
        
        # Create a vertical box to contain headerbar and toolbars
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create the main headerbar
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")  # Add flat-header style
        self.setup_headerbar_content(win)
        win.headerbar_box.append(win.headerbar)
        
        # Create file toolbar with revealer
        win.file_toolbar_revealer = Gtk.Revealer()
        win.file_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.file_toolbar_revealer.set_transition_duration(250)
        win.file_toolbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create and add file toolbar
        win.file_toolbar = self.create_file_toolbar(win)
        win.file_toolbar_revealer.set_child(win.file_toolbar)
        win.headerbar_box.append(win.file_toolbar_revealer)
        
        # Create formatting toolbar with revealer
        win.formatting_toolbar_revealer = Gtk.Revealer()
        win.formatting_toolbar_revealer.set_margin_start(0)
        win.formatting_toolbar_revealer.set_margin_end(0)
        win.formatting_toolbar_revealer.set_margin_top(0)
        win.formatting_toolbar_revealer.set_margin_bottom(0)
        win.formatting_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.formatting_toolbar_revealer.set_transition_duration(250)
        win.formatting_toolbar_revealer.set_reveal_child(True)  # Visible by default
        
        # Create and add formatting toolbar
        win.toolbar = self.create_formatting_toolbar(win)
        win.formatting_toolbar_revealer.set_child(win.toolbar)
        win.headerbar_box.append(win.formatting_toolbar_revealer)
        
        # Set the headerbar_box as the child of the headerbar_revealer
        win.headerbar_revealer.set_child(win.headerbar_box)
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
        except:
            print("Warning: Could not set up JavaScript message handlers")
                    
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        # Find bar with revealer
        win.find_bar = self.create_find_bar(win)
        content_box.append(win.find_bar)
        
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
        win.zoom_revealer.set_transition_duration(200)
        win.zoom_revealer.set_reveal_child(False)  # Hidden by default
        
        # Create zoom control element inside the revealer
        zoom_control_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        zoom_control_box.add_css_class("linked")  # Use linked styling for cleaner appearance
        zoom_control_box.set_halign(Gtk.Align.END)
        
        # Create zoom level label
        win.zoom_label = Gtk.Label(label="100%")
        win.zoom_label.set_width_chars(4)  # Set a fixed width for the label
        win.zoom_label.set_margin_start(6)
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
        win.zoom_scale.set_size_request(200, -1)  # Set a reasonable width
        win.zoom_scale.set_round_digits(0)  # Round to integer values

        # Add only marks without any text
        # Using NULL for the text parameter to create marks without labels
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
#        title_widget.set_subtitle("Untitled")  # Will be updated with document name
        win.title_widget = title_widget  # Store for later updates
        
        # Save reference to update title 
        win.headerbar.set_title_widget(title_widget)
        
        # Add buttons to header bar
        win.headerbar.pack_start(menu_button)
        
        # Create window menu button on the right side
        self.add_window_menu_button(win)
            
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # --- File operations group (New, Open, Save, Save As) ---
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_group.add_css_class("linked")  # Apply linked styling
        file_group.set_margin_start(4)

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
        file_toolbar.append(file_group)
        
        # --- Edit operations group (Cut, Copy, Paste, Print) ---
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        edit_group.add_css_class("linked")  # Apply linked styling
        edit_group.set_margin_start(6)
        
        # Cut button
        cut_button = Gtk.Button(icon_name="edit-cut-symbolic")
        cut_button.set_tooltip_text("Cut")
        cut_button.connect("clicked", lambda btn: self.on_cut_clicked(win, btn))

        # Copy button
        copy_button = Gtk.Button(icon_name="edit-copy-symbolic")
        copy_button.set_tooltip_text("Copy")
        copy_button.connect("clicked", lambda btn: self.on_copy_clicked(win, btn))

        # Paste button
        paste_button = Gtk.Button(icon_name="edit-paste-symbolic")
        paste_button.set_tooltip_text("Paste")
        paste_button.connect("clicked", lambda btn: self.on_paste_clicked(win, btn))
        
        # Print button
        print_button = Gtk.Button(icon_name="document-print-symbolic")
        print_button.set_tooltip_text("Print Document")
        print_button.connect("clicked", lambda btn: self.on_print_clicked(win, btn) if hasattr(self, "on_print_clicked") else None)
        
        # Add buttons to edit group
        edit_group.append(cut_button)
        edit_group.append(copy_button)
        edit_group.append(paste_button)
        edit_group.append(print_button)
        
        # Add edit group to toolbar
        file_toolbar.append(edit_group)
        
        # --- History operations group (Undo, Redo, Find) ---
        history_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        history_group.add_css_class("linked")  # Apply linked styling
        history_group.set_margin_start(6)
        
        # Undo button
        win.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        win.undo_button.set_tooltip_text("Undo")
        win.undo_button.connect("clicked", lambda btn: self.on_undo_clicked(win, btn))
        win.undo_button.set_sensitive(False)  # Initially disabled
        
        # Redo button
        win.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        win.redo_button.set_tooltip_text("Redo")
        win.redo_button.connect("clicked", lambda btn: self.on_redo_clicked(win, btn))
        win.redo_button.set_sensitive(False)  # Initially disabled
        
        # Find-Replace toggle button
        win.find_button = Gtk.ToggleButton()
        find_icon = Gtk.Image.new_from_icon_name("edit-find-replace-symbolic")
        win.find_button.set_child(find_icon)
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))

        # Add buttons to history group
        history_group.append(win.undo_button)
        history_group.append(win.redo_button)
        history_group.append(win.find_button)
        
        # Add history group to toolbar
        file_toolbar.append(history_group)
        
        # --- Spacing operations group (Line Spacing, Paragraph Spacing) ---
        spacing_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        spacing_group.add_css_class("linked")  # Apply linked styling
        spacing_group.set_margin_start(6)
        
        # Line spacing button menu
        line_spacing_button = Gtk.MenuButton(icon_name="line_space_new")
        line_spacing_button.set_size_request(40, 36)
        line_spacing_button.set_tooltip_text("Line Spacing")
        line_spacing_button.add_css_class("flat")
        
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
        para_spacing_button.add_css_class("flat")
        
        # Create paragraph spacing menu
        para_spacing_menu = Gio.Menu()
        
        # Add paragraph spacing options
        para_spacing_menu.append("None", "win.paragraph-spacing('0')")
        para_spacing_menu.append("Small (5px)", "win.paragraph-spacing('5')")
        para_spacing_menu.append("Medium (15px)", "win.paragraph-spacing('15')")
        para_spacing_menu.append("Large (30px)", "win.paragraph-spacing('30')")
        para_spacing_menu.append("Custom...", "win.paragraph-spacing-dialog")
        
        para_spacing_button.set_menu_model(para_spacing_menu)
        
        # Column layout button menu
        column_button = Gtk.MenuButton(icon_name="columns-symbolic")
        column_button.set_size_request(40, 36)
        column_button.set_tooltip_text("Column Layout")
        column_button.add_css_class("flat")
        
        # Create column menu
        column_menu = Gio.Menu()
        
        # Add column options
        column_menu.append("Single Column", "win.set-columns('1')")
        column_menu.append("Two Columns", "win.set-columns('2')")
        column_menu.append("Three Columns", "win.set-columns('3')")
        column_menu.append("Four Columns", "win.set-columns('4')")
        column_menu.append("Remove Columns", "win.set-columns('0')")
        
        column_button.set_menu_model(column_menu)
        
        # Add buttons to spacing group
        spacing_group.append(line_spacing_button)
        spacing_group.append(para_spacing_button)
        spacing_group.append(column_button)
        
        text_box_button = Gtk.Button(icon_name="insert-text-symbolic")  # Using a standard GTK icon
        text_box_button.set_size_request(40, 36)
        text_box_button.set_tooltip_text("Insert Text Box")
        text_box_button.connect("clicked", lambda btn: self.on_insert_text_box_clicked(win, btn))
        spacing_group.append(text_box_button)


        image_button = Gtk.Button(icon_name="insert-image-symbolic")
        image_button.set_size_request(40, 36)
        image_button.set_tooltip_text("Insert Image")
        image_button.connect("clicked", lambda btn: self.on_insert_image_clicked(win, btn))
        spacing_group.append(image_button)
        
        
        
        # Add spacing group to toolbar
        file_toolbar.append(spacing_group)        

        
        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar


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
        
        # Create Ctrl+T shortcut for toggling the toolbar
        trigger_toolbar = Gtk.ShortcutTrigger.parse_string("<Control>t")
        action_toolbar = Gtk.CallbackAction.new(lambda *args: self.toggle_formatting_toolbar(win, *args))
        shortcut_toolbar = Gtk.Shortcut.new(trigger_toolbar, action_toolbar)
        controller.add_shortcut(shortcut_toolbar)
        
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
        is_revealed = win.file_toolbar_revealer.get_reveal_child()
        win.file_toolbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"File Toolbar {status}")
        return True         
             
    def toggle_formatting_toolbar(self, win, *args):
        """Toggle the visibility of the toolbar with animation"""
        is_revealed = win.formatting_toolbar_revealer.get_reveal_child()
        win.formatting_toolbar_revealer.set_reveal_child(not is_revealed)
        status = "hidden" if is_revealed else "shown"
        win.statusbar.set_text(f"Formatting Toolbar {status}")
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
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const editor = document.getElementById('editor');
            
            // Give the editor a proper tabindex to ensure it can capture keyboard focus
            editor.setAttribute('tabindex', '0');
            
            // Capture tab key to prevent focus from shifting
            editor.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    // Prevent the default focus shift action
                    e.preventDefault();
                    
                    // Insert tab character as a styled span
                    document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    
                    // Trigger input event to register the change for undo/redo
                    const event = new Event('input', {
                        bubbles: true,
                        cancelable: true
                    });
                    editor.dispatchEvent(event);
                }
            });
            
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
            win.statusbar.set_text("Zoom controls shown")
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
        {self.init_editor_js()}
        """

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
#####################
    # Python handler function

    def on_insert_text_box_clicked(self, win, btn):
        """Handle text box insertion button click"""
        win.statusbar.set_text("Inserting text box...")
        
        # Execute JavaScript to insert a text box at the cursor position
        js_code = """
        (function() {
            insertTextBox();
            return true;
        })();
        """
        self.execute_js(win, js_code)

    # JavaScript functions for text box handling
    def text_box_js(self):
        """JavaScript for text box functionality"""
        return """
        // Text box variables
        let activeTextBox = null;
        let isDragging = false;
        let isResizing = false;
        let isRotating = false;
        let lastX = 0;
        let lastY = 0;
        let lastAngle = 0;
        let textBoxCounter = 0;
        
        // Insert a text box at the cursor position
        function insertTextBox() {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Get the current selection range
            const range = selection.getRangeAt(0);
            
            // Create a wrapper to hold the text box
            const textBoxWrapper = document.createElement('div');
            textBoxWrapper.className = 'editor-text-box-wrapper';
            textBoxWrapper.contentEditable = 'false'; // Make the wrapper non-editable
            textBoxWrapper.style.position = 'relative';
            textBoxWrapper.style.display = 'inline-block';
            textBoxWrapper.style.minWidth = '50px';
            textBoxWrapper.style.minHeight = '30px';
            textBoxWrapper.style.margin = '10px';
            textBoxWrapper.style.padding = '0';
            textBoxWrapper.style.zIndex = '1';
            // Remove the outline to avoid alignment issues
            textBoxWrapper.style.outline = 'none';
            
            // Create a unique ID for this text box
            textBoxCounter++;
            const textBoxId = 'text-box-' + textBoxCounter;
            textBoxWrapper.id = textBoxId;
            
            // Create the actual editable text box inside the wrapper
            const textBox = document.createElement('div');
            textBox.className = 'editor-text-box-content';
            textBox.contentEditable = 'true';
            textBox.style.width = '100%';
            textBox.style.height = '100%';
            textBox.style.border = '1px solid #ccc';
            textBox.style.padding = '10px';
            textBox.style.backgroundColor = 'white';
            textBox.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
            textBox.style.overflow = 'hidden';
            textBox.style.cursor = 'text';
            textBox.style.boxSizing = 'border-box';
            textBox.innerHTML = '';
            textBox.setAttribute('data-textbox-id', textBoxId);
            
            // Store rotation angle in the wrapper
            textBoxWrapper.dataset.angle = '0';
            textBoxWrapper.style.transform = 'rotate(0deg)';
            
            // Create a visual border for selection that matches the dashed outline
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'text-box-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '2px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            // Create and add the controls container
            const controls = document.createElement('div');
            controls.className = 'text-box-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            // Create and add the move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '24px';
            moveHandle.style.height = '24px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.title = 'Move';
            
            // Create and add the rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '24px';
            rotateHandle.style.height = '24px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.title = 'Rotate';
            
            // Create and add the resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '24px';
            resizeHandle.style.height = '24px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.title = 'Resize';
            
            // Add handles to controls
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            // Add elements to the wrapper
            textBoxWrapper.appendChild(textBox);
            textBoxWrapper.appendChild(selectionBorder);
            textBoxWrapper.appendChild(controls);
            
            // Create a transparent clickable overlay for better selection
            const overlay = document.createElement('div');
            overlay.className = 'text-box-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px'; // Extended hit area
            overlay.style.left = '-15px'; // Extended hit area
            overlay.style.right = '-15px'; // Extended hit area
            overlay.style.bottom = '-15px'; // Extended hit area
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997'; // Below the selection border but above content
            overlay.style.display = 'none'; // Initially hidden
            
            textBoxWrapper.appendChild(overlay);
            
            // Set up event handlers for the text box wrapper
            
            // Prevent the default behavior of Enter key in the text box
            textBox.addEventListener('keydown', function(e) {
                // Let the Enter key work normally inside the text box
                if (e.key === 'Enter') {
                    e.stopPropagation(); // Don't let it bubble up to document
                    // Default behavior of creating a new line is fine
                }
            });
            
            // Text box wrapper click event
            textBoxWrapper.addEventListener('mousedown', function(e) {
                // Determine if click is on the content or controls
                const contentBox = textBoxWrapper.querySelector('.editor-text-box-content');
                const isContentClick = contentBox && (e.target === contentBox || contentBox.contains(e.target));
                const isControlClick = e.target.closest('.text-box-controls') !== null;
                
                // If clicking on controls, let the specific handler deal with it
                if (isControlClick) {
                    return;
                }
                
                // Ensure this text box is active
                if (activeTextBox !== textBoxWrapper) {
                    if (activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                    activateTextBox(textBoxWrapper);
                }
                
                // If clicking inside the content, allow normal text editing
                if (isContentClick) {
                    return;
                }
                
                // If clicking on wrapper but not content, prevent default
                e.preventDefault();
                e.stopPropagation();
            });
            
            // Handle move
            moveHandle.addEventListener('mousedown', function(e) {
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle resize
            resizeHandle.addEventListener('mousedown', function(e) {
                isResizing = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle rotate
            rotateHandle.addEventListener('mousedown', function(e) {
                isRotating = true;
                const rect = textBoxWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Insert the text box at the current selection
            range.deleteContents();
            range.insertNode(textBoxWrapper);
            
            // Create a new range and place the cursor inside the text box
            const newRange = document.createRange();
            newRange.selectNodeContents(textBox);
            newRange.collapse(true); // Collapse to the start of the content
            selection.removeAllRanges();
            selection.addRange(newRange);
            
            // Focus the text box
            textBox.focus();
            
            // Add mouse event listeners to the document if not already added
            if (!window.textBoxEventsAdded) {
                // Handle mouse movement for dragging, resizing, and rotating
                document.addEventListener('mousemove', handleMouseMove);
                
                // Handle mouse up to stop dragging, resizing, and rotating
                document.addEventListener('mouseup', function() {
                    if (isDragging || isResizing || isRotating) {
                        isDragging = false;
                        isResizing = false;
                        isRotating = false;
                        
                        // If we made changes, save state
                        saveState();
                    }
                });
                
                // Handle clicks on the editor to deactivate text boxes
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    // Check if the click is directly on the editor or a non-text-box element
                    const isTextBoxClick = e.target.closest('.editor-text-box-wrapper') !== null;
                    
                    if (!isTextBoxClick && activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                });
                
                // Mark that we've added the event handlers
                window.textBoxEventsAdded = true;
            }
            
            // Enable text box controls
            activateTextBox(textBoxWrapper);
            
            // Save state after insertion
            saveState();
            
            return true;
        }
        
        // Handle mouse movement for dragging, resizing, and rotating
        function handleMouseMove(e) {
            if (!activeTextBox) return;
            
            if (isDragging) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current position or default to 0
                const currentLeft = parseInt(activeTextBox.style.left) || 0;
                const currentTop = parseInt(activeTextBox.style.top) || 0;
                
                // Update position
                activeTextBox.style.position = 'relative';
                activeTextBox.style.left = `${currentLeft + dx}px`;
                activeTextBox.style.top = `${currentTop + dy}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isResizing) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current dimensions
                const currentWidth = activeTextBox.offsetWidth;
                const currentHeight = activeTextBox.offsetHeight;
                
                // Apply minimum sizes
                activeTextBox.style.width = `${Math.max(100, currentWidth + dx)}px`;
                activeTextBox.style.height = `${Math.max(50, currentHeight + dy)}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isRotating) {
                const rect = activeTextBox.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - lastAngle;
                
                const currentAngle = parseFloat(activeTextBox.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                activeTextBox.style.transform = `rotate(${newAngle}deg)`;
                activeTextBox.dataset.angle = newAngle.toString();
                
                lastAngle = angle;
            }
        }
        
        // Activate a text box (show controls)
        function activateTextBox(textBoxWrapper) {
            if (activeTextBox && activeTextBox !== textBoxWrapper) {
                deactivateTextBox(activeTextBox);
            }
            
            activeTextBox = textBoxWrapper;
            
            // Get the content element
            const textBox = textBoxWrapper.querySelector('.editor-text-box-content');
            if (textBox) {
                textBox.style.border = '1px solid #4285f4';
                textBox.style.boxShadow = '0 0 8px rgba(66, 133, 244, 0.4)';
            }
            
            // Show selection border (dashed outline)
            const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = textBoxWrapper.querySelector('.text-box-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            textBoxWrapper.style.zIndex = '10';
            
            // Show controls
            const controls = textBoxWrapper.querySelector('.text-box-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        // Deactivate a text box (hide controls)
        function deactivateTextBox(textBoxWrapper) {
            if (textBoxWrapper) {
                // Get the content element
                const textBox = textBoxWrapper.querySelector('.editor-text-box-content');
                if (textBox) {
                    textBox.style.border = '1px solid #ccc';
                    textBox.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
                }
                
                // Hide selection border
                const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = textBoxWrapper.querySelector('.text-box-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                textBoxWrapper.style.zIndex = '1';
                
                // Hide controls
                const controls = textBoxWrapper.querySelector('.text-box-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (activeTextBox === textBoxWrapper) {
                    activeTextBox = null;
                }
            }
        }
        
        // Add global CSS for text boxes
        function addTextBoxStyles() {
            if (!document.getElementById('text-box-styles')) {
                const style = document.createElement('style');
                style.id = 'text-box-styles';
                style.textContent = `
                    .editor-text-box-content:focus {
                        outline: none;
                    }
                    
                    .editor-text-box-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-text-box-wrapper .editor-text-box-content {
                        cursor: text;
                    }
                    
                    .text-box-selection-border {
                        pointer-events: none;
                    }
                    
                    .text-box-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-text-box-content {
                            background-color: #333;
                            color: #fff;
                            border-color: #666;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // Initialize text box functionality
        document.addEventListener('DOMContentLoaded', function() {
            addTextBoxStyles();
        });
        """

    # Add this to the get_editor_js method
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
        {self.text_box_js()}
        {self.image_js()}
        {self.init_editor_js()}
        """
################################
    def on_insert_image_clicked(self, win, btn):
        """Handle image insertion button click"""
        win.statusbar.set_text("Inserting image...")

        # Create a file chooser dialog using Gtk.FileChooserNative
        dialog = Gtk.FileChooserNative(
            title="Select an Image",
            transient_for=win,  # Set the transient parent correctly
            action=Gtk.FileChooserAction.OPEN,
            accept_label="_Open",
            cancel_label="_Cancel"
        )

        # Add image file filters
        filter_image = Gtk.FileFilter()
        filter_image.set_name("Image files")
        filter_image.add_mime_type("image/png")
        filter_image.add_mime_type("image/jpeg")
        filter_image.add_mime_type("image/gif")
        dialog.set_filter(filter_image)

        dialog.connect("response", lambda dlg, response: self.on_image_dialog_response(dlg, response, win))
        dialog.show()

    def on_image_dialog_response(self, dialog, response, win):
        """Handle the response from the image file chooser dialog"""
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file and (file_path := file.get_path()):
                # Convert file path to a data URL for JavaScript
                import base64
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    mime_type = "image/png" if file_path.endswith(".png") else "image/jpeg"
                    data_url = f"data:{mime_type};base64,{encoded_string}"

                # Execute JavaScript to insert the image
                js_code = f"""
                (function() {{
                    insertImage('{data_url}');
                    return true;
                }})();
                """
                self.execute_js(win, js_code)
            else:
                win.statusbar.set_text("Failed to select a valid image file.")
        dialog.destroy() 
        
    def text_box_js(self):
        """JavaScript for text box functionality"""
        return """
        // Text box variables (namespaced)
        const textBoxState = {
            activeTextBox: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            lastAngle: 0,
            textBoxCounter: 0
        };
        
        // Insert a text box at the cursor position
        function insertTextBox() {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            const range = selection.getRangeAt(0);
            
            const textBoxWrapper = document.createElement('div');
            textBoxWrapper.className = 'editor-text-box-wrapper';
            textBoxWrapper.contentEditable = 'false';
            textBoxWrapper.style.position = 'relative';
            textBoxWrapper.style.display = 'inline-block';
            textBoxWrapper.style.minWidth = '50px';
            textBoxWrapper.style.minHeight = '30px';
            textBoxWrapper.style.margin = '10px';
            textBoxWrapper.style.padding = '0';
            textBoxWrapper.style.zIndex = '1';
            textBoxWrapper.style.outline = 'none';
            
            textBoxState.textBoxCounter++;
            const textBoxId = 'text-box-' + textBoxState.textBoxCounter;
            textBoxWrapper.id = textBoxId;
            
            const textBox = document.createElement('div');
            textBox.className = 'editor-text-box-content';
            textBox.contentEditable = 'true';
            textBox.style.width = '100%';
            textBox.style.height = '100%';
            textBox.style.border = '1px solid #ccc';
            textBox.style.padding = '10px';
            textBox.style.backgroundColor = 'white';
            textBox.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
            textBox.style.overflow = 'hidden';
            textBox.style.cursor = 'text';
            textBox.style.boxSizing = 'border-box';
            textBox.innerHTML = '';
            textBox.setAttribute('data-textbox-id', textBoxId);
            
            textBoxWrapper.dataset.angle = '0';
            textBoxWrapper.style.transform = 'rotate(0deg)';
            
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'text-box-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '2px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            const controls = document.createElement('div');
            controls.className = 'text-box-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '24px';
            moveHandle.style.height = '24px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.title = 'Move';
            
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '24px';
            rotateHandle.style.height = '24px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.title = 'Rotate';
            
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '24px';
            resizeHandle.style.height = '24px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.title = 'Resize';
            
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            textBoxWrapper.appendChild(textBox);
            textBoxWrapper.appendChild(selectionBorder);
            textBoxWrapper.appendChild(controls);
            
            const overlay = document.createElement('div');
            overlay.className = 'text-box-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            textBoxWrapper.appendChild(overlay);
            
            textBox.addEventListener('keydown', function(e) {
                if (e.key === 'Enter') {
                    e.stopPropagation();
                }
            });
            
            textBoxWrapper.addEventListener('mousedown', function(e) {
                const contentBox = textBoxWrapper.querySelector('.editor-text-box-content');
                const isContentClick = contentBox && (e.target === contentBox || contentBox.contains(e.target));
                const isControlClick = e.target.closest('.text-box-controls') !== null;
                
                if (isControlClick) {
                    return;
                }
                
                if (textBoxState.activeTextBox !== textBoxWrapper) {
                    if (textBoxState.activeTextBox) {
                        deactivateTextBox(textBoxState.activeTextBox);
                    }
                    activateTextBox(textBoxWrapper);
                }
                
                if (isContentClick) {
                    return;
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            moveHandle.addEventListener('mousedown', function(e) {
                textBoxState.isDragging = true;
                textBoxState.lastX = e.clientX;
                textBoxState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                textBoxState.isResizing = true;
                textBoxState.lastX = e.clientX;
                textBoxState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                textBoxState.isRotating = true;
                const rect = textBoxWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                textBoxState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            range.deleteContents();
            range.insertNode(textBoxWrapper);
            
            const newRange = document.createRange();
            newRange.selectNodeContents(textBox);
            newRange.collapse(true);
            selection.removeAllRanges();
            selection.addRange(newRange);
            
            textBox.focus();
            
            if (!window.textBoxEventsAdded) {
                document.addEventListener('mousemove', handleTextBoxMouseMove);
                document.addEventListener('mouseup', function() {
                    if (textBoxState.isDragging || textBoxState.isResizing || textBoxState.isRotating) {
                        textBoxState.isDragging = false;
                        textBoxState.isResizing = false;
                        textBoxState.isRotating = false;
                        saveState();
                    }
                });
                
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    const isTextBoxClick = e.target.closest('.editor-text-box-wrapper') !== null;
                    if (!isTextBoxClick && textBoxState.activeTextBox) {
                        deactivateTextBox(textBoxState.activeTextBox);
                    }
                });
                
                window.textBoxEventsAdded = true;
            }
            
            activateTextBox(textBoxWrapper);
            saveState();
            return true;
        }
        
        function handleTextBoxMouseMove(e) {
            if (!textBoxState.activeTextBox) return;
            
            if (textBoxState.isDragging) {
                const dx = e.clientX - textBoxState.lastX;
                const dy = e.clientY - textBoxState.lastY;
                
                const currentLeft = parseInt(textBoxState.activeTextBox.style.left) || 0;
                const currentTop = parseInt(textBoxState.activeTextBox.style.top) || 0;
                
                textBoxState.activeTextBox.style.position = 'relative';
                textBoxState.activeTextBox.style.left = `${currentLeft + dx}px`;
                textBoxState.activeTextBox.style.top = `${currentTop + dy}px`;
                
                textBoxState.lastX = e.clientX;
                textBoxState.lastY = e.clientY;
            }
            else if (textBoxState.isResizing) {
                const dx = e.clientX - textBoxState.lastX;
                const dy = e.clientY - textBoxState.lastY;
                
                const currentWidth = textBoxState.activeTextBox.offsetWidth;
                const currentHeight = textBoxState.activeTextBox.offsetHeight;
                
                textBoxState.activeTextBox.style.width = `${Math.max(100, currentWidth + dx)}px`;
                textBoxState.activeTextBox.style.height = `${Math.max(50, currentHeight + dy)}px`;
                
                textBoxState.lastX = e.clientX;
                textBoxState.lastY = e.clientY;
            }
            else if (textBoxState.isRotating) {
                const rect = textBoxState.activeTextBox.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - textBoxState.lastAngle;
                
                const currentAngle = parseFloat(textBoxState.activeTextBox.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                textBoxState.activeTextBox.style.transform = `rotate(${newAngle}deg)`;
                textBoxState.activeTextBox.dataset.angle = newAngle.toString();
                
                textBoxState.lastAngle = angle;
            }
        }
        
        function activateTextBox(textBoxWrapper) {
            if (textBoxState.activeTextBox && textBoxState.activeTextBox !== textBoxWrapper) {
                deactivateTextBox(textBoxState.activeTextBox);
            }
            
            textBoxState.activeTextBox = textBoxWrapper;
            
            const textBox = textBoxWrapper.querySelector('.editor-text-box-content');
            if (textBox) {
                textBox.style.border = '1px solid #4285f4';
                textBox.style.boxShadow = '0 0 8px rgba(66, 133, 244, 0.4)';
            }
            
            const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            const overlay = textBoxWrapper.querySelector('.text-box-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            textBoxWrapper.style.zIndex = '10';
            
            const controls = textBoxWrapper.querySelector('.text-box-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        function deactivateTextBox(textBoxWrapper) {
            if (textBoxWrapper) {
                const textBox = textBoxWrapper.querySelector('.editor-text-box-content');
                if (textBox) {
                    textBox.style.border = '1px solid #ccc';
                    textBox.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
                }
                
                const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                const overlay = textBoxWrapper.querySelector('.text-box-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                textBoxWrapper.style.zIndex = '1';
                
                const controls = textBoxWrapper.querySelector('.text-box-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (textBoxState.activeTextBox === textBoxWrapper) {
                    textBoxState.activeTextBox = null;
                }
            }
        }
        
        function addTextBoxStyles() {
            if (!document.getElementById('text-box-styles')) {
                const style = document.createElement('style');
                style.id = 'text-box-styles';
                style.textContent = `
                    .editor-text-box-content:focus {
                        outline: none;
                    }
                    
                    .editor-text-box-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-text-box-wrapper .editor-text-box-content {
                        cursor: text;
                    }
                    
                    .text-box-selection-border {
                        pointer-events: none;
                    }
                    
                    .text-box-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-text-box-content {
                            background-color: #333;
                            color: #fff;
                            border-color: #666;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            addTextBoxStyles();
        });
        """

    def image_js(self):
        """JavaScript for image functionality"""
        return """
        // Image variables (namespaced)
        const imageState = {
            activeImage: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            lastAngle: 0,
            imageCounter: 0
        };
        
        function insertImage(dataUrl) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            const range = selection.getRangeAt(0);
            
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.contentEditable = 'false';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.minWidth = '100px';
            imageWrapper.style.minHeight = '100px';
            imageWrapper.style.margin = '10px';
            imageWrapper.style.padding = '0';
            imageWrapper.style.zIndex = '1';
            imageWrapper.style.outline = 'none';
            
            imageState.imageCounter++;
            const imageId = 'image-' + imageState.imageCounter;
            imageWrapper.id = imageId;
            
            const image = document.createElement('img');
            image.className = 'editor-image-content';
            image.src = dataUrl;
            image.style.width = '100%';
            image.style.height = '100%';
            image.style.border = '1px solid #ccc';
            image.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
            image.style.objectFit = 'contain';
            image.style.cursor = 'default';
            image.style.boxSizing = 'border-box';
            image.setAttribute('data-image-id', imageId);
            
            imageWrapper.dataset.angle = '0';
            imageWrapper.style.transform = 'rotate(0deg)';
            
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'image-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '2px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            const controls = document.createElement('div');
            controls.className = 'image-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '24px';
            moveHandle.style.height = '24px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.title = 'Move';
            
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '24px';
            rotateHandle.style.height = '24px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.title = 'Rotate';
            
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '24px';
            resizeHandle.style.height = '24px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.title = 'Resize';
            
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            imageWrapper.appendChild(image);
            imageWrapper.appendChild(selectionBorder);
            imageWrapper.appendChild(controls);
            
            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            imageWrapper.appendChild(overlay);
            
            imageWrapper.addEventListener('mousedown', function(e) {
                const isControlClick = e.target.closest('.image-controls') !== null;
                
                if (isControlClick) {
                    return;
                }
                
                if (imageState.activeImage !== imageWrapper) {
                    if (imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                    activateImage(imageWrapper);
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            moveHandle.addEventListener('mousedown', function(e) {
                imageState.isDragging = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                imageState.isResizing = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                imageState.isRotating = true;
                const rect = imageWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                imageState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            range.deleteContents();
            range.insertNode(imageWrapper);
            
            if (!window.imageEventsAdded) {
                document.addEventListener('mousemove', handleImageMouseMove);
                
                document.addEventListener('mouseup', function() {
                    if (imageState.isDragging || imageState.isResizing || imageState.isRotating) {
                        imageState.isDragging = false;
                        imageState.isResizing = false;
                        imageState.isRotating = false;
                        saveState();
                    }
                });
                
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    const isImageClick = e.target.closest('.editor-image-wrapper') !== null;
                    
                    if (!isImageClick && imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                });
                
                window.imageEventsAdded = true;
            }
            
            activateImage(imageWrapper);
            saveState();
            return true;
        }
        
        function handleImageMouseMove(e) {
            if (!imageState.activeImage) return;
            
            if (imageState.isDragging) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentLeft = parseInt(imageState.activeImage.style.left) || 0;
                const currentTop = parseInt(imageState.activeImage.style.top) || 0;
                
                imageState.activeImage.style.position = 'relative';
                imageState.activeImage.style.left = `${currentLeft + dx}px`;
                imageState.activeImage.style.top = `${currentTop + dy}px`;
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isResizing) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentWidth = imageState.activeImage.offsetWidth;
                const currentHeight = imageState.activeImage.offsetHeight;
                
                imageState.activeImage.style.width = `${Math.max(100, currentWidth + dx)}px`;
                imageState.activeImage.style.height = `${Math.max(100, currentHeight + dy)}px`;
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isRotating) {
                const rect = imageState.activeImage.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - imageState.lastAngle;
                
                const currentAngle = parseFloat(imageState.activeImage.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                imageState.activeImage.style.transform = `rotate(${newAngle}deg)`;
                imageState.activeImage.dataset.angle = newAngle.toString();
                
                imageState.lastAngle = angle;
            }
        }
        
        function activateImage(imageWrapper) {
            if (imageState.activeImage && imageState.activeImage !== imageWrapper) {
                deactivateImage(imageState.activeImage);
            }
            
            imageState.activeImage = imageWrapper;
            
            const image = imageWrapper.querySelector('.editor-image-content');
            if (image) {
                image.style.border = '1px solid #4285f4';
                image.style.boxShadow = '0 0 8px rgba(66, 133, 244, 0.4)';
            }
            
            const selectionBorder = imageWrapper.querySelector('.image-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            const overlay = imageWrapper.querySelector('.image-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            imageWrapper.style.zIndex = '10';
            
            const controls = imageWrapper.querySelector('.image-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        function deactivateImage(imageWrapper) {
            if (imageWrapper) {
                const image = imageWrapper.querySelector('.editor-image-content');
                if (image) {
                    image.style.border = '1px solid #ccc';
                    image.style.boxShadow = '0 0 5px rgba(0,0,0,0.2)';
                }
                
                const selectionBorder = imageWrapper.querySelector('.image-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                const overlay = imageWrapper.querySelector('.image-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                imageWrapper.style.zIndex = '1';
                
                const controls = imageWrapper.querySelector('.image-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (imageState.activeImage === imageWrapper) {
                    imageState.activeImage = null;
                }
            }
        }
        
        function addImageStyles() {
            if (!document.getElementById('image-styles')) {
                const style = document.createElement('style');
                style.id = 'image-styles';
                style.textContent = `
                    .editor-image-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-image-content {
                        cursor: default;
                    }
                    
                    .image-selection-border {
                        pointer-events: none;
                    }
                    
                    .image-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-image-content {
                            background-color: #333;
                            border-color: #666;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            addImageStyles();
        });
        """
#################################################
    # Image JavaScript (continued)
    def image_js(self):
        """JavaScript for image functionality"""
        return """
        // Image variables (namespaced)
        const imageState = {
            activeImage: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            lastAngle: 0,
            imageCounter: 0
        };
        
        function insertImage(dataUrl) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            const range = selection.getRangeAt(0);
            
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.contentEditable = 'false';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.minWidth = '50px';
            imageWrapper.style.minHeight = '50px';
            imageWrapper.style.margin = '10px';
            imageWrapper.style.padding = '0';
            imageWrapper.style.zIndex = '1';
            imageWrapper.style.outline = 'none';
            
            imageState.imageCounter++;
            const imageId = 'image-' + imageState.imageCounter;
            imageWrapper.id = imageId;
            
            const image = document.createElement('img');
            image.className = 'editor-image-content';
            image.src = dataUrl;
            image.style.width = '100%';
            image.style.height = '100%';
            // Remove border
            image.style.border = 'none';
            // Remove shadow
            image.style.boxShadow = 'none';
            image.style.objectFit = 'contain';
            image.style.cursor = 'default';
            image.style.boxSizing = 'border-box';
            image.setAttribute('data-image-id', imageId);
            
            imageWrapper.dataset.angle = '0';
            imageWrapper.style.transform = 'rotate(0deg)';
            
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'image-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '1px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            const controls = document.createElement('div');
            controls.className = 'image-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '20px';
            moveHandle.style.height = '20px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '10px';
            moveHandle.title = 'Move';
            
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '20px';
            rotateHandle.style.height = '20px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '12px';
            rotateHandle.title = 'Rotate';
            
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '20px';
            resizeHandle.style.height = '20px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '12px';
            resizeHandle.title = 'Resize';
            
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            imageWrapper.appendChild(image);
            imageWrapper.appendChild(selectionBorder);
            imageWrapper.appendChild(controls);
            
            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            imageWrapper.appendChild(overlay);
            
            imageWrapper.addEventListener('mousedown', function(e) {
                const isControlClick = e.target.closest('.image-controls') !== null;
                
                if (isControlClick) {
                    return;
                }
                
                if (imageState.activeImage !== imageWrapper) {
                    if (imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                    activateImage(imageWrapper);
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            moveHandle.addEventListener('mousedown', function(e) {
                imageState.isDragging = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                imageState.isResizing = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                imageState.isRotating = true;
                const rect = imageWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                imageState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Add a load event handler to properly initialize the image dimensions
            image.onload = function() {
                const imgWidth = this.naturalWidth;
                const imgHeight = this.naturalHeight;
                
                // Set initial size proportionally
                // Don't make images too big initially; limit to reasonable size
                const maxWidth = 400;
                const maxHeight = 300;
                
                if (imgWidth > maxWidth || imgHeight > maxHeight) {
                    const ratio = Math.min(maxWidth / imgWidth, maxHeight / imgHeight);
                    imageWrapper.style.width = (imgWidth * ratio) + 'px';
                    imageWrapper.style.height = (imgHeight * ratio) + 'px';
                } else {
                    imageWrapper.style.width = imgWidth + 'px';
                    imageWrapper.style.height = imgHeight + 'px';
                }
                
                // Make sure the image maintains its aspect ratio when resized
                image.style.objectFit = 'contain';
                
                // Save state after initializing the image
                saveState();
            };
            
            range.deleteContents();
            range.insertNode(imageWrapper);
            
            if (!window.imageEventsAdded) {
                document.addEventListener('mousemove', handleImageMouseMove);
                
                document.addEventListener('mouseup', function() {
                    if (imageState.isDragging || imageState.isResizing || imageState.isRotating) {
                        imageState.isDragging = false;
                        imageState.isResizing = false;
                        imageState.isRotating = false;
                        saveState();
                    }
                });
                
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    const isImageClick = e.target.closest('.editor-image-wrapper') !== null;
                    
                    if (!isImageClick && imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                });
                
                window.imageEventsAdded = true;
            }
            
            activateImage(imageWrapper);
            // First save state happens after image loads
            return true;
        }
        
        function handleImageMouseMove(e) {
            if (!imageState.activeImage) return;
            
            if (imageState.isDragging) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentLeft = parseInt(imageState.activeImage.style.left) || 0;
                const currentTop = parseInt(imageState.activeImage.style.top) || 0;
                
                imageState.activeImage.style.position = 'relative';
                imageState.activeImage.style.left = `${currentLeft + dx}px`;
                imageState.activeImage.style.top = `${currentTop + dy}px`;
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isResizing) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentWidth = imageState.activeImage.offsetWidth;
                const currentHeight = imageState.activeImage.offsetHeight;
                
                // Get the original image element to maintain aspect ratio
                const imageElement = imageState.activeImage.querySelector('img');
                if (imageElement && imageElement.naturalWidth && imageElement.naturalHeight) {
                    // Calculate the aspect ratio of the original image
                    const aspectRatio = imageElement.naturalWidth / imageElement.naturalHeight;
                    
                    // Determine which dimension to prioritize based on the drag direction
                    if (Math.abs(dx) > Math.abs(dy)) {
                        // Prioritize width change
                        const newWidth = Math.max(50, currentWidth + dx);
                        imageState.activeImage.style.width = `${newWidth}px`;
                        imageState.activeImage.style.height = `${newWidth / aspectRatio}px`;
                    } else {
                        // Prioritize height change
                        const newHeight = Math.max(50, currentHeight + dy);
                        imageState.activeImage.style.height = `${newHeight}px`;
                        imageState.activeImage.style.width = `${newHeight * aspectRatio}px`;
                    }
                } else {
                    // Fallback if we can't get the natural dimensions
                    imageState.activeImage.style.width = `${Math.max(50, currentWidth + dx)}px`;
                    imageState.activeImage.style.height = `${Math.max(50, currentHeight + dy)}px`;
                }
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isRotating) {
                const rect = imageState.activeImage.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - imageState.lastAngle;
                
                const currentAngle = parseFloat(imageState.activeImage.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                imageState.activeImage.style.transform = `rotate(${newAngle}deg)`;
                imageState.activeImage.dataset.angle = newAngle.toString();
                
                imageState.lastAngle = angle;
            }
        }
        
        function activateImage(imageWrapper) {
            if (imageState.activeImage && imageState.activeImage !== imageWrapper) {
                deactivateImage(imageState.activeImage);
            }
            
            imageState.activeImage = imageWrapper;
            
            // Show selection border
            const selectionBorder = imageWrapper.querySelector('.image-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = imageWrapper.querySelector('.image-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            imageWrapper.style.zIndex = '10';
            
            // Show controls
            const controls = imageWrapper.querySelector('.image-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        function deactivateImage(imageWrapper) {
            if (imageWrapper) {
                // Hide selection border
                const selectionBorder = imageWrapper.querySelector('.image-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = imageWrapper.querySelector('.image-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                imageWrapper.style.zIndex = '1';
                
                // Hide controls
                const controls = imageWrapper.querySelector('.image-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (imageState.activeImage === imageWrapper) {
                    imageState.activeImage = null;
                }
            }
        }
        
        function addImageStyles() {
            if (!document.getElementById('image-styles')) {
                const style = document.createElement('style');
                style.id = 'image-styles';
                style.textContent = `
                    .editor-image-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-image-content {
                        cursor: default;
                    }
                    
                    .image-selection-border {
                        pointer-events: none;
                    }
                    
                    .image-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-image-content {
                            background-color: #333;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        document.addEventListener('DOMContentLoaded', function() {
            addImageStyles();
        });
        """

    # This function allows text and image functions to work together
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
        {self.text_box_js()}
        {self.image_js()}
        {self.init_editor_js()}
        """
    # Text Box JavaScript
    def text_box_js(self):
        """JavaScript for text box functionality"""
        return """
        // Text box variables
        let activeTextBox = null;
        let isDragging = false;
        let isResizing = false;
        let isRotating = false;
        let lastX = 0;
        let lastY = 0;
        let lastAngle = 0;
        let textBoxCounter = 0;
        
        // Insert a text box at the cursor position
        function insertTextBox() {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Get the current selection range
            const range = selection.getRangeAt(0);
            
            // Create a wrapper to hold the text box
            const textBoxWrapper = document.createElement('div');
            textBoxWrapper.className = 'editor-text-box-wrapper';
            textBoxWrapper.contentEditable = 'false'; // Make the wrapper non-editable
            textBoxWrapper.style.position = 'relative';
            textBoxWrapper.style.display = 'inline-block';
            textBoxWrapper.style.minWidth = '50px';
            textBoxWrapper.style.minHeight = '30px';
            textBoxWrapper.style.margin = '10px';
            textBoxWrapper.style.padding = '0';
            textBoxWrapper.style.zIndex = '1';
            textBoxWrapper.style.outline = 'none';
            
            // Create a unique ID for this text box
            textBoxCounter++;
            const textBoxId = 'text-box-' + textBoxCounter;
            textBoxWrapper.id = textBoxId;
            
            // Create the actual editable text box inside the wrapper
            const textBox = document.createElement('div');
            textBox.className = 'editor-text-box-content';
            textBox.contentEditable = 'true';
            textBox.style.width = '100%';
            textBox.style.height = '100%';
            // Remove border in normal state
            textBox.style.border = 'none';
            textBox.style.padding = '10px';
            textBox.style.backgroundColor = 'white';
            // Remove shadow in normal state
            textBox.style.boxShadow = 'none';
            textBox.style.overflow = 'hidden';
            textBox.style.cursor = 'text';
            textBox.style.boxSizing = 'border-box';
            textBox.innerHTML = '';
            textBox.setAttribute('data-textbox-id', textBoxId);
            
            // Store rotation angle in the wrapper
            textBoxWrapper.dataset.angle = '0';
            textBoxWrapper.style.transform = 'rotate(0deg)';
            
            // Create a visual border for selection that's completely hidden by default
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'text-box-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '1px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            // Create and add the controls container
            const controls = document.createElement('div');
            controls.className = 'text-box-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            // Create and add the move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '20px';
            moveHandle.style.height = '20px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '10px';
            moveHandle.title = 'Move';
            
            // Create and add the rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '20px';
            rotateHandle.style.height = '20px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '12px';
            rotateHandle.title = 'Rotate';
            
            // Create and add the resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '20px';
            resizeHandle.style.height = '20px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '12px';
            resizeHandle.title = 'Resize';
            
            // Add handles to controls
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            // Add elements to the wrapper
            textBoxWrapper.appendChild(textBox);
            textBoxWrapper.appendChild(selectionBorder);
            textBoxWrapper.appendChild(controls);
            
            // Create a transparent clickable overlay for better selection
            const overlay = document.createElement('div');
            overlay.className = 'text-box-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px'; // Extended hit area
            overlay.style.left = '-15px'; // Extended hit area
            overlay.style.right = '-15px'; // Extended hit area
            overlay.style.bottom = '-15px'; // Extended hit area
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997'; // Below the selection border but above content
            overlay.style.display = 'none'; // Initially hidden
            
            textBoxWrapper.appendChild(overlay);
            
            // Set up event handlers for the text box wrapper
            
            // Prevent the default behavior of Enter key in the text box
            textBox.addEventListener('keydown', function(e) {
                // Let the Enter key work normally inside the text box
                if (e.key === 'Enter') {
                    e.stopPropagation(); // Don't let it bubble up to document
                    // Default behavior of creating a new line is fine
                }
            });
            
            // Text box wrapper click event
            textBoxWrapper.addEventListener('mousedown', function(e) {
                // Determine if click is on the content or controls
                const contentBox = textBoxWrapper.querySelector('.editor-text-box-content');
                const isContentClick = contentBox && (e.target === contentBox || contentBox.contains(e.target));
                const isControlClick = e.target.closest('.text-box-controls') !== null;
                
                // If clicking on controls, let the specific handler deal with it
                if (isControlClick) {
                    return;
                }
                
                // Ensure this text box is active
                if (activeTextBox !== textBoxWrapper) {
                    if (activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                    activateTextBox(textBoxWrapper);
                }
                
                // If clicking inside the content, allow normal text editing
                if (isContentClick) {
                    return;
                }
                
                // If clicking on wrapper but not content, prevent default
                e.preventDefault();
                e.stopPropagation();
            });
            
            // Handle move
            moveHandle.addEventListener('mousedown', function(e) {
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle resize
            resizeHandle.addEventListener('mousedown', function(e) {
                isResizing = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle rotate
            rotateHandle.addEventListener('mousedown', function(e) {
                isRotating = true;
                const rect = textBoxWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Insert the text box at the current selection
            range.deleteContents();
            range.insertNode(textBoxWrapper);
            
            // Create a new range and place the cursor inside the text box
            const newRange = document.createRange();
            newRange.selectNodeContents(textBox);
            newRange.collapse(true); // Collapse to the start of the content
            selection.removeAllRanges();
            selection.addRange(newRange);
            
            // Focus the text box
            textBox.focus();
            
            // Add mouse event listeners to the document if not already added
            if (!window.textBoxEventsAdded) {
                // Handle mouse movement for dragging, resizing, and rotating
                document.addEventListener('mousemove', handleTextBoxMouseMove);
                
                // Handle mouse up to stop dragging, resizing, and rotating
                document.addEventListener('mouseup', function() {
                    if (isDragging || isResizing || isRotating) {
                        isDragging = false;
                        isResizing = false;
                        isRotating = false;
                        
                        // If we made changes, save state
                        saveState();
                    }
                });
                
                // Handle clicks on the editor to deactivate text boxes
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    // Check if the click is directly on the editor or a non-text-box element
                    const isTextBoxClick = e.target.closest('.editor-text-box-wrapper') !== null;
                    
                    if (!isTextBoxClick && activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                });
                
                // Mark that we've added the event handlers
                window.textBoxEventsAdded = true;
            }
            
            // Enable text box controls
            activateTextBox(textBoxWrapper);
            
            // Save state after insertion
            saveState();
            
            return true;
        }
        
        // Handle mouse movement for dragging, resizing, and rotating
        function handleTextBoxMouseMove(e) {
            if (!activeTextBox) return;
            
            if (isDragging) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current position or default to 0
                const currentLeft = parseInt(activeTextBox.style.left) || 0;
                const currentTop = parseInt(activeTextBox.style.top) || 0;
                
                // Update position
                activeTextBox.style.position = 'relative';
                activeTextBox.style.left = `${currentLeft + dx}px`;
                activeTextBox.style.top = `${currentTop + dy}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isResizing) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current dimensions
                const currentWidth = activeTextBox.offsetWidth;
                const currentHeight = activeTextBox.offsetHeight;
                
                // Apply minimum sizes and update directly
                activeTextBox.style.width = `${Math.max(50, currentWidth + dx)}px`;
                activeTextBox.style.height = `${Math.max(30, currentHeight + dy)}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isRotating) {
                const rect = activeTextBox.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - lastAngle;
                
                const currentAngle = parseFloat(activeTextBox.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                activeTextBox.style.transform = `rotate(${newAngle}deg)`;
                activeTextBox.dataset.angle = newAngle.toString();
                
                lastAngle = angle;
            }
        }
        
        // Activate a text box (show controls)
        function activateTextBox(textBoxWrapper) {
            if (activeTextBox && activeTextBox !== textBoxWrapper) {
                deactivateTextBox(activeTextBox);
            }
            
            activeTextBox = textBoxWrapper;
            
            // Show selection border (dashed outline)
            const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = textBoxWrapper.querySelector('.text-box-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            textBoxWrapper.style.zIndex = '10';
            
            // Show controls
            const controls = textBoxWrapper.querySelector('.text-box-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        // Deactivate a text box (hide controls)
        function deactivateTextBox(textBoxWrapper) {
            if (textBoxWrapper) {
                // Hide selection border
                const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = textBoxWrapper.querySelector('.text-box-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                textBoxWrapper.style.zIndex = '1';
                
                // Hide controls
                const controls = textBoxWrapper.querySelector('.text-box-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (activeTextBox === textBoxWrapper) {
                    activeTextBox = null;
                }
            }
        }
        
        // Add global CSS for text boxes
        function addTextBoxStyles() {
            if (!document.getElementById('text-box-styles')) {
                const style = document.createElement('style');
                style.id = 'text-box-styles';
                style.textContent = `
                    .editor-text-box-content:focus {
                        outline: none;
                    }
                    
                    .editor-text-box-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-text-box-wrapper .editor-text-box-content {
                        cursor: text;
                    }
                    
                    .text-box-selection-border {
                        pointer-events: none;
                    }
                    
                    .text-box-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-text-box-content {
                            background-color: #333;
                            color: #fff;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // Initialize text box functionality
        document.addEventListener('DOMContentLoaded', function() {
            addTextBoxStyles();
        });
        """
        
################################
    # JavaScript functions for image handling
    def image_js(self):
        """JavaScript for image functionality"""
        return """
        // Image variables (namespaced)
        const imageState = {
            activeImage: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            lastAngle: 0,
            imageCounter: 0
        };
        
        // Insert an image at the cursor position
        function insertImage(dataUrl) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            const range = selection.getRangeAt(0);
            
            // Create an image element with all needed components
            const imageWrapper = createImageElement(dataUrl);
            
            // Insert the image at the current selection
            range.deleteContents();
            range.insertNode(imageWrapper);
            
            // Add global event listeners if not already added
            setupImageEventListeners();
            
            // Activate the image (show controls)
            activateImage(imageWrapper);
            
            // First save state happens after image loads
            return true;
        }
        
        // Create a complete image element with all components
        function createImageElement(dataUrl) {
            const imageWrapper = document.createElement('div');
            imageWrapper.className = 'editor-image-wrapper';
            imageWrapper.contentEditable = 'false';
            imageWrapper.style.position = 'relative';
            imageWrapper.style.display = 'inline-block';
            imageWrapper.style.minWidth = '50px';
            imageWrapper.style.minHeight = '50px';
            imageWrapper.style.margin = '10px';
            imageWrapper.style.padding = '0';
            imageWrapper.style.zIndex = '1';
            imageWrapper.style.outline = 'none';
            
            imageState.imageCounter++;
            const imageId = 'image-' + imageState.imageCounter;
            imageWrapper.id = imageId;
            imageWrapper.setAttribute('data-image-element', 'true');
            
            const image = document.createElement('img');
            image.className = 'editor-image-content';
            image.src = dataUrl;
            image.style.width = '100%';
            image.style.height = '100%';
            image.style.border = 'none';
            image.style.boxShadow = 'none';
            image.style.objectFit = 'contain';
            image.style.cursor = 'default';
            image.style.boxSizing = 'border-box';
            image.setAttribute('data-image-id', imageId);
            
            imageWrapper.dataset.angle = '0';
            imageWrapper.style.transform = 'rotate(0deg)';
            
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'image-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '1px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            const controls = document.createElement('div');
            controls.className = 'image-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '20px';
            moveHandle.style.height = '20px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '10px';
            moveHandle.title = 'Move';
            
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '20px';
            rotateHandle.style.height = '20px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '12px';
            rotateHandle.title = 'Rotate';
            
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '20px';
            resizeHandle.style.height = '20px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '12px';
            resizeHandle.title = 'Resize';
            
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            imageWrapper.appendChild(image);
            imageWrapper.appendChild(selectionBorder);
            imageWrapper.appendChild(controls);
            
            const overlay = document.createElement('div');
            overlay.className = 'image-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            imageWrapper.appendChild(overlay);
            
            imageWrapper.addEventListener('mousedown', function(e) {
                const isControlClick = e.target.closest('.image-controls') !== null;
                
                if (isControlClick) {
                    return;
                }
                
                if (imageState.activeImage !== imageWrapper) {
                    if (imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                    activateImage(imageWrapper);
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            moveHandle.addEventListener('mousedown', function(e) {
                imageState.isDragging = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                imageState.isResizing = true;
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                imageState.isRotating = true;
                const rect = imageWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                imageState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Add a load event handler to properly initialize the image dimensions
            image.onload = function() {
                const imgWidth = this.naturalWidth;
                const imgHeight = this.naturalHeight;
                
                // Set initial size proportionally
                // Don't make images too big initially; limit to reasonable size
                const maxWidth = 400;
                const maxHeight = 300;
                
                if (imgWidth > maxWidth || imgHeight > maxHeight) {
                    const ratio = Math.min(maxWidth / imgWidth, maxHeight / imgHeight);
                    imageWrapper.style.width = (imgWidth * ratio) + 'px';
                    imageWrapper.style.height = (imgHeight * ratio) + 'px';
                } else {
                    imageWrapper.style.width = imgWidth + 'px';
                    imageWrapper.style.height = imgHeight + 'px';
                }
                
                // Make sure the image maintains its aspect ratio when resized
                image.style.objectFit = 'contain';
                
                // Save state after initializing the image
                saveState();
            };
            
            return imageWrapper;
        }
        
        // Reconstruct an image element after paste
        function reconstructImage(element) {
            // Get the img element inside the wrapper
            const imgElement = element.querySelector('img');
            if (!imgElement || !imgElement.src) {
                // Not enough info to reconstruct
                return;
            }
            
            // Save attributes
            const src = imgElement.src;
            const width = element.style.width;
            const height = element.style.height;
            const left = element.style.left;
            const top = element.style.top;
            const transform = element.style.transform;
            const angle = element.dataset.angle || '0';
            
            // Create a new properly structured image element
            const newImage = createImageElement(src);
            
            // Apply saved attributes
            if (width) newImage.style.width = width;
            if (height) newImage.style.height = height;
            if (left) newImage.style.left = left;
            if (top) newImage.style.top = top;
            if (transform) newImage.style.transform = transform;
            newImage.dataset.angle = angle;
            
            // Replace the old element with the new one
            element.parentNode.replaceChild(newImage, element);
            
            // Save state after reconstruction
            saveState();
        }
        
        // Set up global event listeners
        function setupImageEventListeners() {
            if (!window.imageEventsAdded) {
                document.addEventListener('mousemove', handleImageMouseMove);
                
                document.addEventListener('mouseup', function() {
                    if (imageState.isDragging || imageState.isResizing || imageState.isRotating) {
                        imageState.isDragging = false;
                        imageState.isResizing = false;
                        imageState.isRotating = false;
                        saveState();
                    }
                });
                
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    const isImageClick = e.target.closest('.editor-image-wrapper') !== null;
                    
                    if (!isImageClick && imageState.activeImage) {
                        deactivateImage(imageState.activeImage);
                    }
                });
                
                // Handle copy events
                document.addEventListener('copy', function(e) {
                    if (imageState.activeImage) {
                        const selection = window.getSelection();
                        const range = selection.getRangeCount() > 0 ? selection.getRangeAt(0) : null;
                        
                        // Check if the active image is within the current selection
                        if (range && range.intersectsNode(imageState.activeImage)) {
                            // Mark for copy
                            imageState.activeImage.setAttribute('data-image-copy', 'true');
                            
                            // Remove after copy
                            setTimeout(function() {
                                imageState.activeImage.removeAttribute('data-image-copy');
                            }, 0);
                        }
                    }
                });
                
                // Handle paste to reconstruct images
                document.addEventListener('paste', function(e) {
                    setTimeout(function() {
                        // Look for any divs that might be images
                        const editor = document.getElementById('editor');
                        
                        // Find all image elements that need reconstruction
                        // This includes both divs with img children and divs marked as image elements
                        const possibleImages = Array.from(editor.querySelectorAll('div')).filter(div => {
                            return (div.querySelector('img') && !div.querySelector('.image-controls')) || 
                                   (div.classList.contains('editor-image-wrapper') && !div.querySelector('.image-controls'));
                        });
                        
                        possibleImages.forEach(function(element) {
                            reconstructImage(element);
                        });
                    }, 0);
                });
                
                window.imageEventsAdded = true;
            }
        }
        
        function handleImageMouseMove(e) {
            if (!imageState.activeImage) return;
            
            if (imageState.isDragging) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentLeft = parseInt(imageState.activeImage.style.left) || 0;
                const currentTop = parseInt(imageState.activeImage.style.top) || 0;
                
                imageState.activeImage.style.position = 'relative';
                imageState.activeImage.style.left = `${currentLeft + dx}px`;
                imageState.activeImage.style.top = `${currentTop + dy}px`;
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isResizing) {
                const dx = e.clientX - imageState.lastX;
                const dy = e.clientY - imageState.lastY;
                
                const currentWidth = imageState.activeImage.offsetWidth;
                const currentHeight = imageState.activeImage.offsetHeight;
                
                // Get the original image element to maintain aspect ratio
                const imageElement = imageState.activeImage.querySelector('img');
                if (imageElement && imageElement.naturalWidth && imageElement.naturalHeight) {
                    // Calculate the aspect ratio of the original image
                    const aspectRatio = imageElement.naturalWidth / imageElement.naturalHeight;
                    
                    // Determine which dimension to prioritize based on the drag direction
                    if (Math.abs(dx) > Math.abs(dy)) {
                        // Prioritize width change
                        const newWidth = Math.max(50, currentWidth + dx);
                        imageState.activeImage.style.width = `${newWidth}px`;
                        imageState.activeImage.style.height = `${newWidth / aspectRatio}px`;
                    } else {
                        // Prioritize height change
                        const newHeight = Math.max(50, currentHeight + dy);
                        imageState.activeImage.style.height = `${newHeight}px`;
                        imageState.activeImage.style.width = `${newHeight * aspectRatio}px`;
                    }
                } else {
                    // Fallback if we can't get the natural dimensions
                    imageState.activeImage.style.width = `${Math.max(50, currentWidth + dx)}px`;
                    imageState.activeImage.style.height = `${Math.max(50, currentHeight + dy)}px`;
                }
                
                imageState.lastX = e.clientX;
                imageState.lastY = e.clientY;
            }
            else if (imageState.isRotating) {
                const rect = imageState.activeImage.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - imageState.lastAngle;
                
                const currentAngle = parseFloat(imageState.activeImage.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                imageState.activeImage.style.transform = `rotate(${newAngle}deg)`;
                imageState.activeImage.dataset.angle = newAngle.toString();
                
                imageState.lastAngle = angle;
            }
        }
        
        function activateImage(imageWrapper) {
            if (imageState.activeImage && imageState.activeImage !== imageWrapper) {
                deactivateImage(imageState.activeImage);
            }
            
            imageState.activeImage = imageWrapper;
            
            // Show selection border
            const selectionBorder = imageWrapper.querySelector('.image-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = imageWrapper.querySelector('.image-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            imageWrapper.style.zIndex = '10';
            
            // Show controls
            const controls = imageWrapper.querySelector('.image-controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        function deactivateImage(imageWrapper) {
            if (imageWrapper) {
                // Hide selection border
                const selectionBorder = imageWrapper.querySelector('.image-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = imageWrapper.querySelector('.image-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                imageWrapper.style.zIndex = '1';
                
                // Hide controls
                const controls = imageWrapper.querySelector('.image-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (imageState.activeImage === imageWrapper) {
                    imageState.activeImage = null;
                }
            }
        }
        
        function addImageStyles() {
            if (!document.getElementById('image-styles')) {
                const style = document.createElement('style');
                style.id = 'image-styles';
                style.textContent = `
                    .editor-image-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-image-content {
                        cursor: default;
                    }
                    
                    .image-selection-border {
                        pointer-events: none;
                    }
                    
                    .image-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .image-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-image-content {
                            background-color: #333;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // Initialize image functionality
        document.addEventListener('DOMContentLoaded', function() {
            addImageStyles();
            setupImageEventListeners();
        });
        """

    # JavaScript functions for text box handling
    def text_box_js(self):
        """JavaScript for text box functionality"""
        return """
        // Text box variables
        let activeTextBox = null;
        let isDragging = false;
        let isResizing = false;
        let isRotating = false;
        let lastX = 0;
        let lastY = 0;
        let lastAngle = 0;
        let textBoxCounter = 0;
        
        // Insert a text box at the cursor position
        function insertTextBox() {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            // Get the current selection range
            const range = selection.getRangeAt(0);
            
            // Create a wrapper to hold the text box
            const textBoxWrapper = createTextBoxElement();
            
            // Insert the text box at the current selection
            range.deleteContents();
            range.insertNode(textBoxWrapper);
            
            // Create a new range and place the cursor inside the text box
            const textBox = textBoxWrapper.querySelector('.editor-text-box-content');
            const newRange = document.createRange();
            newRange.selectNodeContents(textBox);
            newRange.collapse(true); // Collapse to the start of the content
            selection.removeAllRanges();
            selection.addRange(newRange);
            
            // Focus the text box
            textBox.focus();
            
            // Add mouse event listeners to the document if not already added
            setupGlobalEventListeners();
            
            // Enable text box controls
            activateTextBox(textBoxWrapper);
            
            // Save state after insertion
            saveState();
            
            return true;
        }
        
        // Create a text box element with all needed properties and event handlers
        function createTextBoxElement(content = '') {
            // Create a wrapper to hold the text box
            const textBoxWrapper = document.createElement('div');
            textBoxWrapper.className = 'editor-text-box-wrapper';
            textBoxWrapper.contentEditable = 'false'; // Make the wrapper non-editable
            textBoxWrapper.style.position = 'relative';
            textBoxWrapper.style.display = 'inline-block';
            textBoxWrapper.style.minWidth = '50px';
            textBoxWrapper.style.minHeight = '30px';
            textBoxWrapper.style.margin = '10px';
            textBoxWrapper.style.padding = '0';
            textBoxWrapper.style.zIndex = '1';
            textBoxWrapper.style.outline = 'none';
            
            // Create a unique ID for this text box
            textBoxCounter++;
            const textBoxId = 'text-box-' + textBoxCounter;
            textBoxWrapper.id = textBoxId;
            
            // Create the actual editable text box inside the wrapper
            const textBox = document.createElement('div');
            textBox.className = 'editor-text-box-content';
            textBox.contentEditable = 'true';
            textBox.style.width = '100%';
            textBox.style.height = '100%';
            textBox.style.border = 'none';
            textBox.style.padding = '10px';
            textBox.style.backgroundColor = 'white';
            textBox.style.boxShadow = 'none';
            textBox.style.overflow = 'hidden';
            textBox.style.cursor = 'text';
            textBox.style.boxSizing = 'border-box';
            textBox.innerHTML = content || '';
            textBox.setAttribute('data-textbox-id', textBoxId);
            
            // Store rotation angle in the wrapper
            textBoxWrapper.dataset.angle = '0';
            textBoxWrapper.style.transform = 'rotate(0deg)';
            
            // Create a visual border for selection that's completely hidden by default
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'text-box-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '1px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            // Create and add the controls container
            const controls = document.createElement('div');
            controls.className = 'text-box-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            // Create and add the move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '20px';
            moveHandle.style.height = '20px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '10px';
            moveHandle.title = 'Move';
            
            // Create and add the rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '20px';
            rotateHandle.style.height = '20px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '12px';
            rotateHandle.title = 'Rotate';
            
            // Create and add the resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '20px';
            resizeHandle.style.height = '20px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '12px';
            resizeHandle.title = 'Resize';
            
            // Add handles to controls
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            // Add elements to the wrapper
            textBoxWrapper.appendChild(textBox);
            textBoxWrapper.appendChild(selectionBorder);
            textBoxWrapper.appendChild(controls);
            
            // Create a transparent clickable overlay for better selection
            const overlay = document.createElement('div');
            overlay.className = 'text-box-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px'; // Extended hit area
            overlay.style.left = '-15px'; // Extended hit area
            overlay.style.right = '-15px'; // Extended hit area
            overlay.style.bottom = '-15px'; // Extended hit area
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997'; // Below the selection border but above content
            overlay.style.display = 'none'; // Initially hidden
            
            textBoxWrapper.appendChild(overlay);
            
            // Set up event handlers for the text box wrapper
            
            // Prevent the default behavior of Enter key in the text box
            textBox.addEventListener('keydown', function(e) {
                // Let the Enter key work normally inside the text box
                if (e.key === 'Enter') {
                    e.stopPropagation(); // Don't let it bubble up to document
                    // Default behavior of creating a new line is fine
                }
            });
            
            // Handle focus and blur on the content
            textBox.addEventListener('focus', function() {
                // When the text box content gets focus, make the parent wrapper active
                if (activeTextBox !== textBoxWrapper) {
                    if (activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                    activateTextBox(textBoxWrapper, false); // Activate without showing controls
                }
            });
            
            // Text box wrapper click event
            textBoxWrapper.addEventListener('mousedown', function(e) {
                // Determine if click is on the content or controls
                const contentBox = textBoxWrapper.querySelector('.editor-text-box-content');
                const isContentClick = contentBox && (e.target === contentBox || contentBox.contains(e.target));
                const isControlClick = e.target.closest('.text-box-controls') !== null;
                
                // If clicking on controls, let the specific handler deal with it
                if (isControlClick) {
                    return;
                }
                
                // Ensure this text box is active
                if (activeTextBox !== textBoxWrapper) {
                    if (activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                    activateTextBox(textBoxWrapper, !isContentClick); // Show controls only if not clicking content
                } else if (!isContentClick) {
                    // Toggle controls visibility when clicking on the wrapper (not content)
                    const controls = textBoxWrapper.querySelector('.text-box-controls');
                    if (controls.style.display === 'none') {
                        showControls(textBoxWrapper);
                    } else {
                        hideControls(textBoxWrapper);
                    }
                }
                
                // If clicking inside the content, allow normal text editing
                if (isContentClick) {
                    return;
                }
                
                // If clicking on wrapper but not content, prevent default
                e.preventDefault();
                e.stopPropagation();
            });
            
            // Handle move
            moveHandle.addEventListener('mousedown', function(e) {
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle resize
            resizeHandle.addEventListener('mousedown', function(e) {
                isResizing = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Handle rotate
            rotateHandle.addEventListener('mousedown', function(e) {
                isRotating = true;
                const rect = textBoxWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            return textBoxWrapper;
        }
        
        // Set up global event listeners for all text boxes
        function setupGlobalEventListeners() {
            if (!window.textBoxEventsAdded) {
                // Handle mouse movement for dragging, resizing, and rotating
                document.addEventListener('mousemove', handleTextBoxMouseMove);
                
                // Handle mouse up to stop dragging, resizing, and rotating
                document.addEventListener('mouseup', function() {
                    if (isDragging || isResizing || isRotating) {
                        isDragging = false;
                        isResizing = false;
                        isRotating = false;
                        
                        // If we made changes, save state
                        saveState();
                    }
                });
                
                // Handle clicks on the editor to deactivate text boxes
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    // Check if the click is directly on the editor or a non-text-box element
                    const isTextBoxClick = e.target.closest('.editor-text-box-wrapper') !== null;
                    
                    if (!isTextBoxClick && activeTextBox) {
                        deactivateTextBox(activeTextBox);
                    }
                });
                
                // Handle copy events to properly handle text boxes
                document.addEventListener('copy', function(e) {
                    // If we're copying a selection that contains our text box
                    if (activeTextBox) {
                        const selection = window.getSelection();
                        const range = selection.getRangeCount() > 0 ? selection.getRangeAt(0) : null;
                        
                        // Check if we're just selecting inside the text box content
                        const contentBox = activeTextBox.querySelector('.editor-text-box-content');
                        if (contentBox && range && contentBox.contains(range.commonAncestorContainer)) {
                            // This is a normal text selection inside the text box, allow default behavior
                            return;
                        }
                        
                        // Check if the active text box is within the current selection
                        if (range && range.intersectsNode(activeTextBox)) {
                            // If we're copying the text box itself, mark it with a data attribute
                            activeTextBox.setAttribute('data-textbox-copy', 'true');
                            
                            // After copy is done, remove the attribute
                            setTimeout(function() {
                                activeTextBox.removeAttribute('data-textbox-copy');
                            }, 0);
                        }
                    }
                });
                
                // Handle paste to properly reconstruct text boxes
                document.addEventListener('paste', function(e) {
                    setTimeout(function() {
                        // Look for any divs that might have been text boxes
                        const editor = document.getElementById('editor');
                        const possibleTextBoxes = editor.querySelectorAll('div.editor-text-box-wrapper');
                        
                        possibleTextBoxes.forEach(function(element) {
                            // Check if this is a pasted text box that needs reconstruction
                            if (!element.querySelector('.text-box-controls')) {
                                reconstructTextBox(element);
                            }
                        });
                    }, 0);
                });
                
                // Mark that we've added the event handlers
                window.textBoxEventsAdded = true;
            }
        }
        
        // Reconstruct a text box after paste
        function reconstructTextBox(element) {
            // Save content and attributes
            const content = element.innerHTML;
            const id = element.id || ('text-box-' + (++textBoxCounter));
            const width = element.style.width;
            const height = element.style.height;
            const left = element.style.left;
            const top = element.style.top;
            const transform = element.style.transform;
            const angle = element.dataset.angle || '0';
            
            // Create a new properly structured text box
            const newTextBox = createTextBoxElement(content);
            
            // Apply saved attributes
            if (width) newTextBox.style.width = width;
            if (height) newTextBox.style.height = height;
            if (left) newTextBox.style.left = left;
            if (top) newTextBox.style.top = top;
            if (transform) newTextBox.style.transform = transform;
            newTextBox.dataset.angle = angle;
            
            // Replace the old element with the new one
            element.parentNode.replaceChild(newTextBox, element);
            
            // Make sure event listeners are set up
            setupGlobalEventListeners();
            
            // Save state after reconstruction
            saveState();
        }
        
        // Handle mouse movement for dragging, resizing, and rotating
        function handleTextBoxMouseMove(e) {
            if (!activeTextBox) return;
            
            if (isDragging) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current position or default to 0
                const currentLeft = parseInt(activeTextBox.style.left) || 0;
                const currentTop = parseInt(activeTextBox.style.top) || 0;
                
                // Update position
                activeTextBox.style.position = 'relative';
                activeTextBox.style.left = `${currentLeft + dx}px`;
                activeTextBox.style.top = `${currentTop + dy}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isResizing) {
                const dx = e.clientX - lastX;
                const dy = e.clientY - lastY;
                
                // Get current dimensions
                const currentWidth = activeTextBox.offsetWidth;
                const currentHeight = activeTextBox.offsetHeight;
                
                // Apply minimum sizes and update directly
                activeTextBox.style.width = `${Math.max(50, currentWidth + dx)}px`;
                activeTextBox.style.height = `${Math.max(30, currentHeight + dy)}px`;
                
                lastX = e.clientX;
                lastY = e.clientY;
            }
            else if (isRotating) {
                const rect = activeTextBox.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - lastAngle;
                
                const currentAngle = parseFloat(activeTextBox.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                activeTextBox.style.transform = `rotate(${newAngle}deg)`;
                activeTextBox.dataset.angle = newAngle.toString();
                
                lastAngle = angle;
            }
        }
        
        // Show controls for a text box
        function showControls(textBoxWrapper) {
            const controls = textBoxWrapper.querySelector('.text-box-controls');
            if (controls) {
                controls.style.display = 'block';
            }
            
            const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
        }
        
        // Hide controls for a text box
        function hideControls(textBoxWrapper) {
            const controls = textBoxWrapper.querySelector('.text-box-controls');
            if (controls) {
                controls.style.display = 'none';
            }
        }
        
        // Activate a text box (optionally show controls)
        function activateTextBox(textBoxWrapper, showControlsFlag = true) {
            if (activeTextBox && activeTextBox !== textBoxWrapper) {
                deactivateTextBox(activeTextBox);
            }
            
            activeTextBox = textBoxWrapper;
            
            // Show selection border (dashed outline)
            const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = textBoxWrapper.querySelector('.text-box-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            textBoxWrapper.style.zIndex = '10';
            
            // Optionally show controls
            if (showControlsFlag) {
                showControls(textBoxWrapper);
            }
        }
        
        // Deactivate a text box (hide controls)
        function deactivateTextBox(textBoxWrapper) {
            if (textBoxWrapper) {
                // Hide selection border
                const selectionBorder = textBoxWrapper.querySelector('.text-box-selection-border');
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = textBoxWrapper.querySelector('.text-box-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                // Hide controls
                hideControls(textBoxWrapper);
                
                textBoxWrapper.style.zIndex = '1';
                
                if (activeTextBox === textBoxWrapper) {
                    activeTextBox = null;
                }
            }
        }
        
        // Add global CSS for text boxes
        function addTextBoxStyles() {
            if (!document.getElementById('text-box-styles')) {
                const style = document.createElement('style');
                style.id = 'text-box-styles';
                style.textContent = `
                    .editor-text-box-content:focus {
                        outline: none;
                    }
                    
                    .editor-text-box-wrapper {
                        break-inside: avoid;
                        page-break-inside: avoid;
                        cursor: pointer;
                        box-sizing: border-box;
                    }
                    
                    .editor-text-box-wrapper .editor-text-box-content {
                        cursor: text;
                    }
                    
                    .text-box-selection-border {
                        pointer-events: none;
                    }
                    
                    .text-box-controls .move-handle {
                        left: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .rotate-handle {
                        right: -12px;
                        top: -12px;
                    }
                    
                    .text-box-controls .resize-handle {
                        right: -12px;
                        bottom: -12px;
                    }
                    
                    @media (prefers-color-scheme: dark) {
                        .editor-text-box-content {
                            background-color: #333;
                            color: #fff;
                        }
                    }
                `;
                document.head.appendChild(style);
            }
        }
        
        // Initialize text box functionality
        document.addEventListener('DOMContentLoaded', function() {
            addTextBoxStyles();
            setupGlobalEventListeners();
        });
        """
        
###########################
    # Python handler for table insertion
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
        width_combo.set_selected(1)  # Default to 100%
        
        width_box.append(width_label)
        width_box.append(width_combo)
        content_box.append(width_box)
        
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
            width_options.get_string(width_combo.get_selected())
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Set dialog content and present
        dialog.set_child(content_box)
        dialog.present(win)
        
    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option):
        """Handle response from the table dialog"""
        dialog.close()
        
        # Prepare the width value
        width_value = "auto"
        if width_option != "Auto":
            width_value = width_option
        
        # Execute JavaScript to insert the table
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}");
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table inserted")


    # Update get_editor_js to include the table functionality
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
        {self.text_box_js()}
        {self.image_js()}
        {self.table_js()}
        {self.init_editor_js()}
        """


    # Continuation of create_file_toolbar method with table button added
    def create_file_toolbar(self, win):
        """Create the file toolbar with linked button groups"""
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        # --- File operations group (New, Open, Save, Save As) ---
        file_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_group.add_css_class("linked")  # Apply linked styling
        file_group.set_margin_start(4)

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
        file_toolbar.append(file_group)
        
        # --- Edit operations group (Cut, Copy, Paste, Print) ---
        edit_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        edit_group.add_css_class("linked")  # Apply linked styling
        edit_group.set_margin_start(6)
        
        # Cut button
        cut_button = Gtk.Button(icon_name="edit-cut-symbolic")
        cut_button.set_tooltip_text("Cut")
        cut_button.connect("clicked", lambda btn: self.on_cut_clicked(win, btn))

        # Copy button
        copy_button = Gtk.Button(icon_name="edit-copy-symbolic")
        copy_button.set_tooltip_text("Copy")
        copy_button.connect("clicked", lambda btn: self.on_copy_clicked(win, btn))

        # Paste button
        paste_button = Gtk.Button(icon_name="edit-paste-symbolic")
        paste_button.set_tooltip_text("Paste")
        paste_button.connect("clicked", lambda btn: self.on_paste_clicked(win, btn))
        
        # Print button
        print_button = Gtk.Button(icon_name="document-print-symbolic")
        print_button.set_tooltip_text("Print Document")
        print_button.connect("clicked", lambda btn: self.on_print_clicked(win, btn) if hasattr(self, "on_print_clicked") else None)
        
        # Add buttons to edit group
        edit_group.append(cut_button)
        edit_group.append(copy_button)
        edit_group.append(paste_button)
        edit_group.append(print_button)
        
        # Add edit group to toolbar
        file_toolbar.append(edit_group)
        
        # --- History operations group (Undo, Redo, Find) ---
        history_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        history_group.add_css_class("linked")  # Apply linked styling
        history_group.set_margin_start(6)
        
        # Undo button
        win.undo_button = Gtk.Button(icon_name="edit-undo-symbolic")
        win.undo_button.set_tooltip_text("Undo")
        win.undo_button.connect("clicked", lambda btn: self.on_undo_clicked(win, btn))
        win.undo_button.set_sensitive(False)  # Initially disabled
        
        # Redo button
        win.redo_button = Gtk.Button(icon_name="edit-redo-symbolic")
        win.redo_button.set_tooltip_text("Redo")
        win.redo_button.connect("clicked", lambda btn: self.on_redo_clicked(win, btn))
        win.redo_button.set_sensitive(False)  # Initially disabled
        
        # Find-Replace toggle button
        win.find_button = Gtk.ToggleButton()
        find_icon = Gtk.Image.new_from_icon_name("edit-find-replace-symbolic")
        win.find_button.set_child(find_icon)
        win.find_button.set_tooltip_text("Find and Replace (Ctrl+F)")
        win.find_button_handler_id = win.find_button.connect("toggled", lambda btn: self.on_find_button_toggled(win, btn))

        # Add buttons to history group
        history_group.append(win.undo_button)
        history_group.append(win.redo_button)
        history_group.append(win.find_button)
        
        # Add history group to toolbar
        file_toolbar.append(history_group)
        
        # --- Insert operations group (Table, Text Box, Image) ---
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        insert_group.add_css_class("linked")  # Apply linked styling
        insert_group.set_margin_start(6)
        
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
        
        # Add buttons to insert group
        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        
        # Add insert group to toolbar
        file_toolbar.append(insert_group)
        
        # --- Spacing operations group (Line Spacing, Paragraph Spacing) ---
        spacing_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        spacing_group.add_css_class("linked")  # Apply linked styling
        spacing_group.set_margin_start(6)
        
        # Line spacing button menu
        line_spacing_button = Gtk.MenuButton(icon_name="line_space_new")
        line_spacing_button.set_size_request(40, 36)
        line_spacing_button.set_tooltip_text("Line Spacing")
        line_spacing_button.add_css_class("flat")
        
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
        para_spacing_button.add_css_class("flat")
        
        # Create paragraph spacing menu
        para_spacing_menu = Gio.Menu()
        
        # Add paragraph spacing options
        para_spacing_menu.append("None", "win.paragraph-spacing('0')")
        para_spacing_menu.append("Small (5px)", "win.paragraph-spacing('5')")
        para_spacing_menu.append("Medium (15px)", "win.paragraph-spacing('15')")
        para_spacing_menu.append("Large (30px)", "win.paragraph-spacing('30')")
        para_spacing_menu.append("Custom...", "win.paragraph-spacing-dialog")
        
        para_spacing_button.set_menu_model(para_spacing_menu)
        
        # Column layout button menu
        column_button = Gtk.MenuButton(icon_name="columns-symbolic")
        column_button.set_size_request(40, 36)
        column_button.set_tooltip_text("Column Layout")
        column_button.add_css_class("flat")
        
        # Create column menu
        column_menu = Gio.Menu()
        
        # Add column options
        column_menu.append("Single Column", "win.set-columns('1')")
        column_menu.append("Two Columns", "win.set-columns('2')")
        column_menu.append("Three Columns", "win.set-columns('3')")
        column_menu.append("Four Columns", "win.set-columns('4')")
        column_menu.append("Remove Columns", "win.set-columns('0')")
        
        column_button.set_menu_model(column_menu)
        
        # Add buttons to spacing group
        spacing_group.append(line_spacing_button)
        spacing_group.append(para_spacing_button)
        spacing_group.append(column_button)
        
        # Add spacing group to toolbar
        file_toolbar.append(spacing_group)
        
        # Add spacer (expanding box) at the end
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar
    #########################
    def table_js(self):
        """JavaScript for table functionality"""
        return """
        // Table variables (namespaced like imageState)
        const tableState = {
            activeTable: null,
            isDragging: false,
            isResizing: false,
            isRotating: false,
            lastX: 0,
            lastY: 0,
            lastAngle: 0,
            tableCounter: 0
        };
        
        // Insert a table at the cursor position
        function insertTable(rows, cols, hasHeader, borderWidth, widthValue) {
            const selection = window.getSelection();
            if (!selection.rangeCount) return false;
            
            const range = selection.getRangeAt(0);
            
            // Create table element with requested properties
            const tableWrapper = document.createElement('div');
            // Calculate appropriate width based on settings
            let finalWidth;
            if (widthValue === 'auto') {
                finalWidth = '95%';
            } else if (widthValue === '100%') {
                // Keep 30px less for 100% to avoid scrollbar interference
                finalWidth = 'calc(100% - 30px)';
            } else {
                finalWidth = widthValue;
            }
            
            // Set proper attributes
            tableWrapper.className = 'editor-table-wrapper';
            tableWrapper.contentEditable = 'false';
            tableWrapper.style.position = 'relative';
            tableWrapper.style.display = 'inline-block';
            tableWrapper.style.width = finalWidth;
            tableWrapper.style.margin = '10px';
            tableWrapper.style.padding = '0';
            tableWrapper.style.zIndex = '1';
            tableWrapper.style.outline = 'none';
            tableWrapper.style.overflow = 'visible'; // Explicitly set overflow to visible
            
            const table = document.createElement('table');
            table.className = 'editor-table';
            table.style.borderCollapse = 'collapse';
            table.style.width = '100%';
            table.style.tableLayout = 'fixed';
            table.style.backgroundColor = '#fff';
            
            if (borderWidth > 0) {
                table.style.border = `${borderWidth}px solid #999`;
            }
            
            // Create table header if requested
            if (hasHeader) {
                const thead = document.createElement('thead');
                const headerRow = document.createElement('tr');
                
                for (let i = 0; i < cols; i++) {
                    const th = document.createElement('th');
                    th.innerHTML = `Header ${i+1}`;
                    th.style.padding = '8px';
                    th.style.textAlign = 'left';
                    th.style.fontWeight = 'bold';
                    th.style.backgroundColor = '#e0e0e0';
                    
                    if (borderWidth > 0) {
                        th.style.border = `${borderWidth}px solid #999`;
                    }
                    
                    headerRow.appendChild(th);
                }
                
                thead.appendChild(headerRow);
                table.appendChild(thead);
            }
            
            // Create table body
            const tbody = document.createElement('tbody');
            
            // Create rows and cells
            const startRow = hasHeader ? 1 : 0;
            for (let i = startRow; i < rows; i++) {
                const row = document.createElement('tr');
                
                for (let j = 0; j < cols; j++) {
                    const cell = document.createElement('td');
                    cell.innerHTML = '';
                    cell.style.padding = '8px';
                    cell.style.textAlign = 'left';
                    cell.style.minHeight = '20px';
                    
                    if (borderWidth > 0) {
                        cell.style.border = `${borderWidth}px solid #999`;
                    }
                    
                    row.appendChild(cell);
                }
                
                tbody.appendChild(row);
            }
            
            table.appendChild(tbody);
            tableWrapper.appendChild(table);
            
            // Create a unique ID for this table
            tableState.tableCounter++;
            const tableId = 'table-' + tableState.tableCounter;
            tableWrapper.id = tableId;
            tableWrapper.setAttribute('data-table-element', 'true');
            
            // Store rotation angle in the wrapper
            tableWrapper.dataset.angle = '0';
            tableWrapper.style.transform = 'rotate(0deg)';
            
            // Create a new way to handle the selection border
            // Create a wrapper specifically for the table that will contain the border
            const tableContentWrapper = document.createElement('div');
            tableContentWrapper.className = 'table-content-wrapper';
            tableContentWrapper.style.position = 'relative';
            tableContentWrapper.style.display = 'inline-block';
            tableContentWrapper.style.boxSizing = 'border-box';
            tableContentWrapper.style.overflow = 'visible';
            tableContentWrapper.style.margin = '0';
            tableContentWrapper.style.padding = '0';
            
            // Move the table into this wrapper
            tableContentWrapper.appendChild(table);
            
            // Add selection border inside this wrapper
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'table-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.right = '0';
            selectionBorder.style.bottom = '0';
            selectionBorder.style.border = '2px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '2';
            selectionBorder.style.boxSizing = 'border-box';
            
            // Add the selection border to the table content wrapper
            tableContentWrapper.appendChild(selectionBorder);
            
            // Now add this wrapper to the main table wrapper
            tableWrapper.appendChild(tableContentWrapper);
            
            // Add controls (similar to image and text box controls)
            const controls = document.createElement('div');
            controls.className = 'table-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            // Add move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-15px';
            moveHandle.style.left = '-15px';
            moveHandle.style.width = '24px';
            moveHandle.style.height = '24px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '12px';
            moveHandle.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3)';
            moveHandle.title = 'Move';
            
            // Add rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-15px';
            rotateHandle.style.right = '-15px';
            rotateHandle.style.width = '24px';
            rotateHandle.style.height = '24px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '14px';
            rotateHandle.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3)';
            rotateHandle.title = 'Rotate';
            
            // Add resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-15px';
            resizeHandle.style.right = '-15px';
            resizeHandle.style.width = '24px';
            resizeHandle.style.height = '24px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '14px';
            resizeHandle.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3)';
            resizeHandle.title = 'Resize';
            
            // Add handles to controls
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            // Add overlay for better selection (like image and text box)
            const overlay = document.createElement('div');
            overlay.className = 'table-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            // Add controls and overlay to the wrapper
            tableWrapper.appendChild(selectionBorder);
            tableWrapper.appendChild(controls);
            tableWrapper.appendChild(overlay);
            
            // Add event listeners for table interaction
            tableWrapper.addEventListener('mousedown', function(e) {
                // Check if clicking on a cell for editing
                const cell = e.target.closest('td, th');
                if (cell) {
                    // Don't interfere with cell editing, but still activate the table
                    const tableWrapper = cell.closest('.editor-table-wrapper');
                    if (tableState.activeTable !== tableWrapper) {
                        if (tableState.activeTable) {
                            deactivateTable(tableState.activeTable);
                        }
                        activateTable(tableWrapper);
                    }
                    return;
                }
                
                // Ignore clicks on controls
                const isControlClick = e.target.closest('.table-controls') !== null;
                if (isControlClick) {
                    return;
                }
                
                // Activate table when clicking on the wrapper but not a cell
                if (tableState.activeTable !== tableWrapper) {
                    if (tableState.activeTable) {
                        deactivateTable(tableState.activeTable);
                    }
                    activateTable(tableWrapper);
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            // Fix the cell click handling to ensure table is always activated
            table.addEventListener('click', function(e) {
                const clickedCell = e.target.closest('td, th');
                if (clickedCell) {
                    // Always activate the table when a cell is clicked
                    if (tableState.activeTable !== tableWrapper) {
                        if (tableState.activeTable) {
                            deactivateTable(tableState.activeTable);
                        }
                        activateTable(tableWrapper);
                    }
                }
            });
            
            // Force table activation when any part of the table is clicked
            table.addEventListener('mousedown', function(e) {
                // Activate the table (will be called before cell handlers)
                if (tableState.activeTable !== tableWrapper) {
                    if (tableState.activeTable) {
                        deactivateTable(tableState.activeTable);
                    }
                    activateTable(tableWrapper);
                }
            });
            
            // Handle specific controls
            moveHandle.addEventListener('mousedown', function(e) {
                tableState.isDragging = true;
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                tableState.isResizing = true;
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                tableState.isRotating = true;
                const rect = tableWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                tableState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Insert the table at the current selection
            range.deleteContents();
            range.insertNode(tableWrapper);
            
            // Set up table editing capabilities
            makeTableEditable(table);
            
            // Add table context menu for column/row operations
            addTableContextMenu(table);
            
            // Set up global event listeners if not already added
            setupTableEventListeners();
            
            // Ensure handle styles are consistently applied
            moveHandle.style.left = '-15px';
            moveHandle.style.top = '-15px';
            rotateHandle.style.right = '-15px';
            rotateHandle.style.top = '-15px';
            resizeHandle.style.right = '-15px';
            resizeHandle.style.bottom = '-15px';
            
            // Make selection border more visible
            selectionBorder.style.border = '2px dashed #4285f4';
            selectionBorder.style.boxSizing = 'border-box';
            selectionBorder.style.pointerEvents = 'none';
            
            // Activate the table (show controls)
            activateTable(tableWrapper);
            
            // Fix any cell editability issues - delayed to ensure DOM is ready
            setTimeout(() => {
                const allCells = table.querySelectorAll('th, td');
                allCells.forEach(cell => {
                    cell.setAttribute('contenteditable', 'true');
                    cell.style.cursor = 'text';
                    cell.style.pointerEvents = 'auto';
                });
            }, 100);
            
            // Save state after table insertion
            saveState();
            
            return true;
        }
        
        // Make cells in the table properly editable
        function makeTableEditable(table) {
            // Make sure all cells are editable
            const cells = table.querySelectorAll('th, td');
            
            cells.forEach(cell => {
                // Set proper attributes for editing
                cell.setAttribute('contenteditable', 'true');
                cell.style.cursor = 'text';
                cell.style.userSelect = 'text';
                cell.style.WebkitUserSelect = 'text';
                
                // Ensure cells have minimum size
                cell.style.minWidth = '30px';
                cell.style.minHeight = '22px';
                
                // Remove any pointer-events blocking
                cell.style.pointerEvents = 'auto';
                
                // Remove any elements that might interfere with editing
                const overlays = cell.querySelectorAll('div[style*="position: absolute"]');
                overlays.forEach(overlay => overlay.remove());
                
                // Prevent Enter key from creating new paragraph in cell
                cell.addEventListener('keydown', function(e) {
                    if (e.key === 'Enter' && !e.shiftKey) {
                        e.preventDefault();
                        
                        // Move to the next cell or row when Enter is pressed
                        const currentRow = cell.parentElement;
                        const cellIndex = Array.from(currentRow.cells).indexOf(cell);
                        const nextCell = currentRow.cells[cellIndex + 1];
                        
                        if (nextCell) {
                            // Move to next cell in the same row
                            nextCell.focus();
                        } else {
                            // Find the next row
                            const nextRow = currentRow.nextElementSibling;
                            if (nextRow) {
                                // Move to the first cell in the next row
                                nextRow.cells[0].focus();
                            }
                        }
                    }
                    else if (e.key === 'Tab') {
                        e.preventDefault();
                        
                        // Move to the next cell or to first cell of next row
                        const currentRow = cell.parentElement;
                        const rows = Array.from(table.rows);
                        const rowIndex = rows.indexOf(currentRow);
                        const cellIndex = Array.from(currentRow.cells).indexOf(cell);
                        
                        if (e.shiftKey) {
                            // Move to previous cell or to last cell of previous row
                            if (cellIndex > 0) {
                                currentRow.cells[cellIndex - 1].focus();
                            } else if (rowIndex > 0) {
                                const prevRow = rows[rowIndex - 1];
                                prevRow.cells[prevRow.cells.length - 1].focus();
                            }
                        } else {
                            // Move to next cell or to first cell of next row
                            if (cellIndex < currentRow.cells.length - 1) {
                                currentRow.cells[cellIndex + 1].focus();
                            } else if (rowIndex < rows.length - 1) {
                                rows[rowIndex + 1].cells[0].focus();
                            }
                        }
                    }
                });
                
                // Add a click handler to focus and select text
                cell.addEventListener('click', function(e) {
                    // Find the table wrapper
                    const tableWrapper = cell.closest('.editor-table-wrapper');
                    
                    // Activate the table if it's not already active
                    if (tableWrapper && tableState.activeTable !== tableWrapper) {
                        if (tableState.activeTable) {
                            deactivateTable(tableState.activeTable);
                        }
                        activateTable(tableWrapper);
                    }
                    
                    // Focus this cell if it's not already focused
                    if (document.activeElement !== cell) {
                        cell.focus();
                    }
                    
                    // Don't prevent default - allow normal cell editing
                });
                
                // Add a mousedown handler to ensure table activation
                cell.addEventListener('mousedown', function(e) {
                    // Find the table wrapper
                    const tableWrapper = cell.closest('.editor-table-wrapper');
                    
                    // Activate the table if it's not already active
                    if (tableWrapper && tableState.activeTable !== tableWrapper) {
                        if (tableState.activeTable) {
                            deactivateTable(tableState.activeTable);
                        }
                        activateTable(tableWrapper);
                    }
                    
                    // Don't stop propagation or prevent default - allow cell to be focused
                });
            });
        }
        
        // Add right-click context menu for table operations
        function addTableContextMenu(table) {
            // First, create a custom context menu for the table
            const tableMenu = document.createElement('div');
            tableMenu.className = 'table-context-menu';
            tableMenu.style.display = 'none';
            tableMenu.style.position = 'absolute';
            tableMenu.style.backgroundColor = 'white';
            tableMenu.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            tableMenu.style.padding = '5px 0';
            tableMenu.style.borderRadius = '4px';
            tableMenu.style.zIndex = '1000';
            
            // Add menu items
            const menuItems = [
                { text: 'Insert Row Above', action: 'insertRowAbove' },
                { text: 'Insert Row Below', action: 'insertRowBelow' },
                { text: 'Insert Column Left', action: 'insertColumnLeft' },
                { text: 'Insert Column Right', action: 'insertColumnRight' },
                { text: 'Delete Row', action: 'deleteRow' },
                { text: 'Delete Column', action: 'deleteColumn' },
                { text: 'Merge Cells', action: 'mergeCells' },
                { text: 'Split Cell', action: 'splitCell' }
            ];
            
            menuItems.forEach(item => {
                const menuItem = document.createElement('div');
                menuItem.className = 'table-menu-item';
                menuItem.textContent = item.text;
                menuItem.dataset.action = item.action;
                menuItem.style.padding = '8px 10px';
                menuItem.style.cursor = 'pointer';
                
                menuItem.addEventListener('mouseover', function() {
                    this.style.backgroundColor = '#f0f0f0';
                });
                
                menuItem.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'transparent';
                });
                
                tableMenu.appendChild(menuItem);
            });
            
            // Add the menu to the document
            document.body.appendChild(tableMenu);
            
            // Track current cell and table for context menu actions
            let currentCell = null;
            let currentTable = null;
            
            // Add contextmenu event listener to the table
            table.addEventListener('contextmenu', function(e) {
                const cell = e.target.closest('td, th');
                if (cell) {
                    e.preventDefault();
                    
                    // Save current cell and table reference
                    currentCell = cell;
                    currentTable = table;
                    
                    // Position the menu at the cursor
                    tableMenu.style.display = 'block';
                    tableMenu.style.left = e.pageX + 'px';
                    tableMenu.style.top = e.pageY + 'px';
                    
                    // Add click event listener to handle menu item clicks
                    document.addEventListener('click', handleTableMenuClick);
                }
            });
            
            // Close the menu when clicking anywhere else
            document.addEventListener('click', function(e) {
                if (!e.target.closest('.table-context-menu')) {
                    tableMenu.style.display = 'none';
                }
            });
            
            // Close the menu when context menu opens elsewhere
            document.addEventListener('contextmenu', function(e) {
                if (!e.target.closest('table.editor-table')) {
                    tableMenu.style.display = 'none';
                }
            });
            
            // Handle table menu actions
            function handleTableMenuClick(e) {
                const menuItem = e.target.closest('.table-menu-item');
                if (!menuItem) return;
                
                tableMenu.style.display = 'none';
                document.removeEventListener('click', handleTableMenuClick);
                
                const action = menuItem.dataset.action;
                if (!currentCell || !currentTable) return;
                
                // Get current row and column indices
                const row = currentCell.parentElement;
                const rowIndex = Array.from(currentTable.rows).indexOf(row);
                const colIndex = Array.from(row.cells).indexOf(currentCell);
                
                // Execute the requested action
                switch (action) {
                    case 'insertRowAbove':
                        insertRow(currentTable, rowIndex);
                        break;
                    case 'insertRowBelow':
                        insertRow(currentTable, rowIndex + 1);
                        break;
                    case 'insertColumnLeft':
                        insertColumn(currentTable, colIndex);
                        break;
                    case 'insertColumnRight':
                        insertColumn(currentTable, colIndex + 1);
                        break;
                    case 'deleteRow':
                        deleteRow(currentTable, rowIndex);
                        break;
                    case 'deleteColumn':
                        deleteColumn(currentTable, colIndex);
                        break;
                    case 'mergeCells':
                        // Implement cell merging (requires selection)
                        alert('Cell merging requires selecting multiple cells first');
                        break;
                    case 'splitCell':
                        // Implement cell splitting (for merged cells)
                        if (currentCell.colSpan > 1 || currentCell.rowSpan > 1) {
                            splitCell(currentCell);
                        } else {
                            alert('This cell is not merged');
                        }
                        break;
                }
                
                // Save state after table modification
                saveState();
            }
        }
        
        // Table manipulation functions
        
        // Insert a new row at the specified index
        function insertRow(table, rowIndex) {
            if (rowIndex < 0 || rowIndex > table.rows.length) return;
            
            const newRow = table.insertRow(rowIndex);
            const referenceRow = rowIndex > 0 ? table.rows[rowIndex - 1] : table.rows[rowIndex + 1];
            
            if (!referenceRow) return;
            
            // Create cells matching the number in the reference row
            for (let i = 0; i < referenceRow.cells.length; i++) {
                const newCell = newRow.insertCell(-1);
                newCell.innerHTML = '';
                
                // Copy styles from reference row
                const refCell = referenceRow.cells[i];
                newCell.style.border = refCell.style.border;
                newCell.style.padding = refCell.style.padding;
                newCell.style.textAlign = refCell.style.textAlign;
                
                // Make the cell editable
                newCell.setAttribute('contenteditable', 'true');
                
                // Add event listeners for cell editing
                addCellEventListeners(newCell);
            }
        }
        
        // Insert a new column at the specified index
        function insertColumn(table, colIndex) {
            if (colIndex < 0) return;
            
            // Loop through each row and insert a cell at the specified index
            for (let i = 0; i < table.rows.length; i++) {
                const row = table.rows[i];
                
                if (colIndex > row.cells.length) continue;
                
                const newCell = row.insertCell(colIndex);
                newCell.innerHTML = '';
                
                // Copy styles from adjacent cell if available
                const refCellIndex = colIndex > 0 ? colIndex - 1 : colIndex + 1;
                if (refCellIndex >= 0 && refCellIndex < row.cells.length) {
                    const refCell = row.cells[refCellIndex];
                    newCell.style.border = refCell.style.border;
                    newCell.style.padding = refCell.style.padding;
                    newCell.style.textAlign = refCell.style.textAlign;
                    
                    // If we're in the header row, add header styling
                    if (row.parentElement.tagName === 'THEAD') {
                        newCell.style.fontWeight = 'bold';
                        newCell.style.backgroundColor = '#f2f2f2';
                    }
                }
                
                // Make the cell editable
                newCell.setAttribute('contenteditable', 'true');
                
                // Add event listeners for cell editing
                addCellEventListeners(newCell);
            }
        }
        
        // Delete a row at the specified index
        function deleteRow(table, rowIndex) {
            if (rowIndex < 0 || rowIndex >= table.rows.length) return;
            
            // Make sure we don't delete the last row
            if (table.rows.length <= 1) {
                alert('Cannot delete the last row');
                return;
            }
            
            table.deleteRow(rowIndex);
        }
        
        // Delete a column at the specified index
        function deleteColumn(table, colIndex) {
            if (colIndex < 0) return;
            
            // Make sure we don't delete the last column
            if (table.rows[0].cells.length <= 1) {
                alert('Cannot delete the last column');
                return;
            }
            
            // Loop through each row and delete the cell at the specified index
            for (let i = 0; i < table.rows.length; i++) {
                const row = table.rows[i];
                if (colIndex < row.cells.length) {
                    row.deleteCell(colIndex);
                }
            }
        }
        
        // Split a merged cell back into individual cells
        function splitCell(cell) {
            const row = cell.parentElement;
            const table = row.closest('table');
            const rowIndex = Array.from(table.rows).indexOf(row);
            const colIndex = Array.from(row.cells).indexOf(cell);
            
            const rowSpan = cell.rowSpan || 1;
            const colSpan = cell.colSpan || 1;
            
            // Reset the spans
            cell.rowSpan = 1;
            cell.colSpan = 1;
            
            // Add missing cells
            if (colSpan > 1) {
                for (let i = 1; i < colSpan; i++) {
                    const newCell = row.insertCell(colIndex + i);
                    newCell.innerHTML = '';
                    newCell.style.border = cell.style.border;
                    newCell.style.padding = cell.style.padding;
                    newCell.setAttribute('contenteditable', 'true');
                    addCellEventListeners(newCell);
                }
            }
            
            if (rowSpan > 1) {
                for (let i = 1; i < rowSpan; i++) {
                    const nextRow = table.rows[rowIndex + i];
                    if (nextRow) {
                        for (let j = 0; j < colSpan; j++) {
                            const newCell = nextRow.insertCell(colIndex + j);
                            newCell.innerHTML = '';
                            newCell.style.border = cell.style.border;
                            newCell.style.padding = cell.style.padding;
                            newCell.setAttribute('contenteditable', 'true');
                            addCellEventListeners(newCell);
                        }
                    }
                }
            }
        }
        
        // Add event listeners to a cell
        function addCellEventListeners(cell) {
            // Prevent Enter key from creating new paragraph in cell
            cell.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    
                    // Move to the next cell or row when Enter is pressed
                    const currentRow = cell.parentElement;
                    const cellIndex = Array.from(currentRow.cells).indexOf(cell);
                    const nextCell = currentRow.cells[cellIndex + 1];
                    
                    if (nextCell) {
                        // Move to next cell in the same row
                        nextCell.focus();
                    } else {
                        // Find the next row
                        const nextRow = currentRow.nextElementSibling;
                        if (nextRow) {
                            // Move to the first cell in the next row
                            nextRow.cells[0].focus();
                        }
                    }
                }
                else if (e.key === 'Tab') {
                    e.preventDefault();
                    
                    // Move to the next cell or to first cell of next row
                    const currentRow = cell.parentElement;
                    const table = currentRow.closest('table');
                    const rows = Array.from(table.rows);
                    const rowIndex = rows.indexOf(currentRow);
                    const cellIndex = Array.from(currentRow.cells).indexOf(cell);
                    
                    if (e.shiftKey) {
                        // Move to previous cell or to last cell of previous row
                        if (cellIndex > 0) {
                            currentRow.cells[cellIndex - 1].focus();
                        } else if (rowIndex > 0) {
                            const prevRow = rows[rowIndex - 1];
                            prevRow.cells[prevRow.cells.length - 1].focus();
                        }
                    } else {
                        // Move to next cell or to first cell of next row
                        if (cellIndex < currentRow.cells.length - 1) {
                            currentRow.cells[cellIndex + 1].focus();
                        } else if (rowIndex < rows.length - 1) {
                            rows[rowIndex + 1].cells[0].focus();
                        }
                    }
                }
            });
        }
        
        // Setup global event listeners for tables
        function setupTableEventListeners() {
            if (!window.tableEventsAdded) {
                document.addEventListener('mousemove', handleTableMouseMove);
                
                document.addEventListener('mouseup', function() {
                    if (tableState.isDragging || tableState.isResizing || tableState.isRotating) {
                        tableState.isDragging = false;
                        tableState.isResizing = false;
                        tableState.isRotating = false;
                        saveState();
                    }
                });
                
                document.getElementById('editor').addEventListener('mousedown', function(e) {
                    const isTableClick = e.target.closest('.editor-table-wrapper') !== null;
                    
                    if (!isTableClick && tableState.activeTable) {
                        deactivateTable(tableState.activeTable);
                    }
                });
                
                // Handle copy events
                document.addEventListener('copy', function(e) {
                    if (tableState.activeTable) {
                        const selection = window.getSelection();
                        const range = selection.getRangeCount() > 0 ? selection.getRangeAt(0) : null;
                        
                        // Check if the active table is within the current selection
                        if (range && range.intersectsNode(tableState.activeTable)) {
                            // Mark for copy
                            tableState.activeTable.setAttribute('data-table-copy', 'true');
                            
                            // Remove after copy
                            setTimeout(function() {
                                tableState.activeTable.removeAttribute('data-table-copy');
                            }, 0);
                        }
                    }
                });
                
                // Handle paste to reconstruct tables
                document.addEventListener('paste', function(e) {
                    setTimeout(function() {
                        // Look for any divs with tables that need reconstruction
                        const editor = document.getElementById('editor');
                        
                        // Find table elements that need reconstruction
                        const possibleTables = Array.from(editor.querySelectorAll('div')).filter(div => {
                            return (div.querySelector('table') && !div.querySelector('.table-controls')) || 
                                   (div.classList.contains('editor-table-wrapper') && !div.querySelector('.table-controls'));
                        });
                        
                        possibleTables.forEach(function(element) {
                            reconstructTable(element);
                        });
                    }, 0);
                });
                
                window.tableEventsAdded = true;
            }
        }
        
        // Handle mouse movement for table manipulations
        function handleTableMouseMove(e) {
            if (!tableState.activeTable) return;
            
            if (tableState.isDragging) {
                const dx = e.clientX - tableState.lastX;
                const dy = e.clientY - tableState.lastY;
                
                const currentLeft = parseInt(tableState.activeTable.style.left) || 0;
                const currentTop = parseInt(tableState.activeTable.style.top) || 0;
                
                tableState.activeTable.style.position = 'relative';
                tableState.activeTable.style.left = `${currentLeft + dx}px`;
                tableState.activeTable.style.top = `${currentTop + dy}px`;
                
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
            }
            else if (tableState.isResizing) {
                const dx = e.clientX - tableState.lastX;
                const dy = e.clientY - tableState.lastY;
                
                const currentWidth = tableState.activeTable.offsetWidth;
                const currentHeight = tableState.activeTable.offsetHeight;
                
                // Apply minimum sizes and update dimensions
                tableState.activeTable.style.width = `${Math.max(100, currentWidth + dx)}px`;
                
                // For tables, we may not want to directly manipulate the height
                // as it should typically be determined by content
                // But for consistency with other elements, we allow it
                tableState.activeTable.style.height = `${Math.max(50, currentHeight + dy)}px`;
                
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
            }
            else if (tableState.isRotating) {
                const rect = tableState.activeTable.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                
                const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                const angleDiff = angle - tableState.lastAngle;
                
                const currentAngle = parseFloat(tableState.activeTable.dataset.angle) || 0;
                const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                
                tableState.activeTable.style.transform = `rotate(${newAngle}deg)`;
                tableState.activeTable.dataset.angle = newAngle.toString();
                
                tableState.lastAngle = angle;
            }
        }
        
        // Activate a table (show controls)
        function activateTable(tableWrapper) {
            if (tableState.activeTable && tableState.activeTable !== tableWrapper) {
                deactivateTable(tableState.activeTable);
            }
            
            tableState.activeTable = tableWrapper;
            
            // Show selection border (now in the table-content-wrapper)
            const contentWrapper = tableWrapper.querySelector('.table-content-wrapper');
            const selectionBorder = contentWrapper ? contentWrapper.querySelector('.table-selection-border') : null;
            if (selectionBorder) {
                selectionBorder.style.display = 'block';
            }
            
            // Show extended detection area
            const overlay = tableWrapper.querySelector('.table-overlay');
            if (overlay) {
                overlay.style.display = 'block';
            }
            
            tableWrapper.style.zIndex = '10';
            
            // Show controls
            const controls = tableWrapper.querySelector('.table-controls');
            if (controls) {
                controls.style.display = 'block';
            }
            
            // Ensure table cells remain editable
            const table = tableWrapper.querySelector('table');
            if (table) {
                const cells = table.querySelectorAll('th, td');
                cells.forEach(cell => {
                    cell.setAttribute('contenteditable', 'true');
                    cell.style.cursor = 'text';
                    cell.style.pointerEvents = 'auto';
                });
            }
        }
        
        // Deactivate a table (hide controls)
        function deactivateTable(tableWrapper) {
            if (tableWrapper) {
                // Hide selection border (now in table-content-wrapper)
                const contentWrapper = tableWrapper.querySelector('.table-content-wrapper');
                const selectionBorder = contentWrapper ? contentWrapper.querySelector('.table-selection-border') : null;
                if (selectionBorder) {
                    selectionBorder.style.display = 'none';
                }
                
                // Hide extended detection area
                const overlay = tableWrapper.querySelector('.table-overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                }
                
                tableWrapper.style.zIndex = '1';
                
                // Hide controls
                const controls = tableWrapper.querySelector('.table-controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                
                if (tableState.activeTable === tableWrapper) {
                    tableState.activeTable = null;
                }
            }
        }
        
        // Reconstruct a table after paste
        function reconstructTable(element) {
            // Get the table element inside the wrapper if it exists
            const tableElement = element.querySelector('table');
            if (!tableElement) {
                // Not enough info to reconstruct
                return;
            }
            
            // Save attributes and table content
            const tableHTML = tableElement.outerHTML;
            const width = element.style.width;
            const height = element.style.height;
            const left = element.style.left;
            const top = element.style.top;
            const transform = element.style.transform;
            const angle = element.dataset.angle || '0';
            
            // Create a new wrapper with controls
            const newWrapper = document.createElement('div');
            newWrapper.className = 'editor-table-wrapper';
            newWrapper.contentEditable = 'false';
            newWrapper.style.position = 'relative';
            newWrapper.style.display = 'inline-block';
            newWrapper.style.margin = '10px';
            newWrapper.style.padding = '0';
            newWrapper.style.zIndex = '1';
            newWrapper.style.outline = 'none';
            newWrapper.style.overflow = 'visible'; // Explicitly set overflow to visible
            
            // Create a unique ID for this table
            tableState.tableCounter++;
            const tableId = 'table-' + tableState.tableCounter;
            newWrapper.id = tableId;
            newWrapper.setAttribute('data-table-element', 'true');
            
            // Insert the original table HTML
            newWrapper.innerHTML = tableHTML;
            
            // Add selection border
            const selectionBorder = document.createElement('div');
            selectionBorder.className = 'table-selection-border';
            selectionBorder.style.position = 'absolute';
            selectionBorder.style.top = '0';
            selectionBorder.style.left = '0';
            selectionBorder.style.width = '100%';
            selectionBorder.style.height = '100%';
            selectionBorder.style.border = '1px dashed #4285f4';
            selectionBorder.style.pointerEvents = 'none';
            selectionBorder.style.display = 'none';
            selectionBorder.style.zIndex = '998';
            selectionBorder.style.boxSizing = 'border-box';
            
            // Add controls
            const controls = document.createElement('div');
            controls.className = 'table-controls';
            controls.style.position = 'absolute';
            controls.style.top = '0';
            controls.style.left = '0';
            controls.style.width = '100%';
            controls.style.height = '100%';
            controls.style.pointerEvents = 'none';
            controls.style.display = 'none';
            controls.style.zIndex = '999';
            
            // Add move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '❖';
            moveHandle.style.position = 'absolute';
            moveHandle.style.top = '-12px';
            moveHandle.style.left = '-12px';
            moveHandle.style.width = '20px';
            moveHandle.style.height = '20px';
            moveHandle.style.borderRadius = '50%';
            moveHandle.style.backgroundColor = '#4285f4';
            moveHandle.style.color = 'white';
            moveHandle.style.display = 'flex';
            moveHandle.style.alignItems = 'center';
            moveHandle.style.justifyContent = 'center';
            moveHandle.style.cursor = 'move';
            moveHandle.style.pointerEvents = 'auto';
            moveHandle.style.zIndex = '1000';
            moveHandle.style.fontSize = '10px';
            moveHandle.title = 'Move';
            
            // Add rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '↻';
            rotateHandle.style.position = 'absolute';
            rotateHandle.style.top = '-12px';
            rotateHandle.style.right = '-12px';
            rotateHandle.style.width = '20px';
            rotateHandle.style.height = '20px';
            rotateHandle.style.borderRadius = '50%';
            rotateHandle.style.backgroundColor = '#4285f4';
            rotateHandle.style.color = 'white';
            rotateHandle.style.display = 'flex';
            rotateHandle.style.alignItems = 'center';
            rotateHandle.style.justifyContent = 'center';
            rotateHandle.style.cursor = 'pointer';
            rotateHandle.style.pointerEvents = 'auto';
            rotateHandle.style.zIndex = '1000';
            rotateHandle.style.fontSize = '12px';
            rotateHandle.title = 'Rotate';
            
            // Add resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '⤡';
            resizeHandle.style.position = 'absolute';
            resizeHandle.style.bottom = '-12px';
            resizeHandle.style.right = '-12px';
            resizeHandle.style.width = '20px';
            resizeHandle.style.height = '20px';
            resizeHandle.style.borderRadius = '50%';
            resizeHandle.style.backgroundColor = '#4285f4';
            resizeHandle.style.color = 'white';
            resizeHandle.style.display = 'flex';
            resizeHandle.style.alignItems = 'center';
            resizeHandle.style.justifyContent = 'center';
            resizeHandle.style.cursor = 'nwse-resize';
            resizeHandle.style.pointerEvents = 'auto';
            resizeHandle.style.zIndex = '1000';
            resizeHandle.style.fontSize = '12px';
            resizeHandle.title = 'Resize';
            
            // Add overlay
            const overlay = document.createElement('div');
            overlay.className = 'table-overlay';
            overlay.style.position = 'absolute';
            overlay.style.top = '-15px';
            overlay.style.left = '-15px';
            overlay.style.right = '-15px';
            overlay.style.bottom = '-15px';
            overlay.style.cursor = 'pointer';
            overlay.style.zIndex = '997';
            overlay.style.display = 'none';
            
            // Add controls to wrapper
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            newWrapper.appendChild(selectionBorder);
            newWrapper.appendChild(controls);
            newWrapper.appendChild(overlay);
            
            // Apply saved attributes
            if (width) newWrapper.style.width = width;
            if (height) newWrapper.style.height = height;
            if (left) newWrapper.style.left = left;
            if (top) newWrapper.style.top = top;
            if (transform) newWrapper.style.transform = transform;
            newWrapper.dataset.angle = angle;
            
            // Set up event listeners for the reconstructed table
            newWrapper.addEventListener('mousedown', function(e) {
                const isControlClick = e.target.closest('.table-controls') !== null;
                
                if (isControlClick) {
                    return;
                }
                
                if (tableState.activeTable !== newWrapper) {
                    if (tableState.activeTable) {
                        deactivateTable(tableState.activeTable);
                    }
                    activateTable(newWrapper);
                }
                
                e.preventDefault();
                e.stopPropagation();
            });
            
            // Set up control handles
            moveHandle.addEventListener('mousedown', function(e) {
                tableState.isDragging = true;
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            resizeHandle.addEventListener('mousedown', function(e) {
                tableState.isResizing = true;
                tableState.lastX = e.clientX;
                tableState.lastY = e.clientY;
                e.stopPropagation();
                e.preventDefault();
            });
            
            rotateHandle.addEventListener('mousedown', function(e) {
                tableState.isRotating = true;
                const rect = newWrapper.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                tableState.lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
                e.preventDefault();
            });
            
            // Replace the old element with the new one
            element.parentNode.replaceChild(newWrapper, element);
            
            // Make table cells editable
            const newTable = newWrapper.querySelector('table');
            if (newTable) {
                makeTableEditable(newTable);
                addTableContextMenu(newTable);
            }
            
            // Save state after reconstruction
            saveState();
        }
        
            // Add styles for tables
            const styleContent = `
                .editor-table-wrapper {
                    break-inside: avoid;
                    page-break-inside: avoid;
                    cursor: pointer;
                    box-sizing: border-box;
                    overflow: visible !important; /* Force visible overflow */
                }
                
                .table-content-wrapper {
                    position: relative;
                    display: inline-block;
                    box-sizing: border-box;
                    margin: 0;
                    padding: 0;
                    overflow: visible !important;
                }
                
                .editor-table {
                    margin: 0;
                    padding: 0;
                    border-collapse: collapse;
                    width: 100%;
                    overflow: visible !important; /* Force visible overflow */
                }
                
                .editor-table th,
                .editor-table td {
                    min-width: 1em;
                    min-height: 1.2em;
                    position: relative;
                }
                
                .editor-table th:focus,
                .editor-table td:focus {
                    outline: 2px solid #4285f4;
                    outline-offset: -2px;
                }
                
                .table-context-menu {
                    user-select: none;
                    background-color: white;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    border-radius: 4px;
                    overflow: hidden;
                }
                
                .table-menu-item {
                    font-size: 14px;
                    padding: 8px 16px;
                }
                
                .table-menu-item:hover {
                    background-color: #f0f0f0;
                }
                
                .table-selection-border {
                    pointer-events: none;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    width: auto;
                    height: auto;
                    border: 2px dashed #4285f4;
                    position: absolute;
                    box-sizing: border-box;
                }
                
                .table-controls .move-handle {
                    left: -15px;
                    top: -15px;
                    width: 24px;
                    height: 24px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                }
                
                .table-controls .rotate-handle {
                    right: -15px;
                    top: -15px;
                    width: 24px;
                    height: 24px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                }
                
                .table-controls .resize-handle {
                    right: -15px;
                    bottom: -15px;
                    width: 24px;
                    height: 24px;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                }
                
                @media (prefers-color-scheme: dark) {
                    .editor-table {
                        background-color: #333;
                    }
                    
                    .editor-table th {
                        background-color: #444;
                    }
                    
                    .editor-table td {
                        background-color: #333;
                        color: #fff;
                    }
                    
                    .table-context-menu {
                        background-color: #333;
                        color: #fff;
                    }
                    
                    .table-menu-item:hover {
                        background-color: #555 !important;
                    }
                }
            `;
            
            if (!document.getElementById('table-styles')) {
                const style = document.createElement('style');
                style.id = 'table-styles';
                style.textContent = styleContent;
                document.head.appendChild(style);
            }
        
        // Initialize table functionality
        document.addEventListener('DOMContentLoaded', function() {
            addTableStyles();
            setupTableEventListeners();
        });
        """
##########################################
    def table_js(self):
        """Return the JavaScript for table functionality."""
        return """
        // Table handling functionality
        function insertTable(rows, cols, hasHeader, borderWidth, widthOption) {
            // Set default values if not provided
            hasHeader = hasHeader !== undefined ? hasHeader : true;
            borderWidth = borderWidth !== undefined ? borderWidth : 1;
            widthOption = widthOption || "100%";
            
            // Create width style
            let widthStyle = "";
            if (widthOption !== "auto") {
                widthStyle = ` width: ${widthOption};`;
            }
            
            // Create table HTML
            let table = `<table border="${borderWidth}" cellspacing="0" cellpadding="5" 
                           class="editable-table" style="border-collapse: collapse;${widthStyle}">`;
            
            // Create header row if requested
            if (hasHeader) {
                table += '<thead><tr>';
                for (let j = 0; j < cols; j++) {
                    table += '<th style="min-width: 50px; text-align: left; padding: 8px; border: ' + 
                             borderWidth + 'px solid #000;">Header ' + (j + 1) + '</th>';
                }
                table += '</tr></thead>';
                rows--; // Reduce body rows by one since we have a header
            }
            
            // Create table body
            table += '<tbody>';
            for (let i = 0; i < rows; i++) {
                table += '<tr>';
                for (let j = 0; j < cols; j++) {
                    table += '<td style="min-width: 50px; padding: 8px; border: ' + 
                             borderWidth + 'px solid #000;"> </td>';
                }
                table += '</tr>';
            }
            table += '</tbody>';
            table += '</table><p></p>';
            
            // Insert the table HTML
            document.execCommand('insertHTML', false, table);
            
            // Activate the table once it's inserted
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editable-table');
                const newTable = tables[tables.length - 1];
                if (newTable) {
                    activateTable(newTable);
                    // Notify Python side that a table was clicked
                    if (window.webkit && window.webkit.messageHandlers && 
                        window.webkit.messageHandlers.tableClicked) {
                        window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                    }
                }
            }, 10);
            
            // Save state for undo/redo
            if (!window.isUndoRedo) {
                saveState();
            }
        }
        
        // Activate table editing handles and functionality
        function activateTable(table) {
            if (!table) return;
            
            // Add data attribute to mark as active
            table.setAttribute('data-active', 'true');
            
            // Add click event listener to the table if not already added
            if (!table.hasAttribute('data-initialized')) {
                table.setAttribute('data-initialized', 'true');
                
                // Handle cell selection and editing
                table.addEventListener('click', function(e) {
                    const cell = e.target.closest('td, th');
                    if (cell) {
                        // Focus the cell for editing
                        cell.setAttribute('contenteditable', 'true');
                        cell.focus();
                        
                        // Notify Python side that a table was clicked
                        if (window.webkit && window.webkit.messageHandlers && 
                            window.webkit.messageHandlers.tableClicked) {
                            window.webkit.messageHandlers.tableClicked.postMessage('table-cell-clicked');
                        }
                    }
                });
                
                // Make cells editable on double-click
                table.addEventListener('dblclick', function(e) {
                    const cell = e.target.closest('td, th');
                    if (cell) {
                        // Make sure cell is focused and editable
                        cell.setAttribute('contenteditable', 'true');
                        cell.focus();
                        
                        // Select all text in the cell
                        const selection = window.getSelection();
                        const range = document.createRange();
                        range.selectNodeContents(cell);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                });
            }
            
            // Add resize handles if not already present
            if (!table.querySelector('.table-handle')) {
                addTableHandles(table);
            }
        }
        
        // Add resize handles to the table
        function addTableHandles(table) {
            // Create container for table and handles
            const tableContainer = document.createElement('div');
            tableContainer.className = 'table-container';
            tableContainer.style.position = 'relative';
            tableContainer.style.display = 'inline-block';
            
            // Wrap table with the container
            table.parentNode.insertBefore(tableContainer, table);
            tableContainer.appendChild(table);
            
            // Add column resize handles to first row
            const firstRow = table.querySelector('tr');
            if (firstRow) {
                const cells = firstRow.querySelectorAll('th, td');
                
                cells.forEach((cell, index) => {
                    if (index < cells.length - 1) {  // Skip last cell
                        const handle = document.createElement('div');
                        handle.className = 'column-resize-handle table-handle';
                        handle.style.position = 'absolute';
                        handle.style.top = '0';
                        handle.style.right = '0';
                        handle.style.width = '5px';
                        handle.style.height = '100%';
                        handle.style.cursor = 'col-resize';
                        handle.style.backgroundColor = 'transparent';
                        handle.style.zIndex = '100';
                        
                        // Show handle on hover
                        handle.addEventListener('mouseenter', function() {
                            this.style.backgroundColor = '#0d6efd';
                        });
                        
                        handle.addEventListener('mouseleave', function() {
                            this.style.backgroundColor = 'transparent';
                        });
                        
                        // Add resize functionality
                        handle.addEventListener('mousedown', function(e) {
                            e.preventDefault();
                            const startX = e.clientX;
                            const cellWidth = cell.offsetWidth;
                            
                            const handleMove = function(moveEvent) {
                                const deltaX = moveEvent.clientX - startX;
                                cell.style.width = (cellWidth + deltaX) + 'px';
                            };
                            
                            const handleUp = function() {
                                document.removeEventListener('mousemove', handleMove);
                                document.removeEventListener('mouseup', handleUp);
                                saveState(); // Save state after resize
                            };
                            
                            document.addEventListener('mousemove', handleMove);
                            document.addEventListener('mouseup', handleUp);
                        });
                        
                        cell.style.position = 'relative';
                        cell.appendChild(handle);
                    }
                });
            }
            
            // Add row resize handles
            const rows = table.querySelectorAll('tr');
            rows.forEach((row, index) => {
                if (index < rows.length - 1) {  // Skip last row
                    const handle = document.createElement('div');
                    handle.className = 'row-resize-handle table-handle';
                    handle.style.position = 'absolute';
                    handle.style.left = '0';
                    handle.style.bottom = '0';
                    handle.style.width = '100%';
                    handle.style.height = '5px';
                    handle.style.cursor = 'row-resize';
                    handle.style.backgroundColor = 'transparent';
                    handle.style.zIndex = '100';
                    
                    // Show handle on hover
                    handle.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = '#0d6efd';
                    });
                    
                    handle.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'transparent';
                    });
                    
                    // Add resize functionality
                    handle.addEventListener('mousedown', function(e) {
                        e.preventDefault();
                        const startY = e.clientY;
                        const rowHeight = row.offsetHeight;
                        
                        const handleMove = function(moveEvent) {
                            const deltaY = moveEvent.clientY - startY;
                            row.style.height = (rowHeight + deltaY) + 'px';
                        };
                        
                        const handleUp = function() {
                            document.removeEventListener('mousemove', handleMove);
                            document.removeEventListener('mouseup', handleUp);
                            saveState(); // Save state after resize
                        };
                        
                        document.addEventListener('mousemove', handleMove);
                        document.addEventListener('mouseup', handleUp);
                    });
                    
                    row.style.position = 'relative';
                    row.appendChild(handle);
                }
            });
            
            // Add table operations menu
            addTableOperationsMenu(table, tableContainer);
        }
        
        // Add table operations menu
        function addTableOperationsMenu(table, tableContainer) {
            // Create menu button
            const menuButton = document.createElement('div');
            menuButton.className = 'table-menu-button table-handle';
            menuButton.innerHTML = '⋮'; // Vertical ellipsis
            menuButton.style.position = 'absolute';
            menuButton.style.top = '-20px';
            menuButton.style.right = '0';
            menuButton.style.width = '20px';
            menuButton.style.height = '20px';
            menuButton.style.backgroundColor = '#f0f0f0';
            menuButton.style.border = '1px solid #ccc';
            menuButton.style.borderRadius = '3px';
            menuButton.style.textAlign = 'center';
            menuButton.style.lineHeight = '18px';
            menuButton.style.cursor = 'pointer';
            menuButton.style.zIndex = '101';
            
            // Create dropdown menu
            const menu = document.createElement('div');
            menu.className = 'table-operation-menu';
            menu.style.position = 'absolute';
            menu.style.top = '0';
            menu.style.right = '0';
            menu.style.backgroundColor = '#ffffff';
            menu.style.border = '1px solid #ccc';
            menu.style.borderRadius = '3px';
            menu.style.padding = '5px 0';
            menu.style.boxShadow = '0 2px 5px rgba(0,0,0,0.2)';
            menu.style.display = 'none';
            menu.style.zIndex = '102';
            
            // Menu options
            const operations = [
                { text: 'Insert Row Above', action: () => insertRowAbove(table) },
                { text: 'Insert Row Below', action: () => insertRowBelow(table) },
                { text: 'Insert Column Left', action: () => insertColumnLeft(table) },
                { text: 'Insert Column Right', action: () => insertColumnRight(table) },
                { text: 'Delete Row', action: () => deleteSelectedRow(table) },
                { text: 'Delete Column', action: () => deleteSelectedColumn(table) },
                { text: 'Delete Table', action: () => deleteTable(table) }
            ];
            
            // Add menu items
            operations.forEach(op => {
                const item = document.createElement('div');
                item.className = 'table-menu-item';
                item.textContent = op.text;
                item.style.padding = '5px 15px';
                item.style.cursor = 'pointer';
                
                item.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#f0f0f0';
                });
                
                item.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'transparent';
                });
                
                item.addEventListener('click', function(e) {
                    e.stopPropagation();
                    op.action();
                    menu.style.display = 'none';
                    saveState(); // Save state after operation
                });
                
                menu.appendChild(item);
            });
            
            // Toggle menu display
            menuButton.addEventListener('click', function(e) {
                e.stopPropagation();
                menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
            });
            
            // Hide menu when clicking elsewhere
            document.addEventListener('click', function() {
                menu.style.display = 'none';
            });
            
            tableContainer.appendChild(menuButton);
            tableContainer.appendChild(menu);
        }
        
        // Table operations
        function insertRowAbove(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const row = activeCell.parentNode;
            const newRow = document.createElement('tr');
            const cellCount = row.cells.length;
            
            for (let i = 0; i < cellCount; i++) {
                const cell = document.createElement('td');
                cell.style.border = row.cells[i].style.border;
                cell.style.padding = row.cells[i].style.padding;
                cell.style.minWidth = row.cells[i].style.minWidth;
                cell.innerHTML = ' ';
                newRow.appendChild(cell);
            }
            
            row.parentNode.insertBefore(newRow, row);
            activateTable(table);
        }
        
        function insertRowBelow(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const row = activeCell.parentNode;
            const newRow = document.createElement('tr');
            const cellCount = row.cells.length;
            
            for (let i = 0; i < cellCount; i++) {
                const cell = document.createElement('td');
                cell.style.border = row.cells[i].style.border;
                cell.style.padding = row.cells[i].style.padding;
                cell.style.minWidth = row.cells[i].style.minWidth;
                cell.innerHTML = ' ';
                newRow.appendChild(cell);
            }
            
            if (row.nextSibling) {
                row.parentNode.insertBefore(newRow, row.nextSibling);
            } else {
                row.parentNode.appendChild(newRow);
            }
            
            activateTable(table);
        }
        
        function insertColumnLeft(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const cellIndex = activeCell.cellIndex;
            const rows = table.querySelectorAll('tr');
            
            rows.forEach(row => {
                const newCell = document.createElement(row.parentNode.tagName === 'THEAD' ? 'th' : 'td');
                newCell.style.border = activeCell.style.border;
                newCell.style.padding = activeCell.style.padding;
                newCell.style.minWidth = activeCell.style.minWidth;
                newCell.innerHTML = ' ';
                
                if (cellIndex === 0) {
                    row.insertBefore(newCell, row.cells[0]);
                } else {
                    row.insertBefore(newCell, row.cells[cellIndex]);
                }
            });
            
            activateTable(table);
        }
        
        function insertColumnRight(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const cellIndex = activeCell.cellIndex;
            const rows = table.querySelectorAll('tr');
            
            rows.forEach(row => {
                const newCell = document.createElement(row.parentNode.tagName === 'THEAD' ? 'th' : 'td');
                newCell.style.border = activeCell.style.border;
                newCell.style.padding = activeCell.style.padding;
                newCell.style.minWidth = activeCell.style.minWidth;
                newCell.innerHTML = ' ';
                
                if (cellIndex === row.cells.length - 1) {
                    row.appendChild(newCell);
                } else {
                    row.insertBefore(newCell, row.cells[cellIndex + 1]);
                }
            });
            
            activateTable(table);
        }
        
        function deleteSelectedRow(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const row = activeCell.parentNode;
            
            // Check if this is the last row
            if (table.querySelectorAll('tr').length <= 1) {
                deleteTable(table);
                return;
            }
            
            row.parentNode.removeChild(row);
            activateTable(table);
        }
        
        function deleteSelectedColumn(table) {
            const activeCell = document.querySelector('td:focus, th:focus');
            if (!activeCell) return;
            
            const cellIndex = activeCell.cellIndex;
            const rows = table.querySelectorAll('tr');
            
            // Check if this is the last column
            if (rows[0].cells.length <= 1) {
                deleteTable(table);
                return;
            }
            
            rows.forEach(row => {
                if (row.cells[cellIndex]) {
                    row.removeChild(row.cells[cellIndex]);
                }
            });
            
            activateTable(table);
        }
        
        function deleteTable(table) {
            const container = table.closest('.table-container');
            if (container) {
                container.parentNode.removeChild(container);
            } else {
                table.parentNode.removeChild(table);
            }
            
            saveState();
        }
        
        // Initialize tables when editor loads
        document.addEventListener('DOMContentLoaded', function() {
            // Find all tables and activate them
            const tables = document.querySelectorAll('table.editable-table');
            tables.forEach(table => {
                activateTable(table);
            });
        });
        
        // Custom event for activating tables after content changes
        document.addEventListener('content-changed', function() {
            setTimeout(() => {
                const tables = document.querySelectorAll('table.editable-table:not([data-initialized])');
                tables.forEach(table => {
                    activateTable(table);
                });
            }, 100);
        });

        """


def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())    
