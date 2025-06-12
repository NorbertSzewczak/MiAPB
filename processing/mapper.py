from collections import defaultdict
from models.dmn_model import DMNModel
from bpmn_python.bpmn_diagram_rep import BpmnDiagramGraph
import bpmn_python.bpmn_python_consts as consts

# Keywords for element type detection
KEYWORDS_START_EVENT = ["received", "incoming", "message", "start", "trigger"]
KEYWORDS_DATA_STORES = ["database", "repository", "store", "storage"]
KEYWORDS_DATA_OBJECTS = ["document", "file", "data", "object", "record"]
KEYWORDS_SUMATOR = ["sumator", "join", "merge", "combine"]
KEYWORDS_USER_TASK = ["user", "task", "input", "provide"]


def map_dmn_to_bpmn(dmn_model: DMNModel) -> BpmnDiagramGraph:
    """Maps a DMN model to a BPMN diagram following the algorithm."""
    bpmn_graph = BpmnDiagramGraph()
    bpmn_graph.create_new_diagram_graph(diagram_name="mapped_from_dmn")
    process_id = bpmn_graph.add_process_to_diagram()

    # Initialize tracking dictionaries
    decision_levels = {}
    decision_positions = {}
    input_positions = {}
    active_flows = {}
    elements_by_target = defaultdict(list)
    input_elements = {}
    decision_tasks = {}
    knowledge_stores = {}
    knowledge_annotations = {}

    # Get starting decisions
    start_decisions = set()
    try:
        for decision_id, _ in dmn_model.get_start_decisions():
            start_decisions.add(decision_id)
            decision_levels[decision_id] = 0
    except AttributeError:
        for decision_id, _ in dmn_model.decisions:
            if not any(tgt == decision_id and any(src == d_id for d_id, _ in dmn_model.decisions) 
                      for src, tgt in dmn_model.information_requirements):
                start_decisions.add(decision_id)
                decision_levels[decision_id] = 0

    # Calculate decision levels
    def calculate_levels(node_id, level=0, visited=None):
        if visited is None:
            visited = set()
        if node_id in visited:
            return
        visited.add(node_id)
        decision_levels[node_id] = max(decision_levels.get(node_id, 0), level)
        for src, tgt in dmn_model.information_requirements:
            if src == node_id:
                calculate_levels(tgt, level + 1, visited)

    for decision_id in start_decisions:
        calculate_levels(decision_id)

    # Get starting inputs
    start_inputs = set()
    try:
        for input_id, _ in dmn_model.get_start_inputs():
            start_inputs.add(input_id)
    except AttributeError:
        for src, tgt in dmn_model.information_requirements:
            if tgt in start_decisions:
                for input_id, _ in dmn_model.input_data:
                    if src == input_id:
                        start_inputs.add(input_id)

    # Positioning parameters
    x_spacing = 200
    y_spacing = 100
    base_y = 150

    # Group decisions by levels
    decisions_by_level = defaultdict(list)
    for decision_id, level in decision_levels.items():
        decisions_by_level[level].append(decision_id)

    # Create start event
    start_id, _ = bpmn_graph.add_start_event_to_diagram(process_id, start_event_name="Process Start")
    bpmn_graph.diagram_graph.node[start_id][consts.Consts.x] = "100"
    bpmn_graph.diagram_graph.node[start_id][consts.Consts.y] = str(base_y)
    bpmn_graph.diagram_graph.node[start_id][consts.Consts.width] = "36"
    bpmn_graph.diagram_graph.node[start_id][consts.Consts.height] = "36"

    # Map inputs to decisions
    input_to_decision = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if any(src == input_id for input_id, _ in dmn_model.input_data):
            input_to_decision[src].append(tgt)

    # Calculate input levels
    input_levels = {}
    for input_id, _ in dmn_model.input_data:
        if input_id in input_to_decision:
            input_levels[input_id] = min(decision_levels.get(tgt, 0) for tgt in input_to_decision[input_id])
        else:
            input_levels[input_id] = 0

    # Group inputs by level
    inputs_by_level = defaultdict(list)
    for input_id, _ in dmn_model.input_data:
        inputs_by_level[input_levels.get(input_id, 0)].append(input_id)

    # Create gateway if multiple start inputs
    start_connector = start_id
    if len(start_inputs) > 1:
        split_gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name="Start Split")
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.x] = "170"
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.y] = str(base_y)
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.width] = "50"
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.height] = "50"
        bpmn_graph.add_sequence_flow_to_diagram(process_id, start_id, split_gateway_id)
        start_connector = split_gateway_id

    # Create starting input elements
    for level, inputs in sorted(inputs_by_level.items()):
        x_pos = 250 + level * x_spacing
        for i, input_id in enumerate(inputs):
            if input_id in start_inputs:
                input_name = next((name for id_, name in dmn_model.input_data if id_ == input_id), "Input")
                y_pos = base_y + i * y_spacing

                if any(keyword in input_name.lower() for keyword in KEYWORDS_START_EVENT):
                    # Create message start event
                    event_id, _ = bpmn_graph.add_start_event_to_diagram(
                        process_id,
                        start_event_name=f"{input_name} received",
                        start_event_definition="message"
                    )
                    bpmn_graph.diagram_graph.node[event_id][consts.Consts.x] = str(x_pos)
                    bpmn_graph.diagram_graph.node[event_id][consts.Consts.y] = str(y_pos)
                    bpmn_graph.diagram_graph.node[event_id][consts.Consts.width] = "36"
                    bpmn_graph.diagram_graph.node[event_id][consts.Consts.height] = "36"
                    input_elements[input_id] = event_id
                else:
                    # Create user task
                    task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Provide {input_name}")
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(x_pos)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(y_pos)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
                    input_elements[input_id] = task_id

                # Connect to start connector
                bpmn_graph.add_sequence_flow_to_diagram(process_id, start_connector, input_elements[input_id])
                active_flows[start_connector] = input_elements[input_id]
                input_positions[input_id] = (x_pos, y_pos)

    # Create decision tasks
    for level, decisions in sorted(decisions_by_level.items()):
        x_pos = 450 + level * x_spacing
        for i, decision_id in enumerate(decisions):
            decision_name = next((name for id_, name in dmn_model.decisions if id_ == decision_id), "Decision")
            y_pos = base_y + i * y_spacing

            task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Decide {decision_name}")
            bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "businessRuleTask"
            bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(x_pos)
            bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(y_pos)
            bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
            bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
            decision_tasks[decision_id] = task_id
            decision_positions[decision_id] = (x_pos, y_pos)

    # Map decisions to inputs
    decision_to_inputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if any(src == input_id for input_id, _ in dmn_model.input_data) and tgt in decision_tasks:
            decision_to_inputs[tgt].append(src)

    # Find paths between decisions
    decision_paths = {}
    for src_id, _ in dmn_model.decisions:
        for tgt_id, _ in dmn_model.decisions:
            for src, tgt in dmn_model.information_requirements:
                if src == src_id and tgt == tgt_id and src_id in decision_tasks and tgt_id in decision_tasks:
                    decision_paths[(src_id, tgt_id)] = (decision_positions[src_id], decision_positions[tgt_id])

    # Create non-starting inputs
    for input_id, input_name in dmn_model.input_data:
        if input_id not in start_inputs:
            # Find target decisions
            target_decisions = [tgt for src, tgt in dmn_model.information_requirements 
                               if src == input_id and tgt in decision_tasks]
            
            if target_decisions:
                target_id = target_decisions[0]
                target_element = decision_tasks[target_id]
                
                # Find source decisions
                source_decisions = [src for src, tgt in dmn_model.information_requirements 
                                   if tgt == target_id and src in decision_tasks]
                
                # Find insertion point
                insertion_src = None
                for src, tgt in active_flows.items():
                    if tgt == target_element:
                        insertion_src = src
                        break
                
                if not insertion_src and source_decisions:
                    insertion_src = decision_tasks[source_decisions[0]]
                
                # Create user task at appropriate position
                tgt_x = int(bpmn_graph.diagram_graph.node[target_element][consts.Consts.x])
                tgt_y = int(bpmn_graph.diagram_graph.node[target_element][consts.Consts.y])
                
                # Position the input task
                input_x = tgt_x - 150 if not insertion_src else tgt_x
                input_y = tgt_y
                
                # Create user task
                task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Provide {input_name}")
                bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
                bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(input_x)
                bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(input_y)
                bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
                bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
                input_elements[input_id] = task_id
                input_positions[input_id] = (input_x, input_y)
                
                # Shift target element if needed
                if insertion_src:
                    bpmn_graph.diagram_graph.node[target_element][consts.Consts.x] = str(tgt_x + 150)
                    
                    # Remove direct connection
                    for u, v in list(bpmn_graph.diagram_graph.edges()):
                        if u == insertion_src and v == target_element:
                            bpmn_graph.diagram_graph.remove_edge(u, v)
                    
                    # Add connections through input
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, insertion_src, task_id)
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, task_id, target_element)
                    
                    # Update active flows
                    active_flows[insertion_src] = task_id
                    active_flows[task_id] = target_element
                else:
                    # Connect directly to target
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, task_id, target_element)
                    active_flows[task_id] = target_element

    # Add gateways for decisions with multiple inputs
    gateway_targets = set()
    gateway_by_target = {}

    for decision_id, inputs in decision_to_inputs.items():
        if len(inputs) > 1:
            # Create gateway
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Join for {decision_id}")
            
            # Position gateway
            decision_x, decision_y = decision_positions[decision_id]
            gateway_x = decision_x - 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(decision_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"
            
            # Connect inputs to gateway
            for input_id in inputs:
                if input_id in input_elements:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, input_elements[input_id], gateway_id)
                    active_flows[input_elements[input_id]] = gateway_id
            
            # Connect gateway to decision
            bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[decision_id])
            active_flows[gateway_id] = decision_tasks[decision_id]
            
            gateway_targets.add(decision_id)
            gateway_by_target[decision_id] = gateway_id
        else:
            # Direct connection for single input
            for input_id in inputs:
                if input_id in input_elements:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, input_elements[input_id], decision_tasks[decision_id])
                    active_flows[input_elements[input_id]] = decision_tasks[decision_id]

    # Connect decisions to decisions
    decision_inputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if src in decision_tasks and tgt in decision_tasks:
            decision_inputs[tgt].append(src)

    # Add gateways for decisions with multiple decision inputs
    gateway_sources = defaultdict(set)
    for tgt, sources in decision_inputs.items():
        if len(sources) > 1:
            # Create gateway
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Join for {tgt}")
            
            # Position gateway
            tgt_x, tgt_y = decision_positions[tgt]
            gateway_x = tgt_x - 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(tgt_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"
            
            # Connect sources to gateway
            for src in sources:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], gateway_id)
                gateway_sources[gateway_id].add(src)
                active_flows[decision_tasks[src]] = gateway_id
            
            # Connect gateway to target
            bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[tgt])
            active_flows[gateway_id] = decision_tasks[tgt]
            
            gateway_targets.add(tgt)
            gateway_by_target[tgt] = gateway_id
        elif tgt not in gateway_targets:
            # Direct connection for single source
            for src in sources:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], decision_tasks[tgt])
                active_flows[decision_tasks[src]] = decision_tasks[tgt]

    # Handle decisions with multiple outputs
    decision_outputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if src in decision_tasks and tgt in decision_tasks:
            decision_outputs[src].append(tgt)

    # Add gateways for decisions with multiple outputs
    gateway_by_source = {}
    for src, targets in decision_outputs.items():
        if len(targets) > 1:
            # Create gateway
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Split for {src}")
            
            # Position gateway
            src_x, src_y = decision_positions[src]
            gateway_x = src_x + 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(src_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"
            
            # Connect source to gateway
            bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], gateway_id)
            active_flows[decision_tasks[src]] = gateway_id
            
            # Connect gateway to targets
            for tgt in targets:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[tgt])
                active_flows[gateway_id] = decision_tasks[tgt]
            
            gateway_by_source[src] = gateway_id

    # Find terminal decisions
    terminal_decisions = {decision_id for decision_id, _ in dmn_model.decisions 
                         if not any(src == decision_id for src, _ in dmn_model.information_requirements)}

    # Create data stores for business knowledge models
    max_level = max(decision_levels.values()) if decision_levels else 0
    
    # Find connections between business knowledge models and decisions
    knowledge_to_decisions = defaultdict(list)
    for src, tgt in dmn_model.knowledge_requirements:
        if src in [k_id for k_id, _ in dmn_model.business_knowledge] and tgt in decision_tasks:
            knowledge_to_decisions[src].append(tgt)
    
    # Place business knowledge models
    for i, (knowledge_id, knowledge_name) in enumerate(dmn_model.business_knowledge):
        # Position based on connected decisions or default position
        if knowledge_id in knowledge_to_decisions and knowledge_to_decisions[knowledge_id]:
            decision_id = knowledge_to_decisions[knowledge_id][0]
            if decision_id in decision_positions:
                x, y = decision_positions[decision_id]
                store_x = x - 150  # Left of the decision
                store_y = y + 80   # Below the decision
            else:
                store_x = 450 + (max_level + 1) * x_spacing
                store_y = base_y + i * y_spacing * 2
        else:
            store_x = 450 + (max_level + 1) * x_spacing
            store_y = base_y + i * y_spacing * 2
        
        # Create data store
        store_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=knowledge_name)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.type] = "dataStoreReference"
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.x] = str(store_x)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.y] = str(store_y)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.width] = "50"
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.height] = "50"
        knowledge_stores[knowledge_id] = store_id
    
    # Find connections between knowledge sources and decisions/knowledge models
    source_to_targets = defaultdict(list)
    for src, tgt in dmn_model.authority_requirements:
        if src in [s_id for s_id, _ in dmn_model.knowledge_sources]:
            if tgt in decision_tasks:
                source_to_targets[src].append(("decision", tgt))
            elif tgt in [k_id for k_id, _ in dmn_model.business_knowledge]:
                source_to_targets[src].append(("knowledge", tgt))
    
    # Create annotations for knowledge sources
    for i, (source_id, source_name) in enumerate(dmn_model.knowledge_sources):
        # Position based on connected elements or default position
        if source_id in source_to_targets and source_to_targets[source_id]:
            target_type, target_id = source_to_targets[source_id][0]
            if target_type == "decision" and target_id in decision_positions:
                x, y = decision_positions[target_id]
                anno_x = x + 150  # Right of the decision
                anno_y = y - 80   # Above the decision
            elif target_type == "knowledge" and target_id in knowledge_stores:
                store_id = knowledge_stores[target_id]
                store_x = int(bpmn_graph.diagram_graph.node[store_id][consts.Consts.x])
                store_y = int(bpmn_graph.diagram_graph.node[store_id][consts.Consts.y])
                anno_x = store_x + 150  # Right of the knowledge model
                anno_y = store_y - 80    # Above the knowledge model
            else:
                anno_x = 450 + (max_level + 2) * x_spacing
                anno_y = base_y + i * y_spacing * 2
        else:
            anno_x = 450 + (max_level + 2) * x_spacing
            anno_y = base_y + i * y_spacing * 2
        
        # Create text annotation
        annotation_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=source_name)
        bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.type] = "textAnnotation"
        bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.x] = str(anno_x)
        bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.y] = str(anno_y)
        bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.width] = "100"
        bpmn_graph.diagram_graph.node[annotation_id][consts.Consts.height] = "50"
        bpmn_graph.diagram_graph.node[annotation_id]["text"] = source_name
        knowledge_annotations[source_id] = annotation_id
    
    # Connect knowledge requirements
    for src, tgt in dmn_model.knowledge_requirements:
        if src in knowledge_stores and tgt in decision_tasks:
            bpmn_graph.add_sequence_flow_to_diagram(process_id, knowledge_stores[src], decision_tasks[tgt])
            active_flows[knowledge_stores[src]] = decision_tasks[tgt]
    
    # Connect authority requirements
    for src, tgt in dmn_model.authority_requirements:
        if src in knowledge_annotations:
            if tgt in decision_tasks:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, knowledge_annotations[src], decision_tasks[tgt])
                active_flows[knowledge_annotations[src]] = decision_tasks[tgt]
            elif tgt in knowledge_stores:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, knowledge_annotations[src], knowledge_stores[tgt])
                active_flows[knowledge_annotations[src]] = knowledge_stores[tgt]

    # Add end events for terminal decisions
    if terminal_decisions:
        if len(terminal_decisions) > 1:
            # Create join gateway
            end_gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name="Output Parallel Join")
            
            # Position gateway
            avg_x = sum(decision_positions[d][0] for d in terminal_decisions if d in decision_positions) / len(terminal_decisions)
            avg_y = sum(decision_positions[d][1] for d in terminal_decisions if d in decision_positions) / len(terminal_decisions)
            
            bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.x] = str(int(avg_x) + 100)
            bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.y] = str(int(avg_y))
            bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.height] = "50"
            
            # Connect terminal decisions to gateway
            for decision_id in terminal_decisions:
                if decision_id in decision_tasks:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[decision_id], end_gateway_id)
                    active_flows[decision_tasks[decision_id]] = end_gateway_id
            
            # Create end event
            end_id, _ = bpmn_graph.add_end_event_to_diagram(process_id, end_event_name="Decision Results Sent",
                                                          end_event_definition="message")
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(int(avg_x) + 200)
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(int(avg_y))
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.width] = "36"
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.height] = "36"
            
            # Connect gateway to end event
            bpmn_graph.add_sequence_flow_to_diagram(process_id, end_gateway_id, end_id)
            active_flows[end_gateway_id] = end_id

    # Remove redundant connections
    edges_to_remove = []
    for src_id, tgt_id in dmn_model.information_requirements:
        if src_id in decision_tasks and tgt_id in decision_tasks:
            src_task = decision_tasks[src_id]
            tgt_task = decision_tasks[tgt_id]
            
            # Check if there's a gateway path
            if (src_id in gateway_by_source or tgt_id in gateway_by_target):
                for u, v in bpmn_graph.diagram_graph.edges():
                    if u == src_task and v == tgt_task:
                        edges_to_remove.append((u, v))

    # Remove redundant edges
    for u, v in edges_to_remove:
        bpmn_graph.diagram_graph.remove_edge(u, v)

    return bpmn_graph