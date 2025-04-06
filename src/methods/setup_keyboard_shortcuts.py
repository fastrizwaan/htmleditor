from gi.repository import Gtk, GLib


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
