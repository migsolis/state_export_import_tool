import argparse
import pandas as pd
import xml.etree.ElementTree as ET
from numpy import float64

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
        if type(values[e]) == float64:
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


def excel_to_xml(import_table: pd.DataFrame) -> ET.ElementTree:
    # xml_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><EquipmentStateRoot></EquipmentStateRoot>'
    root = ET.Element('EquipmentStateRoot')
    doc = ET.ElementTree(root)

    create_tree(0, import_table, "~", root)
    ET.indent(root)
    ET.dump(root)
    return doc



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default='output')
    args = parser.parse_args()
    
    import_table = pd.read_csv(args.path)

    doc = excel_to_xml(import_table)

    doc.write(f'{args.name}.xml')