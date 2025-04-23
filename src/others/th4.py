#!/usr/bin/env python3
import sys
import os
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('Pango', '1.0')
gi.require_version('Gdk', '4.0')
from gi.repository import Gtk, Adw, Pango, Gdk, GLib, Gio

class RichTextEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.RichTextEditor",
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
        self.connect('activate', self.on_activate)
        self.current_file = None
        self.modified = False
        
    def on_activate(self, app):
        # Set up the main window
        self.win = Adw.ApplicationWindow(application=app)
        self.win.set_default_size(800, 600)
        self.win.set_title("Rich Text Editor")
        
        # Create Adw header bar with controls
        self.header = Adw.HeaderBar()
        self.menu_button = Gtk.MenuButton()
        self.menu_button.set_icon_name("open-menu-symbolic")
        
        # Create menu model
        menu = Gio.Menu()
        menu.append("New", "app.new")
        menu.append("Open", "app.open")
        menu.append("Save", "app.save")
        menu.append("Save As", "app.save_as")
        menu.append("About", "app.about")
        menu.append("Quit", "app.quit")
        
        # Set up menu actions
        self.create_action("new", self.on_new_clicked)
        self.create_action("open", self.on_open_clicked)
        self.create_action("save", self.on_save_clicked)
        self.create_action("save_as", self.on_save_as_clicked)
        self.create_action("about", self.on_about_clicked)
        self.create_action("quit", self.on_quit)
        
        self.menu_button.set_menu_model(menu)
        self.header.pack_end(self.menu_button)
        
        # Add formatting toolbar buttons
        self.format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.format_box.add_css_class("toolbar")
        
        # Font selection combobox
        font_label = Gtk.Label.new("Font:")
        font_label.set_margin_start(5)
        self.format_box.append(font_label)
        
        # Create font dropdown
        self.font_combo = self.create_font_dropdown()
        self.format_box.append(self.font_combo)
        
        # Font size dropdown
        size_label = Gtk.Label.new("Size:")
        size_label.set_margin_start(5)
        self.format_box.append(size_label)
        
        # Create size dropdown
        self.font_size_combo = self.create_size_dropdown()
        self.format_box.append(self.font_size_combo)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Bold button
        self.bold_button = Gtk.ToggleButton()
        self.bold_button.set_icon_name("format-text-bold-symbolic")
        self.bold_button.set_tooltip_text("Bold")
        self.bold_button.connect("toggled", self.on_bold_toggled)
        self.format_box.append(self.bold_button)
        
        # Italic button
        self.italic_button = Gtk.ToggleButton()
        self.italic_button.set_icon_name("format-text-italic-symbolic")
        self.italic_button.set_tooltip_text("Italic")
        self.italic_button.connect("toggled", self.on_italic_toggled)
        self.format_box.append(self.italic_button)
        
        # Underline button
        self.underline_button = Gtk.ToggleButton()
        self.underline_button.set_icon_name("format-text-underline-symbolic")
        self.underline_button.set_tooltip_text("Underline")
        self.underline_button.connect("toggled", self.on_underline_toggled)
        self.format_box.append(self.underline_button)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Alignment buttons
        self.align_left_button = Gtk.ToggleButton()
        self.align_left_button.set_icon_name("format-justify-left-symbolic")
        self.align_left_button.set_tooltip_text("Align Left")
        self.align_left_button.connect("toggled", self.on_align_toggled, "left")
        self.format_box.append(self.align_left_button)
        
        self.align_center_button = Gtk.ToggleButton()
        self.align_center_button.set_icon_name("format-justify-center-symbolic")
        self.align_center_button.set_tooltip_text("Align Center")
        self.align_center_button.connect("toggled", self.on_align_toggled, "center")
        self.format_box.append(self.align_center_button)
        
        self.align_right_button = Gtk.ToggleButton()
        self.align_right_button.set_icon_name("format-justify-right-symbolic")
        self.align_right_button.set_tooltip_text("Align Right")
        self.align_right_button.connect("toggled", self.on_align_toggled, "right")
        self.format_box.append(self.align_right_button)
        
        # Add separator
        self.format_box.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))
        
        # Font color button
        self.color_button = Gtk.ColorButton()
        self.color_button.set_tooltip_text("Text Color")
        self.color_button.connect("color-set", self.on_color_set)
        self.format_box.append(self.color_button)
        
        # Add a second toolbar for paragraph styles
        self.para_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.para_box.add_css_class("toolbar")
        
        # Paragraph style label and dropdown
        para_label = Gtk.Label.new("Paragraph:")
        para_label.set_margin_start(5)
        self.para_box.append(para_label)
        
        # Create paragraph style dropdown
        self.para_combo = self.create_paragraph_dropdown()
        self.para_box.append(self.para_combo)
        
        # Line spacing dropdown
        spacing_label = Gtk.Label.new("Line Spacing:")
        spacing_label.set_margin_start(10)
        self.para_box.append(spacing_label)
        
        # Create line spacing dropdown
        self.line_spacing_combo = self.create_spacing_dropdown()
        self.para_box.append(self.line_spacing_combo)
        
        # Create ScrolledWindow for TextView
        self.scrolled_window = Gtk.ScrolledWindow()
        self.scrolled_window.set_vexpand(True)
        self.scrolled_window.set_hexpand(True)
        
        # Create TextView with buffer
        self.textbuffer = Gtk.TextBuffer()
        self.textview = Gtk.TextView.new_with_buffer(self.textbuffer)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_top_margin(10)
        self.textview.set_bottom_margin(10)
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(10)
        
        # Connect buffer signals
        self.textbuffer.connect("changed", self.on_buffer_changed)
        
        # Add TextView to ScrolledWindow
        self.scrolled_window.set_child(self.textview)
        
        # Create status bar
        self.statusbar = Gtk.Label()
        self.statusbar.set_xalign(0)
        self.statusbar.set_margin_start(10)
        self.statusbar.set_margin_end(10)
        self.statusbar.set_margin_top(5)
        self.statusbar.set_margin_bottom(5)
        self.update_statusbar()
        
        # Set up the layout
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.vbox.append(self.header)
        self.vbox.append(self.format_box)
        self.vbox.append(self.para_box)
        self.vbox.append(self.scrolled_window)
        self.vbox.append(self.statusbar)
        
        self.win.set_content(self.vbox)
        self.win.present()
        
        # Set up tags for text styling
        self.setup_text_tags()
        
        # Connect selection change signal
        self.textbuffer.connect("notify::cursor-position", self.on_cursor_position_changed)
        
        # Default font family name and size
        self.current_font_family = "Sans"
        self.current_font_size = 12
    
    def create_font_dropdown(self):
        """Create and return the font family dropdown"""
        # Get system font families
        font_context = self.win.get_pango_context()
        font_families = font_context.list_families()
        
        # Create font combo box
        font_combo = Gtk.DropDown()
        font_model = Gio.ListStore.new(Gtk.StringObject)
        
        # Sort font families alphabetically
        sorted_families = sorted(font_families, key=lambda f: f.get_name())
        
        for font_family in sorted_families:
            font_model.append(Gtk.StringObject.new(font_family.get_name()))
        
        font_combo.set_model(font_model)
        font_combo.set_selected(0)  # Default to first font
        
        # Set up the factory for displaying the font names
        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)
        font_combo.set_factory(factory)
        
        font_combo.connect("notify::selected", self.on_font_changed)
        return font_combo
    
    def create_size_dropdown(self):
        """Create and return the font size dropdown"""
        size_combo = Gtk.DropDown()
        size_model = Gio.ListStore.new(Gtk.StringObject)
        
        # Common font sizes
        font_sizes = ["8", "9", "10", "11", "12", "14", "16", "18", "20", "22", "24", "26", "28", "36", "48", "72"]
        for size in font_sizes:
            size_model.append(Gtk.StringObject.new(size))
        
        size_combo.set_model(size_model)
        # Set default size to 12pt (index 4)
        size_combo.set_selected(4)
        
        # Set up factory for displaying font sizes
        size_factory = Gtk.SignalListItemFactory()
        size_factory.connect("setup", self._on_factory_setup)
        size_factory.connect("bind", self._on_factory_bind)
        size_combo.set_factory(size_factory)
        
        size_combo.connect("notify::selected", self.on_font_size_selected)
        return size_combo
    
    def create_paragraph_dropdown(self):
        """Create and return the paragraph style dropdown"""
        para_combo = Gtk.DropDown()
        para_model = Gio.ListStore.new(Gtk.StringObject)
        
        # Paragraph styles
        para_styles = ["Normal", "Heading 1", "Heading 2", "Heading 3", "Blockquote", "Preformatted"]
        for style in para_styles:
            para_model.append(Gtk.StringObject.new(style))
        
        para_combo.set_model(para_model)
        para_combo.set_selected(0)  # Default to normal
        
        # Set up factory for displaying paragraph styles
        para_factory = Gtk.SignalListItemFactory()
        para_factory.connect("setup", self._on_factory_setup)
        para_factory.connect("bind", self._on_factory_bind)
        para_combo.set_factory(para_factory)
        
        para_combo.connect("notify::selected", self.on_paragraph_style_changed)
        return para_combo
    
    def create_spacing_dropdown(self):
        """Create and return the line spacing dropdown"""
        spacing_combo = Gtk.DropDown()
        spacing_model = Gio.ListStore.new(Gtk.StringObject)
        
        # Line spacing options
        spacing_options = ["1.0", "1.15", "1.5", "2.0"]
        for spacing in spacing_options:
            spacing_model.append(Gtk.StringObject.new(spacing))
        
        spacing_combo.set_model(spacing_model)
        spacing_combo.set_selected(0)  # Default to 1.0
        
        # Set up factory for line spacing
        spacing_factory = Gtk.SignalListItemFactory()
        spacing_factory.connect("setup", self._on_factory_setup)
        spacing_factory.connect("bind", self._on_factory_bind)
        spacing_combo.set_factory(spacing_factory)
        
        spacing_combo.connect("notify::selected", self.on_line_spacing_changed)
        return spacing_combo
    
    # Factory functions for dropdown lists
    def _on_factory_setup(self, factory, list_item):
        """Set up the signal list item factory"""
        label = Gtk.Label()
        label.set_halign(Gtk.Align.START)
        list_item.set_child(label)
    
    def _on_factory_bind(self, factory, list_item):
        """Bind data to the list item"""
        label = list_item.get_child()
        string_object = list_item.get_item()
        label.set_text(string_object.get_string())
    
    def setup_text_tags(self):
        """Initialize the text tags for the buffer"""
        self.textbuffer.create_tag("bold", weight=Pango.Weight.BOLD)
        self.textbuffer.create_tag("italic", style=Pango.Style.ITALIC)
        self.textbuffer.create_tag("underline", underline=Pango.Underline.SINGLE)
        
        # Create tags for font sizes (8pt to 72pt)
        for size in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]:
            self.textbuffer.create_tag(f"size-{size}", size_points=size)
        
        # Create alignment tags
        self.textbuffer.create_tag("left", justification=Gtk.Justification.LEFT)
        self.textbuffer.create_tag("center", justification=Gtk.Justification.CENTER)
        self.textbuffer.create_tag("right", justification=Gtk.Justification.RIGHT)
        
        # Create line spacing tags
        self.textbuffer.create_tag("spacing-1.0", pixels_inside_wrap=0)
        self.textbuffer.create_tag("spacing-1.15", pixels_inside_wrap=2)
        self.textbuffer.create_tag("spacing-1.5", pixels_inside_wrap=6)
        self.textbuffer.create_tag("spacing-2.0", pixels_inside_wrap=12)
        
        # Create paragraph style tags
        # Normal - default, no special styling
        # Heading 1
        self.textbuffer.create_tag("heading-1", weight=Pango.Weight.BOLD, size_points=24)
        # Heading 2
        self.textbuffer.create_tag("heading-2", weight=Pango.Weight.BOLD, size_points=18)
        # Heading 3
        self.textbuffer.create_tag("heading-3", weight=Pango.Weight.BOLD, size_points=14)
        # Blockquote
        self.textbuffer.create_tag("blockquote", left_margin=30, right_margin=30, 
                                  style=Pango.Style.ITALIC, pixels_inside_wrap=6)
        # Preformatted
        self.textbuffer.create_tag("preformatted", family="Monospace", left_margin=20,
                                  wrap_mode=Gtk.WrapMode.NONE)
    
    def create_action(self, name, callback):
        """Add an app action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
    
    def on_buffer_changed(self, buffer):
        """Handle text buffer changes"""
        self.modified = True
        self.update_statusbar()
    
    def update_statusbar(self):
        """Update the status bar with current file and modified status"""
        status = ""
        if self.current_file:
            status = f"Editing: {os.path.basename(self.current_file)}"
        else:
            status = "New Document"
            
        if self.modified:
            status += " (modified)"
            
        self.statusbar.set_text(status)
        
    def on_cursor_position_changed(self, buffer, param):
        """Update formatting buttons when cursor position changes"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                self.update_format_buttons(start, end)
        else:
            cursor = self.textbuffer.get_insert()
            pos = self.textbuffer.get_iter_at_mark(cursor)
            self.update_format_buttons_at_iter(pos)
    
    def update_format_buttons(self, start, end):
        """Update format buttons based on selected text"""
        # Check if entire selection has bold
        has_bold = True
        has_italic = True
        has_underline = True
        
        pos = start.copy()
        while pos.compare(end) < 0:
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("bold")):
                has_bold = False
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("italic")):
                has_italic = False
            if not pos.has_tag(self.textbuffer.get_tag_table().lookup("underline")):
                has_underline = False
            
            if not (has_bold or has_italic or has_underline):
                break
            
            pos.forward_char()
        
        # Update toggle button states without triggering signals
        self.bold_button.handler_block_by_func(self.on_bold_toggled)
        self.bold_button.set_active(has_bold)
        self.bold_button.handler_unblock_by_func(self.on_bold_toggled)
        
        self.italic_button.handler_block_by_func(self.on_italic_toggled)
        self.italic_button.set_active(has_italic)
        self.italic_button.handler_unblock_by_func(self.on_italic_toggled)
        
        self.underline_button.handler_block_by_func(self.on_underline_toggled)
        self.underline_button.set_active(has_underline)
        self.underline_button.handler_unblock_by_func(self.on_underline_toggled)
    
    def update_format_buttons_at_iter(self, iter):
        """Update format buttons based on text at cursor position"""
        # Check for basic formatting tags
        has_bold = iter.has_tag(self.textbuffer.get_tag_table().lookup("bold"))
        has_italic = iter.has_tag(self.textbuffer.get_tag_table().lookup("italic"))
        has_underline = iter.has_tag(self.textbuffer.get_tag_table().lookup("underline"))
        
        # Update toggle button states without triggering signals
        self.bold_button.handler_block_by_func(self.on_bold_toggled)
        self.bold_button.set_active(has_bold)
        self.bold_button.handler_unblock_by_func(self.on_bold_toggled)
        
        self.italic_button.handler_block_by_func(self.on_italic_toggled)
        self.italic_button.set_active(has_italic)
        self.italic_button.handler_unblock_by_func(self.on_italic_toggled)
        
        self.underline_button.handler_block_by_func(self.on_underline_toggled)
        self.underline_button.set_active(has_underline)
        self.underline_button.handler_unblock_by_func(self.on_underline_toggled)
        
        # Update alignment buttons
        has_left = iter.has_tag(self.textbuffer.get_tag_table().lookup("left"))
        has_center = iter.has_tag(self.textbuffer.get_tag_table().lookup("center"))
        has_right = iter.has_tag(self.textbuffer.get_tag_table().lookup("right"))
        
        self.align_left_button.handler_block_by_func(self.on_align_toggled)
        self.align_left_button.set_active(has_left)
        self.align_left_button.handler_unblock_by_func(self.on_align_toggled)
        
        self.align_center_button.handler_block_by_func(self.on_align_toggled)
        self.align_center_button.set_active(has_center)
        self.align_center_button.handler_unblock_by_func(self.on_align_toggled)
        
        self.align_right_button.handler_block_by_func(self.on_align_toggled)
        self.align_right_button.set_active(has_right)
        self.align_right_button.handler_unblock_by_func(self.on_align_toggled)
        
        # Update font and size selectors
        self.update_font_selectors(iter)
        
        # Update paragraph style
        self.update_paragraph_style(iter)
    
    def update_paragraph_style(self, iter):
        """Update the paragraph style dropdown based on the current position"""
        # Get paragraph style
        para_style = 0  # Default to "Normal"
        
        if iter.has_tag(self.textbuffer.get_tag_table().lookup("heading-1")):
            para_style = 1  # Heading 1
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("heading-2")):
            para_style = 2  # Heading 2
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("heading-3")):
            para_style = 3  # Heading 3
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("blockquote")):
            para_style = 4  # Blockquote
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("preformatted")):
            para_style = 5  # Preformatted
        
        # Update paragraph style combo
        if self.para_combo.get_selected() != para_style:
            self.para_combo.set_selected(para_style)
        
        # Update line spacing
        spacing_style = 0  # Default to 1.0
        
        if iter.has_tag(self.textbuffer.get_tag_table().lookup("spacing-1.15")):
            spacing_style = 1  # 1.15
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("spacing-1.5")):
            spacing_style = 2  # 1.5
        elif iter.has_tag(self.textbuffer.get_tag_table().lookup("spacing-2.0")):
            spacing_style = 3  # 2.0
        
        # Update line spacing combo
        if self.line_spacing_combo.get_selected() != spacing_style:
            self.line_spacing_combo.set_selected(spacing_style)
    
    def update_font_selectors(self, iter):
        """Update font family and size selectors based on the current position"""
        # Find font family
        found_family = False
        font_index = 0
        
        tags = iter.get_tags()
        for tag in tags:
            tag_name = tag.get_property("name")
            if tag_name and tag_name.startswith("font-"):
                family = tag_name[5:]  # Remove "font-" prefix
                
                # Find index in font model
                model = self.font_combo.get_model()
                for i in range(model.get_n_items()):
                    string_obj = model.get_item(i)
                    if string_obj.get_string() == family:
                        font_index = i
                        found_family = True
                        break
                
                if found_family:
                    break
        
        # Update font combo if font found
        if found_family and self.font_combo.get_selected() != font_index:
            self.font_combo.set_selected(font_index)
        
        # Find font size
        font_size = 12  # Default
        size_index = 4  # Index for size 12 in the dropdown (0-based)
        
        for tag in tags:
            tag_name = tag.get_property("name")
            if tag_name and tag_name.startswith("size-"):
                try:
                    size = int(tag_name[5:])  # Remove "size-" prefix
                    font_size = size
                    
                    # Find index in size model
                    sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
                    if size in sizes:
                        size_index = sizes.index(size)
                    
                    break
                except ValueError:
                    pass
        
        # Update size combo
        if self.font_size_combo.get_selected() != size_index:
            self.font_size_combo.set_selected(size_index)
    
    def on_bold_toggled(self, button):
        """Toggle bold formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("bold", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("bold", start, end)
    
    def on_italic_toggled(self, button):
        """Toggle italic formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("italic", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("italic", start, end)
    
    def on_underline_toggled(self, button):
        """Toggle underline formatting"""
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                if button.get_active():
                    self.textbuffer.apply_tag_by_name("underline", start, end)
                else:
                    self.textbuffer.remove_tag_by_name("underline", start, end)
    
    def on_align_toggled(self, button, align_type):
        """Toggle text alignment"""
        # Uncheck other alignment buttons
        if button.get_active():
            for btn, align in [(self.align_left_button, "left"), 
                               (self.align_center_button, "center"), 
                               (self.align_right_button, "right")]:
                if btn != button:
                    btn.handler_block_by_func(self.on_align_toggled)
                    btn.set_active(False)
                    btn.handler_unblock_by_func(self.on_align_toggled)
            
            if self.textbuffer.get_has_selection():
                bounds = self.textbuffer.get_selection_bounds()
                if bounds:
                    start, end = bounds
                    for tag in ["left", "center", "right"]:
                        self.textbuffer.remove_tag_by_name(tag, start, end)
                    self.textbuffer.apply_tag_by_name(align_type, start, end)
            else:
                # If no selection, apply to current paragraph
                cursor_mark = self.textbuffer.get_insert()
                cursor_iter = self.textbuffer.get_iter_at_mark(cursor_mark)
                
                # Find paragraph start and end
                para_start = cursor_iter.copy()
                para_start.set_line_offset(0)
                
                para_end = cursor_iter.copy()
                if not para_end.ends_line():
                    para_end.forward_to_line_end()
                
                for tag in ["left", "center", "right"]:
                    self.textbuffer.remove_tag_by_name(tag, para_start, para_end)
                self.textbuffer.apply_tag_by_name(align_type, para_start, para_end)
    
        
    def on_font_changed(self, dropdown, param_spec):
        """Handle font family selection"""
        selected = dropdown.get_selected()
        model = dropdown.get_model()
        string_object = model.get_item(selected)
        font_family = string_object.get_string()
        
        self.current_font_family = font_family
        
        # Apply to selected text
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                
                # Remove any existing font family tags
                tags = start.get_tags()
                font_tags = []
                for tag in tags:
                    tag_name = tag.get_property("name")
                    if tag_name and tag_name.startswith("font-"):
                        font_tags.append(tag)
                
                for tag in font_tags:
                    self.textbuffer.remove_tag(tag, start, end)
                
                # Create or get font tag
                tag_name = f"font-{font_family}"
                tag = self.textbuffer.get_tag_table().lookup(tag_name)
                
                if not tag:
                    tag = self.textbuffer.create_tag(tag_name, family=font_family)
                
                self.textbuffer.apply_tag(tag, start, end)
    
    def on_font_size_selected(self, dropdown, param_spec):
        """Handle font size selection from dropdown"""
        selected = dropdown.get_selected()
        model = dropdown.get_model()
        string_object = model.get_item(selected)
        size_str = string_object.get_string()
        
        try:
            size = int(size_str)
            self.current_font_size = size
            
            # Apply to selected text
            if self.textbuffer.get_has_selection():
                bounds = self.textbuffer.get_selection_bounds()
                if bounds:
                    start, end = bounds
                    
                    # Remove any existing size tags
                    for size_tag in [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]:
                        self.textbuffer.remove_tag_by_name(f"size-{size_tag}", start, end)
                    
                    # Apply new size tag
                    self.textbuffer.apply_tag_by_name(f"size-{size}", start, end)
        except ValueError:
            pass
    
    def on_paragraph_style_changed(self, dropdown, param_spec):
        """Handle paragraph style selection"""
        selected = dropdown.get_selected()
        model = dropdown.get_model()
        string_object = model.get_item(selected)
        style = string_object.get_string()
        
        # Apply to current paragraph or selection
        cursor_mark = self.textbuffer.get_insert()
        cursor_iter = self.textbuffer.get_iter_at_mark(cursor_mark)
        
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            start, end = bounds
            
            # Get paragraph bounds to ensure whole paragraphs are styled
            para_start = start.copy()
            para_start.set_line_offset(0)
            
            para_end = end.copy()
            if not para_end.ends_line() and not para_end.is_end():
                para_end.forward_to_line_end()
            
            # Remove existing paragraph style tags
            for tag_name in ["heading-1", "heading-2", "heading-3", "blockquote", "preformatted"]:
                self.textbuffer.remove_tag_by_name(tag_name, para_start, para_end)
            
            # Apply new style if not "Normal"
            if style == "Heading 1":
                self.textbuffer.apply_tag_by_name("heading-1", para_start, para_end)
            elif style == "Heading 2":
                self.textbuffer.apply_tag_by_name("heading-2", para_start, para_end)
            elif style == "Heading 3":
                self.textbuffer.apply_tag_by_name("heading-3", para_start, para_end)
            elif style == "Blockquote":
                self.textbuffer.apply_tag_by_name("blockquote", para_start, para_end)
            elif style == "Preformatted":
                self.textbuffer.apply_tag_by_name("preformatted", para_start, para_end)
        else:
            # Get current paragraph bounds
            para_start = cursor_iter.copy()
            para_start.set_line_offset(0)
            
            para_end = cursor_iter.copy()
            if not para_end.ends_line():
                para_end.forward_to_line_end()
            
            # Remove existing paragraph style tags
            for tag_name in ["heading-1", "heading-2", "heading-3", "blockquote", "preformatted"]:
                self.textbuffer.remove_tag_by_name(tag_name, para_start, para_end)
            
            # Apply new style if not "Normal"
            if style == "Heading 1":
                self.textbuffer.apply_tag_by_name("heading-1", para_start, para_end)
            elif style == "Heading 2":
                self.textbuffer.apply_tag_by_name("heading-2", para_start, para_end)
            elif style == "Heading 3":
                self.textbuffer.apply_tag_by_name("heading-3", para_start, para_end)
            elif style == "Blockquote":
                self.textbuffer.apply_tag_by_name("blockquote", para_start, para_end)
            elif style == "Preformatted":
                self.textbuffer.apply_tag_by_name("preformatted", para_start, para_end)
    
    def on_line_spacing_changed(self, dropdown, param_spec):
        """Handle line spacing selection"""
        selected = dropdown.get_selected()
        model = dropdown.get_model()
        string_object = model.get_item(selected)
        spacing = string_object.get_string()
        
        # Apply to current paragraph or selection
        cursor_mark = self.textbuffer.get_insert()
        cursor_iter = self.textbuffer.get_iter_at_mark(cursor_mark)
        
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            start, end = bounds
            
            # Get paragraph bounds to ensure whole paragraphs are styled
            para_start = start.copy()
            para_start.set_line_offset(0)
            
            para_end = end.copy()
            if not para_end.ends_line() and not para_end.is_end():
                para_end.forward_to_line_end()
            
            # Remove existing spacing tags
            for tag_name in ["spacing-1.0", "spacing-1.15", "spacing-1.5", "spacing-2.0"]:
                self.textbuffer.remove_tag_by_name(tag_name, para_start, para_end)
            
            # Apply new spacing
            self.textbuffer.apply_tag_by_name(f"spacing-{spacing}", para_start, para_end)
        else:
            # Get current paragraph bounds
            para_start = cursor_iter.copy()
            para_start.set_line_offset(0)
            
            para_end = cursor_iter.copy()
            if not para_end.ends_line():
                para_end.forward_to_line_end()
            
            # Remove existing spacing tags
            for tag_name in ["spacing-1.0", "spacing-1.15", "spacing-1.5", "spacing-2.0"]:
                self.textbuffer.remove_tag_by_name(tag_name, para_start, para_end)
            
            # Apply new spacing
            self.textbuffer.apply_tag_by_name(f"spacing-{spacing}", para_start, para_end)
    
    def on_color_set(self, button):
        """Set text color"""
        color = button.get_rgba()
        color_str = f"#{int(color.red*255):02x}{int(color.green*255):02x}{int(color.blue*255):02x}"
        
        # Create or get color tag
        tag_name = f"color-{color_str}"
        tag = self.textbuffer.get_tag_table().lookup(tag_name)
        
        if not tag:
            tag = self.textbuffer.create_tag(tag_name, foreground=color_str)
        
        if self.textbuffer.get_has_selection():
            bounds = self.textbuffer.get_selection_bounds()
            if bounds:
                start, end = bounds
                
                # Remove any existing color tags
                # In GTK4, we need to iterate over tags differently
                current_tags = []
                for tag_iter in start.get_tags():
                    tag_name = tag_iter.get_property("name")
                    if tag_name and tag_name.startswith("color-"):
                        current_tags.append(tag_iter)
                
                # Remove all color tags from the selection
                for tag_iter in current_tags:
                    self.textbuffer.remove_tag(tag_iter, start, end)
                
                # Apply new color tag
                self.textbuffer.apply_tag(tag, start, end)
    
    def on_new_clicked(self, action, parameter):
        """Handle New button click"""
        if self.modified:
            dialog = Adw.MessageDialog.new(self.win, "Save changes?", 
                                          "Do you want to save changes to the current document?")
            dialog.add_response("discard", "Discard")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("save", "Save")
            dialog.set_default_response("save")
            dialog.set_close_response("cancel")
            
            dialog.connect("response", self.on_new_dialog_response)
            dialog.present()
        else:
            self.clear_document()
    
    def on_new_dialog_response(self, dialog, response):
        """Handle response from new document dialog"""
        if response == "save":
            self.on_save_clicked(None, None)
            self.clear_document()
        elif response == "discard":
            self.clear_document()
    
    def clear_document(self):
        """Clear the document for new file"""
        self.textbuffer.set_text("")
        self.current_file = None
        self.modified = False
        self.update_statusbar()
    
    def on_open_clicked(self, action, parameter):
        """Handle Open button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Open File")
        
        # Create file filter for HTML files
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        filter_html.add_pattern("*.htm")
        
        # Create file filter for all files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_html)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.open(self.win, None, self.on_open_dialog_response)
    
    def on_open_dialog_response(self, dialog, result):
        """Handle response from open file dialog"""
        try:
            file = dialog.open_finish(result)
            if file:
                self.open_file(file.get_path())
        except GLib.Error as error:
            print(f"Error opening file: {error.message}")
    
    def open_file(self, filepath):
        """Open a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Clear existing content
            self.textbuffer.set_text("")
            
            if filepath.lower().endswith(('.html', '.htm')):
                self.load_html(content)
            else:
                # Just load as plain text
                self.textbuffer.set_text(content)
            
            self.current_file = filepath
            self.modified = False
            self.update_statusbar()
            
        except Exception as e:
            dialog = Adw.MessageDialog.new(self.win, "Error", f"Failed to open file: {str(e)}")
            dialog.add_response("ok", "OK")
            dialog.present()
            
    def load_html(self, html_content):
        """Parse HTML content and load it into the buffer with formatting using lxml"""
        try:
            from lxml import etree
            from lxml.html import fromstring, tostring
            import re
            import html
            
            # Clear the buffer first
            self.textbuffer.set_text("")
            
            # Parse HTML content
            root = fromstring(html_content)
            
            # Function to process elements recursively
            def process_element(element, parent_styles=None):
                if parent_styles is None:
                    parent_styles = {}
                
                # Get element's own style
                element_styles = parent_styles.copy()
                
                # Process inline style attribute
                if 'style' in element.attrib:
                    style_text = element.attrib['style']
                    style_parts = [s.strip() for s in style_text.split(';') if s.strip()]
                    
                    for style_part in style_parts:
                        if ':' in style_part:
                            prop, value = style_part.split(':', 1)
                            prop = prop.strip().lower()
                            value = value.strip().lower()
                            
                            if prop == 'font-weight' and value in ['bold', 'bolder', '700', '800', '900']:
                                element_styles['bold'] = True
                            elif prop == 'font-style' and value == 'italic':
                                element_styles['italic'] = True
                            elif prop == 'text-decoration' and 'underline' in value:
                                element_styles['underline'] = True
                            elif prop == 'color':
                                element_styles['color'] = value
                            elif prop == 'font-family':
                                element_styles['font-family'] = value.strip('"\'')
                            elif prop == 'font-size':
                                # Try to extract a numeric size value
                                size_match = re.search(r'(\d+)(?:pt|px)', value)
                                if size_match:
                                    try:
                                        size = int(size_match.group(1))
                                        element_styles['font-size'] = size
                                    except ValueError:
                                        pass
                            elif prop == 'text-align':
                                if value in ['left', 'center', 'right']:
                                    element_styles['text-align'] = value
                            elif prop == 'line-height':
                                try:
                                    # Handle numeric line height (1.5, 2.0, etc.)
                                    line_height = float(value)
                                    if 0.9 <= line_height <= 1.1:
                                        element_styles['line-spacing'] = '1.0'
                                    elif 1.1 < line_height <= 1.3:
                                        element_styles['line-spacing'] = '1.15'
                                    elif 1.3 < line_height <= 1.7:
                                        element_styles['line-spacing'] = '1.5'
                                    elif line_height > 1.7:
                                        element_styles['line-spacing'] = '2.0'
                                except ValueError:
                                    pass
                
                # Process element type
                tag = element.tag.lower()
                
                # Handle heading tags
                if tag in ['h1', 'h2', 'h3']:
                    para_style = f"heading-{tag[1]}"
                    
                    # Get current cursor position
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    # Add newlines if needed
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    # Insert the heading text
                    heading_start = self.textbuffer.get_end_iter()
                    
                    # Process text content
                    inner_text = []
                    if element.text:
                        inner_text.append(element.text)
                    
                    # Process children
                    for child in element:
                        process_element(child, element_styles)
                        if child.tail:
                            inner_text.append(child.tail)
                    
                    # Insert any text content directly in this element
                    if inner_text:
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), "".join(inner_text))
                    
                    # Apply heading style
                    heading_end = self.textbuffer.get_end_iter()
                    self.textbuffer.apply_tag_by_name(para_style, heading_start, heading_end)
                    
                    # Add a newline after the heading
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                # Handle paragraph tags
                elif tag == 'p':
                    # Get current cursor position
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    # Add newlines if needed
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    para_start = self.textbuffer.get_end_iter()
                    
                    # Process text content
                    if element.text:
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), element.text)
                    
                    # Process children
                    for child in element:
                        process_element(child, element_styles)
                        if child.tail:
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), child.tail)
                    
                    para_end = self.textbuffer.get_end_iter()
                    
                    # Apply paragraph alignment if specified
                    if 'text-align' in element_styles:
                        self.textbuffer.apply_tag_by_name(element_styles['text-align'], para_start, para_end)
                    
                    # Apply line spacing if specified
                    if 'line-spacing' in element_styles:
                        self.textbuffer.apply_tag_by_name(f"spacing-{element_styles['line-spacing']}", para_start, para_end)
                    
                    # Add a newline after the paragraph
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                # Handle blockquote
                elif tag == 'blockquote':
                    # Get current cursor position
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    # Add newlines if needed
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    quote_start = self.textbuffer.get_end_iter()
                    
                    # Process text content
                    if element.text:
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), element.text)
                    
                    # Process children
                    for child in element:
                        process_element(child, element_styles)
                        if child.tail:
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), child.tail)
                    
                    quote_end = self.textbuffer.get_end_iter()
                    
                    # Apply blockquote style
                    self.textbuffer.apply_tag_by_name("blockquote", quote_start, quote_end)
                    
                    # Add a newline after the blockquote
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                # Handle preformatted text
                elif tag == 'pre':
                    # Get current cursor position
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    # Add newlines if needed
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    pre_start = self.textbuffer.get_end_iter()
                    
                    # Preserve exact text content for preformatted text
                    text_content = ""
                    if element.text:
                        text_content += element.text
                    
                    # Include all child content exactly as-is
                    text_content += "".join(etree.tostring(child, encoding='unicode', method='text') for child in element)
                    
                    # Insert the preformatted text
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), text_content)
                    
                    pre_end = self.textbuffer.get_end_iter()
                    
                    # Apply preformatted style
                    self.textbuffer.apply_tag_by_name("preformatted", pre_start, pre_end)
                    
                    # Add a newline after the pre block
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                # Handle basic formatting tags
                elif tag in ['b', 'strong', 'i', 'em', 'u', 'span', 'div', 'a']:
                    start_iter = self.textbuffer.get_end_iter()
                    
                    # Insert text content
                    if element.text:
                        self.textbuffer.insert(start_iter, element.text)
                    
                    # Apply styles based on tag
                    end_iter = self.textbuffer.get_end_iter()
                    
                    if tag in ['b', 'strong'] or element_styles.get('bold'):
                        self.textbuffer.apply_tag_by_name("bold", start_iter, end_iter)
                    
                    if tag in ['i', 'em'] or element_styles.get('italic'):
                        self.textbuffer.apply_tag_by_name("italic", start_iter, end_iter)
                    
                    if tag == 'u' or element_styles.get('underline'):
                        self.textbuffer.apply_tag_by_name("underline", start_iter, end_iter)
                    
                    # Apply font family if specified
                    if 'font-family' in element_styles:
                        family = element_styles['font-family']
                        tag_name = f"font-{family}"
                        
                        # Create tag if it doesn't exist
                        if not self.textbuffer.get_tag_table().lookup(tag_name):
                            self.textbuffer.create_tag(tag_name, family=family)
                        
                        self.textbuffer.apply_tag_by_name(tag_name, start_iter, end_iter)
                    
                    # Apply font size if specified
                    if 'font-size' in element_styles:
                        size = element_styles['font-size']
                        # Map to closest size in our size list
                        sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
                        closest_size = min(sizes, key=lambda x: abs(x - size))
                        self.textbuffer.apply_tag_by_name(f"size-{closest_size}", start_iter, end_iter)
                    
                    # Apply text color if specified
                    if 'color' in element_styles:
                        color = element_styles['color']
                        tag_name = f"color-{color}"
                        
                        # Create tag if it doesn't exist
                        if not self.textbuffer.get_tag_table().lookup(tag_name):
                            self.textbuffer.create_tag(tag_name, foreground=color)
                        
                        self.textbuffer.apply_tag_by_name(tag_name, start_iter, end_iter)
                    
                    # Process children with current styles
                    for child in element:
                        process_element(child, element_styles)
                        
                        # Insert any trailing text
                        if child.tail:
                            tail_start = self.textbuffer.get_end_iter()
                            self.textbuffer.insert(tail_start, child.tail)
                            tail_end = self.textbuffer.get_end_iter()
                            
                            # Apply parent element's styles to tail text
                            if tag in ['b', 'strong'] or element_styles.get('bold'):
                                self.textbuffer.apply_tag_by_name("bold", tail_start, tail_end)
                            
                            if tag in ['i', 'em'] or element_styles.get('italic'):
                                self.textbuffer.apply_tag_by_name("italic", tail_start, tail_end)
                            
                            if tag == 'u' or element_styles.get('underline'):
                                self.textbuffer.apply_tag_by_name("underline", tail_start, tail_end)
                            
                            # Apply font family to tail text
                            if 'font-family' in element_styles:
                                family = element_styles['font-family']
                                tag_name = f"font-{family}"
                                self.textbuffer.apply_tag_by_name(tag_name, tail_start, tail_end)
                            
                            # Apply font size to tail text
                            if 'font-size' in element_styles:
                                size = element_styles['font-size']
                                sizes = [8, 9, 10, 11, 12, 14, 16, 18, 20, 22, 24, 26, 28, 36, 48, 72]
                                closest_size = min(sizes, key=lambda x: abs(x - size))
                                self.textbuffer.apply_tag_by_name(f"size-{closest_size}", tail_start, tail_end)
                            
                            # Apply text color to tail text
                            if 'color' in element_styles:
                                color = element_styles['color']
                                tag_name = f"color-{color}"
                                self.textbuffer.apply_tag_by_name(tag_name, tail_start, tail_end)
                
                # Handle line breaks
                elif tag == 'br':
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                
                # Handle lists
                elif tag in ['ul', 'ol']:
                    # Get current cursor position
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    # Add newline if needed
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    # Process list items
                    list_type = "•" if tag == 'ul' else "1."  # Bullet or number
                    item_num = 1
                    
                    for child in element:
                        if child.tag.lower() == 'li':
                            # Create list marker
                            marker = list_type
                            if list_type == "1.":
                                marker = f"{item_num}."
                                item_num += 1
                            
                            # Insert list marker
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), f"{marker} ")
                            
                            item_start = self.textbuffer.get_end_iter()
                            
                            # Insert item text
                            if child.text:
                                self.textbuffer.insert(self.textbuffer.get_end_iter(), child.text)
                            
                            # Process child elements of list item
                            for grandchild in child:
                                process_element(grandchild, element_styles)
                                if grandchild.tail:
                                    self.textbuffer.insert(self.textbuffer.get_end_iter(), grandchild.tail)
                            
                            # Add newline after each list item
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                    # Add extra newline after the list
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                
                # Handle tables (basic support)
                elif tag == 'table':
                    # Add newline before table
                    insert_mark = self.textbuffer.get_insert()
                    insert_iter = self.textbuffer.get_iter_at_mark(insert_mark)
                    
                    if not insert_iter.starts_line() and insert_iter.get_offset() > 0:
                        self.textbuffer.insert(insert_iter, "\n")
                    
                    # Process table rows
                    for child in element:
                        if child.tag.lower() in ['tr', 'thead', 'tbody', 'tfoot']:
                            # For thead/tbody/tfoot, process their tr children
                            if child.tag.lower() in ['thead', 'tbody', 'tfoot']:
                                for tr in child:
                                    if tr.tag.lower() == 'tr':
                                        # Process row
                                        cells = []
                                        for cell in tr:
                                            if cell.tag.lower() in ['td', 'th']:
                                                # Get cell text
                                                cell_text = ""
                                                if cell.text:
                                                    cell_text += cell.text
                                                
                                                # Add child element text
                                                for grandchild in cell:
                                                    cell_text += etree.tostring(grandchild, encoding='unicode', method='text')
                                                    if grandchild.tail:
                                                        cell_text += grandchild.tail
                                                
                                                cells.append(cell_text.strip())
                                        
                                        # Insert row as tab-separated text
                                        if cells:
                                            self.textbuffer.insert(self.textbuffer.get_end_iter(), "\t".join(cells))
                                            self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                            else:  # Process tr directly
                                # Process row
                                cells = []
                                for cell in child:
                                    if cell.tag.lower() in ['td', 'th']:
                                        # Get cell text
                                        cell_text = ""
                                        if cell.text:
                                            cell_text += cell.text
                                        
                                        # Add child element text
                                        for grandchild in cell:
                                            cell_text += etree.tostring(grandchild, encoding='unicode', method='text')
                                            if grandchild.tail:
                                                cell_text += grandchild.tail
                                        
                                        cells.append(cell_text.strip())
                                
                                # Insert row as tab-separated text
                                if cells:
                                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\t".join(cells))
                                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                    
                    # Add newline after table
                    self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                
                # Handle body and other container elements by processing children
                elif tag in ['html', 'body', 'div', 'main', 'article', 'section', 'header', 'footer']:
                    # Process text directly in this element
                    if element.text and element.text.strip():
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), element.text)
                    
                    # Process children
                    for child in element:
                        process_element(child, element_styles)
                        if child.tail and child.tail.strip():
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), child.tail)
                
                # Default case: just insert text content
                else:
                    if element.text:
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), element.text)
                    
                    for child in element:
                        process_element(child, element_styles)
                        if child.tail:
                            self.textbuffer.insert(self.textbuffer.get_end_iter(), child.tail)
            
            # Start processing from the root element
            process_element(root)
            
        except ImportError:
            # Fallback to the simpler parser if lxml is not available
            self._load_html_simple(html_content)
        except Exception as e:
            print(f"Error parsing HTML with lxml: {str(e)}")
            # Fallback to simpler parsing
            self._load_html_simple(html_content)

    def _load_html_simple(self, html_content):
        """Simple HTML parser fallback method"""
        # This is your existing load_html implementation
        try:
            # Simple HTML parser (basic implementation)
            # Strip HTML tags and convert some basic formatting
            in_tag = False
            in_style = False
            tag_name = ""
            style_text = ""
            plain_text = ""
            format_stack = []
            
            i = 0
            while i < len(html_content):
                if html_content[i] == '<':
                    in_tag = True
                    tag_name = ""
                    i += 1
                    # Check if closing tag
                    is_closing = False
                    if i < len(html_content) and html_content[i] == '/':
                        is_closing = True
                        i += 1
                    
                    # Get tag name
                    while i < len(html_content) and html_content[i] != '>' and html_content[i] != ' ':
                        tag_name += html_content[i]
                        i += 1
                    
                    # Handle style attribute
                    if i < len(html_content) and html_content[i] == ' ':
                        while i < len(html_content) and html_content[i] != '>':
                            if html_content[i:i+7] == ' style="':
                                in_style = True
                                i += 8  # Skip past style="
                                while i < len(html_content) and html_content[i] != '"':
                                    style_text += html_content[i]
                                    i += 1
                                in_style = False
                            else:
                                i += 1
                    
                    # Skip to end of tag
                    while i < len(html_content) and html_content[i] != '>':
                        i += 1
                    
                    # Process tag
                    if is_closing:
                        if format_stack and format_stack[-1][0] == tag_name.lower():
                            # Apply formatting for the tag we're closing
                            tag_type, start_pos = format_stack.pop()
                            end_iter = self.textbuffer.get_end_iter()
                            
                            if tag_type == 'b' or tag_type == 'strong':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("bold", start_iter, end_iter)
                            elif tag_type == 'i' or tag_type == 'em':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("italic", start_iter, end_iter)
                            elif tag_type == 'u':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("underline", start_iter, end_iter)
                            elif tag_type == 'h1':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("heading-1", start_iter, end_iter)
                            elif tag_type == 'h2':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("heading-2", start_iter, end_iter)
                            elif tag_type == 'h3':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("heading-3", start_iter, end_iter)
                            elif tag_type == 'blockquote':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("blockquote", start_iter, end_iter)
                            elif tag_type == 'pre':
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                self.textbuffer.apply_tag_by_name("preformatted", start_iter, end_iter)
                    else:
                        if tag_name.lower() in ['b', 'strong', 'i', 'em', 'u', 'h1', 'h2', 'h3', 'blockquote', 'pre']:
                            # Push formatting tag to stack
                            format_stack.append((tag_name.lower(), len(plain_text)))
                        elif tag_name.lower() == 'br':
                            plain_text += '\n'
                        elif tag_name.lower() == 'p':
                            if plain_text and not plain_text.endswith('\n\n'):
                                plain_text += '\n\n'
                    
                    in_tag = False
                else:
                    if not in_tag:
                        plain_text += html_content[i]
                    i += 1
            
            # Set the plain text to buffer
            self.textbuffer.set_text(plain_text)
            
        except Exception as e:
            print(f"Error parsing HTML with simple parser: {str(e)}")
            # Fallback: just set the raw HTML
            self.textbuffer.set_text(html_content)    
    def on_save_clicked(self, action, parameter):
        """Handle Save button click"""
        if self.current_file:
            self.save_file(self.current_file)
        else:
            self.on_save_as_clicked(action, parameter)
    
    def on_save_as_clicked(self, action, parameter):
        """Handle Save As button click"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Save File")
        
        # Create file filter for HTML files
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        filter_html.add_pattern("*.html")
        
        # Create file filter for all files
        filter_all = Gtk.FileFilter()
        filter_all.set_name("All files")
        filter_all.add_pattern("*")
        
        filters = Gio.ListStore.new(Gtk.FileFilter)
        filters.append(filter_html)
        filters.append(filter_all)
        dialog.set_filters(filters)
        
        dialog.save(self.win, None, self.on_save_dialog_response)
    
    def on_save_dialog_response(self, dialog, result):
        """Handle response from save file dialog"""
        try:
            file = dialog.save_finish(result)
            if file:
                filepath = file.get_path()
                # Add .html extension if none is specified
                if not filepath.lower().endswith(('.html', '.htm')):
                    filepath += '.html'
                self.save_file(filepath)
        except GLib.Error as error:
            print(f"Error saving file: {error.message}")
    
    def save_file(self, filepath):
        """Save file to given path"""
        try:
            html_content = self.generate_html()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.current_file = filepath
            self.modified = False
            self.update_statusbar()
            
        except Exception as e:
            dialog = Adw.MessageDialog.new(self.win, "Error", f"Failed to save file: {str(e)}")
            dialog.add_response("ok", "OK")
            dialog.present()
    
    def generate_html(self):
        """Generate HTML from the current buffer content with formatting"""
        html = ['<!DOCTYPE html>\n<html>\n<head>\n<meta charset="utf-8">\n<title>Rich Text Editor Document</title>\n</head>\n<body>\n']
        
        # Get all text
        start = self.textbuffer.get_start_iter()
        end = self.textbuffer.get_end_iter()
        text = self.textbuffer.get_text(start, end, include_hidden_chars=True)
        
        # Process text with tags
        offset = 0
        html_parts = []
        last_offset = 0
        open_tags = []
        in_paragraph = False
        paragraph_align = None
        current_para_style = None
        
        while offset < len(text):
            # Get all tags at current position
            iter = self.textbuffer.get_iter_at_offset(offset)
            tags = iter.get_tags()
            
            # Check for tag changes
            if tags or offset == 0:
                # Append any text since last tag change
                if offset > last_offset:
                    html_parts.append(text[last_offset:offset])
                
                # Close any open format tags if we're at a tag boundary
                if offset > 0 and offset > last_offset:
                    # Close tags in reverse order they were opened
                    for tag in reversed(open_tags):
                        html_parts.append(f"</{tag}>")
                    open_tags = []
                
                # Open new tags
                open_tags = []
                alignment = None
                para_style = None
                line_spacing = None
                font_family = None
                font_size = None
                
                for tag in tags:
                    tag_name = tag.get_property("name")
                    
                    if tag_name == "bold":
                        html_parts.append("<b>")
                        open_tags.append("b")
                    elif tag_name == "italic":
                        html_parts.append("<i>")
                        open_tags.append("i")
                    elif tag_name == "underline":
                        html_parts.append("<u>")
                        open_tags.append("u")
                    elif tag_name.startswith("size-"):
                        size = tag_name.split("-")[1]
                        font_size = size
                    elif tag_name.startswith("font-"):
                        family = tag_name[5:]  # Strip 'font-' prefix
                        font_family = family
                    elif tag_name.startswith("color-"):
                        color = tag_name.split("-")[1]
                        html_parts.append(f'<span style="color: {color};">')
                        open_tags.append("span")
                    elif tag_name in ["left", "center", "right"]:
                        alignment = tag_name
                    elif tag_name == "heading-1":
                        para_style = "h1"
                    elif tag_name == "heading-2":
                        para_style = "h2"
                    elif tag_name == "heading-3":
                        para_style = "h3"
                    elif tag_name == "blockquote":
                        para_style = "blockquote"
                    elif tag_name == "preformatted":
                        para_style = "pre"
                    elif tag_name.startswith("spacing-"):
                        line_spacing = tag_name.split("-")[1]
                
                # Apply font styles if needed
                style_parts = []
                if font_family:
                    style_parts.append(f"font-family: {font_family}")
                if font_size:
                    style_parts.append(f"font-size: {font_size}pt")
                
                if style_parts:
                    style_attr = "; ".join(style_parts)
                    html_parts.append(f'<span style="{style_attr}">')
                    open_tags.append("span")
                
                # Handle paragraph style and alignment
                if para_style and not current_para_style:
                    # Close any previous paragraph
                    if in_paragraph:
                        html_parts.append("</p>")
                    
                    if para_style in ["h1", "h2", "h3"]:
                        html_parts.append(f'<{para_style}>')
                        in_paragraph = False  # Headings are their own block elements
                        current_para_style = para_style
                    elif para_style == "blockquote":
                        style_attr = "margin-left: 30px; margin-right: 30px; font-style: italic;"
                        if alignment:
                            style_attr += f" text-align: {alignment};"
                        if line_spacing:
                            style_attr += f" line-height: {line_spacing};"
                        html_parts.append(f'<blockquote style="{style_attr}">')
                        in_paragraph = True
                        current_para_style = para_style
                    elif para_style == "pre":
                        html_parts.append('<pre style="margin-left: 20px; font-family: monospace;">')
                        in_paragraph = True
                        current_para_style = para_style
                elif alignment and not in_paragraph:
                    style_attr = f"text-align: {alignment};"
                    if line_spacing:
                        style_attr += f" line-height: {line_spacing};"
                    html_parts.append(f'<p style="{style_attr}">')
                    in_paragraph = True
                    paragraph_align = alignment
                
                last_offset = offset
            
            # Check for line breaks
            if offset < len(text) and text[offset] == '\n':
                # Close tags before line break
                for tag in reversed(open_tags):
                    html_parts.append(f"</{tag}>")
                
                # Close paragraph or heading if open
                if in_paragraph:
                    html_parts.append("</p>")
                    in_paragraph = False
                elif current_para_style in ["h1", "h2", "h3"]:
                    html_parts.append(f"</{current_para_style}>")
                    current_para_style = None
                elif current_para_style == "blockquote":
                    html_parts.append("</blockquote>")
                    current_para_style = None
                elif current_para_style == "pre":
                    html_parts.append("</pre>")
                    current_para_style = None
                
                # Add line break in regular text
                if not current_para_style:
                    html_parts.append("<br>\n")
                
                # Reopen tags after line break
                need_paragraph = True
                
                # Determine paragraph style for next line
                next_iter = self.textbuffer.get_iter_at_offset(offset + 1)
                if next_iter.get_char():  # Make sure we're not at end of buffer
                    next_tags = next_iter.get_tags()
                    for tag in next_tags:
                        tag_name = tag.get_property("name")
                        next_para_style = None
                        next_alignment = None
                        next_line_spacing = None
                        
                        if tag_name == "heading-1":
                            html_parts.append("<h1>")
                            current_para_style = "h1"
                            need_paragraph = False
                        elif tag_name == "heading-2":
                            html_parts.append("<h2>")
                            current_para_style = "h2" 
                            need_paragraph = False
                        elif tag_name == "heading-3":
                            html_parts.append("<h3>")
                            current_para_style = "h3"
                            need_paragraph = False
                        elif tag_name == "blockquote":
                            style_attr = "margin-left: 30px; margin-right: 30px; font-style: italic;"
                            if next_alignment:
                                style_attr += f" text-align: {next_alignment};"
                            if next_line_spacing:
                                style_attr += f" line-height: {next_line_spacing};"
                            html_parts.append(f'<blockquote style="{style_attr}">')
                            current_para_style = "blockquote"
                            need_paragraph = False
                            in_paragraph = True
                        elif tag_name == "preformatted":
                            html_parts.append('<pre style="margin-left: 20px; font-family: monospace;">')
                            current_para_style = "pre"
                            need_paragraph = False
                            in_paragraph = True
                        elif tag_name in ["left", "center", "right"]:
                            next_alignment = tag_name
                        elif tag_name.startswith("spacing-"):
                            next_line_spacing = tag_name.split("-")[1]
                
                # Open regular paragraph if needed
                if need_paragraph:
                    style_attr = ""
                    if paragraph_align:
                        style_attr += f"text-align: {paragraph_align};"
                    
                    if style_attr:
                        html_parts.append(f'<p style="{style_attr}">')
                    else:
                        html_parts.append('<p>')
                    in_paragraph = True
                
                # Reopen any styling tags
                for tag in open_tags:
                    if tag == "b":
                        html_parts.append("<b>")
                    elif tag == "i":
                        html_parts.append("<i>")
                    elif tag == "u":
                        html_parts.append("<u>")
                    elif tag == "span":
                        # This is a simplified approach; in a full implementation,
                        # you'd need to track which span had which attributes
                        html_parts.append("<span>")
                
                last_offset = offset + 1
            
            offset += 1
        
        # Append any remaining text
        if last_offset < len(text):
            html_parts.append(text[last_offset:])
        
          # Close any open tags
        for tag in reversed(open_tags):
            html_parts.append(f"</{tag}>")
        
        # Close paragraph, heading, or other block element if open
        if in_paragraph:
            html_parts.append("</p>")
        elif current_para_style in ["h1", "h2", "h3"]:
            html_parts.append(f"</{current_para_style}>")
        elif current_para_style == "blockquote":
            html_parts.append("</blockquote>")
        elif current_para_style == "pre":
            html_parts.append("</pre>")
        
        # Join all parts
        html.append(''.join(html_parts))
        html.append('\n</body>\n</html>')
        
        return ''.join(html)
    
    def on_about_clicked(self, action, parameter):
        """Show about dialog"""
        about = Adw.AboutWindow.new()
        about.set_application_name("Rich Text Editor")
        about.set_version("1.0")
        about.set_developer_name("PyGObject Developer")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments("A rich text editor with HTML support.")
        about.set_website("https://github.com/example/rich-text-editor")
        about.set_transient_for(self.win)
        about.present()
    
    def on_quit(self, action, parameter):
        """Quit the application"""
        if self.modified:
            dialog = Adw.MessageDialog.new(self.win, "Save changes?", 
                                          "Do you want to save changes to the current document?")
            dialog.add_response("discard", "Discard")
            dialog.add_response("cancel", "Cancel")
            dialog.add_response("save", "Save")
            dialog.set_default_response("save")
            dialog.set_close_response("cancel")
            
            dialog.connect("response", self.on_quit_dialog_response)
            dialog.present()
        else:
            self.quit()
    
    def on_quit_dialog_response(self, dialog, response):
        """Handle response from quit dialog"""
        if response == "save":
            self.on_save_clicked(None, None)
            self.quit()
        elif response == "discard":
            self.quit()

    # In your open_file method, modify the code to call the appropriate HTML importer
    def open_file(self, filepath):
        """Open a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Clear existing content
            self.textbuffer.set_text("")
            
            if filepath.lower().endswith(('.html', '.htm')):
                # First try using the improved HTML importer
                try:
                    self.load_html_improved(content)
                except Exception as e:
                    print(f"Advanced HTML import failed: {str(e)}")
                    # Fallback to simpler method if the improved one fails
                    self.load_html_simple(content)
            else:
                # Just load as plain text
                self.textbuffer.set_text(content)
            
            self.current_file = filepath
            self.modified = False
            self.update_statusbar()
            
        except Exception as e:
            dialog = Adw.MessageDialog.new(self.win, "Error", f"Failed to open file: {str(e)}")
            dialog.add_response("ok", "OK")
            dialog.present()

    def load_html_improved(self, html_content):
        """Load HTML content with improved handling for whitespace and special characters"""
        try:
            # Try using a Python HTML parser for more accurate results
            from html.parser import HTMLParser
            import html
            
            class HTMLToTextParser(HTMLParser):
                def __init__(self, textbuffer):
                    super().__init__()
                    self.textbuffer = textbuffer
                    self.in_body = False
                    self.in_head = False
                    self.in_title = False
                    self.tag_stack = []
                    self.format_stack = []
                    self.skip_stack = []  # Tags whose content should be skipped
                    
                    # Track if we need a newline before next content
                    self.need_newline = False
                    self.had_content = False
                
                def handle_starttag(self, tag, attrs):
                    tag = tag.lower()
                    
                    # Skip head section and its contents
                    if tag == 'head':
                        self.in_head = True
                        self.skip_stack.append(tag)
                        return
                    
                    if self.in_head:
                        self.skip_stack.append(tag)
                        return
                    
                    # Skip script, style and other non-content tags
                    if tag in ['script', 'style', 'meta', 'link']:
                        self.skip_stack.append(tag)
                        return
                    
                    # Track when we enter the body
                    if tag == 'body':
                        self.in_body = True
                    
                    # Handle block elements - add newline before if needed
                    if tag in ['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'blockquote', 'pre']:
                        self.need_newline = True
                    
                    # Track tag stack for proper nesting
                    self.tag_stack.append(tag)
                    
                    # Handle formatting tags
                    if tag in ['b', 'strong', 'i', 'em', 'u', 'h1', 'h2', 'h3', 'blockquote', 'pre']:
                        # Remember position to apply formatting later
                        cursor_mark = self.textbuffer.get_insert()
                        cursor_pos = self.textbuffer.get_iter_at_mark(cursor_mark).get_offset()
                        self.format_stack.append((tag, cursor_pos))
                    
                    # Handle line breaks
                    if tag == 'br':
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                        self.need_newline = False
                
                def handle_endtag(self, tag):
                    tag = tag.lower()
                    
                    # Handle end of head section
                    if tag == 'head':
                        self.in_head = False
                        if self.skip_stack and self.skip_stack[-1] == tag:
                            self.skip_stack.pop()
                        return
                    
                    # Skip content in skipped tags
                    if self.skip_stack:
                        if self.skip_stack[-1] == tag:
                            self.skip_stack.pop()
                        return
                    
                    # Handle body end
                    if tag == 'body':
                        self.in_body = False
                    
                    # Pop last tag from stack if it matches
                    if self.tag_stack and self.tag_stack[-1] == tag:
                        self.tag_stack.pop()
                    
                    # Handle end of formatting tags
                    if tag in ['b', 'strong', 'i', 'em', 'u', 'h1', 'h2', 'h3', 'blockquote', 'pre']:
                        # Find matching start tag in format stack
                        for i in range(len(self.format_stack) - 1, -1, -1):
                            if self.format_stack[i][0] == tag or \
                               (tag in ['b', 'strong'] and self.format_stack[i][0] in ['b', 'strong']) or \
                               (tag in ['i', 'em'] and self.format_stack[i][0] in ['i', 'em']):
                                fmt_tag, start_pos = self.format_stack.pop(i)
                                start_iter = self.textbuffer.get_iter_at_offset(start_pos)
                                end_iter = self.textbuffer.get_end_iter()
                                
                                # Apply formatting
                                if fmt_tag in ['b', 'strong']:
                                    self.textbuffer.apply_tag_by_name("bold", start_iter, end_iter)
                                elif fmt_tag in ['i', 'em']:
                                    self.textbuffer.apply_tag_by_name("italic", start_iter, end_iter)
                                elif fmt_tag == 'u':
                                    self.textbuffer.apply_tag_by_name("underline", start_iter, end_iter)
                                elif fmt_tag == 'h1':
                                    self.textbuffer.apply_tag_by_name("heading-1", start_iter, end_iter)
                                elif fmt_tag == 'h2':
                                    self.textbuffer.apply_tag_by_name("heading-2", start_iter, end_iter)
                                elif fmt_tag == 'h3':
                                    self.textbuffer.apply_tag_by_name("heading-3", start_iter, end_iter)
                                elif fmt_tag == 'blockquote':
                                    self.textbuffer.apply_tag_by_name("blockquote", start_iter, end_iter)
                                elif fmt_tag == 'pre':
                                    self.textbuffer.apply_tag_by_name("preformatted", start_iter, end_iter)
                                break
                    
                    # Add newline after block elements if there was actual content
                    if tag in ['div', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'ul', 'ol', 'li', 'table', 'blockquote', 'pre'] and self.had_content:
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), "\n")
                        self.need_newline = False
                        self.had_content = False
                
                def handle_data(self, data):
                    # Skip content in skipped tags
                    if self.skip_stack:
                        return
                    
                    if data.strip():  # Only process non-whitespace
                        # Add a newline before content if needed
                        if self.need_newline:
                            cursor_mark = self.textbuffer.get_insert()
                            cursor_pos = self.textbuffer.get_iter_at_mark(cursor_mark).get_offset()
                            if cursor_pos > 0:
                                end_iter = self.textbuffer.get_end_iter()
                                if not end_iter.starts_line():
                                    self.textbuffer.insert(end_iter, "\n")
                            self.need_newline = False
                        
                        # Insert the actual text
                        self.textbuffer.insert(self.textbuffer.get_end_iter(), data)
                        self.had_content = True
            
            # Clear the buffer first
            self.textbuffer.set_text("")
            
            # Create parser and feed the HTML content
            parser = HTMLToTextParser(self.textbuffer)
            parser.feed(html_content)
            
        except ImportError:
            # Fallback to the basic parser if html.parser is not available
            self.load_html_simple(html_content)
        except Exception as e:
            print(f"HTML parsing error: {str(e)}")
            # Fallback to the basic parser
            self.load_html_simple(html_content)

    def load_html_simple(self, html_content):
        """Simple HTML parser that just extracts text with minimal formatting"""
        try:
            import re
            import html
            
            # Clear buffer
            self.textbuffer.set_text("")
            
            # Remove all scripts, styles, and head sections first
            html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<style.*?</style>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<head.*?</head>', '', html_content, flags=re.DOTALL)
            
            # Replace common block elements with newlines to maintain structure
            html_content = re.sub(r'<(div|p|h\d|li|tr|blockquote)[^>]*>', '\n', html_content)
            html_content = re.sub(r'</(div|p|h\d|li|tr|blockquote)>', '\n', html_content)
            
            # Handle line breaks
            html_content = re.sub(r'<br[^>]*>', '\n', html_content)
            
            # Remove all remaining HTML tags
            html_content = re.sub(r'<[^>]*>', '', html_content)
            
            # Decode HTML entities
            html_content = html.unescape(html_content)
            
            # Fix excessive whitespace
            html_content = re.sub(r'\n{3,}', '\n\n', html_content)  # No more than two consecutive newlines
            html_content = re.sub(r' {2,}', ' ', html_content)      # No more than one consecutive space
            html_content = html_content.strip()
            
            # Set the text with minimal formatting
            self.textbuffer.set_text(html_content)
            
        except Exception as e:
            print(f"Simple HTML parsing error: {str(e)}")
            # Last resort fallback - just strip all tags
            try:
                text = re.sub(r'<[^>]*>', '', html_content)
                text = html.unescape(text)
                self.textbuffer.set_text(text.strip())
            except:
                # If all else fails, just set the raw content
                self.textbuffer.set_text(html_content)


def main(args):
    app = RichTextEditor()
    return app.run(args)

if __name__ == "__main__":
    sys.exit(main(sys.argv))
