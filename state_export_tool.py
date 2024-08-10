import pandas as pd
import xml.etree.ElementTree as ET
import argparse

class StateExportTool():
    ROOT_CHAR = "~"

    def __init__(self, path):
        self.path = path
        self.state_count = 0
        self.current_count = 0

        if path:
            self.parse_xml(self.path)

    def parse_xml(self, path: str):
        if path:
            self.path = path
        
        try:
            self.xml_tree = ET.parse(self.path)
            root = self.xml_tree.getroot()
            self.state_count =len(root.findall('.//EquipmentState'))
        except:
            raise Exception('Invalid export file path')
    
    def convert_to_df(self) -> None:
        root = self.xml_tree.getroot()
        if root.tag != 'EquipmentStateRoot':
            raise Exception(f'Invalid XML root, {root.tag}')
    
        import_table = pd.DataFrame()
        for state_class in root:
            if state_class.tag != 'EquipmentStateClass':
                continue
            import_table = self.destructure(state_class, import_table)

        state_class = import_table.pop('StateClass')
        roles = import_table.pop('Roles')
        parents = import_table.pop('Parent')
        paths = import_table.pop('Path')

        import_table['Roles'] = roles
        import_table['Parent'] = parents
        import_table['Path'] = paths
        import_table.insert(1, 'StateClass', state_class)
        import_table.sort_values('Path', inplace=True)
        split_path = import_table['Path'].str.split('/', expand=True).drop(0, axis=1)
        split_path.columns = [f'ReasonLevel{i}' for i in range(1, split_path.shape[1] + 1)]

        self.import_table = pd.concat([import_table, split_path], axis=1)

    def destructure(self, node: ET.ElementTree, df: pd.DataFrame, parent: str = ROOT_CHAR, state_class: str = '') -> pd.DataFrame:
        deep_children = []
        row_data = {}
        row_data['NodeType'] = node.tag
        
        for child in node:
            if len(child) == 0:
                row_data[child.tag] = child.text if child.text else ''
            elif child.tag == 'Roles':
                row_data[child.tag] = ET.tostring(child).decode('ascii').replace(' ', '').replace('\n','')
            else:
                deep_children.append(child)
        row_data['StateClass'] = state_class
        if node.tag == 'EquipmentStateClass':
            state_class = row_data['Name']
        row_data['Parent'] = parent
        row_data['Path'] = parent + '/' + row_data['Name']
        row = pd.DataFrame([row_data])
        df = pd.concat([df, row])
        self.update_current_count(df.shape[0])
        for child in deep_children:  
            df = self.destructure(child, df, f'{parent}/{row_data["Name"]}', state_class)

        return df

    def update_current_count(self, value: int) -> None:
        self.current_count = value
    
    def to_csv(self, path: str='states_table.csv') -> None:
        self.import_table.to_csv(path, index=False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default="states_table")
    args = parser.parse_args()

    converter = StateExportTool(args.path)
    converter.convert_to_df()
    print(f'Did the thing...')
    converter.to_csv(f'{args.name}.csv')