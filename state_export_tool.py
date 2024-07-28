import pandas as pd
import xml.etree.ElementTree as ET
import argparse

def destructure(node: ET.ElementTree, df: pd.DataFrame, parent: str ='~'):
    row_data = {}
    for child in node:
        if len(child) == 0:
            row_data[child.tag] = child.text
        else:
            df = destructure(child, df, f'{parent}/{row_data["Name"]}')

    row_data['Parent'] = parent
    row_data['Path'] = parent + '/' + row_data['Name']
    row = pd.DataFrame([row_data])
    return pd.concat([df, row])

def process_state_class(state_class):
    class_data = {}
    import_table = pd.DataFrame()

    for child in state_class:
        if child.tag == 'EquipmentState':
            import_table = destructure(child, import_table)
        else:
            if len(child) > 0:
                class_data[child.tag] = str(ET.tostring(child, encoding='utf8'))
            else:
                class_data[child.tag] = child.text
    import_table['EquipmentStateClass'] = class_data['Name']
    import_table.insert(0, 'EquipmentStateClass', import_table.pop('EquipmentStateClass'))
    class_data = pd.DataFrame([class_data])
    return class_data, import_table.sort_values(by='Path')

def main(path: str, name: str):
    try:
        xml_data = ET.parse(path)
    except:
        raise Exception('Invalid export file path')

    root = xml_data.getroot()
    if root.tag != 'EquipmentStateRoot':
        raise Exception(f'Invalid XML root, {root.tag}')
 
    for child in root:
        if child.tag != 'EquipmentStateClass':
            continue
        
        class_attr, import_table = process_state_class(child)

        class_attr.to_csv(f"class_{class_attr.loc[0, 'Name']}.csv", index=False)
        import_table.to_csv(f"{class_attr.loc[0, 'Name']}.csv", index=False)
        with pd.ExcelWriter(path=f'{name}.xlsx', mode='w') as writer:
            class_attr.to_excel(excel_writer=writer, sheet_name='EquipmentStateClass', index=False)
            import_table.to_excel(excel_writer=writer, sheet_name=class_attr.loc[0, 'Name'], index=False)

    print(f'Did the thing...')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default="output")

    args = parser.parse_args()

    main(args.path, args.name)
    