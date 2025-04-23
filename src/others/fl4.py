#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

class WrapBoxWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up window properties
        self.set_default_size(600, 400)
        self.set_title("WrapBox Mixed Items Demo")
        
        # Create main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.set_content(main_box)
        
        # Create header
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Create a scrolled window
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_hexpand(True)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        main_box.append(scrolled)
        
        # Create a clamp to contain the wrap box
        clamp = Adw.Clamp()
        scrolled.set_child(clamp)
        
        # Create WrapBox
        # Check if constructor accepts spacing parameter (as shown in your pasted code)
        try:
            self.wrapbox = Adw.WrapBox(spacing=10)  # Try with 10px spacing
        except (TypeError, ValueError):
            # Fallback if constructor doesn't accept spacing parameter
            self.wrapbox = Adw.WrapBox()
            
            # Try to set spacing via property (for version 1.7+)
            try:
                self.wrapbox.set_child_spacing(10)
            except AttributeError:
                print("Warning: 10px spacing not applied - AdwWrapBox spacing not available")
                
        self.wrapbox.set_orientation(Gtk.Orientation.HORIZONTAL)
#        self.wrapbox.set_maximum_line_length(800)  # Set maximum width before wrapping
        clamp.set_child(self.wrapbox)
        
        # Setup CSS provider for styling items
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(b"""
            .item-box {
                padding: 0px 0px;
                border-radius: 6px;
                background-color: alpha(currentColor, 0.08);
                margin: 5px;  /* Add margin as fallback for spacing */
            }
            
            .icon-box {
                padding: 6px;
                border-radius: 6px;
                background-color: alpha(currentColor, 0.08);
                margin: 5px;  /* Add margin as fallback for spacing */
            }
        """)
        
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Add a mix of words and icons to WrapBox
        items = [
            {"type": "text", "content": "one"},
            {"type": "icon", "content": "numeric-1-symbolic"},
            {"type": "text", "content": "two"},
            {"type": "text", "content": "abcdefgh"},
            {"type": "icon", "content": "window-close-symbolic"},
            {"type": "text", "content": "fourteen"},
            {"type": "icon", "content": "numeric-1-symbolic"},
            {"type": "icon", "content": "window-close-symbolic"},
            {"type": "text", "content": "Python"},
            {"type": "icon", "content": "applications-science-symbolic"},
            {"type": "text", "content": "GTK4"},
            {"type": "icon", "content": "emblem-system-symbolic"},
            {"type": "text", "content": "Libadwaita"},
            {"type": "icon", "content": "user-desktop-symbolic"},
            {"type": "text", "content": "FlowBox"},
            {"type": "icon", "content": "edit-find-symbolic"}
        ]
        
        for item in items:
            if item["type"] == "text":
                self.add_word_to_wrapbox(item["content"])
            else:
                self.add_icon_to_wrapbox(item["content"])
    
    def add_word_to_wrapbox(self, word):
        # Create a label for the word
        label = Gtk.Label()
        label.set_text(word)
        
        # Create a container for styling
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.append(label)
        box.add_css_class("item-box")
        
        # Add to WrapBox
        self.wrapbox.append(box)
    
    def add_icon_to_wrapbox(self, icon_name):
        # Create an icon
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_pixel_size(16)
        
        # Create a container for styling
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.append(icon)
        box.add_css_class("icon-box")
        
        # Add to WrapBox
        self.wrapbox.append(box)

class WrapBoxApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        win = WrapBoxWindow(application=app)
        win.present()

if __name__ == "__main__":
    app = WrapBoxApp(application_id="com.example.adw.wrapbox")
    app.run(sys.argv)
