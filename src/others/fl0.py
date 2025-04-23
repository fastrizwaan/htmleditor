#!/usr/bin/env python3
import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

class FlowBoxWindow(Adw.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up window properties
        self.set_default_size(600, 400)
        self.set_title("FlowBox Word Demo")
        
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
        
        # Create FlowBox
        self.flowbox = Gtk.FlowBox()
        self.flowbox.set_valign(Gtk.Align.START)
        self.flowbox.set_max_children_per_line(20)
        self.flowbox.set_min_children_per_line(1)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.flowbox.set_homogeneous(False)
        
        # Make items pack closely
        self.flowbox.set_column_spacing(4)
        self.flowbox.set_row_spacing(4)
        
        # Add FlowBox to scrolled window
        scrolled.set_child(self.flowbox)
        
        # Add words to FlowBox
        words = [
            "Hello", "World", "Python", "GTK4", "Libadwaita", 
            "FlowBox", "Widget", "Application", "Programming", "Interface",
            "Development", "Software", "Example", "Code", "Computer",
            "Technology", "Design", "Graphics", "User", "Experience"
        ]
        
        for word in words:
            self.add_word_to_flowbox(word)
    
    def add_word_to_flowbox(self, word):
        # Create a label for the word
        label = Gtk.Label()
        label.set_text(word)
        
        # Create a container for styling
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        box.append(label)
        box.add_css_class("word-box")
        
        # Add some padding and styling to make it look nice
        context = box.get_style_context()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(b"""
            .word-box {
                padding: 6px 12px;
                border-radius: 6px;
                background-color: alpha(currentColor, 0.08);
            }
        """)
        
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Add to FlowBox
        self.flowbox.append(box)

class FlowBoxApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
        
    def on_activate(self, app):
        win = FlowBoxWindow(application=app)
        win.present()

if __name__ == "__main__":
    app = FlowBoxApp(application_id="com.example.adw.flowbox")
    app.run(sys.argv)
