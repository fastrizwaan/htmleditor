    def on_insert_text_box_clicked(self, win, btn):
        """Handle text box insertion button click"""
        win.statusbar.set_text("Inserting text box...")
        
        # Create a dialog to configure the text box
        dialog = Adw.Dialog()
        dialog.set_title("Insert Text Box")
        dialog.set_content_width(350)
        
        # Create layout for dialog content
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        # Width input with +/- buttons
        width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        width_label = Gtk.Label(label="Width (px):")
        width_label.set_halign(Gtk.Align.START)
        width_label.set_hexpand(True)
        
        width_adjustment = Gtk.Adjustment(value=150, lower=50, upper=800, step_increment=10)
        width_spin = Gtk.SpinButton()
        width_spin.set_adjustment(width_adjustment)
        
        # Create a box for the spinner and +/- buttons
        width_spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        width_spinner_box.add_css_class("linked")

        
        width_spinner_box.append(width_spin)


        
        width_box.append(width_label)
        width_box.append(width_spinner_box)
        content_box.append(width_box)
        
        # Height input with +/- buttons
        height_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        height_label = Gtk.Label(label="Height (px):")
        height_label.set_halign(Gtk.Align.START)
        height_label.set_hexpand(True)
        
        height_adjustment = Gtk.Adjustment(value=100, lower=30, upper=600, step_increment=10)
        height_spin = Gtk.SpinButton()
        height_spin.set_adjustment(height_adjustment)
        
        # Create a box for the spinner and +/- buttons
        height_spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        height_spinner_box.add_css_class("linked")
        height_spinner_box.append(height_spin)

        
        height_box.append(height_label)
        height_box.append(height_spinner_box)
        content_box.append(height_box)
        
        # Border width with +/- buttons
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        border_label = Gtk.Label(label="Border width:")
        border_label.set_halign(Gtk.Align.START)
        border_label.set_hexpand(True)
        
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=5, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_adjustment(border_adjustment)
        
        # Create a box for the spinner and +/- buttons
        border_spinner_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        border_spinner_box.add_css_class("linked")
        
        border_spinner_box.append(border_spin)

        
        border_box.append(border_label)
        border_box.append(border_spinner_box)
        content_box.append(border_box)
        
        # Floating option checkbox
        float_check = Gtk.CheckButton(label="Free-floating (text wraps around)")
        float_check.set_active(True)  # Enabled by default for text boxes
        content_box.append(float_check)
        
        # Button box
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(16)
        
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        
        insert_button = Gtk.Button(label="Insert")
        insert_button.add_css_class("suggested-action")
        insert_button.connect("clicked", lambda btn: self._on_textbox_dialog_response(
            win, dialog, 
            width_spin.get_value_as_int(),
            height_spin.get_value_as_int(),
            border_spin.get_value_as_int(),
            float_check.get_active()
        ))
        
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        # Set dialog content and present
        dialog.set_child(content_box)
        dialog.present(win)

    def _on_textbox_dialog_response(self, win, dialog, width, height, border_width, is_floating):
        """Handle response from the text box dialog"""
        dialog.close()
        
        # Create a modified insert_table call with 1 row, 1 column (single cell)
        js_code = f"""
        (function() {{
            // Insert a single-cell table with auto width
            insertTable(1, 1, false, {border_width}, "auto", {str(is_floating).lower()});
            
            // Get the newly created table
            setTimeout(() => {{
                const tables = document.querySelectorAll('table.editor-table');
                const newTable = tables[tables.length - 1] || document.querySelector('table:last-of-type');
                if (newTable) {{
                    // Apply styling specific to text box
                    newTable.classList.add('text-box');
                    
                    // Set specific width and height
                    newTable.style.width = '{width}px';
                    
                    // Set background to transparent
                    newTable.style.backgroundColor = 'transparent';
                    newTable.setAttribute('data-bg-color', 'transparent');
                    
                    // Add min-height to make it more box-like
                    const cell = newTable.querySelector('td');
                    if (cell) {{
                        cell.style.height = '{height}px';
                        cell.style.minHeight = '{height}px';
                        cell.style.padding = '10px';
                        cell.innerHTML = ''; // Clear default "Cell" text
                    }}
                    
                    // Set rounded corners
                    newTable.style.borderRadius = '4px';
                    
                    // Set box shadow if it's floating
                    if ({str(is_floating).lower()}) {{
                        newTable.style.boxShadow = '0 2px 8px rgba(0, 0, 0, 0.15)';
                    }}
                }}
            }}, 50);
            
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        
        # Update status message
        if is_floating:
            win.statusbar.set_text("Floating text box inserted")
        else:
            win.statusbar.set_text("Text box inserted") 
