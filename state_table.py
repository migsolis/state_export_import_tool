import pandas as pd
from conversions import CSVConverter, XMLConverter

class StateTable():
    csv_converter = CSVConverter()
    xml_converter = XMLConverter()
    
    def __init__(self, df: pd.DataFrame=None) -> None:
        self.df = df
        self.xml_tree = None

    # Creates a state table instance from a csv file
    @classmethod
    def from_csv(cls, path:str) -> None:
        return cls(StateTable.csv_converter.deserialize(path))

    # Creates a state table instance from a xml file
    @classmethod
    def from_xml(cls, path: str) -> None:
        return cls(StateTable.xml_converter.deserialize(path))

    # Returns the values in a given column name or column index
    def get_column(self, col: int | str) -> list:
        if isinstance(col, int):
            return self.df.iloc[:, col].to_list()
        if isinstance(col, str):
            return self.df.loc[:, col].to_list()
    
    def get_column_count(self) -> int:
        return self.df.shape[1]

    def get_column_names(self) -> list:
        return self.df.columns.to_list()

    def get_row(self, row: int) -> dict:
        return self.df.loc[row].to_dict()
    
    def get_row_count(self) -> int:
        return self.df.shape[0]
    
    def get_value(self, row: int, col: int) -> str | int | float:
        return self.df.iloc[row, col]

    # Writes a csv file to the given path
    def to_csv(self, path: str='state_table') -> None:
        StateTable.csv_converter.serialize(path, self.df)

    def to_dataframe(self):
        return self.df
    
    # Writes a xml file to the given path
    def to_xml(self, path: str='state_table', refresh: bool = False) -> None:
        if self.xml_tree and not refresh:
            self.xml_tree.write(path)
        self.xml_tree = StateTable.xml_converter.serialize(path, self.df)

# Runs validation tests on a given state table
class StateTableChecker():

    # Runs the tests and returns a list of errors found
    def check_for_errors(self, state_table: StateTable) -> list:
        errors = []
        df = state_table.to_dataframe()
        duplicate_codes = self.check_duplicate_state_codes(df)
        if duplicate_codes:
            errors.append(duplicate_codes)

        duplicate_paths = self.check_duplicate_paths(df)
        if duplicate_paths:
            errors.append(duplicate_paths)

        missing_parents = self.check_missing_parent(df)
        if missing_parents:
            errors.append(missing_parents)

        return errors

    # A helper function to help identify missing parents in state paths
    def generate_subpaths(self, path: str) -> set:
        path_parts = path.split('/')
        
        subpath = path_parts[0]
        subpaths = set([subpath])
        for p in path_parts[1:]:
            subpath += "/" + p
            subpaths.add(subpath)
        
        return subpaths

    # A helper function to write error messages to the errors column in the state table dataframe
    def update_error_column(self, df:pd.DataFrame, msg: str, indexes: list) -> None:
        df.loc[indexes, 'Error'] = df.loc[indexes, 'Error'].apply(lambda x, msg: f'{x} | {msg}' if len(x) > 0 else msg, args=(msg,))

    # Checks all state codes for each state class in the state table and returns a dictionary of found errors
    def check_duplicate_state_codes(self, df: pd.DataFrame) -> dict:
        classes = df.loc[df['StateClass'].isna() == False, 'StateClass'].unique()
        duplicates = []
        for c in classes:
            t = df.loc[(df['StateClass'] == c) & (df['NodeType'] != 'EquipmentStateClass')]
            duplicates.extend(list(t.loc[t['Code'].duplicated()].index))
        
        if len(duplicates) > 0:
            self.update_error_column(df, 'Duplicate State Code', duplicates)
            return {'error': 'Duplicate State Code', 'indexes': duplicates}

        return {}

    # Checks all the state paths in the state table for duplicates and returns a dictionary of found errors
    def check_duplicate_paths(self, df: pd.DataFrame) -> dict:
        duplicates = []

        duplicates.extend(list(df.loc[df['Path'].duplicated()].index))
        
        if len(duplicates) > 0:
            self.update_error_column(df, 'Duplicate Path', duplicates)
            return {'error': 'Duplicate Path', 'indexes': duplicates}

        return {}

    # Checks all state paths for missing parents in the path and returns a dictionary with the missing parent paths
    def check_missing_parent(self, df: pd.DataFrame) -> dict:
        parents = set(list(df.loc[0, 'Parent']))
        error_msg = 'Missing parents'
        errors = []

        for i, p in df['Parent'].items():
            if p in parents:
                parents.add(df.loc[i, 'Path'])
                continue
            subpaths = self.generate_subpaths(p)
            missing_parents = subpaths.difference(parents)
            if len(missing_parents) > 0:
                self.update_error_column(df, f'{error_msg}: {missing_parents}', [i])
                errors.append({'index': i, 'content': missing_parents})
        
        if len(errors) > 0:
            return {'error': 'Missing parents', 'indexes': errors}

        return {}

if __name__ == '__main__':
    state_table = StateTable().from_csv('states_table.csv')
    state_table2 = StateTable().from_xml('output.xml')
    print('test')