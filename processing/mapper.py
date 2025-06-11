from collections import defaultdict
from models.dmn_model import DMNModel
from bpmn_python.bpmn_diagram_rep import BpmnDiagramGraph
import bpmn_python.bpmn_python_consts as consts

# Keywords for element type detection
KEYWORDS_START_EVENT = ["received", "incoming", "message", "start", "trigger"]
KEYWORDS_DATA_STORES = ["database", "repository", "store", "storage"]
KEYWORDS_DATA_OBJECTS = ["document", "file", "data", "object", "record"]

def map_dmn_to_bpmn(dmn_model: DMNModel) -> BpmnDiagramGraph:
    """Maps a DMN model to a BPMN diagram following the algorithm."""
    bpmn_graph = BpmnDiagramGraph()
    bpmn_graph.create_new_diagram_graph(diagram_name="mapped_from_dmn")
    process_id = bpmn_graph.add_process_to_diagram()

    # Decision graph analysis
    # Calculate the level of each decision (distance from the beginning)
    decision_levels = {}
    decision_positions = {}
    input_positions = {}

    # Find starting decisions (without inputs from other decisions)
    start_decisions = set()
    for decision_id, _ in dmn_model.decisions:
        is_start = True
        for src, tgt in dmn_model.information_requirements:
            if tgt == decision_id and any(src == d_id for d_id, _ in dmn_model.decisions):
                is_start = False
                break
        if is_start:
            start_decisions.add(decision_id)
            decision_levels[decision_id] = 0

    # Calculate levels for all decisions
    def calculate_levels(node_id, level=0, visited=None):
        if visited is None:
            visited = set()

        if node_id in visited:
            return

        visited.add(node_id)
        decision_levels[node_id] = max(decision_levels.get(node_id, 0), level)

        # Find all nodes to which this node leads
        for src, tgt in dmn_model.information_requirements:
            if src == node_id:
                calculate_levels(tgt, level + 1, visited)

    for decision_id in start_decisions:
        calculate_levels(decision_id)

    # Find input data used by starting decisions
    start_inputs = set()
    for src, tgt in dmn_model.information_requirements:
        if tgt in start_decisions:
            for input_id, _ in dmn_model.input_data:
                if src == input_id:
                    start_inputs.add(input_id)

    # Element mapping
    input_elements = {}
    decision_tasks = {}
    knowledge_stores = {}
    knowledge_annotations = {}

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

    # Find which inputs lead to which decisions
    input_to_decision = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if any(src == input_id for input_id, _ in dmn_model.input_data):
            input_to_decision[src].append(tgt)

    # Calculate level for each input based on the decisions it leads to
    input_levels = {}
    for input_id, _ in dmn_model.input_data:
        if input_id in input_to_decision:
            min_level = min(decision_levels.get(tgt, 0) for tgt in input_to_decision[input_id])
            input_levels[input_id] = min_level
        else:
            input_levels[input_id] = 0

    # Create elements for input data with dynamic positioning
    inputs_by_level = defaultdict(list)
    for input_id, _ in dmn_model.input_data:
        level = input_levels.get(input_id, 0)
        inputs_by_level[level].append(input_id)

    # Create AND gateway after the start event if there is more than one input
    if len(start_inputs) > 1:
        split_gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name="Start Split")
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.x] = "170"
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.y] = str(base_y)
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.width] = "50"
        bpmn_graph.diagram_graph.node[split_gateway_id][consts.Consts.height] = "50"
        bpmn_graph.add_sequence_flow_to_diagram(process_id, start_id, split_gateway_id)
        start_connector = split_gateway_id
    else:
        start_connector = start_id

    # Create elements for input data
    # First create only starting inputs
    for level, inputs in sorted(inputs_by_level.items()):
        x_pos = 250 + level * x_spacing
        for i, input_id in enumerate(inputs):
            if input_id in start_inputs:
                input_name = next((name for id_, name in dmn_model.input_data if id_ == input_id), "Input")
                y_pos = base_y + i * y_spacing

                if any(keyword in input_name.lower() for keyword in KEYWORDS_START_EVENT):
                    # Create message type start event
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

                    # Connect to the start event or gateway
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, start_connector, event_id)
                else:
                    # Create user task
                    task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Provide {input_name}")
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(x_pos)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(y_pos)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
                    input_elements[input_id] = task_id

                    # Connect to the start event or gateway
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, start_connector, task_id)

                input_positions[input_id] = (x_pos, y_pos)

    # We don't create non-starting inputs yet - we'll do it later as intermediate elements

    # Create tasks for decisions with dynamic positioning
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

    # Find which decisions have multiple inputs
    decision_to_inputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if any(src == input_id for input_id, _ in dmn_model.input_data) and tgt in decision_tasks:
            decision_to_inputs[tgt].append(src)

    # Now we create non-starting inputs as intermediate elements on the path
    # First we need to find all paths between decisions
    decision_paths = {}

    # Function for finding paths between decisions
    def find_paths_between_decisions():
        for src_id, _ in dmn_model.decisions:
            for tgt_id, _ in dmn_model.decisions:
                for src, tgt in dmn_model.information_requirements:
                    if src == src_id and tgt == tgt_id:
                        if src_id in decision_tasks and tgt_id in decision_tasks:
                            src_pos = decision_positions[src_id]
                            tgt_pos = decision_positions[tgt_id]
                            decision_paths[(src_id, tgt_id)] = (src_pos, tgt_pos)

    find_paths_between_decisions()

    # Now for each non-starting input, find the path on which it should be placed
    for input_id, input_name in dmn_model.input_data:
        if input_id not in start_inputs:
            # Find the decision to which this input leads
            target_decisions = []
            for src, tgt in dmn_model.information_requirements:
                if src == input_id and tgt in decision_tasks:
                    target_decisions.append(tgt)

            if target_decisions:
                target_id = target_decisions[0]
                target_pos = decision_positions[target_id]

                # Find the decision that leads to this decision
                source_decisions = []
                for src, tgt in dmn_model.information_requirements:
                    if tgt == target_id and src in decision_tasks:
                        source_decisions.append(src)

                # If there is a path between decisions, place the input on that path
                if source_decisions:
                    source_id = source_decisions[0]
                    if (source_id, target_id) in decision_paths:
                        src_pos, tgt_pos = decision_paths[(source_id, target_id)]

                        # Place the input halfway between decisions
                        input_x = (src_pos[0] + tgt_pos[0]) // 2
                        input_y = (src_pos[1] + tgt_pos[1]) // 2

                        # Create a user task for the input
                        task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Provide {input_name}")
                        bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
                        bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(input_x)
                        bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(input_y)
                        bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
                        bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
                        input_elements[input_id] = task_id
                        input_positions[input_id] = (input_x, input_y)

                        # Remove direct connection between decisions
                        # (we can't remove it, so we'll ignore this connection later)

                        # Add connections through the input
                        bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[source_id], task_id)
                        bpmn_graph.add_sequence_flow_to_diagram(process_id, task_id, decision_tasks[target_id])
                else:
                    # If there is no decision leading to this decision, place the input before the decision
                    input_x = target_pos[0] - 150
                    input_y = target_pos[1]

                    # Create a user task for the input
                    task_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=f"Provide {input_name}")
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.type] = "userTask"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.x] = str(input_x)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.y] = str(input_y)
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.width] = "100"
                    bpmn_graph.diagram_graph.node[task_id][consts.Consts.height] = "80"
                    input_elements[input_id] = task_id
                    input_positions[input_id] = (input_x, input_y)

                    # Connect the input to the decision
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, task_id, decision_tasks[target_id])

    # Add AND gateways for decisions with multiple inputs
    gateway_targets = set()  # Set of targets that have gateways

    for decision_id, inputs in decision_to_inputs.items():
        if len(inputs) > 1:
            # Create an AND gateway before the decision
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Join for {decision_id}")

            # Set the position of the gateway
            decision_x, decision_y = decision_positions[decision_id]
            gateway_x = decision_x - 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(decision_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"

            # Connect inputs to the gateway
            for input_id in inputs:
                if input_id in input_elements:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, input_elements[input_id], gateway_id)

            # Connect the gateway to the decision
            bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[decision_id])

            # Remember that this target has a gateway
            gateway_targets.add(decision_id)
        else:
            # Only one input, connect directly
            for input_id in inputs:
                if input_id in input_elements:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, input_elements[input_id], decision_tasks[decision_id])

    # Find decisions with multiple inputs from other decisions
    decision_inputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if src in decision_tasks and tgt in decision_tasks:
            decision_inputs[tgt].append(src)

    # Add AND gateways for decisions with multiple inputs from other decisions
    gateway_sources = defaultdict(set)  # Sources for each gateway
    gateway_by_target = {}  # Gateway for each target

    for tgt, sources in decision_inputs.items():
        if len(sources) > 1:
            # Create an AND gateway
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Join for {tgt}")

            # Set the position of the gateway
            tgt_x, tgt_y = decision_positions[tgt]
            gateway_x = tgt_x - 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(tgt_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"

            # Connect sources to the gateway
            for src in sources:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], gateway_id)
                gateway_sources[gateway_id].add(src)

            # Connect the gateway to the target
            bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[tgt])

            # Remember that this target has a gateway
            gateway_targets.add(tgt)
            gateway_by_target[tgt] = gateway_id
        else:
            # Single connection - only if the target does not already have a gateway
            if tgt not in gateway_targets:
                for src in sources:
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], decision_tasks[tgt])

    # Find decisions with multiple outputs
    decision_outputs = defaultdict(list)
    for src, tgt in dmn_model.information_requirements:
        if src in decision_tasks and tgt in decision_tasks:
            decision_outputs[src].append(tgt)

    # Add AND gateways for decisions with multiple outputs
    gateway_targets_by_source = defaultdict(set)  # Targets for each output gateway
    gateway_by_source = {}  # Gateway for each source

    for src, targets in decision_outputs.items():
        if len(targets) > 1:
            # Create an AND gateway
            gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name=f"Split for {src}")

            # Set the position of the gateway
            src_x, src_y = decision_positions[src]
            gateway_x = src_x + 100
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.x] = str(gateway_x)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.y] = str(src_y)
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.width] = "50"
            bpmn_graph.diagram_graph.node[gateway_id][consts.Consts.height] = "50"

            # Connect the source to the gateway
            bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[src], gateway_id)

            # Connect the gateway to the targets
            for tgt in targets:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, gateway_id, decision_tasks[tgt])
                gateway_targets_by_source[gateway_id].add(tgt)

            # Remember the gateway for this source
            gateway_by_source[src] = gateway_id

    # Find terminal decisions (without outputs)
    terminal_decisions = set()
    for decision_id, _ in dmn_model.decisions:
        is_terminal = True
        for src, _ in dmn_model.information_requirements:
            if src == decision_id:
                is_terminal = False
                break
        if is_terminal:
            terminal_decisions.add(decision_id)

    # Create data stores for business knowledge models
    max_level = max(decision_levels.values()) if decision_levels else 0

    # Find connections between business knowledge models and decisions
    knowledge_to_decisions = defaultdict(list)
    for src, tgt in dmn_model.knowledge_requirements:
        if src in [k_id for k_id, _ in dmn_model.business_knowledge] and tgt in decision_tasks:
            knowledge_to_decisions[src].append(tgt)

    # Place business knowledge models next to the decisions they are connected to
    for i, (knowledge_id, knowledge_name) in enumerate(dmn_model.business_knowledge):
        # If the knowledge model is connected to decisions, place it next to the first one
        if knowledge_id in knowledge_to_decisions and knowledge_to_decisions[knowledge_id]:
            connected_decisions = knowledge_to_decisions[knowledge_id]
            decision_id = connected_decisions[0]
            if decision_id in decision_positions:
                x, y = decision_positions[decision_id]
                store_x = x - 150  # Place to the left of the decision
                store_y = y + 80  # Place slightly below the decision to avoid overlap
            else:
                store_x = 450 + (max_level + 1) * x_spacing
                store_y = base_y + i * y_spacing * 2  # Increase spacing to avoid overlap
        else:
            # If there are no connections, place in the default position
            store_x = 450 + (max_level + 1) * x_spacing
            store_y = base_y + i * y_spacing * 2  # Increase spacing to avoid overlap

        store_id, _ = bpmn_graph.add_task_to_diagram(process_id, task_name=knowledge_name)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.type] = "dataStoreReference"
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.x] = str(store_x)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.y] = str(store_y)
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.width] = "50"
        bpmn_graph.diagram_graph.node[store_id][consts.Consts.height] = "50"
        knowledge_stores[knowledge_id] = store_id

    # Find connections between knowledge sources and decisions or knowledge models
    source_to_targets = defaultdict(list)
    for src, tgt in dmn_model.authority_requirements:
        if src in [s_id for s_id, _ in dmn_model.knowledge_sources]:
            if tgt in decision_tasks:
                source_to_targets[src].append(("decision", tgt))
            elif tgt in [k_id for k_id, _ in dmn_model.business_knowledge]:
                source_to_targets[src].append(("knowledge", tgt))

    # Create annotations for knowledge sources
    for i, (source_id, source_name) in enumerate(dmn_model.knowledge_sources):
        # If the knowledge source is connected to decisions or knowledge models, place it next to them
        if source_id in source_to_targets and source_to_targets[source_id]:
            target_type, target_id = source_to_targets[source_id][0]
            if target_type == "decision" and target_id in decision_positions:
                x, y = decision_positions[target_id]
                anno_x = x + 150  # Place to the right of the decision
                anno_y = y - 80  # Place slightly above the decision to avoid overlap
            elif target_type == "knowledge" and target_id in knowledge_stores:
                store_id = knowledge_stores[target_id]
                store_x = int(bpmn_graph.diagram_graph.node[store_id][consts.Consts.x])
                store_y = int(bpmn_graph.diagram_graph.node[store_id][consts.Consts.y])
                anno_x = store_x + 150  # Place to the right of the knowledge model
                anno_y = store_y - 80  # Place slightly above the knowledge model
            else:
                anno_x = 450 + (max_level + 2) * x_spacing
                anno_y = base_y + i * y_spacing * 2  # Increase spacing to avoid overlap
        else:
            # If there are no connections, place in the default position
            anno_x = 450 + (max_level + 2) * x_spacing
            anno_y = base_y + i * y_spacing * 2  # Increase spacing to avoid overlap

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

    # Connect authority requirements
    for src, tgt in dmn_model.authority_requirements:
        if src in knowledge_annotations:
            if tgt in decision_tasks:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, knowledge_annotations[src], decision_tasks[tgt])
            elif tgt in knowledge_stores:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, knowledge_annotations[src], knowledge_stores[tgt])

    # Remove redundant connections when gateways exist
    # Create a list of all sequence flows
    all_flows = []
    for flow in bpmn_graph.get_flows():
        if len(flow) >= 2:
            all_flows.append((flow[0], flow[1]))

    # Find and remove redundant connections
    flows_to_remove = []

    # Check connections between decisions
    for src_id, tgt_id in dmn_model.information_requirements:
        if src_id in decision_tasks and tgt_id in decision_tasks:
            src_task = decision_tasks[src_id]
            tgt_task = decision_tasks[tgt_id]

            # Check if there is an output gateway for the source
            if src_id in gateway_by_source:
                gateway_id = gateway_by_source[src_id]
                # If the target is one of the gateway's targets, the direct connection is redundant
                if tgt_id in gateway_targets_by_source[gateway_id]:
                    flows_to_remove.append((src_task, tgt_task))

            # Check if there is an input gateway for the target
            if tgt_id in gateway_by_target:
                gateway_id = gateway_by_target[tgt_id]
                # If the source is one of the gateway's sources, the direct connection is redundant
                if src_id in gateway_sources[gateway_id]:
                    flows_to_remove.append((src_task, tgt_task))

    # Add end events for terminal decisions
    if len(terminal_decisions) > 1:
        # Create a join gateway for terminal decisions
        end_gateway_id, _ = bpmn_graph.add_parallel_gateway_to_diagram(process_id, gateway_name="Output Parallel Join")

        # Find the average position for the gateway
        avg_x = sum(decision_positions[d][0] for d in terminal_decisions if d in decision_positions) / len(
            terminal_decisions)
        avg_y = sum(decision_positions[d][1] for d in terminal_decisions if d in decision_positions) / len(
            terminal_decisions)

        bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.x] = str(int(avg_x) + 100)
        bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.y] = str(int(avg_y))
        bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.width] = "50"
        bpmn_graph.diagram_graph.node[end_gateway_id][consts.Consts.height] = "50"

        # Connect terminal decisions to the gateway
        for decision_id in terminal_decisions:
            if decision_id in decision_tasks:
                bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[decision_id], end_gateway_id)

        # Create an end event
        end_id, _ = bpmn_graph.add_end_event_to_diagram(process_id, end_event_name="Decision Results Sent",
                                                        end_event_definition="message")
        bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(int(avg_x) + 200)
        bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(int(avg_y))
        bpmn_graph.diagram_graph.node[end_id][consts.Consts.width] = "36"
        bpmn_graph.diagram_graph.node[end_id][consts.Consts.height] = "36"

        # Connect the gateway to the end event
        bpmn_graph.add_sequence_flow_to_diagram(process_id, end_gateway_id, end_id)
    else:
        # Single terminal decision
        if terminal_decisions:
            decision_id = next(iter(terminal_decisions))
            if decision_id in decision_tasks:
                decision_name = next((name for d_id, name in dmn_model.decisions if d_id == decision_id), "Decision")
                end_id, _ = bpmn_graph.add_end_event_to_diagram(process_id, end_event_name=f"{decision_name} sent",
                                                                end_event_definition="message")

                # Set the position of the end event
                if decision_id in decision_positions:
                    x, y = decision_positions[decision_id]
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(int(x) + 150)
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(y)
                else:
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(450 + (max_level + 1) * x_spacing)
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(base_y)

                bpmn_graph.diagram_graph.node[end_id][consts.Consts.width] = "36"
                bpmn_graph.diagram_graph.node[end_id][consts.Consts.height] = "36"
                bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[decision_id], end_id)
        else:
            # No terminal decisions, create a default end event
            end_id, _ = bpmn_graph.add_end_event_to_diagram(process_id, end_event_name="Process End")
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(450 + (max_level + 1) * x_spacing)
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(base_y)
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.width] = "36"
            bpmn_graph.diagram_graph.node[end_id][consts.Consts.height] = "36"

            # Connect all decision tasks to the end event
            for task_id in decision_tasks.values():
                bpmn_graph.add_sequence_flow_to_diagram(process_id, task_id, end_id)

    # Add end events for cases where two objects exit one and enter another
    source_to_targets = defaultdict(list)
    target_to_sources = defaultdict(list)

    for src, tgt in dmn_model.information_requirements:
        if src in decision_tasks and tgt in decision_tasks:
            source_to_targets[src].append(tgt)
            target_to_sources[tgt].append(src)

    for target, sources in target_to_sources.items():
        if len(sources) >= 2:
            common_sources = set()
            for src in sources:
                if src in target_to_sources and len(target_to_sources[src]) > 0:
                    common_sources.update(target_to_sources[src])

            if common_sources:
                if target in decision_tasks:
                    end_id, _ = bpmn_graph.add_end_event_to_diagram(
                        process_id,
                        end_event_name=f"End after {target}",
                        end_event_definition="terminate"
                    )
                    
                    if target in decision_positions:
                        x, y = decision_positions[target]
                        bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(int(x) + 150)
                        bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(y)
                    else:
                        bpmn_graph.diagram_graph.node[end_id][consts.Consts.x] = str(450 + (max_level + 1) * x_spacing)
                        bpmn_graph.diagram_graph.node[end_id][consts.Consts.y] = str(base_y)
                    
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.width] = "36"
                    bpmn_graph.diagram_graph.node[end_id][consts.Consts.height] = "36"
                    bpmn_graph.add_sequence_flow_to_diagram(process_id, decision_tasks[target], end_id)
    
    return bpmn_graph