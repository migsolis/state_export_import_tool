import argparse
import pandas as pd
import xml.etree.ElementTree as ET
import numpy as np

ROOT_CHAR = '~'

def create_state_class(parent: ET.Element, values: pd.DataFrame) -> ET.Element:
    state_class = ET.SubElement(parent, 'EquipmentStateClass')
    tag = 'Name'
    name = ET.SubElement(state_class, tag)
    name.text = str(values[tag])

    tag = 'OverrideCurrentLineDowntime'
    override = ET.SubElement(state_class, tag)
    override.text = str(values[tag])

    tag = 'Roles'
    if pd.isnull(values['Roles']):
        ET.SubElement(state_class, 'Roles')
    else:
        roles = ET.fromstring(values['Roles'])
        state_class.append(roles)
    
    return state_class

def create_state(parent: ET.Element, values: pd.DataFrame) -> ET.Element:
    elements = ['Name', 'Code', 'Type', 'ShortStopThreshold', 'EnableMeantimeMetrics', 'OverrideCurrentLineDowntime', 'Override', 'Scope']
    state = ET.SubElement(parent, 'EquipmentState')

    for e in elements:
        temp = ET.SubElement(state, e)
        value = values[e]
        if type(values[e]) == np.float64:
            value = int(value)
        
        temp.text = str(value)

    return state

def create_tree(index: int, df: pd.DataFrame, path: str, parent: ET.Element) -> int:
    while index < df.shape[0]:
        if df.loc[index, 'Parent'] != path:
            break
        node = None
        if df.loc[index, 'NodeType'] == 'EquipmentStateClass':
            node = create_state_class(parent,df.iloc[index, :])

        if df.loc[index, 'NodeType'] == 'EquipmentState':
            node = create_state(parent, df.iloc[index, :])

        index = create_tree(index + 1, df, df.loc[index, 'Path'], node)
    return index    


def excel_to_xml(import_table: pd.DataFrame, name: str) -> ET.ElementTree:
    # xml_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><EquipmentStateRoot></EquipmentStateRoot>'
    root = ET.Element('EquipmentStateRoot')
    doc = ET.ElementTree(root)
    
    index = create_tree(0, import_table, ROOT_CHAR, root)
    if index < import_table.shape[0]:
        update_error_column(import_table, 'Error Creating Node', [index])
        generate_output_file(import_table, name)
    ET.indent(root)
    ET.dump(root)
    return doc

def generate_output_file(import_table: pd.DataFrame, name: str):
    import_table.to_csv(f'{name}.csv', index=False)
    exit(1)

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

### Check for error in import files ###
def check_duplicate_state_codes(df: pd.DataFrame) -> bool:
    classes = df.loc[df['StateClass'].isna() == False, 'StateClass'].unique()
    duplicates = []
    for c in classes:
        t = df.loc[df['StateClass'] == c]
        duplicates.extend(list(t.loc[t['Code'].duplicated()].index))
    
    if len(duplicates) > 0:
        update_error_column(df, 'Duplicate State Code', duplicates)
        return True

    return False

def check_duplicate_paths(df: pd.DataFrame) -> bool:
    duplicates = []

    duplicates.extend(list(df.loc[df['Path'].duplicated()].index))
    
    if len(duplicates) > 0:
        update_error_column(df, 'Duplicate Path', duplicates)
        return True

    return False

def check_missing_parent(df: pd.DataFrame) -> bool:
    is_missing_parents = False
    parents = set(list(df.loc[0, 'Parent']))
    error_msg = 'Missing parents'

    for i, p in df['Parent'].items():
        if p in parents:
            parents.add(df.loc[i, 'Path'])
            continue
        subpaths = generate_subpaths(p)
        missing_parents = subpaths.difference(parents)
        if len(missing_parents) > 0:
            update_error_column(df, f'{error_msg}: {missing_parents}', [i])
            is_missing_parents = True
    return is_missing_parents

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default='output')
    args = parser.parse_args()
    
    import_table = pd.read_csv(args.path)
    import_table.drop('Path', axis=1, inplace= True)
    import_table['Path'] = import_table['Parent'] + '/'+ import_table['Name']
    import_table.sort_values('Path', inplace=True)
    import_table['Error'] = ''

    duplicate_codes = check_duplicate_state_codes(import_table)
    duplicate_paths = check_duplicate_paths(import_table)
    missing_parents = check_missing_parent(import_table)

    if duplicate_codes or duplicate_paths or missing_parents:
        generate_output_file(import_table, args.name)

    doc = excel_to_xml(import_table, args.name)

    doc.write(f'{args.name}.xml')