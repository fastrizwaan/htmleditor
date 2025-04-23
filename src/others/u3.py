#!/usr/bin/env python3
import gi
import tempfile
import os
import json

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, GLib, WebKit, Gio

class PaginatedEditor(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.example.PaginatedEditor")
        self.connect('activate', self.on_activate)
        self.tempdir = tempfile.mkdtemp()
        self.editor_html_path = os.path.join(self.tempdir, "editor.html")
        self.content_changed = False
        
    def on_activate(self, app):
        # Create the application window
        self.win = Adw.ApplicationWindow(application=app, default_width=900, default_height=800)
        self.win.set_title("Advanced Paginated Editor")
        
        # Main box layout
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.win.set_content(main_box)
        
        # Create the header bar
        header = Adw.HeaderBar()
        main_box.append(header)
        
        # Add save button
        save_button = Gtk.Button(label="Save")
        save_button.connect("clicked", self.on_save_clicked)
        header.pack_end(save_button)
        
        # Add format options using a menu button
        format_button = Gtk.MenuButton()
        format_button.set_label("Format")
        format_button.set_tooltip_text("Text formatting options")
        
        # Create a popover menu
        format_menu = Gtk.PopoverMenu()
        format_button.set_popover(format_menu)
        header.pack_start(format_button)
        
        # Create WebView
        self.webview = WebKit.WebView()
        self.webview.set_vexpand(True)
        self.webview.set_hexpand(True)
        
        # Connect to signals
        self.webview.connect("load-changed", self.on_load_changed)
        
        # Create scrolled window for the webview
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.webview)
        main_box.append(scrolled)
        
        # Create editor HTML file
        self.create_editor_html()
        
        # Load the editor
        self.webview.load_uri(f"file://{self.editor_html_path}")
        
        # Show the window
        self.win.present()
    
    def create_editor_html(self):
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Advanced Paginated Editor</title>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Noto Sans', Arial, sans-serif;
            overflow-x: hidden;
            background-color: #f5f5f5;
        }
        
        #editor-container {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 30px;
            padding: 40px 20px;
            min-height: 100vh;
        }
        
        .page {
            width: 595px; /* A4 width in pixels at 72dpi */
            height: 842px; /* A4 height in pixels at 72dpi */
            border: 1px solid #ccc;
            box-sizing: border-box;
            position: relative;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            background-color: white;
            overflow: hidden;
            display: flex;
            flex-direction: column;
        }
        
        .page-content {
            position: absolute;
            top: 72px; /* 1 inch top margin */
            left: 72px; /* 1 inch left margin */
            right: 72px; /* 1 inch right margin */
            bottom: 72px; /* 1 inch bottom margin */
            overflow: hidden;
            line-height: 1.5;
            font-size: 12pt;
        }
        
        .page-number {
            position: absolute;
            bottom: 30px;
            left: 0;
            right: 0;
            text-align: center;
            font-size: 10pt;
            color: #888;
            user-select: none;
        }
        
        .document {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            visibility: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            line-height: 1.5;
            font-size: 12pt;
            padding: 0;
            margin: 0;
        }
        
        #editor {
            position: absolute;
            top: 0px;
            left: 0px;
            right: 0px;
            bottom: 0px;
            width: 100%;
            outline: none;
            white-space: pre-wrap;
            word-wrap: break-word;
            overflow: auto;
            padding: 20px;
            box-sizing: border-box;
            line-height: 1.5;
            z-index: 1;
        }
        
        .toolbar {
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: white;
            border-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            padding: 5px 10px;
            display: flex;
            gap: 10px;
            z-index: 100;
        }
        
        .toolbar button {
            background: none;
            border: none;
            border-radius: 4px;
            padding: 5px 10px;
            cursor: pointer;
            font-size: 14px;
        }
        
        .toolbar button:hover {
            background: #f0f0f0;
        }
        
        .toolbar button.active {
            background: #e0e0e0;
        }
        
        .toolbar select {
            height: 30px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        
        .toolbar .separator {
            width: 1px;
            background-color: #ccc;
            margin: 0 5px;
        }
        
        .page-view {
            position: relative;
            z-index: 0;
        }
        
        /* Page break indicator */
        .page-break {
            border-bottom: 1px dashed #999;
            margin: 20px 0;
            user-select: none;
            position: relative;
            height: 20px;
        }
        
        .page-break::after {
            content: 'Page Break';
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #f5f5f5;
            padding: 0 10px;
            font-size: 10px;
            color: #666;
        }
        
        /* Hide the invisible measuring elements */
        .measure-element {
            position: absolute;
            visibility: hidden;
            white-space: pre-wrap;
            word-wrap: break-word;
            width: 451px; /* 595px - 72px*2 (A4 width minus margins) */
        }
        
        /* Loading overlay */
        #loading-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(255, 255, 255, 0.8);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        
        .spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <!-- Loading overlay -->
    <div id="loading-overlay">
        <div class="spinner"></div>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
        <button id="btnBold" title="Bold (Ctrl+B)">B</button>
        <button id="btnItalic" title="Italic (Ctrl+I)"><i>I</i></button>
        <button id="btnUnderline" title="Underline (Ctrl+U)"><u>U</u></button>
        <div class="separator"></div>
        <select id="fontFamily">
            <option value="Arial">Arial</option>
            <option value="Times New Roman">Times New Roman</option>
            <option value="Courier New">Courier New</option>
            <option value="Georgia">Georgia</option>
            <option value="Verdana">Verdana</option>
        </select>
        <select id="fontSize">
            <option value="10">10pt</option>
            <option value="11">11pt</option>
            <option value="12" selected>12pt</option>
            <option value="14">14pt</option>
            <option value="16">16pt</option>
            <option value="18">18pt</option>
            <option value="24">24pt</option>
        </select>
    </div>
    
    <!-- Main editor (hidden, but used for content editing) -->
    <div id="editor" contenteditable="true" spellcheck="false"></div>
    
    <!-- Container for page display -->
    <div id="editor-container"></div>
    
    <!-- Element used for measuring text dimensions -->
    <div id="measure-element" class="measure-element"></div>
    
    <!-- Full document element used for layout calculations -->
    <div id="document" class="document"></div>

    <script>
        // Document model
        class DocumentModel {
            constructor() {
                this.content = '';              // Raw text content
                this.paragraphs = [];           // Array of paragraph objects
                this.styles = {};               // Map of styles keyed by position
                this.pages = [];                // Array of page objects after pagination
                this.selection = { start: 0, end: 0 }; // Current selection range
                this.cursorPosition = 0;        // Current cursor position
                
                // Default style
                this.defaultStyle = {
                    fontFamily: 'Arial',
                    fontSize: '12pt',
                    fontWeight: 'normal',
                    fontStyle: 'normal',
                    textDecoration: 'none',
                    color: '#000000'
                };
            }
            
            // Set content and parse paragraphs
            setContent(content) {
                this.content = content;
                this.parseParagraphs();
            }
            
            // Parse content into paragraphs
            parseParagraphs() {
                // Split by double newlines (paragraph breaks)
                const paragraphTexts = this.content.split(/\\n\\n+/);
                this.paragraphs = paragraphTexts.map((text, index) => {
                    return {
                        id: `p-${index}`,
                        text: text,
                        start: index === 0 ? 0 : this.getParagraphStart(index, paragraphTexts)
                    };
                });
            }
            
            // Calculate paragraph start position
            getParagraphStart(index, paragraphTexts) {
                let position = 0;
                for (let i = 0; i < index; i++) {
                    position += paragraphTexts[i].length + 2; // +2 for paragraph separator
                }
                return position;
            }
            
            // Get content as HTML with styles applied
            getContentAsHtml() {
                if (!this.paragraphs.length) return '';
                
                let html = '';
                this.paragraphs.forEach(paragraph => {
                    html += `<p>${this.getStyledText(paragraph.text, paragraph.start)}</p>`;
                });
                return html;
            }
            
            // Apply styles to text
            getStyledText(text, startPosition) {
                // Simple version - in a real implementation this would apply 
                // character-level styles from the styles map
                return text;
            }
            
            // Insert text at cursor position
            insertText(text) {
                const newContent = 
                    this.content.substring(0, this.cursorPosition) + 
                    text + 
                    this.content.substring(this.cursorPosition);
                
                this.setContent(newContent);
                this.cursorPosition += text.length;
                this.selection = { start: this.cursorPosition, end: this.cursorPosition };
            }
            
            // Delete text in selection range or at cursor
            deleteText() {
                if (this.selection.start === this.selection.end) {
                    // No selection, delete character before cursor
                    if (this.cursorPosition > 0) {
                        const newContent = 
                            this.content.substring(0, this.cursorPosition - 1) + 
                            this.content.substring(this.cursorPosition);
                        
                        this.setContent(newContent);
                        this.cursorPosition--;
                        this.selection = { start: this.cursorPosition, end: this.cursorPosition };
                    }
                } else {
                    // Delete selected text
                    const newContent = 
                        this.content.substring(0, this.selection.start) + 
                        this.content.substring(this.selection.end);
                    
                    this.setContent(newContent);
                    this.cursorPosition = this.selection.start;
                    this.selection = { start: this.cursorPosition, end: this.cursorPosition };
                }
            }
            
            // Apply style to selection
            applyStyle(style) {
                // In a real implementation, this would update the styles map
                // for the selected range
                console.log(`Applying style ${JSON.stringify(style)} to range ${this.selection.start}-${this.selection.end}`);
            }
        }
        
        // Layout engine for pagination
        class LayoutEngine {
            constructor(documentModel) {
                this.document = documentModel;
                this.measureElement = document.getElementById('measure-element');
                this.fullDocumentElement = document.getElementById('document');
                
                // Page dimensions (A4)
                this.pageWidth = 595;  // pixels at 72dpi
                this.pageHeight = 842; // pixels at 72dpi
                
                // Margins (1 inch on all sides)
                this.margins = {
                    top: 72,
                    right: 72,
                    bottom: 72,
                    left: 72
                };
                
                // Calculated content area
                this.contentWidth = this.pageWidth - this.margins.left - this.margins.right;
                this.contentHeight = this.pageHeight - this.margins.top - this.margins.bottom;
            }
            
            // Calculate layout and paginate content
            calculateLayout() {
                // Apply document content to measurement element
                this.fullDocumentElement.innerHTML = this.document.getContentAsHtml();
                this.fullDocumentElement.style.width = `${this.contentWidth}px`;
                
                // Get all paragraph elements
                const paragraphElements = this.fullDocumentElement.querySelectorAll('p');
                
                // Create pages
                this.document.pages = [];
                let currentPage = { content: '', elements: [], height: 0 };
                
                // Process each paragraph for pagination
                Array.from(paragraphElements).forEach(paragraph => {
                    // Clone paragraph for measurement
                    const clone = paragraph.cloneNode(true);
                    this.measureElement.innerHTML = '';
                    this.measureElement.appendChild(clone);
                    
                    const paragraphHeight = clone.offsetHeight;
                    
                    // Check if paragraph fits on current page
                    if (currentPage.height + paragraphHeight > this.contentHeight) {
                        // If not, check if we need to split the paragraph
                        if (currentPage.height === 0) {
                            // Page is empty but paragraph is too large, must split
                            this.splitParagraphAcrossPages(paragraph, currentPage);
                        } else {
                            // Complete the current page and start a new one
                            this.document.pages.push(currentPage);
                            currentPage = { content: '', elements: [], height: 0 };
                            
                            // Now add paragraph to the new page
                            currentPage.elements.push(paragraph.cloneNode(true));
                            currentPage.height += paragraphHeight;
                            currentPage.content += paragraph.outerHTML;
                        }
                    } else {
                        // Paragraph fits on current page
                        currentPage.elements.push(paragraph.cloneNode(true));
                        currentPage.height += paragraphHeight;
                        currentPage.content += paragraph.outerHTML;
                    }
                });
                
                // Add the last page if it has content
                if (currentPage.height > 0) {
                    this.document.pages.push(currentPage);
                }
                
                return this.document.pages;
            }
            
            // Split a paragraph across pages (simplified implementation)
            splitParagraphAcrossPages(paragraph, currentPage) {
                // This is a simplified implementation
                // In a real-world editor, you would need a more sophisticated algorithm
                // that splits text at word boundaries and properly handles inline formatting
                
                const clone = paragraph.cloneNode(true);
                this.measureElement.innerHTML = '';
                this.measureElement.appendChild(clone);
                
                // Get the text content
                const text = paragraph.textContent;
                const words = text.split(' ');
                
                let firstPartWords = [];
                let remainingWords = [...words];
                
                // Binary search to find how many words fit on the current page
                let low = 0;
                let high = words.length;
                
                while (low < high) {
                    const mid = Math.floor((low + high) / 2);
                    
                    // Test with mid words
                    firstPartWords = words.slice(0, mid);
                    clone.textContent = firstPartWords.join(' ');
                    
                    const height = clone.offsetHeight;
                    
                    if (height <= this.contentHeight) {
                        low = mid + 1;
                    } else {
                        high = mid;
                    }
                }
                
                // After binary search, low - 1 is our answer
                firstPartWords = words.slice(0, low - 1);
                remainingWords = words.slice(low - 1);
                
                // Create two paragraph parts
                const firstPart = document.createElement('p');
                firstPart.textContent = firstPartWords.join(' ');
                
                const secondPart = document.createElement('p');
                secondPart.textContent = remainingWords.join(' ');
                
                // Measure the first part
                this.measureElement.innerHTML = '';
                this.measureElement.appendChild(firstPart);
                const firstPartHeight = firstPart.offsetHeight;
                
                // Add first part to current page
                currentPage.elements.push(firstPart);
                currentPage.height += firstPartHeight;
                currentPage.content += firstPart.outerHTML;
                
                // Complete the current page
                this.document.pages.push(currentPage);
                
                // Create a new page with the second part
                const nextPage = { content: '', elements: [], height: 0 };
                
                // Measure the second part
                this.measureElement.innerHTML = '';
                this.measureElement.appendChild(secondPart);
                const secondPartHeight = secondPart.offsetHeight;
                
                // Add second part to the new page
                nextPage.elements.push(secondPart);
                nextPage.height += secondPartHeight;
                nextPage.content += secondPart.outerHTML;
                
                // Start next page
                this.document.pages.push(nextPage);
            }
        }
        
        // View/Controller for the editor
        class EditorController {
            constructor() {
                this.documentModel = new DocumentModel();
                this.layoutEngine = new LayoutEngine(this.documentModel);
                
                // DOM elements
                this.editorElement = document.getElementById('editor');
                this.containerElement = document.getElementById('editor-container');
                this.loadingOverlay = document.getElementById('loading-overlay');
                
                // View mode settings
                this.viewMode = 'page';  // 'page' or 'continuous'
                this.showingPages = false;
                
                // Initialize editor
                this.initializeEditor();
                this.initializeToolbar();
                
                // Initial render with sample text
                this.insertSampleText();
                this.render();
            }
            
            // Sample text for testing
            insertSampleText() {
                const sampleText = 
                    "This is a sample document demonstrating the paginated editor. " +
                    "You can edit this text, and it will automatically flow between pages " +
                    "as you type.\n\n" +
                    "The editor supports automatic pagination with a proper document model. " +
                    "Text is measured accurately to determine page breaks.\n\n" +
                    "You can format text using the toolbar above. As you edit, the text will " +
                    "reflow across pages dynamically.\n\n" +
                    "Paragraphs are preserved as cohesive units, and the editor attempts " +
                    "to avoid orphaned lines at the bottom or top of pages.\n\n" +
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod " +
                    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim " +
                    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea " +
                    "commodo consequat.\n\n" +
                    "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum " +
                    "dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non " +
                    "proident, sunt in culpa qui officia deserunt mollit anim id est laborum.\n\n" +
                    "This editor demonstrates how to implement flowing text that properly handles " +
                    "pagination in a word processor style interface. The text should flow naturally " +
                    "from one page to another as you type or delete content.";
                
                this.documentModel.setContent(sampleText);
            }
            
            // Initialize the editor and event handlers
            initializeEditor() {
                // Set up editor with initial content
                this.editorElement.addEventListener('input', () => this.handleInput());
                this.editorElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
                this.editorElement.addEventListener('mouseup', () => this.handleSelectionChange());
                this.editorElement.addEventListener('keyup', () => this.handleSelectionChange());
                
                // Handle focus events
                this.editorElement.addEventListener('focus', () => {
                    document.querySelector('.toolbar').style.display = 'flex';
                });
                
                this.editorElement.addEventListener('blur', () => {
                    setTimeout(() => {
                        if (document.activeElement.closest('.toolbar') === null) {
                            document.querySelector('.toolbar').style.display = 'none';
                        }
                    }, 100);
                });
                
                // Position editor off-screen initially (we use page view by default)
                this.editorElement.style.position = 'absolute';
                this.editorElement.style.left = '-9999px';
            }
            
            // Initialize toolbar buttons and controls
            initializeToolbar() {
                // Format buttons
                document.getElementById('btnBold').addEventListener('click', () => {
                    this.applyFormat('bold');
                });
                
                document.getElementById('btnItalic').addEventListener('click', () => {
                    this.applyFormat('italic');
                });
                
                document.getElementById('btnUnderline').addEventListener('click', () => {
                    this.applyFormat('underline');
                });
                
                // Font family and size selectors
                document.getElementById('fontFamily').addEventListener('change', (e) => {
                    this.applyFormat('fontFamily', e.target.value);
                });
                
                document.getElementById('fontSize').addEventListener('change', (e) => {
                    this.applyFormat('fontSize', `${e.target.value}pt`);
                });
            }
            
            // Apply formatting to selected text
            applyFormat(format, value) {
                if (format === 'bold') {
                    document.execCommand('bold', false);
                } else if (format === 'italic') {
                    document.execCommand('italic', false);
                } else if (format === 'underline') {
                    document.execCommand('underline', false);
                } else if (format === 'fontFamily') {
                    document.execCommand('fontName', false, value);
                } else if (format === 'fontSize') {
                    // Convert pt to browser font size (1-7)
                    const ptSize = parseInt(value);
                    let sizeIndex;
                    
                    if (ptSize <= 10) sizeIndex = 1;
                    else if (ptSize <= 12) sizeIndex = 2;
                    else if (ptSize <= 14) sizeIndex = 3;
                    else if (ptSize <= 18) sizeIndex = 4;
                    else if (ptSize <= 24) sizeIndex = 5;
                    else if (ptSize <= 36) sizeIndex = 6;
                    else sizeIndex = 7;
                    
                    document.execCommand('fontSize', false, sizeIndex);
                }
                
                this.handleInput();
            }
            
            // Handle input changes
            handleInput() {
                // Update document model with current editor content
                const content = this.getCleanHTMLContent();
                this.documentModel.setContent(this.convertHTMLToPlainText(content));
                
                // Debounce rendering to avoid excessive calculations while typing
                clearTimeout(this.renderTimeout);
                this.renderTimeout = setTimeout(() => {
                    this.render();
                    // Notify Python app of content change
                    this.notifyContentChanged();
                }, 300);
            }
            
            // Convert HTML content to plain text while preserving paragraphs
            convertHTMLToPlainText(html) {
                // Create a temporary div to parse HTML
                const temp = document.createElement('div');
                temp.innerHTML = html;
                
                // Extract text content by paragraph
                const paragraphs = [];
                temp.querySelectorAll('p, div').forEach(paragraph => {
                    paragraphs.push(paragraph.textContent);
                });
                
                // Join paragraphs with double newlines
                return paragraphs.join('\n\n');
            }
            
            // Get cleaned HTML content from editor
            getCleanHTMLContent() {
                // This simplifies the HTML by standardizing paragraph structure
                const content = this.editorElement.innerHTML;
                
                // Replace divs with p tags and normalize content
                let cleaned = content.replace(/<div>/g, '<p>').replace(/<\/div>/g, '</p>');
                
                // Replace series of <br> with paragraph breaks
                cleaned = cleaned.replace(/<br\s*\/?>\s*<br\s*\/?>/g, '</p><p>');
                
                // Ensure content starts and ends with paragraph tags
                if (!cleaned.trim().startsWith('<p>')) {
                    cleaned = '<p>' + cleaned;
                }
                if (!cleaned.trim().endsWith('</p>')) {
                    cleaned = cleaned + '</p>';
                }
                
                return cleaned;
            }
            
            // Handle key presses
            handleKeyDown(e) {
                // Ctrl+S to save
                if (e.ctrlKey && e.key === 's') {
                    e.preventDefault();
                    this.saveDocument();
                }
                
                // Format shortcuts
                if (e.ctrlKey) {
                    if (e.key === 'b') {
                        e.preventDefault();
                        this.applyFormat('bold');
                    } else if (e.key === 'i') {
                        e.preventDefault();
                        this.applyFormat('italic');
                    } else if (e.key === 'u') {
                        e.preventDefault();
                        this.applyFormat('underline');
                    }
                }
            }
            
            // Handle selection changes
            handleSelectionChange() {
                const selection = window.getSelection();
                if (selection.rangeCount > 0) {
                    const range = selection.getRangeAt(0);
                    
                    // Update document model with selection info
                    // In a real implementation, this would map DOM positions to document positions
                    this.documentModel.selection = {
                        start: range.startOffset,
                        end: range.endOffset
                    };
                }
            }
            
            // Render document pages
            render() {
                // Show loading indicator for complex documents
                this.loadingOverlay.style.display = 'flex';
                
                // Use setTimeout to allow UI to update before running intensive calculation
                setTimeout(() => {
                    // Calculate pagination
                    const pages = this.layoutEngine.calculateLayout();
                    
                    // Clear container
                    this.containerElement.innerHTML = '';
                    
                    // Create page elements
                    pages.forEach((page, index) => {
                        const pageElement = document.createElement('div');
                        pageElement.className = 'page';
                        
                        const contentElement = document.createElement('div');
                        contentElement.className = 'page-content';
                        contentElement.innerHTML = page.content;
                        
                        const pageNumberElement = document.createElement('div');
                        pageNumberElement.className = 'page-number';
                        pageNumberElement.textContent = (index + 1).toString();
                        
                        pageElement.appendChild(contentElement);
                        pageElement.appendChild(pageNumberElement);
                        
                        // Handle click on page to focus editor at appropriate position
                        pageElement.addEventListener('click', (e) => {
                            // In a real implementation, this would map click coordinates 
                            // to document position and set cursor accordingly
                            this.focusEditorAtPagePosition(index, e);
                        });
                        
                        this.containerElement.appendChild(pageElement);
                    });
                    
                    // Synchronize editor content if not already in sync
                    const content = this.documentModel.getContentAsHtml();
                    if (this.editorElement.innerHTML !== content) {
                        this.editorElement.innerHTML = content;
                    }
                    
                    // Hide loading indicator
                    this.loadingOverlay.style.display = 'none';
                    
                    this.showingPages = true;
                }, 0);
            }
            
            // Focus editor at position corresponding to click in page view
            focusEditorAtPagePosition(pageIndex, event) {
                // Switch to edit mode
                this.showEditMode();
                
                // In a real implementation, this would calculate the exact cursor position
                // For now, we'll use a simple heuristic based on page index
                let cursorPos = 0;
                for (let i = 0; i < pageIndex; i++) {
                    // Estimate position based on page content length
                    cursorPos += this.documentModel.pages[i].content.length;
                }
                
                // Focus the editor
                this.editorElement.focus();
                
                // Set cursor position (simplified)
                try {
                    const selection = window.getSelection();
                    const range = document.createRange();
                    
                    // Find the appropriate text node (simplified)
                    const textNodes = [];
                    const walker = document.createTreeWalker(
                        this.editorElement, 
                        NodeFilter.SHOW_TEXT
                    );
                    
                    let node;
                    while (node = walker.nextNode()) {
                        textNodes.push(node);
                    }
                    
                    if (textNodes.length > 0) {
                        const targetNode = textNodes[0];
                        range.setStart(targetNode, Math.min(cursorPos, targetNode.length));
                        range.collapse(true);
                        selection.removeAllRanges();
                        selection.addRange(range);
                    }
                } catch (e) {
                    console.error('Error setting cursor position:', e);
                    this.editorElement.focus();
                }
            }
            
            // Switch to edit mode (showing editor directly)
            showEditMode() {
                if (this.viewMode === 'edit') return;
                
                this.viewMode = 'edit';
                this.editorElement.style.position = 'static';
                this.editorElement.style.left = 'auto';
                this.containerElement.style.display = 'none';
                this.editorElement.focus();
            }
            
            // Switch to page view mode
            showPageMode() {
                if (this.viewMode === 'page') return;
                
                this.viewMode = 'page';
                this.editorElement.style.position = 'absolute';
                this.editorElement.style.left = '-9999px';
                this.containerElement.style.display = 'flex';
                this.render();
            }
            
            // Toggle between edit and page view modes
            toggleViewMode() {
                if (this.viewMode === 'page') {
                    this.showEditMode();
                } else {
                    this.showPageMode();
                }
            }
            
            // Save document
            saveDocument() {
                window.webkit.messageHandlers.saveRequested.postMessage('save');
            }
            
            // Notify Python app that content has changed
            notifyContentChanged() {
                window.webkit.messageHandlers.contentChanged.postMessage('changed');
            }
            
            // Get document content as HTML for saving
            getContentAsHtml() {
                // Create a properly formatted HTML document with CSS for pagination
                let html = '<!DOCTYPE html>\n<html>\n<head>\n';
                html += '<meta charset="UTF-8">\n';
                html += '<title>Paginated Document</title>\n';
                html += '<style>\n';
                html += '@page { size: A4; margin: 1in; }\n';
                html += 'body { font-family: Arial, sans-serif; line-height: 1.5; }\n';
                html += 'p { margin: 0 0 1em 0; }\n';
                html += '.page { page-break-after: always; }\n';
                html += '.page:last-child { page-break-after: auto; }\n';
                html += '</style>\n';
                html += '</head>\n<body>\n';
                
                // Add each page with page breaks
                this.documentModel.pages.forEach((page, index) => {
                    html += '<div class="page">\n';
                    html += page.content;
                    html += '\n</div>\n';
                });
                
                html += '</body>\n</html>';
                return html;
            }
            
            // Get document content as plain text
            getContentAsText() {
                return this.documentModel.content;
            }
        }
        
        // Initialize the editor after page load
        document.addEventListener('DOMContentLoaded', () => {
            const editor = new EditorController();
            window.editor = editor;  // Expose editor to global scope for debugging
            
            // Hide loading overlay after initialization
            setTimeout(() => {
                document.getElementById('loading-overlay').style.display = 'none';
            }, 500);
        });
        
        // Function to get document content as HTML (called from Python)
        function getContentAsHtml() {
            return window.editor ? window.editor.getContentAsHtml() : '';
        }
        
        // Function to get document content as text (called from Python)
        function getContentAsText() {
            return window.editor ? window.editor.getContentAsText() : '';
        }
    </script>
</body>
</html>
"""
        with open(self.editor_html_path, 'w') as f:
            f.write(html_content)
            
    def on_load_changed(self, webview, load_event):
        if load_event == WebKit.LoadEvent.FINISHED:
            # Register message handlers for communication between JS and Python
            user_content_manager = self.webview.get_user_content_manager()
            
            # Handler for content changes
            content_changed_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "contentChanged")
            if content_changed_handler:
                user_content_manager.connect("script-message-received::contentChanged", self.on_content_changed)
            
            # Handler for save requests
            save_handler = WebKit.UserContentManager.register_script_message_handler(user_content_manager, "saveRequested")
            if save_handler:
                user_content_manager.connect("script-message-received::saveRequested", self.on_save_requested)
    
    def on_content_changed(self, manager, message):
        self.content_changed = True
    
    def on_save_requested(self, manager, message):
        self.on_save_clicked(None)
    
    def on_save_clicked(self, button):
        # Create file chooser dialog
        dialog = Gtk.FileChooserDialog(
            title="Save Document",
            parent=self.win,
            action=Gtk.FileChooserAction.SAVE
        )
        dialog.add_buttons(
            "_Cancel", Gtk.ResponseType.CANCEL,
            "_Save", Gtk.ResponseType.ACCEPT
        )
        dialog.set_current_name("document.html")
        
        # Set up filters
        filter_html = Gtk.FileFilter()
        filter_html.set_name("HTML files")
        filter_html.add_mime_type("text/html")
        dialog.add_filter(filter_html)
        
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)
        
        dialog.connect("response", self.on_save_dialog_response)
        dialog.present()
    
    def on_save_dialog_response(self, dialog, response):
        if response == Gtk.ResponseType.ACCEPT:
            file_path = dialog.get_file().get_path()
            file_filter = dialog.get_filter()
            
            if file_filter.get_name() == "HTML files":
                # Get HTML content from WebView
                self.webview.evaluate_javascript("getContentAsHtml();", -1, None, None, None, None, self.save_html_callback, file_path)
            else:
                # Get plain text content from WebView
                self.webview.evaluate_javascript("getContentAsText();", -1, None, None, None, None, self.save_text_callback, file_path)
        
        dialog.destroy()
    
    def save_html_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                html_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(html_content)
                
                self.show_notification("Document saved as HTML")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def save_text_callback(self, result, user_data):
        file_path = user_data
        try:
            js_result = self.webview.evaluate_javascript_finish(result)
            if js_result:
                text_content = js_result.get_js_value().to_string()
                
                # Save to file
                with open(file_path, 'w') as f:
                    f.write(text_content)
                
                self.show_notification("Document saved as text")
                self.content_changed = False
        except Exception as e:
            self.show_notification(f"Error saving document: {str(e)}")
    
    def show_notification(self, message):
        toast = Adw.Toast.new(message)
        toast.set_timeout(3)
        
        # Check if we have a toast overlay available
        content = self.win.get_content()
        if isinstance(content, Adw.ToastOverlay):
            toast_overlay = content
        else:
            # Create a toast overlay
            toast_overlay = Adw.ToastOverlay()
            # Get the current content
            current_content = self.win.get_content()
            # Remove it from the window
            self.win.set_content(None)
            # Add it to the toast overlay
            toast_overlay.set_child(current_content)
            # Set the toast overlay as the window content
            self.win.set_content(toast_overlay)
        
        # Add the toast
        toast_overlay.add_toast(toast)
    
    def do_shutdown(self):
        # Clean up temporary files
        if os.path.exists(self.tempdir):
            for file in os.listdir(self.tempdir):
                os.unlink(os.path.join(self.tempdir, file))
            os.rmdir(self.tempdir)
        
        Adw.Application.do_shutdown(self)

if __name__ == "__main__":
    app = PaginatedEditor()
    app.run(None)
