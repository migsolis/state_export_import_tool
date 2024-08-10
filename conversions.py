import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod

columns = ['NodeType', 'StateClass', 'Name', 'OverrideCurrentLineDowntime', 'Code', 'Type', 'ShortStopThreshold', 'EnableMeantimeMetrics', 'Override', 'Scope', 'Roles', 'Parent', 'Path']

class Converter(ABC):
    @abstractmethod
    def deserialize(self, path: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def serialize(self, df, path: str, name: str) -> None:
        pass

class CSVConverter(Converter):
    def deserialize(self, path: str) -> pd.DataFrame:
        try:
            df = pd.read_csv(path, usecols=columns)
            df = self._prep_df(df)
        except:
            raise Exception('Error reading file')
    
        return df

    def serialize(self, df: pd.DataFrame, path: str, name: str) -> None:
        df.to_csv(f'{path}{name}.csv')

    def _prep_df(self, df: pd.DataFrame) -> pd.DataFrame:
        df.drop('Path', axis=1, inplace= True)
        df['Path'] = df['Parent'] + '/'+ df['Name']
        df.sort_values('Path', inplace=True)
        df['Error'] = ''
        return df

class ExcelConverter(Converter):
    def deserialize(self, path: str) -> pd.DataFrame:
        pass

    def serialize(self, df: pd.DataFrame, path: str, name: str) -> None:
        df.to_excel(f'{path}{name}.xlsx')

class XMLConverter(Converter):
    ROOT_CHAR = '~'

    def deserialize(self, path: str=None) -> pd.DataFrame:
        try:
            self.xml_tree = ET.parse(path)
            root = self.xml_tree.getroot()
            self.state_count = len(root.findall('.//EquipmentState'))
        except:
            raise Exception('Invalid export file path')
        
        root = self.xml_tree.getroot()
        if root.tag != 'EquipmentStateRoot':
            raise Exception(f'Invalid XML root, {root.tag}')
    
        df = pd.DataFrame()
        for state_class in root:
            if state_class.tag != 'EquipmentStateClass':
                continue
            df = self._destructure(state_class, df)

        state_class = df.pop('StateClass')
        roles = df.pop('Roles')
        parents = df.pop('Parent')
        paths = df.pop('Path')

        df['Roles'] = roles
        df['Parent'] = parents
        df['Path'] = paths
        df['Error'] = ''
        df.insert(1, 'StateClass', state_class)
        df.sort_values('Path', inplace=True)

        return df
    
    def serialize(self, df: pd.DataFrame, path: str, name: str) -> ET.ElementTree:
        # xml_header = '<?xml version="1.0" encoding="UTF-8" standalone="no"?><EquipmentStateRoot></EquipmentStateRoot>'
        if not df:
            df = self.df
        root = ET.Element('EquipmentStateRoot')
        doc = ET.ElementTree(root)
        
        index = self._create_tree(0, df, self.ROOT_CHAR, root)
        if index < df.shape[0]:
            raise Exception(f'Error Creating node at index {index}')
        
        ET.indent(root)
        ET.dump(root)
        self.xml_tree = doc

        self.xml_tree.write(f'{path}{name}.xml')

    def _create_state(self, parent: ET.Element, values: pd.DataFrame) -> ET.Element:
        elements = ['Name', 'Code', 'Type', 'ShortStopThreshold', 'EnableMeantimeMetrics', 'OverrideCurrentLineDowntime', 'Override', 'Scope']
        state = ET.SubElement(parent, 'EquipmentState')

        for e in elements:
            temp = ET.SubElement(state, e)
            value = values[e]
            if type(values[e]) == np.float64:
                value = int(value)
            
            temp.text = str(value)

        return state

    def _create_state_class(self, parent: ET.Element, values: pd.DataFrame) -> ET.Element:
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

    def _create_tree(self, index: int, df: pd.DataFrame, path: str, parent: ET.Element) -> int:
        while index < df.shape[0]:
            if df.loc[index, 'Parent'] != path:
                break
            node = None
            if df.loc[index, 'NodeType'] == 'EquipmentStateClass':
                node = self._create_state_class(parent,df.iloc[index, :])

            if df.loc[index, 'NodeType'] == 'EquipmentState':
                node = self._create_state(parent, df.iloc[index, :])

            index = self._create_tree(index + 1, df, df.loc[index, 'Path'], node)

        return index    
    
    def _destructure(self, node: ET.ElementTree, df: pd.DataFrame, parent: str=ROOT_CHAR, state_class: str='') -> pd.DataFrame:
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
        self._processed_count(df.shape[0])
        for child in deep_children:  
            df = self._destructure(child, df, f'{parent}/{row_data["Name"]}', state_class)

        return df

    def _processed_count(self, value: int) -> None:
        self.current_count = value