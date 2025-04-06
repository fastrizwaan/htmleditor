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
