import argparse
import pandas as pd
import xml.etree.ElementTree as ET

def create_state_class(parent, values):
    tag = 'Name'
    name = ET.SubElement(parent, tag)
    name.text = str(values[tag])

    tag = 'OverrideCurrentLineDowntime'
    override = ET.SubElement(parent, tag)
    override.text = str(values[tag])

    tag = 'Roles'
    roles = ET.fromstring(values['Roles'])
    parent.append(roles)
    return

def create_state(parent, values):
    elements = ['Name', 'Code', 'Type', 'ShortStopThreshold', 'EnableMeantimeMetrics', 'OverrideCurrentLineDowntime', 'Override', 'Scope']
    state = ET.SubElement(parent, 'EquipmentState')

    for e in elements:
        temp = ET.SubElement(state, e)
        temp.text = str(values[e])

    return state

def create_tree(index, df, path, node) -> int:
    while index < df.shape[0]:
        if df.loc[index, 'Parent'] != path:
            break
        
        state = create_state(node, df.iloc[index, :])
        index = create_tree(index + 1, df, df.loc[index, 'Path'], state)
    return index    


def excel_to_xml(state_classes: pd.DataFrame, states: pd.DataFrame) -> ET.ElementTree:
    xml_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n<EquipmentStateRoot></EquipmentStateRoot>'
    root = ET.Element('EquipmentStateRoot')
    doc = ET.ElementTree(root)
    
    for i in range(state_classes.shape[0]):
        name = state_classes.loc[i, 'Name']
        create_state_class(root, state_classes.iloc[i])
        create_tree(0, states.loc[states['EquipmentStateClass'] == name], "~", root)
    ET.indent(root)
    ET.dump(root)
    return doc



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--path')
    parser.add_argument('-n', '--name', default='output')
    args = parser.parse_args()
    
    state_classes = pd.read_csv('class_Default.csv')
    states = pd.read_csv(args.path)

    doc = excel_to_xml(state_classes, states)

    doc.write(f'{args.name}.xml')