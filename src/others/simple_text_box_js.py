    def text_box_js(self):
        return """
    // Function to insert a text box as a 1x1 table
    function insertTextBox() {
        // Create a styled 1x1 table to serve as a text box
        let textBox = '<table border="1" cellspacing="0" cellpadding="10" class="text-box-table" ' +
                     'style="border-collapse: collapse; min-height: 80px; width: 100%; max-width: 500px; ' +
                     'border: 1px solid #ccc; resize: both; overflow: auto; margin: 10px 0;">' +
                     '<tr><td style="padding: 10px;">Type text here...</td></tr>' +
                     '</table><p></p>';
                     
        document.execCommand('insertHTML', false, textBox);
        
        // Activate the newly inserted table/text box - this uses your existing table activation code
        setTimeout(() => {
            const tables = document.querySelectorAll('table.text-box-table');
            const newTable = tables[tables.length - 1];
            if (newTable) {
                activateTable(newTable);
                window.webkit.messageHandlers.tableClicked.postMessage('table-clicked');
            }
        }, 10);
    }
"""
# simple text_box_js

