import numpy as np
import pandas as pd
import sys
from PySide6.QtCore import (QAbstractTableModel, Qt)
from PySide6.QtWidgets import (QApplication, QHeaderView, QTableView, QVBoxLayout, QWidget)
from state_table import StateTable

class StateTableWidget(QWidget):
    def __init__(self, state_table: StateTable):
        super().__init__()

        self.setWindowTitle('State Table')
        self.layout = QVBoxLayout(self)

        self.state_table = state_table

        self.table = QTableView()
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().hideSection(0)
        self.table.horizontalHeader().hideSection(1)
        self.table.horizontalHeader().hideSection(11)
        self.model = DataFrameTableModel(self.state_table.to_dataframe())
        self.table.setModel(self.model)

        self.layout.addWidget(self.table)

class DataFrameTableModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super(DataFrameTableModel, self).__init__()
        self._data = df
    
    def data(self, index, role):
        if role in [Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole]:
            value = self._data.iloc[index.row(), index.column()]
            
            if pd.isna(value):
                return None
            
            if isinstance(value, (np.float64, np.int64)):
                return  int(value)
            
            return str(value)
        
        if role == Qt.ItemDataRole.TextAlignmentRole:
            value = self._data.iloc[index.row(), index.column()]

            if isinstance(value, (np.float64, np.int64)):
                return  Qt.AlignmentFlag.AlignVCenter + Qt.AlignmentFlag.AlignRight
    def setData(self, index, value, role):
        if role == Qt.ItemDataRole.EditRole:
            self._data.iloc[index.row(), index.column()] = value
            return True
        
        return False

    def flags(self, index):
        return Qt.ItemFlag.ItemIsSelectable|Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsEditable
        
    def headerData(self, section, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[section])
            
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[section])

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self,index):
        return self._data.shape[1]

if __name__ == '__main__':

    app = QApplication(sys.argv)
    app.setStyle('fusion')
    state_table = StateTable.from_csv('states_table.csv')
    widget = StateTableWidget(state_table)
    widget.resize(900, 600)
    widget.show()

    sys.exit(app.exec())