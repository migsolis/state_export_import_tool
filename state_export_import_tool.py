from PySide6.QtCore import (QAbstractTableModel, QDir, QModelIndex, Qt, QTimer, Slot)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFileDialog, QFileSystemModel, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QPushButton, QProgressBar, QMainWindow, QMenu, QMenuBar, QStyleFactory, QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange, QTableView, QTreeView, QVBoxLayout, QWidget)
from PySide6.QtGui import (QIcon, QFont)
from state_table import StateTable
from time import strftime
import sys

class StateExportImportTool(QWidget):
    def __init__(self, data=[]):
        super().__init__()

        self.setWindowTitle('State Export/Import Tool')
        self.setWindowIcon(QIcon('resources/images/edit-solid.svg'))
        self.layout = QGridLayout(self)

        self.button = QPushButton('Open Export Files')
        self.button.clicked.connect(self.open_Files)
        self.template_button = QPushButton('Download CSV Template')
        self.template_button.clicked.connect(self.download_template_button_clicked)
        self.xml_to_excel_button = QPushButton('XML -> CSV')
        self.xml_to_excel_button.setDisabled(True)
        self.xml_to_excel_button.clicked.connect(self.to_csv_button_clicked)
        self.excel_to_xml_button = QPushButton('CSV -> XML')
        self.excel_to_xml_button.setDisabled(True)
        self.excel_to_xml_button.clicked.connect(self.to_xml_button_clicked)
        self.progress_label = QLabel('Select files to convert!')
        # self.progress_label.hide()

        self.table = self.create_table()
        self.progress_bar = self.create_progress_bar()
        # self.progress_bar.hide()

        self.layout.addWidget(self.button, 0, 0, 1, 3)
        self.layout.addWidget(self.template_button, 0, 8, 1, 4)
        self.layout.addWidget(self.table, 1, 0, 1, 12)
        self.layout.addWidget(self.xml_to_excel_button, 2, 2, 1, 3)
        self.layout.addWidget(self.excel_to_xml_button, 2, 7, 1, 3)
        self.layout.addWidget(self.progress_label, 3, 0, 1, 12)
        self.layout.addWidget(self.progress_bar, 4, 0, 1, 12)

        self.state_tables = []
    
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
            row_num = self.insert_table_row(filename=filename, path=path, extension=extension, output_name=output_name)

            state_table = None
            if extension == 'csv':
                state_table = StateTable().from_csv(path)
            elif extension == 'xml':
                state_table = StateTable().from_xml(path)

            self.state_tables.insert(row_num, state_table)

    @Slot()
    def advance_progressbar(self):
        cur_val = self.progress_bar.value()
        max_val = self.progress_bar.maximum()
        self.progress_bar.setValue(cur_val + (max_val - cur_val) / 100)

    @Slot()
    def download_template_button_clicked(self):
        with open('template.csv') as file:
            template_content = file.read()
            # QFileDialog.saveFileContent(file_bytes, 'template.csv')
            filename, _ = QFileDialog.getSaveFileName(self,
                                                      'Save Template File',
                                                      f'{QDir.currentPath()}/state_table_template.csv',
                                                      'CSV (*.csv)')
            
            with open(filename, 'w') as file:
                file.write(template_content)

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

    def save_file(self, file_info):
        pass

    def get_selected_files(self):
        data = []
        for row in range(self.table.rowCount()):
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

    def create_table(self):
        table = QTableWidget(self)
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
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.edit

        return table
    
    def insert_table_row(self, selected=False, filename=None, path=None, extension=None, output_name='', message='') -> int:
        if filename:
            row_num = self.table.rowCount()
            self.table.insertRow(row_num)
            print(f'inserting row {row_num}: {[selected, filename, path, extension, output_name, message]}')
            self.update_table_row(row_num, selected=selected, filename=filename, path=path, extension=extension, output_name=output_name, message=message)
            return row_num

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
    widget.setStyleSheet
    widget.resize(600, 400)
    widget.setFixedSize(600, 300)
    widget.show()

    with open('resources/stylesheets/styles.css') as styles:
        file_string = styles.read()
        widget.setStyleSheet(file_string)
    sys.exit(app.exec())