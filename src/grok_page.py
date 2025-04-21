#!/usr/bin/env python3
import sys
import gi
import re
import os

os.environ['WEBKIT_DISABLE_COMPOSITING_MODE'] = '1'

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
gi.require_version('WebKit', '6.0')

from gi.repository import Gtk, Adw, Gdk, WebKit, GLib, Gio, Pango, PangoCairo, Gdk

class HTMLEditorApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(application_id='io.github.fastrizwaan.htmleditor',
                        flags=Gio.ApplicationFlags.HANDLES_OPEN,
                        **kwargs)
        self.windows = []
        self.window_buttons = {}
        self.connect('activate', self.on_activate)
        self.modified = False
        self.auto_save_enabled = False
        self.auto_save_interval = 60
        self.current_file = None
        self.auto_save_source_id = None

    def do_startup(self):
        Adw.Application.do_startup(self)
        self.setup_css_provider()

    def setup_css_provider(self):
        self.css_provider = Gtk.CssProvider()
        css_data = b"""
        .flat { background: none; }
        .flat:hover { background: rgba(127, 127, 127, 0.25); }
        .flat:checked { background: rgba(127, 127, 127, 0.25); }
        """
        try:
            self.css_provider.load_from_data(css_data)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(),
                self.css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"Error applying CSS provider: {e}")

    def on_activate(self, app):
        win = self.create_window()
        win.present()
        GLib.timeout_add(500, lambda: self.set_initial_focus(win))

    def setup_headerbar_content(self, win):
        win.headerbar.set_margin_top(0)
        win.headerbar.set_margin_bottom(0)
        title_widget = Adw.WindowTitle()
        title_widget.set_title("Untitled  - HTML Editor")
        win.title_widget = title_widget
        win.headerbar.set_title_widget(title_widget)

    def create_file_toolbar(self, win):
        file_toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        file_toolbar.set_margin_start(4)
        file_toolbar.set_margin_end(0)
        file_toolbar.set_margin_top(5)
        file_toolbar.set_margin_bottom(0)
        
        insert_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        insert_group.add_css_class("linked")
        insert_group.set_margin_start(6)

        table_button = Gtk.Button(icon_name="table-symbolic")
        table_button.set_size_request(40, 36)
        table_button.set_tooltip_text("Insert Table")
        table_button.connect("clicked", lambda btn: self.on_insert_table_clicked(win, btn))

        text_box_button = Gtk.Button(icon_name="insert-text-symbolic")
        text_box_button.set_size_request(40, 36)
        text_box_button.set_tooltip_text("Insert Text Box")
        text_box_button.connect("clicked", lambda btn: self.on_insert_text_box_clicked(win, btn))

        image_button = Gtk.Button(icon_name="insert-image-symbolic")
        image_button.set_size_request(40, 36)
        image_button.set_tooltip_text("Insert Image")
        image_button.connect("clicked", lambda btn: self.on_insert_image_clicked(win, btn))

        link_button = Gtk.Button(icon_name="insert-link-symbolic")
        link_button.set_size_request(40, 36)
        link_button.set_tooltip_text("Insert link")
        link_button.connect("clicked", lambda btn: self.on_insert_link_clicked(win, btn))

        insert_group.append(table_button)
        insert_group.append(text_box_button)
        insert_group.append(image_button)
        insert_group.append(link_button)
        file_toolbar.append(insert_group)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        file_toolbar.append(spacer)
        
        return file_toolbar

    def on_insert_table_clicked(self, win, btn):
        win.statusbar.set_text("Inserting table...")
        dialog = Adw.Dialog()
        dialog.set_title("Insert Table")
        dialog.set_content_width(350)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        content_box.set_margin_top(24)
        content_box.set_margin_bottom(24)
        content_box.set_margin_start(24)
        content_box.set_margin_end(24)
        
        rows_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rows_label = Gtk.Label(label="Rows:")
        rows_label.set_halign(Gtk.Align.START)
        rows_label.set_hexpand(True)
        rows_adjustment = Gtk.Adjustment(value=3, lower=1, upper=20, step_increment=1)
        rows_spin = Gtk.SpinButton()
        rows_spin.set_adjustment(rows_adjustment)
        rows_box.append(rows_label)
        rows_box.append(rows_spin)
        content_box.append(rows_box)
        
        cols_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        cols_label = Gtk.Label(label="Columns:")
        cols_label.set_halign(Gtk.Align.START)
        cols_label.set_hexpand(True)
        cols_adjustment = Gtk.Adjustment(value=3, lower=1, upper=10, step_increment=1)
        cols_spin = Gtk.SpinButton()
        cols_spin.set_adjustment(cols_adjustment)
        cols_box.append(cols_label)
        cols_box.append(cols_spin)
        content_box.append(cols_box)
        
        header_check = Gtk.CheckButton(label="Include header row")
        header_check.set_active(True)
        content_box.append(header_check)
        
        border_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        border_label = Gtk.Label(label="Border width:")
        border_label.set_halign(Gtk.Align.START)
        border_label.set_hexpand(True)
        border_adjustment = Gtk.Adjustment(value=1, lower=0, upper=5, step_increment=1)
        border_spin = Gtk.SpinButton()
        border_spin.set_adjustment(border_adjustment)
        border_box.append(border_label)
        border_box.append(border_spin)
        content_box.append(border_box)
        
        width_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        width_label = Gtk.Label(label="Table width:")
        width_label.set_halign(Gtk.Align.START)
        width_label.set_hexpand(True)
        width_combo = Gtk.DropDown()
        width_options = Gtk.StringList()
        width_options.append("Auto")
        width_options.append("100%")
        width_options.append("75%")
        width_options.append("50%")
        width_combo.set_model(width_options)
        width_combo.set_selected(1)
        width_box.append(width_label)
        width_box.append(width_combo)
        content_box.append(width_box)
        
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        button_box.set_halign(Gtk.Align.END)
        button_box.set_margin_top(16)
        cancel_button = Gtk.Button(label="Cancel")
        cancel_button.connect("clicked", lambda btn: dialog.close())
        insert_button = Gtk.Button(label="Insert")
        insert_button.add_css_class("suggested-action")
        insert_button.connect("clicked", lambda btn: self.on_table_dialog_response(
            win, dialog, 
            rows_spin.get_value_as_int(), 
            cols_spin.get_value_as_int(),
            header_check.get_active(),
            border_spin.get_value_as_int(),
            width_options.get_string(width_combo.get_selected())
        ))
        button_box.append(cancel_button)
        button_box.append(insert_button)
        content_box.append(button_box)
        
        dialog.set_child(content_box)
        dialog.present(win)

    def on_table_dialog_response(self, win, dialog, rows, cols, has_header, border_width, width_option):
        dialog.close()
        width_value = "auto" if width_option == "Auto" else width_option
        js_code = f"""
        (function() {{
            insertTable({rows}, {cols}, {str(has_header).lower()}, {border_width}, "{width_value}");
            return true;
        }})();
        """
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table inserted")

    def on_insert_text_box_clicked(self, win, btn):
        win.statusbar.set_text("Inserting text box...")
        js_code = """
        (function() {
            insertTextBox();
            return true;
        })();
        """
        self.execute_js(win, js_code)

    def on_insert_image_clicked(self, win, btn):
        win.statusbar.set_text("Inserting image...")
        dialog = Gtk.FileChooserNative(
            title="Select an Image",
            transient_for=win,
            action=Gtk.FileChooserAction.OPEN,
            accept_label="_Open",
            cancel_label="_Cancel"
        )
        filter_image = Gtk.FileFilter()
        filter_image.set_name("Image files")
        filter_image.add_mime_type("image/png")
        filter_image.add_mime_type("image/jpeg")
        filter_image.add_mime_type("image/gif")
        dialog.set_filter(filter_image)
        dialog.connect("response", lambda dlg, response: self.on_image_dialog_response(dlg, response, win))
        dialog.show()

    def on_image_dialog_response(self, dialog, response, win):
        if response == Gtk.ResponseType.ACCEPT:
            file = dialog.get_file()
            if file and (file_path := file.get_path()):
                import base64
                with open(file_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                    mime_type = "image/png" if file_path.endswith(".png") else "image/jpeg"
                    data_url = f"data:{mime_type};base64,{encoded_string}"
                js_code = f"""
                (function() {{
                    insertImage('{data_url}');
                    return true;
                }})();
                """
                self.execute_js(win, js_code)
            else:
                win.statusbar.set_text("Failed to select a valid image file.")
        dialog.destroy()

    def on_insert_link_clicked(self, win, btn):
        pass  # Implement as needed

    def get_editor_js(self):
        return f"""
        window.undoStack = [];
        window.redoStack = [];
        window.isUndoRedo = false;
        window.lastContent = "";
        var searchResults = [];
        var searchIndex = -1;
        var currentSearchText = "";
        let paginationTimeout;

        {self.set_content_js()}
        {self.insert_table_js()}
        {self.insert_text_box_js()}
        {self.insert_image_js()}
        {self.insert_link_js()}
        {self.init_editor_js()}
        {self.pagination_js()}
        """

    def set_content_js(self):
        return """
        function setContent(html) {
            const pages = document.getElementById('pages');
            let firstPage = pages.querySelector('.page');
            if (!firstPage) {
                firstPage = createNewPage();
                pages.appendChild(firstPage);
            }
            if (!html || html.trim() === '') {
                firstPage.innerHTML = '<div><br></div>';
            } else if (!html.trim().match(/^<(div|p|h[1-6]|ul|ol|table)/i)) {
                firstPage.innerHTML = '<div>' + html + '</div>';
            } else {
                firstPage.innerHTML = html;
            }
            window.lastContent = pages.innerHTML;
            window.undoStack = [window.lastContent];
            window.redoStack = [];
            paginate();
            firstPage.focus();
        }
        """

    def insert_table_js(self):
        return """
        function insertTable(rows, cols, hasHeader, borderWidth, tableWidth) {
            let tableHTML = '<table border="' + borderWidth + '" cellspacing="0" cellpadding="5" ';
            tableHTML += 'class="no-wrap" style="border-collapse: collapse; width: ' + tableWidth + ';">';
            if (hasHeader) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<th style="border: ' + borderWidth + 'px solid #ccc; padding: 5px; background-color: #f0f0f0;">Header ' + (j+1) + '</th>';
                }
                tableHTML += '</tr>';
                rows--;
            }
            for (let i = 0; i < rows; i++) {
                tableHTML += '<tr>';
                for (let j = 0; j < cols; j++) {
                    tableHTML += '<td style="border: ' + borderWidth + 'px solid #ccc; padding: 5px; min-width: 30px;">Cell</td>';
                }
                tableHTML += '</tr>';
            }
            tableHTML += '</table><p></p>';
            document.execCommand('insertHTML', false, tableHTML);
            setTimeout(() => {
                const tables = document.querySelectorAll('table');
                const newTable = tables[tables.length - 1];
                if (newTable) {
                    activateTable(newTable);
                    window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                }
            }, 10);
        }
        var activeTable = null;
        var isDragging = false;
        var isResizing = false;
        var dragStartX = 0;
        var dragStartY = 0;
        var tableStartX = 0;
        var tableStartY = 0;
        function findParentTable(element) {
            while (element && element !== document.body) {
                if (element.tagName === 'TABLE') return element;
                element = element.parentNode;
            }
            return null;
        }
        function activateTable(tableElement) {
            activeTable = tableElement;
            tableElement.style.marginLeft = '';
            tableElement.style.marginTop = '';
            const currentClasses = tableElement.className;
            const alignmentClasses = ['left-align', 'right-align', 'center-align', 'no-wrap'];
            let currentAlignment = 'no-wrap';
            alignmentClasses.forEach(cls => {
                if (currentClasses.includes(cls)) currentAlignment = cls;
            });
            alignmentClasses.forEach(cls => tableElement.classList.remove(cls));
            tableElement.classList.add(currentAlignment);
            if (!tableElement.querySelector('.table-handle')) {
                const resizeHandle = document.createElement('div');
                resizeHandle.className = 'table-handle';
                resizeHandle.setAttribute('contenteditable', 'false');
                resizeHandle.setAttribute('unselectable', 'on');
                resizeHandle.style.userSelect = 'none';
                resizeHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableResize(e, tableElement);
                }, true);
                tableElement.appendChild(resizeHandle);
            }
            if (!tableElement.querySelector('.table-drag-handle')) {
                const dragHandle = document.createElement('div');
                dragHandle.className = 'table-drag-handle';
                dragHandle.innerHTML = '↕';
                dragHandle.title = 'Drag to reposition table between paragraphs';
                dragHandle.setAttribute('contenteditable', 'false');
                dragHandle.setAttribute('unselectable', 'on');
                dragHandle.style.userSelect = 'none';
                dragHandle.addEventListener('mousedown', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    startTableDrag(e, tableElement);
                }, true);
                tableElement.appendChild(dragHandle);
            }
        }
        function deactivateAllTables() {
            const tables = document.querySelectorAll('table');
            tables.forEach(table => {
                const resizeHandle = table.querySelector('.table-handle');
                if (resizeHandle) resizeHandle.remove();
                const dragHandle = table.querySelector('.table-drag-handle');
                if (dragHandle) dragHandle.remove();
            });
            if (activeTable) {
                activeTable = null;
                window.webkit.messageHandlers.tablesDeactivated.postMessage('tables-deactivated');
            }
        }
        function startTableDrag(e, tableElement) {
            e.preventDefault();
            if (!tableElement) return;
            isDragging = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            document.body.style.cursor = 'move';
        }
        function moveTable(e) {
            if (!isDragging || !activeTable) return;
            const currentY = e.clientY;
            const deltaY = currentY - dragStartY;
            if (Math.abs(deltaY) > 30) {
                const pages = document.getElementById('pages');
                const blocks = Array.from(pages.querySelectorAll('.page > *')).filter(node => {
                    const style = window.getComputedStyle(node);
                    return style.display.includes('block') || node.tagName === 'TABLE';
                });
                const tableIndex = blocks.indexOf(activeTable);
                if (deltaY < 0 && tableIndex > 0) {
                    const targetElement = blocks[tableIndex - 1];
                    const page = targetElement.closest('.page');
                    page.insertBefore(activeTable, targetElement);
                    dragStartY = currentY;
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                } else if (deltaY > 0 && tableIndex < blocks.length - 1) {
                    const targetElement = blocks[tableIndex + 1];
                    const page = targetElement.closest('.page');
                    if (targetElement.nextSibling) {
                        page.insertBefore(activeTable, targetElement.nextSibling);
                    } else {
                        page.appendChild(activeTable);
                    }
                    dragStartY = currentY;
                    window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }
                paginate();
            }
        }
        function startTableResize(e, tableElement) {
            e.preventDefault();
            isResizing = true;
            activeTable = tableElement;
            dragStartX = e.clientX;
            dragStartY = e.clientY;
            const style = window.getComputedStyle(tableElement);
            tableStartX = parseInt(style.width) || tableElement.offsetWidth;
            tableStartY = parseInt(style.height) || tableElement.offsetHeight;
        }
        function resizeTable(e) {
            if (!isResizing || !activeTable) return;
            const deltaX = e.clientX - dragStartX;
            const deltaY = e.clientY - dragStartY;
            activeTable.style.width = (tableStartX + deltaX) + 'px';
            activeTable.style.height = (tableStartY + deltaY) + 'px';
        }
        function addTableRow(tableElement, position) {
            if (!tableElement && activeTable) tableElement = activeTable;
            if (!tableElement) return;
            const rows = tableElement.rows;
            if (rows.length > 0) {
                const rowIndex = position !== undefined ? position : rows.length;
                const newRow = tableElement.insertRow(rowIndex);
                for (let i = 0; i < rows[0].cells.length; i++) {
                    const cell = newRow.insertCell(i);
                    cell.innerHTML = ' ';
                    if (rows[0].cells[i].style.border) cell.style.border = rows[0].cells[i].style.border;
                    if (rows[0].cells[i].style.padding) cell.style.padding = rows[0].cells[i].style.padding;
                }
            }
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        function addTableColumn(tableElement, position) {
            if (!tableElement && activeTable) tableElement = activeTable;
            if (!tableElement) return;
            const rows = tableElement.rows;
            for (let i = 0; i < rows.length; i++) {
                const cellIndex = position !== undefined ? position : rows[i].cells.length;
                const cell = rows[i].insertCell(cellIndex);
                cell.innerHTML = ' ';
                if (rows[i].cells.length > 1) {
                    const refCell = cellIndex > 0 ? rows[i].cells[cellIndex - 1] : rows[i].cells[cellIndex + 1];
                    if (refCell) {
                        if (refCell.style.border) cell.style.border = refCell.style.border;
                        if (refCell.style.padding) cell.style.padding = refCell.style.padding;
                        if (refCell.tagName === 'TH' && cell.tagName === 'TD') {
                            const headerCell = document.createElement('th');
                            headerCell.innerHTML = cell.innerHTML;
                            headerCell.style.cssText = cell.style.cssText;
                            if (refCell.style.backgroundColor) headerCell.style.backgroundColor = refCell.style.backgroundColor;
                            cell.parentNode.replaceChild(headerCell, cell);
                        }
                    }
                }
            }
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        function deleteTableRow(tableElement, rowIndex) {
            if (!tableElement && activeTable) tableElement = activeTable;
            if (!tableElement) return;
            const rows = tableElement.rows;
            if (rows.length > 1) {
                const indexToDelete = rowIndex !== undefined ? rowIndex : rows.length - 1;
                if (indexToDelete >= 0 && indexToDelete < rows.length) {
                    tableElement.deleteRow(indexToDelete);
                }
            }
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        function deleteTableColumn(tableElement, colIndex) {
            if (!tableElement && activeTable) tableElement = activeTable;
            if (!tableElement) return;
            const rows = tableElement.rows;
            if (rows.length > 0 && rows[0].cells.length > 1) {
                const indexToDelete = colIndex !== undefined ? colIndex : rows[0].cells.length - 1;
                for (let i = 0; i < rows.length; i++) {
                    if (indexToDelete >= 0 && indexToDelete < rows[i].cells.length) {
                        rows[i].deleteCell(indexToDelete);
                    }
                }
            }
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        function deleteTable(tableElement) {
            if (!tableElement && activeTable) tableElement = activeTable;
            if (!tableElement) return;
            tableElement.parentNode.removeChild(tableElement);
            activeTable = null;
            window.webkit.messageHandlers.tableDeleted.postMessage('table-deleted');
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        function setTableAlignment(alignClass) {
            if (!activeTable) return;
            activeTable.classList.remove('left-align', 'right-align', 'center-align', 'no-wrap');
            activeTable.classList.add(alignClass);
            if (alignClass === 'no-wrap') {
                activeTable.style.width = '100%';
            } else {
                activeTable.style.width = 'auto';
            }
            window.webkit.messageHandlers.contentChanged.postMessage('changed');
        }
        document.addEventListener('DOMContentLoaded', function() {
            const pages = document.getElementById('pages');
            pages.addEventListener('mousedown', function(e) {
                if (e.target.classList.contains('table-handle') || e.target.classList.contains('table-drag-handle')) {
                    e.preventDefault();
                    e.stopPropagation();
                    return;
                }
                let tableElement = findParentTable(e.target);
                if (e.target.classList.contains('table-drag-handle') && e.button === 0) {
                    startTableDrag(e, findParentTable(e.target));
                }
                if (e.target.classList.contains('table-handle')) {
                    startTableResize(e, findParentTable(e.target));
                }
            });
            document.addEventListener('mousemove', function(e) {
                if (isDragging && activeTable) moveTable(e);
                if (isResizing && activeTable) resizeTable(e);
            });
            document.addEventListener('mouseup', function() {
                if (isDragging || isResizing) {
                    isDragging = false;
                    isResizing = false;
                    document.body.style.cursor = '';
                    if (activeTable) window.webkit.messageHandlers.contentChanged.postMessage('changed');
                }
            });
            pages.addEventListener('click', function(e) {
                let tableElement = findParentTable(e.target);
                if (!tableElement && activeTable) {
                    deactivateAllTables();
                } else if (tableElement && tableElement !== activeTable) {
                    deactivateAllTables();
                    activateTable(tableElement);
                    window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
                }
            });
        });
        """

    def insert_text_box_js(self):
        return """
        function insertTextBox() {
            const textBoxHTML = '<table class="text-box-table" border="1" cellspacing="0" cellpadding="5" style="width: 80px; height: 80px;"><tr><td>Text Box</td></tr></table><p></p>';
            document.execCommand('insertHTML', false, textBoxHTML);
        }
        """

    def insert_image_js(self):
        return """
        function insertImage(src) {
            const imgHTML = '<img src="' + src + '" style="max-width: 100%; height: auto;" /><p></p>';
            document.execCommand('insertHTML', false, imgHTML);
        }
        """

    def insert_link_js(self):
        return """
        function insertLink(url, text) {
            const linkHTML = '<a href="' + url + '">' + (text || url) + '</a>';
            document.execCommand('insertHTML', false, linkHTML);
        }
        """

    def pagination_js(self):
        return """
        function createNewPage() {
            const newPage = document.createElement('div');
            newPage.className = 'page';
            newPage.style.height = '1056px';
            newPage.style.width = '816px';
            newPage.style.overflow = 'hidden';
            return newPage;
        }
        function getCurrentSelectionInfo() {
            const selection = window.getSelection();
            if (selection.rangeCount === 0) return null;
            const range = selection.getRangeAt(0);
            let node = range.startContainer;
            let offset = range.startOffset;
            while (node && node.nodeType !== 1) node = node.parentNode;
            if (node && node.tagName === 'DIV' && node.parentNode.classList.contains('page')) {
                return { block: node, offset: offset };
            }
            return null;
        }
        function setSelectionToBlock(block, offset) {
            if (!block) return;
            const textNode = findTextNodeInBlock(block);
            if (textNode) {
                const range = document.createRange();
                range.setStart(textNode, Math.min(offset, textNode.length));
                range.collapse(true);
                window.getSelection().removeAllRanges();
                window.getSelection().addRange(range);
            }
        }
        function findTextNodeInBlock(block) {
            let node = block;
            while (node) {
                if (node.nodeType === 3) return node;
                node = node.firstChild;
            }
            return null;
        }
        function paginate() {
            const selectionInfo = getCurrentSelectionInfo();
            const pagesContainer = document.getElementById('pages');
            let pages = Array.from(pagesContainer.querySelectorAll('.page'));
            if (pages.length === 0) {
                const newPage = createNewPage();
                pagesContainer.appendChild(newPage);
                pages = [newPage];
            }
            let i = 0;
            while (i < pages.length) {
                const page = pages[i];
                const pageHeight = page.clientHeight;
                let cumulativeHeight = 0;
                const children = Array.from(page.children);
                let splitIndex = -1;
                for (let j = 0; j < children.length; j++) {
                    cumulativeHeight += children[j].offsetHeight;
                    if (cumulativeHeight > pageHeight) {
                        splitIndex = j;
                        break;
                    }
                }
                if (splitIndex !== -1) {
                    let nextPage = pages[i + 1];
                    if (!nextPage) {
                        nextPage = createNewPage();
                        pagesContainer.appendChild(nextPage);
                        pages = Array.from(pagesContainer.querySelectorAll('.page'));
                    }
                    const fragment = document.createDocumentFragment();
                    for (let k = splitIndex; k < children.length; k++) {
                        fragment.appendChild(children[k]);
                    }
                    nextPage.insertBefore(fragment, nextPage.firstChild);
                } else {
                    i++;
                }
            }
            pages = Array.from(pagesContainer.querySelectorAll('.page'));
            for (let i = 0; i < pages.length - 1; i++) {
                const page = pages[i];
                const nextPage = pages[i + 1];
                while (page.scrollHeight < page.clientHeight && nextPage.children.length > 0) {
                    const firstChild = nextPage.firstChild;
                    page.appendChild(firstChild);
                    if (page.scrollHeight > page.clientHeight) {
                        nextPage.insertBefore(firstChild, nextPage.firstChild);
                        break;
                    }
                }
            }
            pages = Array.from(pagesContainer.querySelectorAll('.page'));
            for (let i = 0; i < pages.length - 1; i++) {
                if (pages[i].children.length === 0) pages[i].remove();
            }
            if (selectionInfo) setSelectionToBlock(selectionInfo.block, selectionInfo.offset);
        }
        function findParentPage(node) {
            while (node && node !== document.body) {
                if (node.classList.contains('page')) return node;
                node = node.parentNode;
            }
            return null;
        }
        function isAtEndOfPage(page, range) {
            const lastChild = page.lastChild;
            if (!lastChild) return false;
            return range.startContainer === lastChild || (range.startContainer.nodeType === 3 && range.startOffset === range.startContainer.length && range.startContainer.parentNode === lastChild);
        }
        function isAtStartOfPage(page, range) {
            const firstChild = page.firstChild;
            if (!firstChild) return false;
            return range.startContainer === firstChild || (range.startContainer.nodeType === 3 && range.startOffset === 0 && range.startContainer.parentNode === firstChild);
        }
        function moveCursorToNextPage(currentPage) {
            const nextPage = currentPage.nextElementSibling;
            if (nextPage && nextPage.classList.contains('page')) {
                const firstTextNode = findTextNodeInBlock(nextPage.firstChild || nextPage.appendChild(document.createElement('div')));
                if (firstTextNode) {
                    const range = document.createRange();
                    range.setStart(firstTextNode, 0);
                    range.collapse(true);
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                }
            }
        }
        function moveCursorToPreviousPage(currentPage) {
            const prevPage = currentPage.previousElementSibling;
            if (prevPage && prevPage.classList.contains('page')) {
                const lastTextNode = findTextNodeInBlock(prevPage.lastChild || prevPage.appendChild(document.createElement('div')));
                if (lastTextNode) {
                    const range = document.createRange();
                    range.setStart(lastTextNode, lastTextNode.length);
                    range.collapse(true);
                    window.getSelection().removeAllRanges();
                    window.getSelection().addRange(range);
                }
            }
        }
        """

    def init_editor_js(self):
        return """
        document.addEventListener('DOMContentLoaded', function() {
            const pages = document.getElementById('pages');
            pages.setAttribute('tabindex', '0');
            pages.addEventListener('keydown', function(e) {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    document.execCommand('insertHTML', false, '<span class="Apple-tab-span" style="white-space:pre">\\t</span>');
                    const event = new Event('input', { bubbles: true, cancelable: true });
                    pages.dispatchEvent(event);
                }
                const selection = window.getSelection();
                if (!selection.rangeCount) return;
                const range = selection.getRangeAt(0);
                const page = findParentPage(range.startContainer);
                if (!page) return;
                if ((e.key === 'ArrowDown' || e.key === 'Enter') && isAtEndOfPage(page, range)) {
                    e.preventDefault();
                    moveCursorToNextPage(page);
                } else if (e.key === 'ArrowUp' && isAtStartOfPage(page, range)) {
                    e.preventDefault();
                    moveCursorToPreviousPage(page);
                } else if (e.key === 'Backspace' && isAtStartOfPage(page, range) && page.previousElementSibling) {
                    e.preventDefault();
                    const prevPage = page.previousElementSibling;
                    while (page.firstChild) prevPage.appendChild(page.firstChild);
                    page.remove();
                    paginate();
                    moveCursorToPreviousPage(prevPage);
                }
            });
            pages.addEventListener('focus', function onFirstFocus(e) {
                if (!pages.textContent.trim() && pages.innerHTML === '<div class="page"></div>') {
                    const firstPage = pages.querySelector('.page');
                    firstPage.innerHTML = '<div><br></div>';
                    const range = document.createRange();
                    const sel = window.getSelection();
                    const firstDiv = firstPage.querySelector('div');
                    if (firstDiv) {
                        range.setStart(firstDiv, 0);
                        range.collapse(true);
                        sel.removeAllRanges();
                        sel.addRange(range);
                    }
                    pages.removeEventListener('focus', onFirstFocus);
                }
            });
            window.lastContent = pages.innerHTML;
            saveState();
            pages.focus();
            pages.addEventListener('input', function(e) {
                if (document.getSelection().anchorNode === pages) {
                    document.execCommand('formatBlock', false, 'div');
                }
                if (!window.isUndoRedo) {
                    const currentContent = pages.innerHTML;
                    if (currentContent !== window.lastContent) {
                        saveState();
                        window.lastContent = currentContent;
                        window.redoStack = [];
                        clearTimeout(paginationTimeout);
                        paginationTimeout = setTimeout(paginate, 200);
                        window.webkit.messageHandlers.contentChanged.postMessage("changed");
                    }
                }
            });
            if (window.initialContent) setContent(window.initialContent);
        });
        function saveState() {
            window.undoStack.push(document.getElementById('pages').innerHTML);
        }
        """

    def get_initial_html(self):
        return self.get_editor_html('<div><font face="Sans" style="font-size: 11pt;"><br></font></div>')

    def set_initial_focus(self, win):
        try:
            win.webview.grab_focus()
            js_code = """
            (function() {
                const pages = document.getElementById('pages');
                if (!pages) return false;
                pages.focus();
                const firstPage = pages.querySelector('.page');
                if (!firstPage.children.length) {
                    firstPage.innerHTML = '<div><br></div>';
                }
                const range = document.createRange();
                const sel = window.getSelection();
                const firstDiv = firstPage.querySelector('div');
                if (firstDiv) {
                    range.setStart(firstDiv, 0);
                    range.collapse(true);
                    sel.removeAllRanges();
                    sel.addRange(range);
                }
                return true;
            })();
            """
            win.webview.evaluate_javascript(js_code, -1, None, None, None, None, None)
            return False
        except Exception as e:
            print(f"Error setting initial focus: {e}")
            return False

    def create_window(self):
        win = Adw.ApplicationWindow(application=self)
        win.modified = False
        win.auto_save_enabled = False
        win.auto_save_interval = 60
        win.current_file = None
        win.auto_save_source_id = None
        win.set_default_size(800, 600)
        win.set_title("Untitled - HTML Editor")
        
        win.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.main_box.set_vexpand(True)
        win.main_box.set_hexpand(True)
        
        win.headerbar_revealer = Gtk.Revealer()
        win.headerbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.headerbar_revealer.set_transition_duration(250)
        win.headerbar_revealer.set_reveal_child(True)
        
        win.headerbar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.headerbar = Adw.HeaderBar()
        win.headerbar.add_css_class("flat-header")
        self.setup_headerbar_content(win)
        win.headerbar_box.append(win.headerbar)
        
        win.file_toolbar_revealer = Gtk.Revealer()
        win.file_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_DOWN)
        win.file_toolbar_revealer.set_transition_duration(250)
        win.file_toolbar_revealer.set_reveal_child(True)
        win.file_toolbar = self.create_file_toolbar(win)
        win.file_toolbar_revealer.set_child(win.file_toolbar)
        win.headerbar_box.append(win.file_toolbar_revealer)
        
        win.headerbar_revealer.set_child(win.headerbar_box)
        win.main_box.append(win.headerbar_revealer)
        
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        content_box.set_vexpand(True)
        content_box.set_hexpand(True)
        
        win.webview = WebKit.WebView()
        win.webview.set_vexpand(True)
        win.webview.set_hexpand(True)
        win.webview.load_html(self.get_editor_html(), None)
        settings = win.webview.get_settings()
        settings.set_enable_developer_extras(True)
        
        user_content_manager = win.webview.get_user_content_manager()
        user_content_manager.register_script_message_handler("contentChanged")
        user_content_manager.connect("script-message-received::contentChanged", 
                                    lambda mgr, res: self.on_content_changed(win, mgr, res))
        user_content_manager.register_script_message_handler("tableClicked")
        user_content_manager.register_script_message_handler("tableDeleted")
        user_content_manager.register_script_message_handler("tablesDeactivated")
        user_content_manager.connect("script-message-received::tableClicked", 
                                    lambda mgr, res: self.on_table_clicked(win, mgr, res))
        user_content_manager.connect("script-message-received::tableDeleted", 
                                    lambda mgr, res: self.on_table_deleted(win, mgr, res))
        user_content_manager.connect("script-message-received::tablesDeactivated", 
                                    lambda mgr, res: self.on_tables_deactivated(win, mgr, res))
        
        win.webview.load_html(self.get_initial_html(), None)
        content_box.append(win.webview)
        
        win.table_toolbar_revealer = Gtk.Revealer()
        win.table_toolbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.table_toolbar_revealer.set_transition_duration(250)
        win.table_toolbar_revealer.set_reveal_child(False)
        win.table_toolbar = self.create_table_toolbar(win)
        win.table_toolbar_revealer.set_child(win.table_toolbar)
        content_box.append(win.table_toolbar_revealer)
        
        win.statusbar_revealer = Gtk.Revealer()
        win.statusbar_revealer.add_css_class("flat-header")
        win.statusbar_revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        win.statusbar_revealer.set_transition_duration(250)
        win.statusbar_revealer.set_reveal_child(True)
        statusbar_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        statusbar_box.set_margin_start(10)
        statusbar_box.set_margin_end(10)
        statusbar_box.set_margin_top(0)
        statusbar_box.set_margin_bottom(4)
        win.statusbar = Gtk.Label(label="Ready")
        win.statusbar.set_halign(Gtk.Align.START)
        win.statusbar.set_hexpand(True)
        statusbar_box.append(win.statusbar)
        win.statusbar_revealer.set_child(statusbar_box)
        content_box.append(win.statusbar_revealer)

        win.main_box.append(content_box)
        win.set_content(win.main_box)

        case_change_action = Gio.SimpleAction.new("change-case", GLib.VariantType.new("s"))
        case_change_action.connect("activate", lambda action, param: self.on_change_case(win, param.get_string()))
        win.add_action(case_change_action)
        
        self.windows.append(win)
        return win

    def create_table_toolbar(self, win):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        toolbar.set_margin_start(10)
        toolbar.set_margin_end(10)
        toolbar.set_margin_top(5)
        toolbar.set_margin_bottom(5)
        table_label = Gtk.Label(label="Table:")
        table_label.set_margin_end(10)
        toolbar.append(table_label)
        row_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        row_group.add_css_class("linked")
        add_row_above_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_above_button.set_tooltip_text("Add row above")
        add_row_above_button.connect("clicked", lambda btn: self.on_add_row_above_clicked(win))
        row_group.append(add_row_above_button)
        add_row_below_button = Gtk.Button(icon_name="list-add-symbolic")
        add_row_below_button.set_tooltip_text("Add row below")
        add_row_below_button.connect("clicked", lambda btn: self.on_add_row_below_clicked(win))
        row_group.append(add_row_below_button)
        toolbar.append(row_group)
        col_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        col_group.add_css_class("linked")
        col_group.set_margin_start(5)
        add_col_before_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_before_button.set_tooltip_text("Add column before")
        add_col_before_button.connect("clicked", lambda btn: self.on_add_column_before_clicked(win))
        col_group.append(add_col_before_button)
        add_col_after_button = Gtk.Button(icon_name="list-add-symbolic")
        add_col_after_button.set_tooltip_text("Add column after")
        add_col_after_button.connect("clicked", lambda btn: self.on_add_column_after_clicked(win))
        col_group.append(add_col_after_button)
        toolbar.append(col_group)
        separator1 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator1.set_margin_start(5)
        separator1.set_margin_end(5)
        toolbar.append(separator1)
        delete_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        delete_group.add_css_class("linked")
        del_row_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_row_button.set_tooltip_text("Delete row")
        del_row_button.connect("clicked", lambda btn: self.on_delete_row_clicked(win))
        delete_group.append(del_row_button)
        del_col_button = Gtk.Button(icon_name="list-remove-symbolic")
        del_col_button.set_tooltip_text("Delete column")
        del_col_button.connect("clicked", lambda btn: self.on_delete_column_clicked(win))
        delete_group.append(del_col_button)
        del_table_button = Gtk.Button(icon_name="edit-delete-symbolic")
        del_table_button.set_tooltip_text("Delete table")
        del_table_button.connect("clicked", lambda btn: self.on_delete_table_clicked(win))
        delete_group.append(del_table_button)
        toolbar.append(delete_group)
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        separator2.set_margin_start(10)
        separator2.set_margin_end(10)
        toolbar.append(separator2)
        align_label = Gtk.Label(label="Align:")
        align_label.set_margin_end(5)
        toolbar.append(align_label)
        align_group = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=1)
        align_group.add_css_class("linked")
        align_left_button = Gtk.Button(icon_name="format-justify-left-symbolic")
        align_left_button.set_tooltip_text("Align Left (text wraps around right)")
        align_left_button.connect("clicked", lambda btn: self.on_table_align_left(win))
        align_group.append(align_left_button)
        align_center_button = Gtk.Button(icon_name="format-justify-center-symbolic")
        align_center_button.set_tooltip_text("Center (no text wrap)")
        align_center_button.connect("clicked", lambda btn: self.on_table_align_center(win))
        align_group.append(align_center_button)
        align_right_button = Gtk.Button(icon_name="format-justify-right-symbolic")
        align_right_button.set_tooltip_text("Align Right (text wraps around left)")
        align_right_button.connect("clicked", lambda btn: self.on_table_align_right(win))
        align_group.append(align_right_button)
        full_width_button = Gtk.Button(icon_name="format-justify-fill-symbolic")
        full_width_button.set_tooltip_text("Full Width (no text wrap)")
        full_width_button.connect("clicked", lambda btn: self.on_table_full_width(win))
        align_group.append(full_width_button)
        toolbar.append(align_group)
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        toolbar.append(spacer)
        close_button = Gtk.Button(icon_name="window-close-symbolic")
        close_button.set_tooltip_text("Close table toolbar")
        close_button.connect("clicked", lambda btn: self.on_close_table_toolbar_clicked(win))
        toolbar.append(close_button)
        return toolbar

    def on_content_changed(self, win, manager, message):
        win.modified = True
        self.update_window_title(win)
        win.statusbar.set_text("Content modified")

    def update_window_title(self, win):
        if win.current_file:
            filename = os.path.basename(win.current_file)
            title = f"{filename}{' *' if win.modified else ''} - HTML Editor"
        else:
            title = f"Untitled{' *' if win.modified else ''} - HTML Editor"
        win.set_title(title)

    def on_table_clicked(self, win, manager, message):
        win.table_toolbar_revealer.set_reveal_child(True)
        win.statusbar.set_text("Table selected")

    def on_table_deleted(self, win, manager, message):
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("Table deleted")

    def on_tables_deactivated(self, win, manager, message):
        win.table_toolbar_revealer.set_reveal_child(False)
        win.statusbar.set_text("No table selected")

    def execute_js(self, win, script):
        win.webview.evaluate_javascript(script, -1, None, None, None, None, None)

    def on_add_row_above_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                addTableRow(activeTable, 0);
                return;
            }
            let row = cell;
            while (row && row.tagName !== 'TR') row = row.parentNode;
            if (!row) return;
            let rowIndex = row.rowIndex;
            addTableRow(activeTable, rowIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_row_below_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                addTableRow(activeTable);
                return;
            }
            let row = cell;
            while (row && row.tagName !== 'TR') row = row.parentNode;
            if (!row) return;
            let rowIndex = row.rowIndex;
            addTableRow(activeTable, rowIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_column_before_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                addTableColumn(activeTable, 0);
                return;
            }
            let cellIndex = cell.cellIndex;
            addTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_add_column_after_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                addTableColumn(activeTable);
                return;
            }
            let cellIndex = cell.cellIndex;
            addTableColumn(activeTable, cellIndex + 1);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_row_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                deleteTableRow(activeTable);
                return;
            }
            let row = cell;
            while (row && row.tagName !== 'TR') row = row.parentNode;
            if (!row) return;
            let rowIndex = row.rowIndex;
            deleteTableRow(activeTable, rowIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_column_clicked(self, win):
        js_code = """
        (function() {
            if (!activeTable) return;
            let selection = window.getSelection();
            if (selection.rangeCount < 1) return;
            let range = selection.getRangeAt(0);
            let cell = range.startContainer;
            while (cell && cell.tagName !== 'TD' && cell.tagName !== 'TH' && cell !== activeTable) {
                cell = cell.parentNode;
            }
            if (!cell || (cell.tagName !== 'TD' && cell.tagName !== 'TH')) {
                deleteTableColumn(activeTable);
                return;
            }
            let cellIndex = cell.cellIndex;
            deleteTableColumn(activeTable, cellIndex);
        })();
        """
        self.execute_js(win, js_code)

    def on_delete_table_clicked(self, win):
        js_code = "deleteTable(activeTable);"
        self.execute_js(win, js_code)

    def on_table_align_left(self, win):
        js_code = "setTableAlignment('left-align');"
        self.execute_js(win, js_code)

    def on_table_align_center(self, win):
        js_code = "setTableAlignment('center-align');"
        self.execute_js(win, js_code)

    def on_table_align_right(self, win):
        js_code = "setTableAlignment('right-align');"
        self.execute_js(win, js_code)

    def on_table_full_width(self, win):
        js_code = "setTableAlignment('no-wrap');"
        self.execute_js(win, js_code)

    def on_close_table_toolbar_clicked(self, win):
        win.table_toolbar_revealer.set_reveal_child(False)
        js_code = "deactivateAllTables();"
        self.execute_js(win, js_code)
        win.statusbar.set_text("Table toolbar closed")

    def on_change_case(self, win, case_type):
        pass  # Implement as needed

    def get_editor_html(self, content=""):
        content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        return f"""
        <!DOCTYPE html>
        <html style="height: 100%;">
        <head>
            <title>HTML Editor</title>
            <style>
                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    font-family: Sans;
                    background-color: #f0f0f0;
                }}
                #pages {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    height: 100%;
                    overflow: auto;
                    font-family: Sans;
                    font-size: 11pt;
                }}
                .page {{
                    width: 816px;
                    height: 1056px;
                    margin: 20px 0;
                    background: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                    padding: 10px;
                    box-sizing: border-box;
                }}
                .page div {{
                    margin: 0;
                    padding: 0;
                }}
                table {{
                    border-collapse: collapse;
                    margin: 10px 0;
                    position: relative;
                    resize: both;
                    overflow: auto;
                    min-width: 30px;
                    min-height: 30px;
                }}
                table.left-align {{ float: left; margin-right: 10px; clear: none; }}
                table.right-align {{ float: right; margin-left: 10px; clear: none; }}
                table.center-align {{ margin-left: auto; margin-right: auto; float: none; clear: both; }}
                table.no-wrap {{ float: none; clear: both; width: 100%; }}
                table td {{ border: 1px solid #ccc; padding: 5px; min-width: 30px; position: relative; }}
                table th {{ border: 1px solid #ccc; padding: 5px; min-width: 30px; background-color: #f0f0f0; }}
                .table-drag-handle {{
                    position: absolute;
                    top: -16px;
                    left: -1px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 2px;
                    cursor: ns-resize;
                    z-index: 1000;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: white;
                    font-size: 10px;
                }}
                .table-handle {{
                    position: absolute;
                    bottom: -10px;
                    right: -10px;
                    width: 16px;
                    height: 16px;
                    background-color: #4e9eff;
                    border-radius: 8px;
                    cursor: nwse-resize;
                    z-index: 1000;
                }}
                table.text-box-table {{
                    border: 1px solid #ccc !important;
                    border-radius: 4px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    background-color: #fff;
                    width: 80px;
                    height: 80px;
                    min-width: 80px;
                    min-height: 80px;
                    resize: both !important;
                }}
                table.text-box-table td {{ vertical-align: top; }}
                #pages ::selection {{ background-color: #b5d7ff; color: inherit; }}
                @media (prefers-color-scheme: dark) {{
                    html, body {{ background-color: #1e1e1e; color: #c0c0c0; }}
                    .page {{ background-color: #2d2d2d; }}
                    table th {{ background-color: #2a2a2a; }}
                    table td, table th {{ border-color: #444; }}
                    .table-drag-handle, .table-handle {{ background-color: #0078d7; }}
                    table.text-box-table {{ border-color: #444 !important; background-color: #2d2d2d; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
                    #pages ::selection {{ background-color: #264f78; color: inherit; }}
                }}
            </style>
            <script>
                window.initialContent = "{content or '<div><font face=\"Sans\" style=\"font-size: 11pt;\"><br></font></div>'}";
                {self.get_editor_js()}
            </script>
        </head>
        <body>
            <div id="pages" contenteditable="true">
                <div class="page"></div>
            </div>
        </body>
        </html>
        """

def main():
    app = HTMLEditorApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    Adw.init()
    sys.exit(main())
