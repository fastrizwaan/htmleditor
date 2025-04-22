def convert_with_libreoffice(self, input_file, output_format="html"):
    """
    Convert a document using LibreOffice in headless mode with improved image handling
    
    Args:
        input_file: Path to the input file
        output_format: Format to convert to (default: html)
        
    Returns:
        Tuple of (path to the converted file, directory containing image files) or (None, None) if conversion failed
    """
    if not LIBREOFFICE_AVAILABLE:
        print("LibreOffice not available for document conversion")
        return None, None
        
    try:
        # Create a temporary directory for the output
        temp_dir = tempfile.mkdtemp()
        
        # Get the absolute path of the input file
        input_abs_path = os.path.abspath(input_file)
        
        # Prepare the command
        cmd = [
            'libreoffice',
            '--headless',
            '--convert-to', output_format,
            '--outdir', temp_dir,
            input_abs_path
        ]
        
        # Run the conversion process
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30  # 30 second timeout
        )
        
        if process.returncode != 0:
            print(f"LibreOffice conversion failed: {process.stderr}")
            return None, None
            
        # Get the output file name
        base_name = os.path.splitext(os.path.basename(input_file))[0]
        output_file = os.path.join(temp_dir, f"{base_name}.{output_format}")
        
        # Check if the file was actually created
        if not os.path.exists(output_file):
            print(f"LibreOffice did not create output file: {output_file}")
            return None, None
            
        return output_file, temp_dir
        
    except subprocess.TimeoutExpired:
        print("LibreOffice conversion timed out")
        return None, None
    except Exception as e:
        print(f"Error during LibreOffice conversion: {e}")
        return None, None

def load_file(self, win, filepath):
    """Load file content into editor with enhanced format support and image handling"""
    try:
        # Check if file exists
        if not os.path.exists(filepath):
            self.show_error_dialog("File not found")
            return
            
        # Store the original file path format for reference
        win.original_format = os.path.splitext(filepath)[1].lower()
        win.original_filepath = filepath
        
        # Show loading dialog for potentially slow conversions
        loading_dialog = None
        if is_libreoffice_format(filepath) and win.original_format not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            loading_dialog = self.show_loading_dialog(win)
        
        # Process the file based on its format
        file_ext = os.path.splitext(filepath)[1].lower()
        
        # Function to continue loading after potential conversion
        def continue_loading(html_content=None, converted_path=None, image_dir=None):
            try:
                # Close loading dialog if it was shown
                if loading_dialog:
                    loading_dialog.close()
                
                # Initialize content variable
                content = ""
                
                # If we already have HTML content from conversion, use it
                if html_content:
                    content = html_content
                else:
                    # Try to detect file encoding
                    encoding = 'utf-8'  # Default encoding
                    try:
                        import chardet
                        with open(filepath, 'rb') as raw_file:
                            raw_content = raw_file.read()
                            detected = chardet.detect(raw_content)
                            if detected['confidence'] > 0.7:
                                encoding = detected['encoding']
                    except ImportError:
                        pass  # Fallback to utf-8 if chardet not available
                        
                    # Now read the file with the detected encoding
                    try:
                        with open(filepath, 'r', encoding=encoding) as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        # If there's a decode error, try a fallback encoding
                        with open(filepath, 'r', encoding='latin-1') as f:
                            content = f.read()
                
                # Process content based on file type
                if file_ext in ['.mht', '.mhtml']:
                    # Handle MHTML files - extract the HTML content
                    try:
                        import email
                        message = email.message_from_string(content)
                        for part in message.walk():
                            if part.get_content_type() == 'text/html':
                                content = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                                break
                    except ImportError:
                        # Fallback to regex extraction if email module not ideal
                        body_match = re.search(r'Content-Type: text/html.*?charset=["\']?([\w-]+)["\']?.*?(?:\r?\n){2}(.*?)(?:\r?\n){1,2}--', 
                                               content, re.DOTALL | re.IGNORECASE)
                        if body_match:
                            charset, html_content = body_match.groups()
                            content = html_content
                            
                    # Extract body content from the HTML
                    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
                    if body_match:
                        content = body_match.group(1).strip()
                        
                elif file_ext in ['.html', '.htm']:
                    # Handle HTML content
                    body_match = re.search(r'<body[^>]*>(.*?)</body>', content, re.DOTALL | re.IGNORECASE)
                    if body_match:
                        content = body_match.group(1).strip()
                        
                elif file_ext in ['.md', '.markdown']:
                    # Convert markdown to HTML
                    if MARKDOWN_AVAILABLE:
                        try:
                            # Get available extensions
                            available_extensions = []
                            for ext in ['tables', 'fenced_code', 'codehilite', 'nl2br', 'sane_lists', 'smarty', 'attr_list']:
                                try:
                                    # Test if extension can be loaded
                                    markdown.markdown("test", extensions=[ext])
                                    available_extensions.append(ext)
                                except (ImportError, ValueError):
                                    pass
                            
                            # Convert markdown to HTML
                            content = markdown.markdown(content, extensions=available_extensions)
                        except Exception as e:
                            print(f"Error converting markdown: {e}")
                            # Fallback to simple conversion
                            content = self._simple_markdown_to_html(content)
                    else:
                        # Use simplified markdown conversion
                        content = self._simple_markdown_to_html(content)
                elif file_ext == '.txt':
                    # Convert plain text to HTML
                    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                    content = f"<div>{content.replace(chr(10), '<br>')}</div>"
                
                # Process image references for converted LibreOffice documents
                if image_dir and os.path.exists(image_dir):
                    # Store the image directory for reference
                    win.image_dir = image_dir
                    
                    # Process the image references in the content
                    content = self._process_image_references(content, image_dir)
                
                # Ensure content is properly wrapped in a div if not already
                if not (content.strip().startswith('<div') or content.strip().startswith('<p') or 
                        content.strip().startswith('<h')):
                    content = f"<div>{content}</div>"
                
                # Escape for JavaScript
                content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
                js_code = f'setContent("{content}");'
                
                # Check WebView load status and execute JS accordingly
                def execute_when_ready():
                    # Get the current load status
                    load_status = win.webview.get_estimated_load_progress()
                    
                    if load_status == 1.0:  # Fully loaded
                        # Execute directly
                        self.execute_js(win, js_code)
                        return False  # Stop the timeout
                    else:
                        # Set up a handler for when loading finishes
                        def on_load_changed(webview, event):
                            if event == WebKit.LoadEvent.FINISHED:
                                self.execute_js(win, js_code)
                                webview.disconnect_by_func(on_load_changed)
                        
                        win.webview.connect("load-changed", on_load_changed)
                        return False  # Stop the timeout
                
                # Use GLib timeout to ensure we're not in the middle of another operation
                GLib.timeout_add(50, execute_when_ready)
                
                # Update file information
                win.current_file = Gio.File.new_for_path(filepath)
                win.modified = False
                self.update_window_title(win)
                win.statusbar.set_text(f"Opened {os.path.basename(filepath)}")
                
                # Clean up temporary converted file if it exists and is different from original
                if converted_path and converted_path != filepath:
                    try:
                        os.remove(converted_path)
                    except:
                        pass
                        
            except Exception as e:
                # Close loading dialog if it was shown
                if loading_dialog:
                    loading_dialog.close()
                print(f"Error processing file content: {str(e)}")
                win.statusbar.set_text(f"Error processing file: {str(e)}")
                self.show_error_dialog(f"Error processing file: {e}")
        
        # Check if file needs LibreOffice conversion
        if is_libreoffice_format(filepath) and file_ext not in ['.html', '.htm', '.txt', '.md', '.markdown']:
            # Start the conversion in a separate thread to keep UI responsive
            def convert_thread():
                try:
                    # Convert the file to HTML using LibreOffice
                    converted_file, image_dir = convert_with_libreoffice(filepath, "html")
                    
                    if converted_file:
                        # Read the converted HTML file
                        with open(converted_file, 'r', encoding='utf-8') as f:
                            html_content = f.read()
                            
                        # Extract body content
                        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL | re.IGNORECASE)
                        if body_match:
                            html_content = body_match.group(1).strip()
                        
                        # Schedule continuing in the main thread with the HTML content
                        GLib.idle_add(lambda: continue_loading(html_content, converted_file, image_dir))
                    else:
                        # Conversion failed
                        GLib.idle_add(lambda: self.show_error_dialog("Failed to convert document with LibreOffice"))
                        GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                except Exception as e:
                    print(f"Error in conversion thread: {e}")
                    GLib.idle_add(lambda: self.show_error_dialog(f"Conversion error: {e}"))
                    GLib.idle_add(lambda: loading_dialog.close() if loading_dialog else None)
                
                return False  # Don't repeat
            
            # Start the conversion thread
            GLib.idle_add(lambda: GLib.Thread.new(None, convert_thread) and False)
        else:
            # Continue with normal loading for directly supported formats
            continue_loading()
            
    except Exception as e:
        if loading_dialog:
            loading_dialog.close()
        print(f"Error loading file: {str(e)}")
        win.statusbar.set_text(f"Error loading file: {str(e)}")
        self.show_error_dialog(f"Error loading file: {e}")

def _process_image_references(self, html_content, image_dir):
    """Process image references in HTML content converted from LibreOffice documents"""
    try:
        # Check if we need to store the image directory in our app's data directory
        app_data_dir = os.path.join(GLib.get_user_data_dir(), 'htmleditor', 'images')
        os.makedirs(app_data_dir, exist_ok=True)
        
        # Generate a unique session ID for this document
        import uuid
        session_id = str(uuid.uuid4())
        doc_image_dir = os.path.join(app_data_dir, session_id)
        os.makedirs(doc_image_dir, exist_ok=True)
        
        # Define a function to process an image tag
        def process_image_ref(match):
            img_tag = match.group(0)
            src = match.group(1)
            
            # Skip already processed or external images
            if src.startswith(('http://', 'https://', 'data:')):
                return img_tag
                
            # If the src is relative, try to find the image in the image directory
            img_path = os.path.join(image_dir, src)
            if not os.path.exists(img_path):
                # Try removing any directory prefix
                img_path = os.path.join(image_dir, os.path.basename(src))
                
            if os.path.exists(img_path):
                # Copy the image to our data directory
                dest_filename = os.path.basename(img_path)
                dest_path = os.path.join(doc_image_dir, dest_filename)
                
                try:
                    shutil.copy2(img_path, dest_path)
                    
                    # Convert the image to a data URL to embed it directly
                    with open(dest_path, 'rb') as img_file:
                        import base64
                        img_data = base64.b64encode(img_file.read()).decode('utf-8')
                        mime_type = self._get_mime_type(dest_path)
                        data_url = f"data:{mime_type};base64,{img_data}"
                        
                        # Replace the src attribute with the data URL
                        return img_tag.replace(f'src="{src}"', f'src="{data_url}"')
                except Exception as e:
                    print(f"Error copying image {img_path}: {e}")
                    
            # If we couldn't process the image, return the original tag
            return img_tag
        
        # Find and process all image tags
        processed_html = re.sub(r'<img[^>]+src="([^"]+)"[^>]*>', process_image_ref, html_content)
        
        return processed_html
    except Exception as e:
        print(f"Error processing image references: {e}")
        return html_content

def _get_mime_type(self, file_path):
    """Get MIME type for a file"""
    # Simple extension-based MIME type detection
    ext = os.path.splitext(file_path)[1].lower()
    mime_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.svg': 'image/svg+xml',
        '.webp': 'image/webp',
    }
    return mime_map.get(ext, 'application/octet-stream')

def cleanup_temp_files(self, win):
    """Clean up temporary files when closing a window"""
    # Clean up image directory if it exists
    if hasattr(win, 'image_dir') and win.image_dir and os.path.exists(win.image_dir):
        try:
            shutil.rmtree(win.image_dir)
        except Exception as e:
            print(f"Error cleaning up image directory: {e}")
