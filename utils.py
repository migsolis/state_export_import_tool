import pandas as pd
from state_table import StateTable

class StateTableChecker():
    def __init__(self, state_table:StateTable=None):
        self.state_table = state_table

        if self.state_table:
            self.df = self.state_table.get_df()

    def generate_subpaths(path: str) -> set:
        path_parts = path.split('/')
        
        subpath = path_parts[0]
        subpaths = set([subpath])
        for p in path_parts[1:]:
            subpath += "/" + p
            subpaths.add(subpath)
        
        return subpaths

    def update_error_column(df:pd.DataFrame, msg: str, indexes: list) -> None:
        df.loc[indexes, 'Error'] = df.loc[indexes, 'Error'].apply(lambda x, msg: f'{x} | {msg}' if len(x) > 0 else msg, args=(msg,))

    def check_duplicate_state_codes(self, df: pd.DataFrame) -> bool:
        classes = df.loc[df['StateClass'].isna() == False, 'StateClass'].unique()
        duplicates = []
        for c in classes:
            t = df.loc[df['StateClass'] == c]
            duplicates.extend(list(t.loc[t['Code'].duplicated()].index))
        
        if len(duplicates) > 0:
            self.update_error_column(df, 'Duplicate State Code', duplicates)
            return True

        return False

    def check_duplicate_paths(self, df: pd.DataFrame) -> bool:
        duplicates = []

        duplicates.extend(list(df.loc[df['Path'].duplicated()].index))
        
        if len(duplicates) > 0:
            self.update_error_column(df, 'Duplicate Path', duplicates)
            return True

        return False

    def check_missing_parent(self, df: pd.DataFrame) -> bool:
        is_missing_parents = False
        parents = set(list(df.loc[0, 'Parent']))
        error_msg = 'Missing parents'

        for i, p in df['Parent'].items():
            if p in parents:
                parents.add(df.loc[i, 'Path'])
                continue
            subpaths = self.generate_subpaths(p)
            missing_parents = subpaths.difference(parents)
            if len(missing_parents) > 0:
                self.update_error_column(df, f'{error_msg}: {missing_parents}', [i])
                is_missing_parents = True
        return is_missing_parents