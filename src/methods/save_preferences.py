def save_preferences(self, dialog, auto_save_enabled, auto_save_interval):
    """Save preferences settings"""
    previous_auto_save = self.win.auto_save_enabled
    
    self.win.auto_save_enabled = auto_save_enabled
    self.win.auto_save_interval = auto_save_interval
    
    # Update auto-save timer if needed
    if auto_save_enabled != previous_auto_save:
        if auto_save_enabled:
            self.win.start_auto_save_timer()
            self.win.statusbar.set_text("Auto-save enabled")
        else:
            self.win.stop_auto_save_timer()
            self.win.statusbar.set_text("Auto-save disabled")
    elif auto_save_enabled:
        # Restart timer with new interval
        self.win.stop_auto_save_timer()
        self.win.start_auto_save_timer()
        self.win.statusbar.set_text(f"Auto-save interval set to {auto_save_interval} seconds")
    
    dialog.close()
