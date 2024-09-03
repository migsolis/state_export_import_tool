import sys
from PySide6.QtCore import (QDir, Qt, QTimer, Slot)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QFileDialog, QGridLayout, QHeaderView, QLabel, QPushButton, QProgressBar, QTableWidget, QTableWidgetItem, QWidget)
from state_table import StateTable, StateTableChecker
from state_table_widget import StateTableWidget
from utils import template
# from time import strftime

class StateExportImportTool(QWidget):
    def __init__(self, data=[]):
        super().__init__()

        # Creates the window and set the windows grid layout
        self.setWindowTitle('State Export/Import Tool')
        self.layout = QGridLayout(self)
        
        # Create and connect signals open export files and download template buttons
        self.button = QPushButton('Open Export Files')
        self.button.clicked.connect(self.open_Files)
        self.template_button = QPushButton('Download CSV Template')
        self.template_button.clicked.connect(self.download_template_button_clicked)

        # Create and connect signals for the conversion and state table preview buttons
        self.preview_button = QPushButton('Preview State Table')
        self.preview_button.setDisabled(True)
        self.preview_button.clicked.connect(self.preview)
        self.xml_to_excel_button = QPushButton('XML -> CSV')
        self.xml_to_excel_button.setDisabled(True)
        self.xml_to_excel_button.clicked.connect(self.to_csv_button_clicked)
        self.excel_to_xml_button = QPushButton('CSV -> XML')
        self.excel_to_xml_button.setDisabled(True)
        self.excel_to_xml_button.clicked.connect(self.to_xml_button_clicked)
        self.progress_label = QLabel('Select files to convert!')
        # self.progress_label.hide()

        # Creates the table that holds the open files details
        self.table = self.create_table()
        # self.progress_bar = self.create_progress_bar()
        # self.progress_bar.hide()

        # Adds the UI widgets to the main widget container and sets the widget positions in the grid layout
        self.layout.addWidget(self.button, 0, 0, 1, 3)
        self.layout.addWidget(self.template_button, 0, 8, 1, 4)
        self.layout.addWidget(self.table, 1, 0, 1, 12)
        self.layout.addWidget(self.preview_button, 2, 0, 1, 4)
        self.layout.addWidget(self.xml_to_excel_button, 2, 5, 1, 3)
        self.layout.addWidget(self.excel_to_xml_button, 2, 9, 1, 3)
        self.layout.addWidget(self.progress_label, 3, 0, 1, 12)
        # self.layout.addWidget(self.progress_bar, 4, 0, 1, 12)

        # Creates an instance of the state table validation class
        self.state_tables = []
        self.state_table_checker = StateTableChecker()
    
    # Enables/disables conversion buttons based on file table row selection checkboxes
    # Conversion buttons are enabled if all the selected rows are the same file type
    @Slot()
    def cell_changed(self, row, col):
        if col == 0:
            is_csv = False
            is_xml = False
            for i in range(self.table.rowCount()):
                selected = self.table.item(i, 0)
                if selected.checkState() == Qt.CheckState.Checked:
                    file_extension = self.table.item(i, 1).text().split('.')[-1]
                    if file_extension in ['xml']:
                        is_xml = True
                    if file_extension in ['csv']:
                        is_csv = True
            print(f'is_xml {is_xml}, is_csv {is_csv} test {not (is_xml and not is_csv)}')
            self.xml_to_excel_button.setDisabled(not (is_xml and not is_csv))
            self.excel_to_xml_button.setDisabled(not (is_csv and not is_xml))

    @Slot()
    def cell_clicked(self, row, col):
        print(f'Cell clicked row {row} col {col}')

    # Enabled and updates the text of the state table preview button using the selected items file name
    # TODO: Handle updating button after deselecting a row
    @Slot()
    def item_selection_changed(self):
        selected_items = self.table.selectedItems()
        row = self.table.row(selected_items[0])
        print(f'Selection changed, row {row}')

        file_name = selected_items[1].text()
        self.preview_button.setText(f'Preview {file_name}')
        self.preview_button.setDisabled(False)

    # Handles opening the selected files and creating state table instances from the files
    @Slot()
    def open_Files(self):
        files = QFileDialog.getOpenFileNames(self, 
                                             'Select one or more files to open', 
                                             QDir.currentPath(), 
                                             'CSV and XML (*.csv *xml);;CSV (*.csv);; XML (*.xml)'
                                             )
        filenames = files[0]
        files_dict = {f.split('/')[-1]: f for f in filenames}

        for filename, path in files_dict.items():
            print(f'open_Files filename {filename}')
            split_name = filename.split('.')
            output_name = split_name[0]
            # output_name = f'{filename.split('.')[0]}_{strftime('%Y%m%d_%H%M%S')}'
            extension = split_name[-1]
            
            # Create state table from file using the file path
            # TODO: handle read errors or invalid files
            state_table = None
            if extension == 'csv':
                state_table = StateTable().from_csv(path)
            elif extension == 'xml':
                state_table = StateTable().from_xml(path)
            
            message = None
            if state_table:
                errors = self.state_table_checker.check_for_errors(state_table)
                if errors:
                    message = str(errors)
            row_num = self.insert_table_row(filename=filename, path=path, extension=extension, output_name=output_name, message=message)
            self.state_tables.insert(row_num, state_table)

    # Opens the state table widget windows for the selected row in the open files table
    @Slot()
    def preview(self):
        print(f'Preview button clicked')
        selected_items = self.table.selectedItems()
        row = self.table.row(selected_items[0])

        self.state_table_widget = StateTableWidget(self.state_tables[row])
        self.state_table_widget.resize(900, 600)
        self.state_table_widget.show()
    
    # TODO: Display deserialization/serialization progress 
    @Slot()
    def advance_progressbar(self):
        cur_val = self.progress_bar.value()
        max_val = self.progress_bar.maximum()
        self.progress_bar.setValue(cur_val + (max_val - cur_val) / 100)

    # Opens a save file dialog to download a csv state table template
    @Slot()
    def download_template_button_clicked(self):
        filename, _ = QFileDialog.getSaveFileName(self,
                                                    'Save Template File',
                                                    f'{QDir.currentPath()}/state_table_template.csv',
                                                    'CSV (*.csv)')
        
        with open(filename, 'w') as file:
            file.write(template)

    # Opens a save file dialog and generate a csv export of the selected open files
    @Slot()
    def to_csv_button_clicked(self):
        print('XML to CSV button pressed')
        files = self.get_selected_files()
        
        for file in files:
            print(f'file: {file}')
            state_table = self.state_tables[file['row']]

            filename, _ = QFileDialog().getSaveFileName(self,
                                            'Save State Table', 
                                             f'{QDir.currentPath()}/{file['Output Name']}', 
                                             'CSV (*.csv)'
                                             )
            print(filename)
            state_table.to_csv(filename)
                
    # Opens a save file dialog and generate a xml export of the selected open files
    @Slot()
    def to_xml_button_clicked(self):
        print('CSV to XML button pressed')
        files = self.get_selected_files()
        
        for file in files:
            print(f'file: {file}')
            state_table = self.state_tables[file['row']]

            filename, _ = QFileDialog().getSaveFileName(self,
                                            'Save State Table', 
                                             f'{QDir.currentPath()}/{file['Output Name']}', 
                                             'XML (*.xml)'
                                             )
            print(filename)
            state_table.to_xml(filename)

    # Iterate through the open files table and return the selected rows data
    def get_selected_files(self):
        data = []
        for row in range(self.table.rowCount()):
            # gets the checkbox item from the table
            selected = self.table.item(row, 0)
            
            if selected.checkState() != Qt.CheckState.Checked:
                continue
            

            row_data = {'row': row}
            for col in range(1, self.table.columnCount()):
                header_text = self.table.horizontalHeaderItem(col).text()
                item = self.table.item(row, col)
                item_text = item.text() if item else ''
                row_data[header_text] = item_text
            data.append(row_data)
        
        return data

    # Creates the open files table
    def create_table(self):
        table = QTableWidget(self)

        # Configures the column headers, column automatic resizing, and visibility attributes
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([None, 'File Name', 'Path', 'Extension', 'Output Name', 'Message'])
        table.horizontalHeader().setMinimumSectionSize(20)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        # table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().hideSection(2)
        # table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        table.horizontalHeader().hideSection(3)
        table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        # table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)

        table.verticalHeader().setVisible(False)
        table.setRowCount(0)
        table.cellChanged.connect(self.cell_changed)
        table.cellClicked.connect(self.cell_clicked)
        table.itemSelectionChanged.connect(self.item_selection_changed)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.edit

        return table
    
    # Inserts a row into the open files table
    def insert_table_row(self, selected=False, filename=None, path=None, extension=None, output_name='', message='') -> int:
        if filename:
            row_num = self.table.rowCount()
            self.table.insertRow(row_num)
            print(f'inserting row {row_num}: {[selected, filename, path, extension, output_name, message]}')
            self.update_table_row(row_num, selected=selected, filename=filename, path=path, extension=extension, output_name=output_name, message=message)
            return row_num

    # Updates the data for a given row in the open files table
    def update_table_row(self, row, *, selected=False, filename=None, path=None, extension=None, output_name=None, message=None):
        checkbox_item = QTableWidgetItem()
        checkbox_item.setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, checkbox_item)

        if filename != None:
            filename_item = QTableWidgetItem(filename)
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # filename_item.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 1, filename_item)
        
        if path != None:
            path_item = QTableWidgetItem(path)
            self.table.setItem(row, 2, path_item)
        
        if extension != None:
            extension_item = QTableWidgetItem(extension)
            self.table.setItem(row, 3, extension_item)

        if output_name != None:
            output_item = QTableWidgetItem(output_name)
            # output_item.setIcon()
            self.table.setItem(row, 4, output_item)
        
        if message != None:
            message_item = QTableWidgetItem(message)
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 5, message_item)

    # Creates a progress bar with test values
    def create_progress_bar(self):
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 10000)
        timer = QTimer(self)
        timer.timeout.connect(self.advance_progressbar)
        timer.start(1000)
        return progress_bar

if __name__ == '__main__':

    app = QApplication([])
    app.setStyle('fusion')

    widget = StateExportImportTool()
    widget.resize(600, 400)
    widget.setFixedSize(600, 300)
    widget.show()

    sys.exit(app.exec())