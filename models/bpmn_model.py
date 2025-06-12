from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from bpmn_python.bpmn_diagram_rep import BpmnDiagramGraph
import bpmn_python.bpmn_python_consts as consts

class BPMN:
    """
    Class representing BPMN model elements and operations for creating BPMN diagrams.
    Provides methods to create and configure various BPMN elements.
    """
    
    def __init__(self, diagram_name: str = "bpmn_diagram"):
        """
        Initialize a new BPMN model with a BpmnDiagramGraph.
        
        Args:
            diagram_name (str): Name of the BPMN diagram
        """
        self.bpmn_graph = BpmnDiagramGraph()
        self.bpmn_graph.create_new_diagram_graph(diagram_name=diagram_name)
        self.process_id = self.bpmn_graph.add_process_to_diagram()
        
        # Track created elements
        self.elements = {}
        self.flows = []
        
    def create_start_event(self, name: str, x: int, y: int, 
                          event_definition: Optional[str] = None) -> str:
        """
        Create a start event in the BPMN diagram.
        
        Args:
            name (str): Name of the start event
            x (int): X coordinate
            y (int): Y coordinate
            event_definition (str, optional): Type of event definition
            
        Returns:
            str: ID of the created start event
        """
        event_id, _ = self.bpmn_graph.add_start_event_to_diagram(
            self.process_id, 
            start_event_name=name,
            start_event_definition=event_definition
        )
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.width] = "36"
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.height] = "36"
        
        self.elements[event_id] = {
            "type": "startEvent",
            "name": name,
            "position": (x, y)
        }
        
        return event_id
    
    def create_end_event(self, name: str, x: int, y: int,
                        event_definition: Optional[str] = None) -> str:
        """
        Create an end event in the BPMN diagram.
        
        Args:
            name (str): Name of the end event
            x (int): X coordinate
            y (int): Y coordinate
            event_definition (str, optional): Type of event definition
            
        Returns:
            str: ID of the created end event
        """
        event_id, _ = self.bpmn_graph.add_end_event_to_diagram(
            self.process_id, 
            end_event_name=name,
            end_event_definition=event_definition
        )
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.width] = "36"
        self.bpmn_graph.diagram_graph.node[event_id][consts.Consts.height] = "36"
        
        self.elements[event_id] = {
            "type": "endEvent",
            "name": name,
            "position": (x, y)
        }
        
        return event_id
    
    def create_user_task(self, name: str, x: int, y: int, 
                        width: int = 100, height: int = 80) -> str:
        """
        Create a user task in the BPMN diagram.
        
        Args:
            name (str): Name of the user task
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the task
            height (int): Height of the task
            
        Returns:
            str: ID of the created user task
        """
        task_id, _ = self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=name)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = str(height)
        
        self.elements[task_id] = {
            "type": "userTask",
            "name": name,
            "position": (x, y)
        }
        
        return task_id
    
    def create_business_rule_task(self, name: str, x: int, y: int, 
                                width: int = 100, height: int = 80) -> str:
        """
        Create a business rule task in the BPMN diagram.
        
        Args:
            name (str): Name of the business rule task
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the task
            height (int): Height of the task
            
        Returns:
            str: ID of the created business rule task
        """
        task_id, _ = self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=name)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "businessRuleTask"
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = str(height)
        
        self.elements[task_id] = {
            "type": "businessRuleTask",
            "name": name,
            "position": (x, y)
        }
        
        return task_id
    
    def create_parallel_gateway(self, name: str, x: int, y: int, 
                              width: int = 50, height: int = 50) -> str:
        """
        Create a parallel gateway in the BPMN diagram.
        
        Args:
            name (str): Name of the gateway
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the gateway
            height (int): Height of the gateway
            
        Returns:
            str: ID of the created parallel gateway
        """
        gateway_id, _ = self.bpmn_graph.add_parallel_gateway_to_diagram(self.process_id, gateway_name=name)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = str(height)
        
        self.elements[gateway_id] = {
            "type": "parallelGateway",
            "name": name,
            "position": (x, y)
        }
        
        return gateway_id
    
    def create_exclusive_gateway(self, name: str, x: int, y: int, 
                               width: int = 50, height: int = 50) -> str:
        """
        Create an exclusive gateway in the BPMN diagram.
        
        Args:
            name (str): Name of the gateway
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the gateway
            height (int): Height of the gateway
            
        Returns:
            str: ID of the created exclusive gateway
        """
        gateway_id, _ = self.bpmn_graph.add_exclusive_gateway_to_diagram(self.process_id, gateway_name=name)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = str(height)
        
        self.elements[gateway_id] = {
            "type": "exclusiveGateway",
            "name": name,
            "position": (x, y)
        }
        
        return gateway_id
    
    def create_data_store(self, name: str, x: int, y: int, 
                         width: int = 50, height: int = 50) -> str:
        """
        Create a data store in the BPMN diagram.
        
        Args:
            name (str): Name of the data store
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the data store
            height (int): Height of the data store
            
        Returns:
            str: ID of the created data store
        """
        # BpmnDiagramGraph doesn't have add_data_store_to_diagram, use add_task_to_diagram instead
        # and then change the type to dataStoreReference
        store_id, _ = self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=name)
        self.bpmn_graph.diagram_graph.node[store_id][consts.Consts.type] = "dataStoreReference"
        self.bpmn_graph.diagram_graph.node[store_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[store_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[store_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[store_id][consts.Consts.height] = str(height)
        
        self.elements[store_id] = {
            "type": "dataStore",
            "name": name,
            "position": (x, y)
        }
        
        return store_id
    
    def create_data_object(self, name: str, x: int, y: int, 
                          width: int = 36, height: int = 50) -> str:
        """
        Create a data object in the BPMN diagram.
        
        Args:
            name (str): Name of the data object
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the data object
            height (int): Height of the data object
            
        Returns:
            str: ID of the created data object
        """
        # BpmnDiagramGraph doesn't have add_data_object_to_diagram, use add_task_to_diagram instead
        # and then change the type to dataObjectReference
        object_id, _ = self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=name)
        self.bpmn_graph.diagram_graph.node[object_id][consts.Consts.type] = "dataObjectReference"
        self.bpmn_graph.diagram_graph.node[object_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[object_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[object_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[object_id][consts.Consts.height] = str(height)
        
        self.elements[object_id] = {
            "type": "dataObject",
            "name": name,
            "position": (x, y)
        }
        
        return object_id
    
    def create_text_annotation(self, text: str, x: int, y: int, 
                             width: int = 100, height: int = 30) -> str:
        """
        Create a text annotation in the BPMN diagram.
        
        Args:
            text (str): Text content of the annotation
            x (int): X coordinate
            y (int): Y coordinate
            width (int): Width of the annotation
            height (int): Height of the annotation
            
        Returns:
            str: ID of the created text annotation
        """
        # Create a task and manually set the type to textAnnotation
        annotation_id, _ = self.bpmn_graph.add_task_to_diagram(self.process_id, task_name=text)
        self.bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.type] = "textAnnotation"
        self.bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.x] = str(x)
        self.bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.y] = str(y)
        self.bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.width] = str(width)
        self.bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.height] = str(height)
        
        self.elements[annotation_id] = {
            "type": "textAnnotation",
            "text": text,
            "position": (x, y)
        }
        
        return annotation_id
    
    def create_sequence_flow(self, source_id: str, target_id: str, name: str = "") -> str:
        """
        Create a sequence flow between two elements in the BPMN diagram.
        
        Args:
            source_id (str): ID of the source element
            target_id (str): ID of the target element
            name (str): Name of the sequence flow
            
        Returns:
            str: ID of the created sequence flow
        """
        flow_id = self.bpmn_graph.add_sequence_flow_to_diagram(
            self.process_id, 
            source_id, 
            target_id, 
            sequence_flow_name=name
        )
        
        self.flows.append({
            "id": flow_id,
            "source": source_id,
            "target": target_id,
            "name": name
        })
        
        return flow_id
    
    def create_association(self, source_id: str, target_id: str) -> str:
        """
        Create an association between two elements in the BPMN diagram.
        
        Args:
            source_id (str): ID of the source element
            target_id (str): ID of the target element
            
        Returns:
            str: ID of the created association
        """
        # Use add_sequence_flow_to_diagram and manually set the type
        association_id = self.bpmn_graph.add_sequence_flow_to_diagram(
            self.process_id,
            source_id,
            target_id
        )
        
        # Manually set the type attribute for the edge
        for edge in self.bpmn_graph.diagram_graph.edges(data=True):
            if edge[0] == source_id and edge[1] == target_id:
                edge[2][consts.Consts.type] = "association"
                break
        
        self.flows.append({
            "id": association_id,
            "source": source_id,
            "target": target_id,
            "type": "association"
        })
        
        return association_id
    
    def create_data_association(self, source_id: str, target_id: str) -> str:
        """
        Create a data association between two elements in the BPMN diagram.
        
        Args:
            source_id (str): ID of the source element
            target_id (str): ID of the target element
            
        Returns:
            str: ID of the created data association
        """
        # Use add_sequence_flow_to_diagram and manually set the type
        association_id = self.bpmn_graph.add_sequence_flow_to_diagram(
            self.process_id,
            source_id,
            target_id
        )
        
        # Manually set the type attribute for the edge
        for edge in self.bpmn_graph.diagram_graph.edges(data=True):
            if edge[0] == source_id and edge[1] == target_id:
                edge[2][consts.Consts.type] = "dataInputAssociation"
                break
        
        self.flows.append({
            "id": association_id,
            "source": source_id,
            "target": target_id,
            "type": "dataAssociation"
        })
        
        return association_id
    
    def export_xml_file(self, output_path: str, filename: str = "/generated_bpmn.bpmn") -> None:
        """
        Export the BPMN diagram to an XML file.
        
        Args:
            output_path (str): Directory path to save the XML file
            filename (str): Name of the file (with leading slash)
        """
        self.bpmn_graph.export_xml_file(output_path, filename)