import os
import sys
import time
import platform
import signal
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, GLib, Gdk

# Import CEF Python
from cefpython3 import cefpython as cef

# Global variables
is_gtk_thread = False
browser = None
window_info = None
browser_was_closed = False
main_window = None

class CEFBrowserHandler:
    """Custom browser handler for CEF callbacks."""
    
    def OnLoadingStateChange(self, browser, is_loading, **_):
        if not is_loading:
            # Force a focus to ensure keyboard events get captured
            browser.SetFocus(True)
    
    def GetViewRect(self, browser, rect_out, **_):
        # Must return True for rect_out to be used
        width, height = main_window.get_width(), main_window.get_height()
        rect_out.update(x=0, y=0, width=width, height=height)
        return True
    
    def OnPaint(self, browser, element_type, paint_buffer, **_):
        # OnPaint not needed for GTK integration
        pass
    
    def OnPopupShow(self, browser, shown, **_):
        # Control CEF popups
        pass
    
    def OnPopupSize(self, browser, rect_out, **_):
        # Size for popups
        pass
    
    def OnAfterCreated(self, browser, **_):
        """Called after the browser has been created."""
        print("Browser created successfully")
    
    def OnBeforeClose(self, browser, **_):
        """Called before the browser is closed."""
        global browser_was_closed
        browser_was_closed = True

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up window
        self.set_default_size(900, 700)
        self.set_title("CEF Python in GTK4/Libadwaita")
        
        # Create main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Add header bar with Libadwaita styling
        self.header = Adw.HeaderBar()
        self.main_box.append(self.header)
        
        # Add URL entry
        self.url_entry = Gtk.Entry()
        self.url_entry.set_hexpand(True)
        self.url_entry.set_text("data:text/html,<html><body contenteditable style='height:100%; padding:20px; font-family:sans-serif;'>Start typing here...</body></html>")
        self.url_entry.connect("activate", self.on_url_activate)
        self.header.set_title_widget(self.url_entry)
        
        # Add navigation buttons
        self.back_button = Gtk.Button.new_from_icon_name("go-previous-symbolic")
        self.back_button.connect("clicked", self.on_back_clicked)
        self.header.pack_start(self.back_button)
        
        self.forward_button = Gtk.Button.new_from_icon_name("go-next-symbolic")
        self.forward_button.connect("clicked", self.on_forward_clicked)
        self.header.pack_start(self.forward_button)
        
        self.refresh_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        self.refresh_button.connect("clicked", self.on_refresh_clicked)
        self.header.pack_start(self.refresh_button)
        
        # Add browser placeholder (will be filled with CEF)
        self.browser_container = Gtk.DrawingArea()
        self.browser_container.set_vexpand(True)
        self.browser_container.set_hexpand(True)
        self.main_box.append(self.browser_container)
        
        # Connect signals
        self.connect("unrealize", self.on_window_destroy)
        self.browser_container.set_draw_func(self.on_draw)
        
        # Initialize CEF when widget is ready
        self.browser_container.connect("realize", self.on_browser_container_realize)
    
    def on_browser_container_realize(self, widget):
        """Initialize CEF when the drawing area is ready."""
        GLib.idle_add(self.initialize_cef)
    
    def initialize_cef(self):
        """Initialize CEF and create the browser."""
        global browser, window_info, is_gtk_thread, main_window
        
        main_window = self
        is_gtk_thread = True
        
        # Get native window handle
        native = self.browser_container.get_native()
        surface = native.get_surface()
        
        if platform.system() == "Linux":
            # For Linux, we need the XID
            xid = None
            try:
                xid = surface.get_xid()
            except:
                # Wayland doesn't have XIDs, we'll need a different approach
                print("Warning: Running on Wayland. CEF integration might not work properly.")
                # For Wayland, we might need more complex integration or fallbacks
        
        # Initialize CEF
        if not cef.GetAppSetting("external_message_pump"):
            sys.stderr.write("Error: This example requires setting the cef.ApplicationSettings['external_message_pump'] = True\n")
            return
        
        # Create browser
        window_info = cef.WindowInfo()
        
        # Set parent window
        if platform.system() == "Linux" and xid:
            window_info.SetAsChild(xid, [0, 0, self.get_width(), self.get_height()])
        elif platform.system() == "Windows":
            from ctypes import windll
            window_info.SetAsChild(int(windll.user32.GetActiveWindow()), [0, 0, self.get_width(), self.get_height()])
        elif platform.system() == "Darwin":
            window_info.SetAsChild(0, [0, 0, self.get_width(), self.get_height()])
        
        # Browser settings
        browser_settings = {
            "web_security_disabled": True,  # To allow for more flexible content loading
        }
        
        # Create browser
        url = self.url_entry.get_text()
        browser = cef.CreateBrowserSync(window_info=window_info,
                                       settings=browser_settings,
                                       url=url)
        
        # Set handlers
        browser_handler = CEFBrowserHandler()
        browser.SetClientHandler(browser_handler)
        
        # Setup periodic task to pump CEF messages
        GLib.timeout_add(10, self.on_cef_message_loop_work)
        
        return False  # Don't run again
    
    def on_cef_message_loop_work(self):
        """Perform message loop work periodically."""
        if browser_was_closed:
            return False
        cef.MessageLoopWork()
        return True  # Continue running this task
    
    def on_draw(self, widget, cr, width, height):
        """Handle draw events for the browser container."""
        # CEF handles its own drawing
        pass
    
    def on_url_activate(self, entry):
        """Navigate to URL when Enter is pressed in the URL bar."""
        if browser:
            browser.LoadUrl(entry.get_text())
    
    def on_back_clicked(self, button):
        """Navigate back."""
        if browser and browser.CanGoBack():
            browser.GoBack()
    
    def on_forward_clicked(self, button):
        """Navigate forward."""
        if browser and browser.CanGoForward():
            browser.GoForward()
    
    def on_refresh_clicked(self, button):
        """Refresh the current page."""
        if browser:
            browser.Reload()
    
    def on_window_destroy(self, *args, **kwargs):
        """Clean up CEF when window is closing."""
        global browser
        if browser:
            browser.CloseBrowser(True)
            browser = None

class CEFApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)
    
    def on_activate(self, app):
        # Initialize CEF
        self.initialize_cef()
        
        # Create and show the window
        win = MainWindow(application=app)
        win.present()
    
    def initialize_cef(self):
        """Initialize CEF globally."""
        # Check if already initialized
        if cef.GetAppSetting("initialized"):
            return
        
        # CEF settings
        settings = {
            "external_message_pump": True,  # Required for GTK integration
            "multi_threaded_message_loop": False,
            "context_menu": {"enabled": True},
            "debug": False,
            "log_severity": cef.LOGSEVERITY_WARNING,
        }
        
        # Initialize CEF
        sys.excepthook = cef.ExceptHook
        cef.Initialize(settings=settings)
        
        # Set shutdown handler
        signal.signal(signal.SIGINT, signal.SIG_DFL)  # Use default handler for Ctrl+C

    def do_shutdown(self):
        """Clean up CEF when application exits."""
        if cef.GetAppSetting("initialized"):
            cef.Shutdown()
        Adw.Application.do_shutdown(self)

# Main entry point
if __name__ == "__main__":
    # Init Adwaita application
    app = CEFApp(application_id="com.example.CEFBrowser")
    
    # Run the app
    exit_code = app.run(sys.argv)
    
    # Exit
    sys.exit(exit_code)
