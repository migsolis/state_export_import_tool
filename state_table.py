import pandas as pd
from conversions import CSVConverter, XMLConverter

class StateTable():
    csv_converter = CSVConverter()
    xml_converter = XMLConverter()
    
    def __init__(self, df: pd.DataFrame=None):
        self.df = df

    @classmethod
    def from_csv(cls, path:str):
        return cls(StateTable.csv_converter.deserialize(path))

    @classmethod
    def from_xml(cls, path: str):
        return cls(StateTable.xml_converter.deserialize(path))

    def get_row(self, row: int) -> dict:
        return self.df.loc[row].to_dict()

    def to_csv(self, path: str='', name: str='state_table') -> None:
        StateTable.csv_converter.serialize(self.df, path, name)

    def to_dataframe(self):
        return self.df
    
    def to_xml(self, path: str='', name: str='state_table'):
        StateTable.xml_converter.serialize(self.df, path, name)

if __name__ == '__main__':
    state_table = StateTable().from_csv('states_table.csv')
    state_table2 = StateTable().from_xml('output.xml')
    print('test')