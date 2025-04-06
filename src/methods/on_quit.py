def on_quit(self, action, param):
    """Quit the application"""
    for win in self.windows[:]:  # Use a copy to avoid modification during iteration
        win.close()
    self.quit()
