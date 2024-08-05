from PySide6.QtCore import (QAbstractTableModel, QDir, QModelIndex, Qt, QTimer, Slot)
from PySide6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox, QFileDialog, QFileSystemModel, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QPushButton, QProgressBar, QMainWindow, QMenu, QMenuBar, QStyleFactory, QTableWidget, QTableWidgetItem, QTableWidgetSelectionRange, QTableView, QTreeView, QVBoxLayout, QWidget)
from PySide6.QtGui import (QIcon, QFont)
from time import strftime
import random
import time
import sys

class StateExportImportTool(QWidget):
    def __init__(self, data=[]):
        super().__init__()
        self._data = data

        self.setWindowTitle('State Export/Import Tool')
        self.setWindowIcon(QIcon('resources/images/edit-solid.svg'))
        self.layout = QGridLayout(self)

        self.button = QPushButton('Open Export Files')
        self.button.clicked.connect(self.magic)
        self.template_button = QPushButton('Download CSV Template')
        self.template_button.clicked.connect(self.download_template_button_clicked)
        self.xml_to_excel_button = QPushButton('XML -> CSV')
        self.xml_to_excel_button.setDisabled(True)
        self.xml_to_excel_button.clicked.connect(self.xml_to_excel_button_clicked)
        self.excel_to_xml_button = QPushButton('CSV -> XML')
        self.excel_to_xml_button.setDisabled(True)
        self.excel_to_xml_button.clicked.connect(self.excel_to_xml_button_clicked)
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
        # self.table.setRangeSelected(QTableWidgetSelectionRange(row, 0, row, self.table.columnCount() - 1), True)

    @Slot()
    def magic(self):
        files = QFileDialog.getOpenFileNames(self, 
                                             'Select one or more files to open', 
                                             QDir.currentPath(), 
                                             'CSV and XML (*.csv *xml);;CSV (*.csv);; XML (*.xml)'
                                             )
        filenames = files[0]
        files_dict = {f.split('/')[-1]: f for f in filenames}

        for filename, path in files_dict.items():
            print(f'magic filename {filename}')
            output_name = f'{filename.split('.')[0]}'
            # output_name = f'{filename.split('.')[0]}_{strftime('%Y%m%d_%H%M%S')}'

            self.insert_table_row(filename=filename, output_name=output_name)

    @Slot()
    def advance_progressbar(self):
        cur_val = self.progress_bar.value()
        max_val = self.progress_bar.maximum()
        self.progress_bar.setValue(cur_val + (max_val - cur_val) / 100)

    @Slot()
    def download_template_button_clicked(self):
        with open('template.csv') as file:
            file_bytes = bytes(file.read(), 'utf8')
            QFileDialog.saveFileContent(file_bytes, 'template.csv')

    @Slot()
    def xml_to_excel_button_clicked(self):
        print('XML to CSV button pressed')

    @Slot()
    def excel_to_xml_button_clicked(self):
        print('CSV to XML button pressed')

    def create_table(self):
        table = QTableWidget(self)
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels([None, 'File Name', 'Output Name', 'Message'])
        table.horizontalHeader().setMinimumSectionSize(20)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setRowCount(0)
        table.cellChanged.connect(self.cell_changed)
        table.cellClicked.connect(self.cell_clicked)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.edit

        return table
    
    def insert_table_row(self, selected=False, filename=None, output_name='', message=''):
        if filename:
            row_num = self.table.rowCount()
            self.table.insertRow(row_num)
            self.update_table_row(row_num, selected=selected, filename=filename, output_name=output_name, message=message)


    def update_table_row(self, row, *, selected=False, filename=None, output_name=None, message=None):
        checkbox_item = QTableWidgetItem()
        checkbox_item.setCheckState(Qt.CheckState.Checked if selected else Qt.CheckState.Unchecked)
        self.table.setItem(row, 0, checkbox_item)

        if filename != None:
            filename_item = QTableWidgetItem(filename)
            filename_item.setFlags(filename_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            # filename_item.setFlags(Qt.ItemFlag.ItemIsEditable | Qt.ItemFlag.ItemIsSelectable)
            self.table.setItem(row, 1, filename_item)
        
        if output_name != None:
            output_item = QTableWidgetItem(output_name)
            # output_item.setIcon()
            self.table.setItem(row, 2, output_item)
        
        if message != None:
            message_item = QTableWidgetItem(message)
            message_item.setFlags(message_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.table.setItem(row, 3, message_item)

    def create_progress_bar(self):
        progress_bar = QProgressBar()
        progress_bar.setRange(0, 10000)
        timer = QTimer(self)
        timer.timeout.connect(self.advance_progressbar)
        timer.start(1000)
        return progress_bar

    def create_menu(self):
        self._menu_bar = QMenuBar()
        self._file_menu = self._menu_bar.addMenu('&File')
        self.setMenuBar(self._menu_bar)
        

if __name__ == '__main__':

    app = QApplication([])
    app.setStyle('fusion')

    widget = StateExportImportTool()
    widget.setStyleSheet
    widget.resize(600, 300)
    widget.setFixedSize(600, 300)
    widget.show()

    with open('resources/stylesheets/styles.css') as styles:
        file_string = styles.read()
        widget.setStyleSheet(file_string)
    sys.exit(app.exec())