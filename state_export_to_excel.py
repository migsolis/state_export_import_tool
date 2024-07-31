import pandas as pd
import xml.etree.ElementTree as ET
import argparse

ROOT_CHAR = "~"

def destructure(node: ET.ElementTree, df: pd.DataFrame, parent: str = ROOT_CHAR, state_class: str = '') -> pd.DataFrame:
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
    
    for child in deep_children:  
        df = destructure(child, df, f'{parent}/{row_data["Name"]}', state_class)

    return df

def xml_to_excel(path: str) -> pd.DataFrame:
    try:
        xml_data = ET.parse(path)
    except:
        raise Exception('Invalid export file path')

    root = xml_data.getroot()
    if root.tag != 'EquipmentStateRoot':
        raise Exception(f'Invalid XML root, {root.tag}')
 
    import_table = pd.DataFrame()
    for state_class in root:
        if state_class.tag != 'EquipmentStateClass':
            continue
        import_table = destructure(state_class, import_table)

    state_class = import_table.pop('StateClass')
    roles = import_table.pop('Roles')
    parents = import_table.pop('Parent')
    paths = import_table.pop('Path')

    import_table['Roles'] = roles
    import_table['Parent'] = parents
    import_table['Path'] = paths
    import_table.insert(1, 'StateClass', state_class)
    import_table.sort_values('Path', inplace=True)
    return import_table


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default="states_table")
    args = parser.parse_args()
    
    import_table = xml_to_excel(args.path)
    print(f'Did the thing...')
    import_table.to_csv(f'{args.name}.csv', index=False)