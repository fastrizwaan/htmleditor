import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, GLib, Gio, Pango, PangoCairo

def create_formatting_toolbar(self, win):
    """Create the toolbar for formatting options with toggle buttons and dropdowns"""
    # Main horizontal container for the entire toolbar
    formatting_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    formatting_toolbar.set_margin_start(0)
    formatting_toolbar.set_margin_end(0)
    formatting_toolbar.set_margin_top(0)
    formatting_toolbar.set_margin_bottom(4)
    
# === LEFT SECTION ===
    # Create vertical box for the left section
    left_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    left_section.set_hexpand(False)
    
    # Create horizontal box for the top row
    top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    top_row.set_margin_start(5)
    top_row.set_margin_top(5)  # Add top margin to align with right section
    
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

    # Paragraph, font family, font size box        
    pfs_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    pfs_box.add_css_class("linked")
    pfs_box.set_margin_start(2)
    pfs_box.set_margin_end(6)
    
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
    win.paragraph_style_dropdown.set_size_request(122, -1)
    pfs_box.append(win.paragraph_style_dropdown)
    
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
    win.font_dropdown.set_size_request(282, -1)
    win.font_dropdown.set_hexpand(False)
    
    # Create a factory only for the BUTTON part of the dropdown
    button_factory = Gtk.SignalListItemFactory()
    
    def setup_button_label(factory, list_item):
        label = Gtk.Label()
        label.set_ellipsize(Pango.EllipsizeMode.END)  # Ellipsize button text
        label.set_xalign(0)
        label.set_margin_start(6)
        label.set_margin_end(6)
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
        label.set_margin_start(6)
        label.set_margin_end(6)
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
    
    pfs_box.append(win.font_dropdown)
    

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
    win.font_size_dropdown.set_size_request(50, -1)
    
    # Set initial size (12pt)
    initial_size = 6  # Index of size 12 in our list
    win.font_size_dropdown.set_selected(initial_size)
    
    # Connect signal handler
    win.font_size_handler_id = win.font_size_dropdown.connect(
        "notify::selected", lambda dd, param: self.on_font_size_changed(win, dd))
    
    pfs_box.append(win.font_size_dropdown)
    top_row.append(pfs_box)
    
    # Add the top row to the left section
    left_section.append(top_row)
    
    # Create second row for formatting buttons
    bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    bottom_row.set_margin_start(5)
    bottom_row.set_margin_top(4)
    bottom_row.set_margin_bottom(4)
    
    # Create first button group (basic formatting)
    button_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    button_group.set_margin_start(2)
    button_group.set_margin_end(5)
    
    # Bold button
    win.bold_button = Gtk.ToggleButton(icon_name="format-text-bold-symbolic")
    win.bold_button.set_tooltip_text("Bold")
    win.bold_button.set_focus_on_click(False)
    win.bold_button.set_size_request(40, 36)
    win.bold_handler_id = win.bold_button.connect("toggled", lambda btn: self.on_bold_toggled(win, btn))
    button_group.append(win.bold_button)
    
    # Italic button
    win.italic_button = Gtk.ToggleButton(icon_name="format-text-italic-symbolic")
    win.italic_button.set_tooltip_text("Italic")
    win.italic_button.set_focus_on_click(False)
    win.italic_button.set_size_request(40, 36)
    win.italic_handler_id = win.italic_button.connect("toggled", lambda btn: self.on_italic_toggled(win, btn))
    button_group.append(win.italic_button)
    
    # Underline button
    win.underline_button = Gtk.ToggleButton(icon_name="format-text-underline-symbolic")
    win.underline_button.set_tooltip_text("Underline")
    win.underline_button.set_focus_on_click(False)
    win.underline_button.set_size_request(40, 36)
    win.underline_handler_id = win.underline_button.connect("toggled", lambda btn: self.on_underline_toggled(win, btn))
    button_group.append(win.underline_button)
    
    # Strikeout button
    win.strikeout_button = Gtk.ToggleButton(icon_name="format-text-strikethrough-symbolic")
    win.strikeout_button.set_tooltip_text("Strikeout")
    win.strikeout_button.set_focus_on_click(False)
    win.strikeout_button.set_size_request(40, 36)
    win.strikeout_handler_id = win.strikeout_button.connect("toggled", lambda btn: self.on_strikeout_toggled(win, btn))
    button_group.append(win.strikeout_button)
    
    # Subscript button
    win.subscript_button = Gtk.ToggleButton(icon_name="format-text-subscript-symbolic")
    win.subscript_button.set_tooltip_text("Subscript")
    win.subscript_button.set_focus_on_click(False)
    win.subscript_button.set_size_request(40, 36)
    win.subscript_handler_id = win.subscript_button.connect("toggled", lambda btn: self.on_subscript_toggled(win, btn))
    button_group.append(win.subscript_button)
    
    # Superscript button
    win.superscript_button = Gtk.ToggleButton(icon_name="format-text-superscript-symbolic")
    win.superscript_button.set_tooltip_text("Superscript")
    win.superscript_button.set_focus_on_click(False)
    win.superscript_button.set_size_request(40, 36)
    win.superscript_handler_id = win.superscript_button.connect("toggled", lambda btn: self.on_superscript_toggled(win, btn))
    button_group.append(win.superscript_button)    
    
    # Create second button group for colors and other formatting
    button_group2 = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=0)        
    button_group2.set_margin_start(0)
    button_group2.set_margin_end(5)

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

    # Add separator
    separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
    separator.set_margin_bottom(6)
    font_color_box_menu.append(separator)

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
    button_group2.append(win.font_color_button)
    
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
    button_group2.append(win.bg_color_button)
    
    # Clear formatting button
    clear_formatting_button = Gtk.Button(icon_name="eraser-symbolic")
    clear_formatting_button.set_tooltip_text("Remove Text Formatting")
    clear_formatting_button.set_size_request(40, 36)
    clear_formatting_button.connect("clicked", lambda btn: self.on_clear_formatting_clicked(win, btn))
    button_group2.append(clear_formatting_button)
    
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
    button_group2.append(case_menu_button)
    
    # Add the button groups to the bottom row
    bottom_row.append(button_group)
    bottom_row.append(button_group2)
    
    # Add the bottom row to the left section
    left_section.append(bottom_row)
    
# === RIGHT SECTION ===
    # Create vertical box for the right section
    right_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
    right_section.set_margin_start(5)
    right_section.set_margin_end(5)
    right_section.set_hexpand(False)
    right_section.set_valign(Gtk.Align.CENTER)  # Align vertically to center
    
    # Create horizontal box for the top row in right section
    right_top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    right_top_row.set_margin_top(5)
    
    # Create linked button group for list/indent controls
    list_indent_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    
    # Indent button
    indent_button = Gtk.Button(icon_name="format-indent-more-symbolic")
    indent_button.set_tooltip_text("Increase Indent")
    indent_button.set_focus_on_click(False)
    indent_button.set_size_request(40, 36)
    indent_button.connect("clicked", lambda btn: self.on_indent_clicked(win, btn))
    list_indent_group.append(indent_button)
    
    # Outdent button
    outdent_button = Gtk.Button(icon_name="format-indent-less-symbolic")
    outdent_button.set_tooltip_text("Decrease Indent")
    outdent_button.set_focus_on_click(False)
    outdent_button.set_size_request(40, 36)
    outdent_button.connect("clicked", lambda btn: self.on_outdent_clicked(win, btn))
    list_indent_group.append(outdent_button)
    
    # Bullet List button
    win.bullet_list_button = Gtk.ToggleButton(icon_name="view-list-bullet-symbolic")
    win.bullet_list_button.set_tooltip_text("Bullet List")
    win.bullet_list_button.set_focus_on_click(False)
    win.bullet_list_button.set_size_request(40, 36)
    # Store the handler ID directly on the button
    win.bullet_list_button.handler_id = win.bullet_list_button.connect("toggled", 
        lambda btn: self.on_bullet_list_toggled(win, btn))
    list_indent_group.append(win.bullet_list_button)

    # Numbered List button
    win.numbered_list_button = Gtk.ToggleButton(icon_name="view-list-ordered-symbolic")
    win.numbered_list_button.set_tooltip_text("Numbered List")
    win.numbered_list_button.set_focus_on_click(False)
    win.numbered_list_button.set_size_request(40, 36)
    # Store the handler ID directly on the button
    win.numbered_list_button.handler_id = win.numbered_list_button.connect("toggled", 
        lambda btn: self.on_numbered_list_toggled(win, btn))
    list_indent_group.append(win.numbered_list_button)
    
    # Add list/indent group to right top row
    right_top_row.append(list_indent_group)
    
    # Add the right top row to the right section
    right_section.append(right_top_row)
    
    # Create horizontal box for the bottom row in right section
    right_bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
    right_bottom_row.set_margin_top(4)
    right_bottom_row.set_margin_bottom(4)
    
    # Create linked button group for alignment controls
    alignment_group = Gtk.Box(css_classes=["linked"], orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
    
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
    
    # Add alignment group to right bottom row
    right_bottom_row.append(alignment_group)
    
    # Add the right bottom row to the right section
    right_section.append(right_bottom_row)
    
    # Add left section to the main toolbar
    formatting_toolbar.append(left_section)
    
    # Add right section to the main toolbar
    formatting_toolbar.append(right_section)
    
    return formatting_toolbar  

def on_bold_shortcut(self, win, *args):
    """Handle Ctrl+B shortcut for bold formatting"""
    # Execute the bold command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('bold', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('bold');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.bold_handler_id is not None:
        win.bold_button.handler_block(win.bold_handler_id)
        win.bold_button.set_active(not win.bold_button.get_active())
        win.bold_button.handler_unblock(win.bold_handler_id)
    
    win.statusbar.set_text("Bold formatting applied")
    return True

def on_italic_shortcut(self, win, *args):
    """Handle Ctrl+I shortcut for italic formatting"""
    # Execute the italic command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('italic', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('italic');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.italic_handler_id is not None:
        win.italic_button.handler_block(win.italic_handler_id)
        win.italic_button.set_active(not win.italic_button.get_active())
        win.italic_button.handler_unblock(win.italic_handler_id)
    
    win.statusbar.set_text("Italic formatting applied")
    return True

def on_underline_shortcut(self, win, *args):
    """Handle Ctrl+U shortcut for underline formatting"""
    # Execute the underline command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('underline', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('underline');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.underline_handler_id is not None:
        win.underline_button.handler_block(win.underline_handler_id)
        win.underline_button.set_active(not win.underline_button.get_active())
        win.underline_button.handler_unblock(win.underline_handler_id)
    
    win.statusbar.set_text("Underline formatting applied")
    return True

def on_strikeout_shortcut(self, win, *args):
    """Handle Ctrl+Shift+X shortcut for strikeout formatting"""
    # Execute the strikeout command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('strikeThrough', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('strikeThrough');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.strikeout_handler_id is not None:
        win.strikeout_button.handler_block(win.strikeout_handler_id)
        win.strikeout_button.set_active(not win.strikeout_button.get_active())
        win.strikeout_button.handler_unblock(win.strikeout_handler_id)
    
    win.statusbar.set_text("Strikeout formatting applied")
    return True  

def on_subscript_shortcut(self, win, *args):
    """Handle Ctrl+, shortcut for subscript formatting"""
    # Check if superscript is active and deactivate it if needed
    if win.superscript_button.get_active():
        # Block superscript handler to prevent infinite loop
        if win.superscript_handler_id is not None:
            win.superscript_button.handler_block(win.superscript_handler_id)
        
        # Deactivate superscript button
        win.superscript_button.set_active(False)
        
        # Unblock superscript handler
        if win.superscript_handler_id is not None:
            win.superscript_button.handler_unblock(win.superscript_handler_id)
    
    # Execute the subscript command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('subscript', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('subscript');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.subscript_handler_id is not None:
        win.subscript_button.handler_block(win.subscript_handler_id)
        win.subscript_button.set_active(not win.subscript_button.get_active())
        win.subscript_button.handler_unblock(win.subscript_handler_id)
    
    win.statusbar.set_text("Subscript formatting applied")
    return True

def on_superscript_shortcut(self, win, *args):
    """Handle Ctrl+. shortcut for superscript formatting"""
    # Check if subscript is active and deactivate it if needed
    if win.subscript_button.get_active():
        # Block subscript handler to prevent infinite loop
        if win.subscript_handler_id is not None:
            win.subscript_button.handler_block(win.subscript_handler_id)
        
        # Deactivate subscript button
        win.subscript_button.set_active(False)
        
        # Unblock subscript handler
        if win.subscript_handler_id is not None:
            win.subscript_button.handler_unblock(win.subscript_handler_id)
    
    # Execute the superscript command directly in JavaScript
    self.execute_js(win, """
        document.execCommand('superscript', false, null);
        // Return the current state so we can update the button
        document.queryCommandState('superscript');
    """)
    
    # Immediately toggle the button state to provide instant feedback
    if win.superscript_handler_id is not None:
        win.superscript_button.handler_block(win.superscript_handler_id)
        win.superscript_button.set_active(not win.superscript_button.get_active())
        win.superscript_button.handler_unblock(win.superscript_handler_id)
    
    win.statusbar.set_text("Superscript formatting applied")
    return True

def on_bold_toggled(self, win, button):
    """Handle bold toggle button state changes"""
    # Block the handler temporarily
    if win.bold_handler_id is not None:
        button.handler_block(win.bold_handler_id)
    
    try:
        # Apply formatting
        self.execute_js(win, "document.execCommand('bold', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.bold_handler_id is not None:
            button.handler_unblock(win.bold_handler_id)

def on_italic_toggled(self, win, button):
    """Handle italic toggle button state changes"""
    # Block the handler temporarily
    if win.italic_handler_id is not None:
        button.handler_block(win.italic_handler_id)
    
    try:
        # Apply formatting
        self.execute_js(win, "document.execCommand('italic', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.italic_handler_id is not None:
            button.handler_unblock(win.italic_handler_id)

def on_underline_toggled(self, win, button):
    """Handle underline toggle button state changes"""
    # Block the handler temporarily
    if win.underline_handler_id is not None:
        button.handler_block(win.underline_handler_id)
    
    try:
        # Apply formatting
        self.execute_js(win, "document.execCommand('underline', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.underline_handler_id is not None:
            button.handler_unblock(win.underline_handler_id)

def on_strikeout_toggled(self, win, button):
    """Handle strikeout toggle button state changes"""
    # Block the handler temporarily
    if win.strikeout_handler_id is not None:
        button.handler_block(win.strikeout_handler_id)
    
    try:
        # Apply formatting
        self.execute_js(win, "document.execCommand('strikeThrough', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.strikeout_handler_id is not None:
            button.handler_unblock(win.strikeout_handler_id)

def on_subscript_toggled(self, win, button):
    """Handle subscript toggle button state changes"""
    # Block the handler temporarily
    if win.subscript_handler_id is not None:
        button.handler_block(win.subscript_handler_id)
    
    try:
        # Get current button state (after toggle)
        is_active = button.get_active()
        
        # If activating subscript, ensure superscript is deactivated
        if is_active and win.superscript_button.get_active():
            # Block superscript handler to prevent infinite loop
            if win.superscript_handler_id is not None:
                win.superscript_button.handler_block(win.superscript_handler_id)
            
            # Deactivate superscript button
            win.superscript_button.set_active(False)
            
            # Unblock superscript handler
            if win.superscript_handler_id is not None:
                win.superscript_button.handler_unblock(win.superscript_handler_id)
        
        # Apply formatting
        self.execute_js(win, "document.execCommand('subscript', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.subscript_handler_id is not None:
            button.handler_unblock(win.subscript_handler_id)

# Update the superscript toggle handler to deactivate subscript if needed
def on_superscript_toggled(self, win, button):
    """Handle superscript toggle button state changes"""
    # Block the handler temporarily
    if win.superscript_handler_id is not None:
        button.handler_block(win.superscript_handler_id)
    
    try:
        # Get current button state (after toggle)
        is_active = button.get_active()
        
        # If activating superscript, ensure subscript is deactivated
        if is_active and win.subscript_button.get_active():
            # Block subscript handler to prevent infinite loop
            if win.subscript_handler_id is not None:
                win.subscript_button.handler_block(win.subscript_handler_id)
            
            # Deactivate subscript button
            win.subscript_button.set_active(False)
            
            # Unblock subscript handler
            if win.subscript_handler_id is not None:
                win.subscript_button.handler_unblock(win.subscript_handler_id)
        
        # Apply formatting
        self.execute_js(win, "document.execCommand('superscript', false, null);")
        
        # Check if find bar has focus before setting focus to webview
        find_bar_active = win.find_bar_revealer.get_reveal_child()
        find_entry_has_focus = False
        
        if find_bar_active:
            find_entry_has_focus = win.find_entry.has_focus() or win.replace_entry.has_focus()
        
        # Only grab focus to webview if find entries don't have focus
        if not find_entry_has_focus:
            win.webview.grab_focus()
    finally:
        # Unblock the handler
        if win.superscript_handler_id is not None:
            button.handler_unblock(win.superscript_handler_id)


def on_formatting_changed(self, win, manager, result):
    """Update toggle button states based on current formatting"""
    try:
        # Extract the message differently based on WebKit version
        message = None
        if hasattr(result, 'get_js_value'):
            message = result.get_js_value().to_string()
        elif hasattr(result, 'to_string'):
            message = result.to_string()
        elif hasattr(result, 'get_value'):
            message = result.get_value().get_string()
        else:
            # Try to get the value directly
            try:
                message = str(result)
            except:
                print("Could not extract message from result")
                return
        
        # Parse the JSON
        import json
        format_state = json.loads(message)
        
        # Update basic formatting button states without triggering their handlers
        if win.bold_handler_id is not None:
            win.bold_button.handler_block(win.bold_handler_id)
            win.bold_button.set_active(format_state.get('bold', False))
            win.bold_button.handler_unblock(win.bold_handler_id)
        
        if win.italic_handler_id is not None:
            win.italic_button.handler_block(win.italic_handler_id)
            win.italic_button.set_active(format_state.get('italic', False))
            win.italic_button.handler_unblock(win.italic_handler_id)
        
        if win.underline_handler_id is not None:
            win.underline_button.handler_block(win.underline_handler_id)
            win.underline_button.set_active(format_state.get('underline', False))
            win.underline_button.handler_unblock(win.underline_handler_id)
            
        if win.strikeout_handler_id is not None:
            win.strikeout_button.handler_block(win.strikeout_handler_id)
            win.strikeout_button.set_active(format_state.get('strikeThrough', False))
            win.strikeout_button.handler_unblock(win.strikeout_handler_id)
        
        # Update subscript and superscript buttons
        if win.subscript_handler_id is not None:
            win.subscript_button.handler_block(win.subscript_handler_id)
            win.subscript_button.set_active(format_state.get('subscript', False))
            win.subscript_button.handler_unblock(win.subscript_handler_id)
            
        if win.superscript_handler_id is not None:
            win.superscript_button.handler_block(win.superscript_handler_id)
            win.superscript_button.set_active(format_state.get('superscript', False))
            win.superscript_button.handler_unblock(win.superscript_handler_id)
        
        # Update list button states if they exist
        if hasattr(win, 'bullet_list_button') and hasattr(win.bullet_list_button, 'handler_id'):
            win.bullet_list_button.handler_block(win.bullet_list_button.handler_id)
            win.bullet_list_button.set_active(format_state.get('bulletList', False))
            win.bullet_list_button.handler_unblock(win.bullet_list_button.handler_id)
        
        if hasattr(win, 'numbered_list_button') and hasattr(win.numbered_list_button, 'handler_id'):
            win.numbered_list_button.handler_block(win.numbered_list_button.handler_id)
            win.numbered_list_button.set_active(format_state.get('numberedList', False))
            win.numbered_list_button.handler_unblock(win.numbered_list_button.handler_id)
        
        # Update alignment button states
        if hasattr(win, 'alignment_buttons'):
            current_alignment = format_state.get('alignment', 'left')
            for align_type, button in win.alignment_buttons.items():
                if hasattr(button, 'handler_id'):
                    button.handler_block(button.handler_id)
                    button.set_active(align_type == current_alignment)
                    button.handler_unblock(button.handler_id)
        
        # Update paragraph style dropdown
        paragraph_style = format_state.get('paragraphStyle', 'Normal')
        if win.paragraph_style_handler_id is not None and hasattr(win, 'paragraph_style_dropdown'):
            # Map paragraph style to dropdown index
            style_indices = {
                'Normal': 0,
                'Heading 1': 1,
                'Heading 2': 2,
                'Heading 3': 3,
                'Heading 4': 4,
                'Heading 5': 5,
                'Heading 6': 6
            }
            index = style_indices.get(paragraph_style, 0)
            
            # Update the dropdown without triggering the handler
            win.paragraph_style_dropdown.handler_block(win.paragraph_style_handler_id)
            win.paragraph_style_dropdown.set_selected(index)
            win.paragraph_style_dropdown.handler_unblock(win.paragraph_style_handler_id)
        
        # Update font family dropdown
        font_family = format_state.get('fontFamily', '')
        if win.font_handler_id is not None and hasattr(win, 'font_dropdown') and font_family:
            # Find the index of the font in the dropdown
            font_model = win.font_dropdown.get_model()
            found_index = -1
            
            # Iterate through the model to find the matching font
            for i in range(font_model.get_n_items()):
                item = font_model.get_item(i)
                if item and item.get_string().lower() == font_family.lower():
                    found_index = i
                    break
            
            if found_index >= 0:
                # Update the dropdown without triggering the handler
                win.font_dropdown.handler_block(win.font_handler_id)
                win.font_dropdown.set_selected(found_index)
                win.font_dropdown.handler_unblock(win.font_handler_id)
        
        # Update font size dropdown
        font_size = format_state.get('fontSize', '')
        if win.font_size_handler_id is not None and hasattr(win, 'font_size_dropdown') and font_size:
            # Find the index of the size in the dropdown
            size_model = win.font_size_dropdown.get_model()
            found_index = -1
            
            # Iterate through the model to find the matching size
            for i in range(size_model.get_n_items()):
                item = size_model.get_item(i)
                if item and item.get_string() == font_size:
                    found_index = i
                    break
            
            if found_index >= 0:
                # Update the dropdown without triggering the handler
                win.font_size_dropdown.handler_block(win.font_size_handler_id)
                win.font_size_dropdown.set_selected(found_index)
                win.font_size_dropdown.handler_unblock(win.font_size_handler_id)
            
    except Exception as e:
        print(f"Error updating formatting buttons: {e}")


def on_indent_clicked(self, win, button):
    """Handle indent button click"""
    js_code = """
    (function() {
        document.execCommand('indent', false, null);
        return true;
    })();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text("Increased indent")
    win.webview.grab_focus()

def on_outdent_clicked(self, win, button):
    """Handle outdent button click"""
    js_code = """
    (function() {
        document.execCommand('outdent', false, null);
        return true;
    })();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text("Decreased indent")
    win.webview.grab_focus()

def on_bullet_list_toggled(self, win, button):
    """Handle bullet list button toggle"""
    js_code = """
    (function() {
        document.execCommand('insertUnorderedList', false, null);
        return document.queryCommandState('insertUnorderedList');
    })();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text("Toggled bullet list")
    win.webview.grab_focus()

def on_numbered_list_toggled(self, win, button):
    """Handle numbered list button toggle"""
    js_code = """
    (function() {
        document.execCommand('insertOrderedList', false, null);
        return document.queryCommandState('insertOrderedList');
    })();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text("Toggled numbered list")
    win.webview.grab_focus()

def _update_alignment_buttons(self, win, active_alignment):
    """Update alignment toggle button states"""
    for align_type, button in win.alignment_buttons.items():
        # Temporarily block signal handlers to prevent recursion
        handler_id = button.handler_id if hasattr(button, 'handler_id') else None
        if handler_id:
            button.handler_block(handler_id)
        
        # Set active state based on current alignment
        button.set_active(align_type == active_alignment)
        
        # Unblock signal handlers
        if handler_id:
            button.handler_unblock(handler_id)

def on_align_left_toggled(self, win, button):
    """Handle align left button toggle"""
    # Execute alignment command with list support
    js_code = """
    (function() {
        applyAlignmentWithListSupport('left');
        return 'left';  // Return the alignment type
        
        function applyAlignmentWithListSupport(alignment) {
            // Get the current selection
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            
            // First, apply standard alignment using execCommand
            document.execCommand('justifyLeft', false, null);
            
            // Get all affected list elements
            const commonAncestor = range.commonAncestorContainer;
            let container;
            
            if (commonAncestor.nodeType === 3) { // Text node
                container = commonAncestor.parentNode;
            } else {
                container = commonAncestor;
            }
            
            // Find if we're dealing with a list
            const listContainer = findListContainer(container);
            
            if (listContainer) {
                // Apply additional CSS for list alignment
                const listItems = listContainer.querySelectorAll('li');
                listItems.forEach(li => {
                    // Set the CSS for list item alignment
                    li.style.textAlign = 'left';
                    li.style.listStylePosition = 'outside'; // Default
                });
                
                // Reset the list container padding/margin
                listContainer.style.paddingLeft = '';
                listContainer.style.marginLeft = '';
            }
        }
        
        // Helper function to find the list container (ul/ol)
        function findListContainer(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'UL' || element.tagName === 'OL') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
    })();
    """
    
    self.execute_js(win, js_code)
    
    # Update all alignment buttons
    self._update_alignment_buttons(win, 'left')
    
    win.statusbar.set_text("Aligned text left")
    win.webview.grab_focus()

def on_align_center_toggled(self, win, button):
    """Handle align center button toggle"""
    # Execute alignment command with list support
    js_code = """
    (function() {
        applyAlignmentWithListSupport('center');
        return 'center';  // Return the alignment type
        
        function applyAlignmentWithListSupport(alignment) {
            // Get the current selection
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            
            // First, apply standard alignment using execCommand
            document.execCommand('justifyCenter', false, null);
            
            // Get all affected list elements
            const commonAncestor = range.commonAncestorContainer;
            let container;
            
            if (commonAncestor.nodeType === 3) { // Text node
                container = commonAncestor.parentNode;
            } else {
                container = commonAncestor;
            }
            
            // Find if we're dealing with a list
            const listContainer = findListContainer(container);
            
            if (listContainer) {
                // Apply additional CSS for list alignment
                const listItems = listContainer.querySelectorAll('li');
                listItems.forEach(li => {
                    // Set the CSS for list item alignment
                    li.style.textAlign = 'center';
                    li.style.listStylePosition = 'inside';
                });
                
                // Adjust the list container too
                listContainer.style.paddingLeft = '0';
                listContainer.style.marginLeft = '0';
            }
        }
        
        // Helper function to find the list container (ul/ol)
        function findListContainer(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'UL' || element.tagName === 'OL') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
    })();
    """
    
    self.execute_js(win, js_code)
    
    # Update all alignment buttons
    self._update_alignment_buttons(win, 'center')
    
    win.statusbar.set_text("Aligned text center")
    win.webview.grab_focus()

def on_align_right_toggled(self, win, button):
    """Handle align right button toggle"""
    # Execute alignment command with list support
    js_code = """
    (function() {
        applyAlignmentWithListSupport('right');
        return 'right';  // Return the alignment type
        
        function applyAlignmentWithListSupport(alignment) {
            // Get the current selection
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            
            // First, apply standard alignment using execCommand
            document.execCommand('justifyRight', false, null);
            
            // Get all affected list elements
            const commonAncestor = range.commonAncestorContainer;
            let container;
            
            if (commonAncestor.nodeType === 3) { // Text node
                container = commonAncestor.parentNode;
            } else {
                container = commonAncestor;
            }
            
            // Find if we're dealing with a list
            const listContainer = findListContainer(container);
            
            if (listContainer) {
                // Apply additional CSS for list alignment
                const listItems = listContainer.querySelectorAll('li');
                listItems.forEach(li => {
                    // Set the CSS for list item alignment
                    li.style.textAlign = 'right';
                    li.style.listStylePosition = 'inside';
                });
                
                // Adjust the list container too
                listContainer.style.paddingLeft = '0';
                listContainer.style.marginLeft = '0';
            }
        }
        
        // Helper function to find the list container (ul/ol)
        function findListContainer(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'UL' || element.tagName === 'OL') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
    })();
    """
    
    self.execute_js(win, js_code)
    
    # Update all alignment buttons
    self._update_alignment_buttons(win, 'right')
    
    win.statusbar.set_text("Aligned text right")
    win.webview.grab_focus()

def on_align_justify_toggled(self, win, button):
    """Handle justify button toggle"""
    # Execute alignment command with list support
    js_code = """
    (function() {
        applyAlignmentWithListSupport('justify');
        return 'justify';  // Return the alignment type
        
        function applyAlignmentWithListSupport(alignment) {
            // Get the current selection
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return;
            
            const range = selection.getRangeAt(0);
            
            // First, apply standard alignment using execCommand
            document.execCommand('justifyFull', false, null);
            
            // Get all affected list elements
            const commonAncestor = range.commonAncestorContainer;
            let container;
            
            if (commonAncestor.nodeType === 3) { // Text node
                container = commonAncestor.parentNode;
            } else {
                container = commonAncestor;
            }
            
            // Find if we're dealing with a list
            const listContainer = findListContainer(container);
            
            if (listContainer) {
                // Apply additional CSS for list alignment
                const listItems = listContainer.querySelectorAll('li');
                listItems.forEach(li => {
                    // Set the CSS for list item alignment
                    li.style.textAlign = 'justify';
                    li.style.listStylePosition = 'inside';
                });
                
                // Adjust the list container too
                listContainer.style.paddingLeft = '0';
                listContainer.style.marginLeft = '0';
            }
        }
        
        // Helper function to find the list container (ul/ol)
        function findListContainer(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'UL' || element.tagName === 'OL') {
                    return element;
                }
                element = element.parentNode;
            }
            return null;
        }
    })();
    """
    
    self.execute_js(win, js_code)
    
    # Update all alignment buttons
    self._update_alignment_buttons(win, 'justify')
    
    win.statusbar.set_text("Justified text")
    win.webview.grab_focus()

# Also fix the _update_alignment_buttons method
def _update_alignment_buttons(self, win, active_alignment):
    """Update alignment toggle button states"""
    for align_type, button in win.alignment_buttons.items():
        # Each button should have its handler_id stored directly
        if hasattr(button, 'handler_id'):
            button.handler_block(button.handler_id)
        
        # Set active state based on current alignment
        button.set_active(align_type == active_alignment)
        
        # Unblock signal handlers
        if hasattr(button, 'handler_id'):
            button.handler_unblock(button.handler_id)

# Update the selection_change_js method to also track list and alignment states
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
            
            // Get list states
            const isUnorderedList = document.queryCommandState('insertUnorderedList');
            const isOrderedList = document.queryCommandState('insertOrderedList');
            
            // Get alignment states
            const isJustifyLeft = document.queryCommandState('justifyLeft');
            const isJustifyCenter = document.queryCommandState('justifyCenter');
            const isJustifyRight = document.queryCommandState('justifyRight');
            const isJustifyFull = document.queryCommandState('justifyFull');
            
            // Determine the current alignment
            let currentAlignment = 'left'; // Default
            if (isJustifyCenter) currentAlignment = 'center';
            else if (isJustifyRight) currentAlignment = 'right';
            else if (isJustifyFull) currentAlignment = 'justify';
            
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
            
            // Send the state to Python - Now including list and alignment states
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
                    fontSize: fontSize,
                    bulletList: isUnorderedList,
                    numberedList: isOrderedList,
                    alignment: currentAlignment
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
# ---- PARAGRAPH STYLE HANDLER ----
def on_paragraph_style_changed(self, win, dropdown):
    """Handle paragraph style dropdown change"""
    # Get selected style index
    selected = dropdown.get_selected()
    
    # Map selected index to HTML tag
    style_tags = {
        0: "p",       # Normal
        1: "h1",      # Heading 1
        2: "h2",      # Heading 2
        3: "h3",      # Heading 3
        4: "h4",      # Heading 4
        5: "h5",      # Heading 5
        6: "h6"       # Heading 6
    }
    
    # Get the tag to apply
    tag = style_tags.get(selected, "p")
    
    # Apply the selected style using formatBlock command
    js_code = f"""
    (function() {{
        document.execCommand('formatBlock', false, '<{tag}>');
        return true;
    }})();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text(f"Applied {dropdown.get_selected_item().get_string()} style")
    win.webview.grab_focus()

# ---- FONT FAMILY HANDLER ----
def on_font_changed(self, win, dropdown):
    """Handle font family dropdown change"""
    # Get the selected font
    selected_item = dropdown.get_selected_item()
    
    # Skip if it's a separator
    if selected_item.get_string() == "──────────":
        # Revert to previous selection
        if hasattr(win, 'previous_font_selection'):
            dropdown.set_selected(win.previous_font_selection)
        return
    
    # Store current selection for future reference
    win.previous_font_selection = dropdown.get_selected()
    
    # Get the font name
    font_name = selected_item.get_string()
    
    # Apply the font family
    js_code = f"""
    (function() {{
        document.execCommand('fontName', false, '{font_name}');
        return true;
    }})();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text(f"Applied font: {font_name}")
    win.webview.grab_focus()

# ---- FONT SIZE HANDLER ----
def on_font_size_changed(self, win, dropdown):
    """Handle font size dropdown change using direct font-size styling"""
    # Get the selected size
    selected_item = dropdown.get_selected_item()
    size_pt = selected_item.get_string()
    
    # Apply font size using execCommand with proper style attribute
    js_code = f"""
    (function() {{
        // Get the editor
        const editor = document.getElementById('editor');
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0) {{
            const range = selection.getRangeAt(0);
            
            // If text is selected
            if (!range.collapsed) {{
                // Use execCommand to apply the font size
                document.execCommand('fontSize', false, '7');
                
                // Find all font elements with size=7 and set the correct size
                const fontElements = editor.querySelectorAll('font[size="7"]');
                for (const font of fontElements) {{
                    font.removeAttribute('size');
                    font.style.fontSize = '{size_pt}pt';
                }}
                
                // Clean up redundant nested font tags
                cleanupEditorTags();
                
                // Record undo state
                saveState();
                window.lastContent = editor.innerHTML;
                window.redoStack = [];
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
            }} else {{
                // For cursor position (no selection)
                // Store font size for next character
                editor.setAttribute('data-next-font-size', '{size_pt}pt');
                
                // Add handler for next input
                const handleInput = function(e) {{
                    // Remove the handler after first use
                    editor.removeEventListener('input', handleInput);
                    
                    // Get the font size
                    const fontSize = editor.getAttribute('data-next-font-size');
                    if (!fontSize) return;
                    
                    // Get the current selection
                    const sel = window.getSelection();
                    if (sel.rangeCount > 0) {{
                        // Try to select the last character typed
                        const range = sel.getRangeAt(0);
                        if (range.startOffset > 0) {{
                            try {{
                                // Select the last character
                                range.setStart(range.startContainer, range.startOffset - 1);
                                
                                // Apply font size
                                document.execCommand('fontSize', false, '7');
                                
                                // Update the font elements
                                const fontElements = editor.querySelectorAll('font[size="7"]');
                                for (const font of fontElements) {{
                                    font.removeAttribute('size');
                                    font.style.fontSize = fontSize;
                                }}
                                
                                // Restore cursor position
                                range.collapse(false);
                                sel.removeAllRanges();
                                sel.addRange(range);
                                
                                // Clean up tags
                                cleanupEditorTags();
                                
                                // Record state
                                saveState();
                                window.lastContent = editor.innerHTML;
                                window.redoStack = [];
                                try {{
                                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                                }} catch(e) {{
                                    console.log("Could not notify about changes:", e);
                                }}
                            }} catch (error) {{
                                console.error("Error applying font size:", error);
                            }}
                        }}
                    }}
                }};
                
                editor.addEventListener('input', handleInput);
            }}
        }}
        
        // Combined function to clean up tags
        function cleanupEditorTags() {{
            // Clean up redundant nested font tags
            function cleanupNestedFontTags() {{
                const fontTags = editor.querySelectorAll('font');
                
                // Process each font tag
                for (let i = 0; i < fontTags.length; i++) {{
                    const font = fontTags[i];
                    
                    // Check if this font tag has nested font tags
                    const nestedFonts = font.querySelectorAll('font');
                    
                    for (let j = 0; j < nestedFonts.length; j++) {{
                        const nestedFont = nestedFonts[j];
                        
                        // If nested font has no attributes, replace it with its contents
                        if (!nestedFont.hasAttribute('style') && 
                            !nestedFont.hasAttribute('face') && 
                            !nestedFont.hasAttribute('color') &&
                            !nestedFont.hasAttribute('size')) {{
                            
                            const fragment = document.createDocumentFragment();
                            while (nestedFont.firstChild) {{
                                fragment.appendChild(nestedFont.firstChild);
                            }}
                            
                            nestedFont.parentNode.replaceChild(fragment, nestedFont);
                        }}
                    }}
                }}
            }}
            
            // Clean up empty tags
            function cleanupEmptyTags() {{
                // Find all font and span elements
                const elements = [...editor.querySelectorAll('font'), ...editor.querySelectorAll('span')];
                
                // Process in reverse to handle nested elements
                for (let i = elements.length - 1; i >= 0; i--) {{
                    const el = elements[i];
                    if (el.textContent.trim() === '') {{
                        el.parentNode.removeChild(el);
                    }}
                }}
            }}
            
            // Run the cleanup functions multiple times to handle nested cases
            for (let i = 0; i < 2; i++) {{
                cleanupNestedFontTags();
                cleanupEmptyTags();
            }}
        }}
        
        return true;
    }})();
    """
    
    # Execute the JavaScript code
    self.execute_js(win, js_code)
    
    # Run another cleanup after a short delay to catch any remaining issues
    GLib.timeout_add(100, lambda: self.cleanup_editor_tags(win))
    
    win.statusbar.set_text(f"Applied font size: {size_pt}pt")
    win.webview.grab_focus()

def cleanup_editor_tags(self, win):
    """Clean up both empty tags and redundant nested font tags in the editor content"""
    js_code = """
    (function() {
        // Get the editor
        const editor = document.getElementById('editor');
        
        // Clean up redundant nested font tags
        function cleanupNestedFontTags() {
            const fontTags = editor.querySelectorAll('font');
            
            // Process each font tag
            for (let i = 0; i < fontTags.length; i++) {
                const font = fontTags[i];
                
                // Check if this font tag has nested font tags
                const nestedFonts = font.querySelectorAll('font');
                
                for (let j = 0; j < nestedFonts.length; j++) {
                    const nestedFont = nestedFonts[j];
                    
                    // If nested font has no attributes, replace it with its contents
                    if (!nestedFont.hasAttribute('style') && 
                        !nestedFont.hasAttribute('face') && 
                        !nestedFont.hasAttribute('color') &&
                        !nestedFont.hasAttribute('size')) {
                        
                        const fragment = document.createDocumentFragment();
                        while (nestedFont.firstChild) {
                            fragment.appendChild(nestedFont.firstChild);
                        }
                        
                        nestedFont.parentNode.replaceChild(fragment, nestedFont);
                    }
                }
            }
        }
        
        // Clean up empty tags
        function cleanupEmptyTags() {
            // Find all font and span elements
            const elements = [...editor.querySelectorAll('font'), ...editor.querySelectorAll('span')];
            
            // Process in reverse to handle nested elements
            for (let i = elements.length - 1; i >= 0; i--) {
                const el = elements[i];
                if (el.textContent.trim() === '') {
                    el.parentNode.removeChild(el);
                }
            }
        }
        
        // Run the cleanup functions multiple times to handle nested cases
        for (let i = 0; i < 3; i++) {
            cleanupNestedFontTags();
            cleanupEmptyTags();
        }
        
        return true;
    })();
    """
    self.execute_js(win, js_code)
    
def create_color_button(self, color_hex):
    """Create a button with a color swatch"""
    button = Gtk.Button()
    button.set_size_request(18, 18)
    
    # Create a colored box
    color_box = Gtk.Box()
    color_box.set_size_request(16, 16)
    color_box.add_css_class("color-box")
    
    # Set the background color
    css_provider = Gtk.CssProvider()
    css = f".color-box {{ background-color: {color_hex}; border: 1px solid rgba(0,0,0,0.2); border-radius: 2px; }}"
    css_provider.load_from_data(css.encode())
    
    # Apply the CSS
    style_context = color_box.get_style_context()
    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
    button.set_child(color_box)
    return button

def on_font_color_button_clicked(self, win):
    """Handle font color button click (the main button, not the dropdown)"""
    # Get the currently selected color from the indicator
    if hasattr(win, 'current_font_color'):
        color_hex = win.current_font_color
    else:
        color_hex = "#000000"  # Default to black
        win.current_font_color = color_hex
    
    # Apply color to selected text
    self.apply_font_color(win, color_hex)

def on_font_color_selected(self, win, color_hex, popover):
    """Handle selection of a specific font color"""
    # Save the current color
    win.current_font_color = color_hex
    
    # Update the indicator color
    rgba = Gdk.RGBA()
    rgba.parse(color_hex)
    self.set_box_color(win.font_color_indicator, rgba)
    
    # Apply color to selected text
    self.apply_font_color(win, color_hex)
    
    # Close the popover
    popover.popdown()

def on_font_color_automatic_clicked(self, win, popover):
    """Reset font color to automatic (remove color formatting)"""
    # Reset the stored color preference 
    win.current_font_color = "inherit"
    
    # Set the indicator color back to black (representing automatic)
    rgba = Gdk.RGBA()
    rgba.parse("#000000")
    self.set_box_color(win.font_color_indicator, rgba)
    
    # Apply to selected text
    self.apply_font_color(win, "inherit")
    
    # Close the popover
    popover.popdown()

def on_more_font_colors_clicked(self, win, popover):
    """Show a color chooser dialog for more font colors"""
    # Close the popover first
    popover.popdown()
    
    # Create a color chooser dialog
    dialog = Gtk.ColorDialog()
    dialog.set_title("Select Text Color")
    
    # Get the current color to use as default
    if hasattr(win, 'current_font_color') and win.current_font_color != "inherit":
        rgba = Gdk.RGBA()
        rgba.parse(win.current_font_color)
    else:
        rgba = Gdk.RGBA()
        rgba.parse("#000000")  # Default black
    
    # Show the dialog asynchronously
    dialog.choose_rgba(
        win,  # parent window
        rgba,  # initial color
        None,  # cancellable
        lambda dialog, result: self.on_font_color_dialog_response(win, dialog, result)
    )

def on_font_color_dialog_response(self, win, dialog, result):
    """Handle response from the font color chooser dialog"""
    try:
        rgba = dialog.choose_rgba_finish(result)
        if rgba:
            # Convert RGBA to hex
            color_hex = "#{:02x}{:02x}{:02x}".format(
                int(rgba.red * 255),
                int(rgba.green * 255),
                int(rgba.blue * 255)
            )
            
            # Update current color
            win.current_font_color = color_hex
            
            # Update indicator color
            self.set_box_color(win.font_color_indicator, rgba)
            
            # Apply to selected text
            self.apply_font_color(win, color_hex)
    except GLib.Error as error:
        # Handle errors, e.g., user cancelled
        pass

def apply_font_color(self, win, color_hex):
    """Apply selected font color to text or set it for future typing"""
    js_code = f"""
    (function() {{
        // Get the editor
        const editor = document.getElementById('editor');
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0) {{
            const range = selection.getRangeAt(0);
            
            // If text is selected
            if (!range.collapsed) {{
                // Use execCommand to apply the color
                document.execCommand('foreColor', false, '{color_hex}');
                
                // Clean up redundant nested tags
                cleanupEditorTags();
                
                // Record undo state
                saveState();
                window.lastContent = editor.innerHTML;
                window.redoStack = [];
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
            }} else {{
                // For cursor position (no selection)
                // Store color for next character
                editor.setAttribute('data-next-font-color', '{color_hex}');
                
                // Add handler for next input
                const handleInput = function(e) {{
                    // Remove the handler after first use
                    editor.removeEventListener('input', handleInput);
                    
                    // Get the color
                    const fontColor = editor.getAttribute('data-next-font-color');
                    if (!fontColor) return;
                    
                    // Get the current selection
                    const sel = window.getSelection();
                    if (sel.rangeCount > 0) {{
                        // Try to select the last character typed
                        const range = sel.getRangeAt(0);
                        if (range.startOffset > 0) {{
                            try {{
                                // Select the last character
                                range.setStart(range.startContainer, range.startOffset - 1);
                                
                                // Apply color
                                document.execCommand('foreColor', false, fontColor);
                                
                                // Restore cursor position
                                range.collapse(false);
                                sel.removeAllRanges();
                                sel.addRange(range);
                                
                                // Clean up tags
                                cleanupEditorTags();
                                
                                // Record state
                                saveState();
                                window.lastContent = editor.innerHTML;
                                window.redoStack = [];
                                try {{
                                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                                }} catch(e) {{
                                    console.log("Could not notify about changes:", e);
                                }}
                            }} catch (error) {{
                                console.error("Error applying font color:", error);
                            }}
                        }}
                    }}
                }};
                
                editor.addEventListener('input', handleInput);
            }}
        }}
        
        return true;
    }})();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text(f"Text color set to: {color_hex}")
    win.webview.grab_focus()

def on_bg_color_button_clicked(self, win):
    """Handle background color button click (the main button, not the dropdown)"""
    # Get the currently selected color from the indicator
    if hasattr(win, 'current_bg_color'):
        color_hex = win.current_bg_color
    else:
        color_hex = "#FFFF00"  # Default to yellow
        win.current_bg_color = color_hex
    
    # Apply color to selected text
    self.apply_bg_color(win, color_hex)

def on_bg_color_selected(self, win, color_hex, popover):
    """Handle selection of a specific background color"""
    # Save the current color
    win.current_bg_color = color_hex
    
    # Update the indicator color
    rgba = Gdk.RGBA()
    rgba.parse(color_hex)
    self.set_box_color(win.bg_color_indicator, rgba)
    
    # Apply color to selected text
    self.apply_bg_color(win, color_hex)
    
    # Close the popover
    popover.popdown()

def on_bg_color_automatic_clicked(self, win, popover):
    """Reset background color to automatic (remove background color formatting)"""
    # Reset the stored color preference
    win.current_bg_color = "transparent"
    
    # Set the indicator color to transparent
    rgba = Gdk.RGBA()
    rgba.parse("transparent")
    self.set_box_color(win.bg_color_indicator, rgba)
    
    # Apply to selected text
    self.apply_bg_color(win, "transparent")
    
    # Close the popover
    popover.popdown()

def on_more_bg_colors_clicked(self, win, popover):
    """Show a color chooser dialog for more background colors"""
    # Close the popover first
    popover.popdown()
    
    # Create a color chooser dialog
    dialog = Gtk.ColorDialog()
    dialog.set_title("Select Background Color")
    
    # Get the current color to use as default
    if hasattr(win, 'current_bg_color') and win.current_bg_color != "transparent":
        rgba = Gdk.RGBA()
        rgba.parse(win.current_bg_color)
    else:
        rgba = Gdk.RGBA()
        rgba.parse("#FFFF00")  # Default yellow
    
    # Show the dialog asynchronously
    dialog.choose_rgba(
        win,  # parent window
        rgba,  # initial color
        None,  # cancellable
        lambda dialog, result: self.on_bg_color_dialog_response(win, dialog, result)
    )

def on_bg_color_dialog_response(self, win, dialog, result):
    """Handle response from the background color chooser dialog"""
    try:
        rgba = dialog.choose_rgba_finish(result)
        if rgba:
            # Convert RGBA to hex
            color_hex = "#{:02x}{:02x}{:02x}".format(
                int(rgba.red * 255),
                int(rgba.green * 255),
                int(rgba.blue * 255)
            )
            
            # Update current color
            win.current_bg_color = color_hex
            
            # Update indicator color
            self.set_box_color(win.bg_color_indicator, rgba)
            
            # Apply to selected text
            self.apply_bg_color(win, color_hex)
    except GLib.Error as error:
        # Handle errors, e.g., user cancelled
        pass

def apply_bg_color(self, win, color_hex):
    """Apply selected background color to text or set it for future typing"""
    js_code = f"""
    (function() {{
        // Get the editor
        const editor = document.getElementById('editor');
        const selection = window.getSelection();
        
        if (selection.rangeCount > 0) {{
            const range = selection.getRangeAt(0);
            
            // If text is selected
            if (!range.collapsed) {{
                // Use execCommand to apply the background color
                document.execCommand('hiliteColor', false, '{color_hex}');
                
                // Clean up redundant nested tags
                cleanupEditorTags();
                
                // Record undo state
                saveState();
                window.lastContent = editor.innerHTML;
                window.redoStack = [];
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
            }} else {{
                // For cursor position (no selection)
                // Store color for next character
                editor.setAttribute('data-next-bg-color', '{color_hex}');
                
                // Add handler for next input
                const handleInput = function(e) {{
                    // Remove the handler after first use
                    editor.removeEventListener('input', handleInput);
                    
                    // Get the color
                    const bgColor = editor.getAttribute('data-next-bg-color');
                    if (!bgColor) return;
                    
                    // Get the current selection
                    const sel = window.getSelection();
                    if (sel.rangeCount > 0) {{
                        // Try to select the last character typed
                        const range = sel.getRangeAt(0);
                        if (range.startOffset > 0) {{
                            try {{
                                // Select the last character
                                range.setStart(range.startContainer, range.startOffset - 1);
                                
                                // Apply background color
                                document.execCommand('hiliteColor', false, bgColor);
                                
                                // Restore cursor position
                                range.collapse(false);
                                sel.removeAllRanges();
                                sel.addRange(range);
                                
                                // Clean up tags
                                cleanupEditorTags();
                                
                                // Record state
                                saveState();
                                window.lastContent = editor.innerHTML;
                                window.redoStack = [];
                                try {{
                                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                                }} catch(e) {{
                                    console.log("Could not notify about changes:", e);
                                }}
                            }} catch (error) {{
                                console.error("Error applying background color:", error);
                            }}
                        }}
                    }}
                }};
                
                editor.addEventListener('input', handleInput);
            }}
        }}
        
        return true;
    }})();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text(f"Background color set to: {color_hex}")
    win.webview.grab_focus()
    
def set_box_color(self, box, color):
    """Set the background color of a box using CSS"""
    # Create a CSS provider
    css_provider = Gtk.CssProvider()
    
    # Generate CSS based on color
    if isinstance(color, Gdk.RGBA):
        if color.alpha == 0:  # Transparent
            css = ".color-indicator { background-color: transparent; border: 1px dashed rgba(127, 127, 127, 0.5); }"
        else:
            css = f".color-indicator {{ background-color: rgba({int(color.red*255)}, {int(color.green*255)}, {int(color.blue*255)}, {color.alpha}); }}"
    elif color == "transparent":
        css = ".color-indicator { background-color: transparent; border: 1px dashed rgba(127, 127, 127, 0.5); }"
    else:
        css = f".color-indicator {{ background-color: {color}; }}"
    
    # Load the CSS
    css_provider.load_from_data(css.encode())
    
    # Apply to the box
    style_context = box.get_style_context()
    style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
    
def on_clear_formatting_clicked(self, win, button):
    """Remove all formatting from selected text"""
    js_code = """
    (function() {
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            
            // Check if there's selected text
            if (!range.collapsed) {
                // Get the selected text content
                const selectedText = range.toString();
                
                // Remove the formatting by replacing with plain text
                document.execCommand('insertText', false, selectedText);
                
                // Record undo state
                saveState();
                window.lastContent = document.getElementById('editor').innerHTML;
                window.redoStack = [];
                try {
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                } catch(e) {
                    console.log("Could not notify about changes:", e);
                }
                
                return true;
            }
        }
        return false;
    })();
    """
    
    self.execute_js(win, js_code)
    win.statusbar.set_text("Text formatting removed")
    win.webview.grab_focus()

def on_change_case(self, win, case_type):
    """Change the case of selected text"""
    # Define JavaScript function for each case type
    js_transformations = {
        "sentence": """
            function transformText(text) {
                if (!text) return text;
                
                // First convert everything to lowercase
                text = text.toLowerCase();
                
                // Then capitalize the first letter of each sentence
                // Look for sentence-ending punctuation (., !, ?) followed by space or end of string
                // Also handle the first character of the entire text
                return text.replace(/([.!?]\\s+|^)([a-z])/g, function(match, p1, p2) {
                    return p1 + p2.toUpperCase();
                }).replace(/^[a-z]/, function(firstChar) {
                    return firstChar.toUpperCase();
                });
            }
        """,
        "lower": """
            function transformText(text) {
                return text.toLowerCase();
            }
        """,
        "upper": """
            function transformText(text) {
                return text.toUpperCase();
            }
        """,
        "title": """
            function transformText(text) {
                return text.replace(/\\b\\w+/g, function(word) {
                    return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
                });
            }
        """,
        "toggle": """
            function transformText(text) {
                return text.split('').map(function(char) {
                    if (char === char.toUpperCase()) {
                        return char.toLowerCase();
                    } else {
                        return char.toUpperCase();
                    }
                }).join('');
            }
        """
    }
    
    # Get the transformation function for this case type
    transform_function = js_transformations.get(case_type, js_transformations["lower"])
    
    # Create the complete JavaScript code
    js_code = f"""
    (function() {{
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {{
            const range = selection.getRangeAt(0);
            
            // Check if there's selected text
            if (!range.collapsed) {{
                // Get the selected text content
                const selectedText = range.toString();
                
                // Transform the text according to the selected case
                {transform_function}
                const transformedText = transformText(selectedText);
                
                // Replace the selected text with the transformed text
                document.execCommand('insertText', false, transformedText);
                
                // Record undo state
                saveState();
                window.lastContent = document.getElementById('editor').innerHTML;
                window.redoStack = [];
                try {{
                    window.webkit.messageHandlers.contentChanged.postMessage("changed");
                }} catch(e) {{
                    console.log("Could not notify about changes:", e);
                }}
                
                return true;
            }}
        }}
        return false;
    }})();
    """
    
    self.execute_js(win, js_code)
    
    # Update status text based on case type
    status_messages = {
        "sentence": "Applied sentence case",
        "lower": "Applied lowercase",
        "upper": "Applied UPPERCASE",
        "title": "Applied Title Case",
        "toggle": "Applied tOGGLE cASE"
    }
    
    win.statusbar.set_text(status_messages.get(case_type, "Changed text case"))
    win.webview.grab_focus()
