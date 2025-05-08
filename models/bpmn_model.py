from typing import Dict, Any
import xml.etree.ElementTree as ET
import os
import traceback


def read_dmn_file(file_path: str) -> str:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        with open(file_path, 'r', encoding='latin-1') as file:
            return file.read()


class DMNParser:
    def __init__(self, dmn_file_path: str):
        self.file_path = dmn_file_path
        self.content = read_dmn_file(dmn_file_path)

        if self.content.startswith('\ufeff'):
            self.content = self.content[1:]

        self.root = ET.fromstring(self.content)
        self.namespaces = {
            'dmn': 'http://www.omg.org/spec/DMN/20151101/dmn.xsd',
            'dmn2': 'https://www.omg.org/spec/DMN/20191111/MODEL/',
            'semantic': 'http://www.omg.org/spec/DMN/20180521/MODEL/',
        }

    def parse(self) -> Dict[str, Any]:
        dmn_model = {
            'inputs': [],
            'decisions': [],
            'knowledge_sources': []
        }

        for ns_prefix, ns_uri in self.namespaces.items():
            try:
                for input_data in self.root.findall(f'.//{{{ns_uri}}}inputData'):
                    input_dict = {
                        'id': input_data.get('id', f'input_{len(dmn_model["inputs"])}'),
                        'name': input_data.get('name', 'Unnamed Input'),
                        'type': 'string'
                    }
                    dmn_model['inputs'].append(input_dict)

                for decision in self.root.findall(f'.//{{{ns_uri}}}decision'):
                    decision_dict = {
                        'id': decision.get('id', f'decision_{len(dmn_model["decisions"])}'),
                        'name': decision.get('name', 'Unnamed Decision'),
                        'required_inputs': []
                    }
                    dmn_model['decisions'].append(decision_dict)

            except Exception as e:
                print(f"Error parsing with namespace {ns_prefix}: {str(e)}")
                continue

        return dmn_model


def create_bpmndi_elements(process_element, bpmn_root, elements_info):
    """Create BPMNDI element with diagram information"""
    bpmndi = ET.SubElement(bpmn_root, 'bpmndi:BPMNDiagram')
    bpmndi.set('id', 'BPMNDiagram_1')

    plane = ET.SubElement(bpmndi, 'bpmndi:BPMNPlane')
    plane.set('id', 'BPMNPlane_1')
    plane.set('bpmnElement', 'Process_1')

    for element in elements_info:
        try:
            element_type = element.get('element_type', '')  # Changed from 'type' to 'element_type'

            if element_type in ['startEvent', 'endEvent']:
                shape = ET.SubElement(plane, 'bpmndi:BPMNShape')
                shape.set('id', f"{element['id']}_di")
                shape.set('bpmnElement', element['id'])

                bounds = ET.SubElement(shape, 'dc:Bounds')
                bounds.set('x', str(element['x']))
                bounds.set('y', str(element['y']))
                bounds.set('width', '36')
                bounds.set('height', '36')

            elif element_type in ['userTask', 'businessRuleTask']:
                shape = ET.SubElement(plane, 'bpmndi:BPMNShape')
                shape.set('id', f"{element['id']}_di")
                shape.set('bpmnElement', element['id'])

                bounds = ET.SubElement(shape, 'dc:Bounds')
                bounds.set('x', str(element['x']))
                bounds.set('y', str(element['y']))
                bounds.set('width', '100')
                bounds.set('height', '80')

            if 'sourceRef' in element:
                edge = ET.SubElement(plane, 'bpmndi:BPMNEdge')
                edge.set('id', f"{element['id']}_di")
                edge.set('bpmnElement', element['id'])

                waypoint = ET.SubElement(edge, 'di:waypoint')
                waypoint.set('x', str(element['sourceX']))
                waypoint.set('y', str(element['sourceY']))

                waypoint = ET.SubElement(edge, 'di:waypoint')
                waypoint.set('x', str(element['targetX']))
                waypoint.set('y', str(element['targetY']))

        except Exception as e:
            print(f"Error processing element {element}: {str(e)}")
            continue


def convert_dmn_to_bpmn(input_path: str, output_path: str = None) -> bool:
    try:
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Input file not found: {input_path}")

        if output_path is None:
            output_path = os.path.splitext(input_path)[0] + '.bpmn'

        print(f"Parsing DMN file: {input_path}")
        parser = DMNParser(input_path)
        dmn_model = parser.parse()
        print(f"Parsed DMN model: {dmn_model}")

        # Create BPMN XML
        bpmn_root = ET.Element('definitions')
        bpmn_root.set('xmlns', 'http://www.omg.org/spec/BPMN/20100524/MODEL')
        bpmn_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        bpmn_root.set('xmlns:bpmn', 'http://www.omg.org/spec/BPMN/20100524/MODEL')
        bpmn_root.set('xmlns:bpmndi', 'http://www.omg.org/spec/BPMN/20100524/DI')
        bpmn_root.set('xmlns:dc', 'http://www.omg.org/spec/DD/20100524/DC')
        bpmn_root.set('xmlns:di', 'http://www.omg.org/spec/DD/20100524/DI')
        bpmn_root.set('id', 'Definitions_1')
        bpmn_root.set('targetNamespace', 'http://activiti.org/bpmn')

        process = ET.SubElement(bpmn_root, 'process')
        process.set('id', 'Process_1')
        process.set('isExecutable', 'true')

        elements_info = []
        x_position = 180
        y_position = 100

        # Add start event
        start_event = ET.SubElement(process, 'startEvent')
        start_event.set('id', 'StartEvent_1')
        start_event.set('name', 'Start')
        elements_info.append({
            'id': 'StartEvent_1',
            'element_type': 'startEvent',  # Changed from 'type' to 'element_type'
            'x': x_position,
            'y': y_position
        })
        last_id = 'StartEvent_1'
        last_x = x_position + 36
        x_position += 100

        # Add tasks for inputs
        for input_data in dmn_model['inputs']:
            task_id = f"Task_{input_data['id']}"
            task = ET.SubElement(process, 'userTask')
            task.set('id', task_id)
            task.set('name', f"Provide {input_data['name']}")

            elements_info.append({
                'id': task_id,
                'element_type': 'userTask',  # Changed from 'type' to 'element_type'
                'x': x_position,
                'y': y_position - 22
            })

            flow_id = f"Flow_{last_id}_{task_id}"
            flow = ET.SubElement(process, 'sequenceFlow')
            flow.set('id', flow_id)
            flow.set('sourceRef', last_id)
            flow.set('targetRef', task_id)

            elements_info.append({
                'id': flow_id,
                'sourceRef': last_id,
                'targetRef': task_id,
                'sourceX': last_x,
                'sourceY': y_position + 18,
                'targetX': x_position,
                'targetY': y_position + 18
            })

            last_id = task_id
            last_x = x_position + 100
            x_position += 150

        # Add tasks for decisions
        for decision in dmn_model['decisions']:
            task_id = f"Task_{decision['id']}"
            task = ET.SubElement(process, 'businessRuleTask')
            task.set('id', task_id)
            task.set('name', decision['name'])

            elements_info.append({
                'id': task_id,
                'element_type': 'businessRuleTask',  # Changed from 'type' to 'element_type'
                'x': x_position,
                'y': y_position - 22
            })

            flow_id = f"Flow_{last_id}_{task_id}"
            flow = ET.SubElement(process, 'sequenceFlow')
            flow.set('id', flow_id)
            flow.set('sourceRef', last_id)
            flow.set('targetRef', task_id)

            elements_info.append({
                'id': flow_id,
                'sourceRef': last_id,
                'targetRef': task_id,
                'sourceX': last_x,
                'sourceY': y_position + 18,
                'targetX': x_position,
                'targetY': y_position + 18
            })

            last_id = task_id
            last_x = x_position + 100
            x_position += 150

        # Add end event
        end_event = ET.SubElement(process, 'endEvent')
        end_event.set('id', 'EndEvent_1')
        end_event.set('name', 'End')

        elements_info.append({
            'id': 'EndEvent_1',
            'element_type': 'endEvent',  # Changed from 'type' to 'element_type'
            'x': x_position,
            'y': y_position
        })

        flow_id = f"Flow_{last_id}_EndEvent_1"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', last_id)
        flow.set('targetRef', 'EndEvent_1')

        elements_info.append({
            'id': flow_id,
            'sourceRef': last_id,
            'targetRef': 'EndEvent_1',
            'sourceX': last_x,
            'sourceY': y_position + 18,
            'targetX': x_position,
            'targetY': y_position + 18
        })

        print("Creating BPMNDI elements...")
        create_bpmndi_elements(process, bpmn_root, elements_info)

        # Create XML string with proper formatting
        xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_string += ET.tostring(bpmn_root, encoding='unicode', method='xml')

        print(f"Saving to file: {output_path}")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)

        print(f"Successfully converted to {output_path}")
        return True

    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        print("Full traceback:")
        print(traceback.format_exc())
        return False


if __name__ == "__main__":
    input_file = r"C:\Users\lenovo\MiAPB\event_logs\d1.dmn"
    success = convert_dmn_to_bpmn(input_file)
    if success:
        print("Conversion completed successfully")
    else:
        print("Conversion failed")
