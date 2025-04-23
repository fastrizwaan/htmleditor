#!/usr/bin/env python3

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, WebKit, Gdk, GLib, Gio

class TextBoxHandler:
    """JavaScript interface for handling text box operations."""
    def __init__(self, webview):
        self.webview = webview

    def run_js(self, script):
        self.webview.evaluate_javascript(script, -1, None, None, None, None, None)


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        
        # Set up window properties
        self.set_title("Text Box Editor")
        self.set_default_size(800, 600)
        
        # Create WebKit WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Handler for JavaScript communication
        self.handler = TextBoxHandler(self.webview)
        
        # Set up main box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        
        # Create header bar with controls
        header = Adw.HeaderBar()
        add_button = Gtk.Button(label="Add Text Box")
        add_button.connect("clicked", self.on_add_textbox_clicked)
        header.pack_start(add_button)
        
        # Add header and webview to main box
        main_box.append(header)
        main_box.append(self.webview)
        
        # Set the main box as the window's content
        self.set_content(main_box)
        
        # Load the HTML content with our text box implementation
        self.load_html_content()
        
    def load_html_content(self):
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text Box Editor</title>
    <style>
        body {
            font-family: sans-serif;
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #f5f5f5;
            height: 100vh;
        }
        
        .canvas {
            width: 100%;
            height: 100%;
            position: relative;
        }
        
        .text-box {
            position: absolute;
            min-width: 200px;
            min-height: 100px;
            background-color: white;
            border: 1px solid #ccc;
            box-shadow: 0 0 5px rgba(0,0,0,0.2);
            padding: 10px;
            box-sizing: border-box;
            cursor: text;
            overflow: hidden;
        }
        
        .text-box.active {
            border: 2px solid #4285f4;
            z-index: 10;
            box-shadow: 0 0 8px rgba(66, 133, 244, 0.4);
        }
        
        .text-box textarea {
            width: 100%;
            height: 100%;
            border: none;
            outline: none;
            resize: none;
            font-family: inherit;
            font-size: inherit;
            background: transparent;
        }
        
        .controls {
            display: none;
        }
        
        .text-box.active .controls {
            display: block;
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 30;
        }
        
        .move-handle {
            position: absolute;
            top: -10px;
            left: -10px;
            background-color: #4285f4;
            color: white;
            width: 20px;
            height: 20px;
            cursor: move;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            z-index: 30;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
            pointer-events: auto;
        }
        
        .rotate-handle {
            position: absolute;
            top: -10px;
            right: -10px;
            background-color: #4285f4;
            color: white;
            width: 20px;
            height: 20px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 50%;
            z-index: 30;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
            pointer-events: auto;
        }
        
        .resize-handle {
            position: absolute;
            bottom: -10px;
            right: -10px;
            width: 20px;
            height: 20px;
            background-color: #4285f4;
            cursor: nwse-resize;
            z-index: 30;
            border-radius: 50%;
            box-shadow: 0 0 3px rgba(0,0,0,0.3);
            pointer-events: auto;
        }
    </style>
</head>
<body>
    <div class="canvas" id="canvas"></div>
    
    <script>
        let activeTextBox = null;
        let isDragging = false;
        let isResizing = false;
        let isRotating = false;
        let lastX = 0;
        let lastY = 0;
        let lastAngle = 0;
        
        // Create a new text box
        function createTextBox(x, y) {
            const canvas = document.getElementById('canvas');
            
            // Create the text box container
            const textBox = document.createElement('div');
            textBox.className = 'text-box';
            textBox.style.left = `${x}px`;
            textBox.style.top = `${y}px`;
            textBox.style.transform = 'rotate(0deg)';
            textBox.dataset.angle = '0';
            
            // Create the textarea for text input
            const textarea = document.createElement('textarea');
            textarea.placeholder = 'Enter text here...';
            textarea.addEventListener('click', (e) => {
                e.stopPropagation();
            });
            
            // Controls container
            const controls = document.createElement('div');
            controls.className = 'controls';
            
            // Move handle
            const moveHandle = document.createElement('div');
            moveHandle.className = 'move-handle';
            moveHandle.innerHTML = '&#8597;';
            moveHandle.title = "Move";
            moveHandle.addEventListener('mousedown', (e) => {
                isDragging = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
            });
            
            // Rotate handle
            const rotateHandle = document.createElement('div');
            rotateHandle.className = 'rotate-handle';
            rotateHandle.innerHTML = '&#8635;';
            rotateHandle.title = "Rotate";
            rotateHandle.addEventListener('mousedown', (e) => {
                isRotating = true;
                const rect = textBox.getBoundingClientRect();
                const centerX = rect.left + rect.width / 2;
                const centerY = rect.top + rect.height / 2;
                lastAngle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                e.stopPropagation();
            });
            
            // Resize handle
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            resizeHandle.innerHTML = '&#8599;';
            resizeHandle.title = "Resize";
            resizeHandle.style.display = "flex";
            resizeHandle.style.alignItems = "center";
            resizeHandle.style.justifyContent = "center";
            resizeHandle.addEventListener('mousedown', (e) => {
                isResizing = true;
                lastX = e.clientX;
                lastY = e.clientY;
                e.stopPropagation();
            });
            
            // Add controls to text box
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            textBox.appendChild(textarea);
            textBox.appendChild(controls);
            
            // Add text box to canvas
            canvas.appendChild(textBox);
            
            // Add controls to text box
            controls.appendChild(moveHandle);
            controls.appendChild(rotateHandle);
            controls.appendChild(resizeHandle);
            
            textBox.appendChild(textarea);
            textBox.appendChild(controls);
            
            // Add text box to canvas
            canvas.appendChild(textBox);
            
            // Add click handlers for border and text area
            textBox.addEventListener('mousedown', (e) => {
                const rect = textBox.getBoundingClientRect();
                const borderSize = 5; // Border detection area
                const isTextArea = e.target.tagName === 'TEXTAREA';
                
                // Check if click is on the border area
                const isOnBorder = (
                    e.clientX < rect.left + borderSize || 
                    e.clientX > rect.right - borderSize || 
                    e.clientY < rect.top + borderSize || 
                    e.clientY > rect.bottom - borderSize
                );
                
                if (isOnBorder) {
                    // Toggle controls when clicking on border
                    if (activeTextBox === textBox && textBox.classList.contains('active')) {
                        deactivateTextBox();
                    } else {
                        activateTextBox(textBox);
                    }
                    e.stopPropagation();
                } else if (!isTextArea) {
                    // When clicking inside the box but not on the text area, just activate without showing controls
                    if (activeTextBox !== textBox) {
                        if (activeTextBox) {
                            activeTextBox.classList.remove('active');
                        }
                        activeTextBox = textBox;
                    }
                    e.stopPropagation();
                }
            });
            
            return textBox;
        }
        
        // Activate a text box (show controls)
        function activateTextBox(textBox) {
            if (activeTextBox) {
                activeTextBox.classList.remove('active');
            }
            activeTextBox = textBox;
            activeTextBox.classList.add('active');
            
            // Ensure controls are properly showing
            const controls = textBox.querySelector('.controls');
            if (controls) {
                controls.style.display = 'block';
            }
        }
        
        // Deactivate the active text box (hide controls)
        function deactivateTextBox() {
            if (activeTextBox) {
                activeTextBox.classList.remove('active');
                const controls = activeTextBox.querySelector('.controls');
                if (controls) {
                    controls.style.display = 'none';
                }
                activeTextBox = null;
            }
        }
        
        // Special function to activate text box without showing controls
        function activateTextBoxWithoutControls(textBox) {
            if (activeTextBox) {
                activeTextBox.classList.remove('active');
                const controls = activeTextBox.querySelector('.controls');
                if (controls) {
                    controls.style.display = 'none';
                }
            }
            activeTextBox = textBox;
        }
        
        // Initialize event listeners for canvas and window
        function initEventListeners() {
            const canvas = document.getElementById('canvas');
            
            // Deactivate when clicking outside a text box
            canvas.addEventListener('click', (e) => {
                if (e.target === canvas) {
                    deactivateTextBox();
                }
            });
            
            // Handle mouse movement for dragging, rotating and resizing
            window.addEventListener('mousemove', (e) => {
                if (!activeTextBox) return;
                
                if (isDragging) {
                    const dx = e.clientX - lastX;
                    const dy = e.clientY - lastY;
                    
                    const currentLeft = parseInt(activeTextBox.style.left) || 0;
                    const currentTop = parseInt(activeTextBox.style.top) || 0;
                    
                    activeTextBox.style.left = `${currentLeft + dx}px`;
                    activeTextBox.style.top = `${currentTop + dy}px`;
                    
                    lastX = e.clientX;
                    lastY = e.clientY;
                }
                else if (isResizing) {
                    const dx = e.clientX - lastX;
                    const dy = e.clientY - lastY;
                    
                    const currentWidth = activeTextBox.offsetWidth;
                    const currentHeight = activeTextBox.offsetHeight;
                    
                    activeTextBox.style.width = `${Math.max(100, currentWidth + dx)}px`;
                    activeTextBox.style.height = `${Math.max(50, currentHeight + dy)}px`;
                    
                    lastX = e.clientX;
                    lastY = e.clientY;
                }
                else if (isRotating) {
                    const rect = activeTextBox.getBoundingClientRect();
                    const centerX = rect.left + rect.width / 2;
                    const centerY = rect.top + rect.height / 2;
                    
                    const angle = Math.atan2(e.clientY - centerY, e.clientX - centerX);
                    const angleDiff = angle - lastAngle;
                    
                    const currentAngle = parseFloat(activeTextBox.dataset.angle) || 0;
                    const newAngle = currentAngle + (angleDiff * (180 / Math.PI));
                    
                    activeTextBox.style.transform = `rotate(${newAngle}deg)`;
                    activeTextBox.dataset.angle = newAngle.toString();
                    
                    lastAngle = angle;
                }
            });
            
            // Stop dragging, rotating, and resizing on mouse up
            window.addEventListener('mouseup', () => {
                isDragging = false;
                isResizing = false;
                isRotating = false;
            });
        }
        
        // Function to be called from GTK application
        function addTextBox() {
            const canvas = document.getElementById('canvas');
            const centerX = canvas.offsetWidth / 2 - 100;
            const centerY = canvas.offsetHeight / 2 - 75;
            
            const textBox = createTextBox(centerX, centerY);
            activateTextBoxWithoutControls(textBox);
            
            const textarea = textBox.querySelector('textarea');
            textarea.focus();
            
            // Add keyboard shortcuts for select all
            textarea.addEventListener('keydown', function(e) {
                // Handle Ctrl+A to select all text only within this textarea
                if (e.ctrlKey && e.key === 'a') {
                    e.preventDefault();
                    this.select();
                }
            });
        }
        
        // Initialize the canvas
        document.addEventListener('DOMContentLoaded', () => {
            initEventListeners();
        });
    </script>
</body>
</html>
        """
        self.webview.load_html(html_content, "file:///")
    
    def on_add_textbox_clicked(self, button):
        self.handler.run_js("addTextBox()")


class TextBoxApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="org.example.textboxapp", 
                         flags=Gio.ApplicationFlags.FLAGS_NONE)
        
    def do_activate(self):
        win = MainWindow(self)
        win.present()


def main():
    app = TextBoxApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
