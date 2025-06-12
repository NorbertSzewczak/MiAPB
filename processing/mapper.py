from collections import defaultdict
from models.dmn_model import DMNModel
from models.bpmn_model import BPMN
import bpmn_python.bpmn_python_consts as consts

# Keywords for element type detection
KEYWORDS_START_EVENT = ["received", "incoming", "message", "start", "trigger"]
KEYWORDS_DATA_STORES = ["database", "repository", "store", "storage"]
KEYWORDS_DATA_OBJECTS = ["document", "file", "data", "object", "record"]
KEYWORDS_SUMATOR = ["sumator", "join", "merge", "combine"]
KEYWORDS_USER_TASK = ["user", "task", "input", "provide"]


def map_dmn_to_bpmn(dmn_model: DMNModel) -> BPMN:
    """Maps a DMN model to a BPMN diagram following the algorithm."""
    bpmn = BPMN(diagram_name="mapped_from_dmn")

    # Initialize tracking dictionaries
    decision_levels = {}
    decision_positions = {}
    input_positions = {}
    input_elements = {}
    decision_tasks = {}
    knowledge_stores = {}
    knowledge_annotations = {}
    input_sumators = {}  # Track sumators for inputs with multiple targets
    decision_sumators = {}  # Track sumators for decisions with multiple inputs
    output_sumators = {}  # Track sumators for decisions with multiple outputs
    user_tasks = {}  # Track user tasks by their target decision
    connections = []  # Track connections to be made

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

    # Map inputs to decisions and decisions to inputs
    input_to_decision = defaultdict(list)
    decision_to_inputs = defaultdict(list)
    decision_to_decisions = defaultdict(list)

    for src, tgt in dmn_model.information_requirements:
        if any(src == input_id for input_id, _ in dmn_model.input_data):
            input_to_decision[src].append(tgt)
            decision_to_inputs[tgt].append(src)

        elif any(src == decision_id for decision_id, _ in dmn_model.decisions):
            decision_to_decisions[src].append(tgt)
            
    # Find inputs with multiple targets
    inputs_with_multiple_targets = {
        input_id for input_id, targets in input_to_decision.items() 
        if len(targets) > 1
    }
    
    # Count incoming connections for each decision
    decision_incoming_count = {}
    for decision_id, _ in dmn_model.decisions:
        count = 0
        for src, tgt in dmn_model.information_requirements:
            if tgt == decision_id:
                count += 1
        decision_incoming_count[decision_id] = count
    
    # Count outgoing connections for each decision
    decision_outgoing_count = {}
    for decision_id, _ in dmn_model.decisions:
        count = 0
        for src, tgt in dmn_model.information_requirements:
            if src == decision_id:
                count += 1
        decision_outgoing_count[decision_id] = count

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

    # STEP 1: Create start event
    start_id = bpmn.create_start_event("Process Start", 100, base_y)
    
    # STEP 2: Create gateway if multiple start inputs
    start_connector = start_id
    if len(start_inputs) > 1:
        split_gateway_id = bpmn.create_parallel_gateway("Start Split", 170, base_y)
        connections.append((start_id, split_gateway_id))
        start_connector = split_gateway_id

    # STEP 3: Create starting input elements
    for level, inputs in sorted(inputs_by_level.items()):
        x_pos = 250 + level * x_spacing
        for i, input_id in enumerate(inputs):
            if input_id in start_inputs:
                input_name = next((name for id_, name in dmn_model.input_data if id_ == input_id), "Input")
                y_pos = base_y + i * y_spacing

                if any(keyword in input_name.lower() for keyword in KEYWORDS_START_EVENT):
                    # Create message start event
                    event_id = bpmn.create_start_event(
                        f"{input_name} received",
                        x_pos,
                        y_pos,
                        event_definition="message"
                    )
                    input_elements[input_id] = event_id
                else:
                    # Create user task
                    task_id = bpmn.create_user_task(f"Provide {input_name}", x_pos, y_pos)
                    input_elements[input_id] = task_id

                # Connect to start connector
                connections.append((start_connector, input_elements[input_id]))
                input_positions[input_id] = (x_pos, y_pos)
                
                # If this input has multiple targets, create a split gateway
                if input_id in inputs_with_multiple_targets:
                    split_x = x_pos + 100
                    split_y = y_pos
                    split_id = bpmn.create_parallel_gateway(f"Split for {input_name}", split_x, split_y)
                    connections.append((input_elements[input_id], split_id))
                    input_sumators[input_id] = split_id
                    
                    # Connect split gateway directly to each target decision
                    for target_id in input_to_decision[input_id]:
                        if target_id in decision_tasks:
                            if target_id in decision_sumators:
                                connections.append((split_id, decision_sumators[target_id]))
                            else:
                                connections.append((split_id, decision_tasks[target_id]))
                # If input has only one target, connect it directly to the target decision
                elif input_to_decision[input_id]:
                    target_id = input_to_decision[input_id][0]
                    if target_id in decision_tasks:
                        if target_id in decision_sumators:
                            connections.append((input_elements[input_id], decision_sumators[target_id]))
                        else:
                            connections.append((input_elements[input_id], decision_tasks[target_id]))

    # STEP 4: Create decision tasks
    for level, decisions in sorted(decisions_by_level.items()):
        x_pos = 450 + level * x_spacing
        for i, decision_id in enumerate(decisions):
            decision_name = next((name for id_, name in dmn_model.decisions if id_ == decision_id), "Decision")
            y_pos = base_y + i * y_spacing
            
            # Create the decision task
            task_id = bpmn.create_business_rule_task(f"Decide {decision_name}", x_pos, y_pos)
            decision_tasks[decision_id] = task_id
            decision_positions[decision_id] = (x_pos, y_pos)

    # STEP 5: Create sumators for decisions with multiple inputs
    for decision_id, count in decision_incoming_count.items():
        if count > 1:
            decision_pos = decision_positions[decision_id]
            sumator_x = decision_pos[0] - 100
            sumator_y = decision_pos[1]
            sumator_id = bpmn.create_parallel_gateway(f"Join for {decision_id}", sumator_x, sumator_y)
            decision_sumators[decision_id] = sumator_id

    # STEP 6: Create sumators for decisions with multiple outputs
    for decision_id, count in decision_outgoing_count.items():
        if count > 1:
            decision_pos = decision_positions[decision_id]
            sumator_x = decision_pos[0] + 100
            sumator_y = decision_pos[1]
            sumator_id = bpmn.create_parallel_gateway(f"Split for {decision_id}", sumator_x, sumator_y)
            output_sumators[decision_id] = sumator_id
            connections.append((decision_tasks[decision_id], sumator_id))

    # STEP 7: Create user tasks for each input-decision pair
    # Track which inputs have already been processed to avoid duplication
    processed_inputs = set()
    
    for input_id, input_name in dmn_model.input_data:
        target_decisions = input_to_decision[input_id]
        
        # Skip if this input has already been processed and has only one target
        if input_id in processed_inputs and len(target_decisions) == 1:
            continue
            
        # For each target decision, create a user task if needed
        for target_id in target_decisions:
            if target_id in decision_tasks:
                # Create a key for this input-decision pair
                pair_key = (input_id, target_id)
                
                # Skip if this input has only one target and we've already created a direct connection
                if len(target_decisions) == 1 and input_id in input_elements:
                    # Don't create additional user task, just use the existing input element
                    user_tasks[pair_key] = input_elements[input_id]
                    processed_inputs.add(input_id)
                    continue
                
                # Get target position
                target_pos = decision_positions[target_id]
                
                # Determine user task position
                if target_id in decision_sumators:
                    # Place user task between sumator and decision
                    sumator_pos = (target_pos[0] - 100, target_pos[1])
                    task_x = sumator_pos[0] + 50
                    task_y = sumator_pos[1]
                else:
                    # Place user task directly before decision
                    task_x = target_pos[0] - 100
                    task_y = target_pos[1]
                
                # Create the user task
                task_id = bpmn.create_user_task(f"Provide {input_name}", task_x, task_y)
                user_tasks[pair_key] = task_id
                processed_inputs.add(input_id)
                
                # Store connections to be made later
                if target_id in decision_sumators:
                    connections.append((decision_sumators[target_id], task_id))
                    connections.append((task_id, decision_tasks[target_id]))
                else:
                    connections.append((task_id, decision_tasks[target_id]))

    # STEP 8: Connect inputs to user tasks
    for input_id in input_elements:
        target_decisions = input_to_decision[input_id]
        
        # If this input has multiple targets and a sumator
        if input_id in inputs_with_multiple_targets and input_id in input_sumators:
            source = input_sumators[input_id]
        else:
            source = input_elements[input_id]
        
        # Connect to each target's user task
        for target_id in target_decisions:
            pair_key = (input_id, target_id)
            if pair_key in user_tasks:
                connections.append((source, user_tasks[pair_key]))

    # STEP 9: Connect decisions to decisions
    # First collect all user task connections to identify paths through user tasks
    user_task_paths = []
    for input_id, input_name in dmn_model.input_data:
        for src_decision in decision_to_decisions:
            for tgt_decision in decision_to_decisions[src_decision]:
                # Check if this input connects these two decisions through a user task
                if input_id in decision_to_inputs.get(tgt_decision, []) and \
                   (input_id, tgt_decision) in user_tasks and \
                   src_decision in input_to_decision.get(input_id, []):
                    user_task_paths.append((src_decision, tgt_decision))
    
    # Now connect decisions to decisions, avoiding duplicates
    for src_id, target_ids in decision_to_decisions.items():
        # Get the source element (either the decision or its output sumator)
        if src_id in output_sumators:
            source = output_sumators[src_id]
        else:
            source = decision_tasks[src_id]
        
        # Connect to each target
        for tgt_id in target_ids:
            # Skip if there's already a path through a user task
            if (src_id, tgt_id) in user_task_paths:
                continue
                
            # Check if there's a user task for any input to this target
            has_user_task = False
            for input_id in decision_to_inputs.get(tgt_id, []):
                pair_key = (input_id, tgt_id)
                if pair_key in user_tasks:
                    has_user_task = True
                    break
            
            # If target has a sumator, connect to it
            if tgt_id in decision_sumators:
                connections.append((source, decision_sumators[tgt_id]))
            # If target has no user task, connect directly
            elif not has_user_task:
                connections.append((source, decision_tasks[tgt_id]))

    # STEP 10: Create knowledge sources and annotations
    for knowledge_id, knowledge_name in dmn_model.knowledge_sources:
        # Find related decisions
        related_decisions = []
        for src, tgt in dmn_model.authority_requirements:
            if src == knowledge_id:
                for decision_id, _ in dmn_model.decisions:
                    if tgt == decision_id and decision_id in decision_tasks:
                        related_decisions.append(decision_id)
        
        if related_decisions:
            # Use the position of the first related decision to place this knowledge source
            decision_id = related_decisions[0]
            decision_pos = decision_positions[decision_id]
            knowledge_x = decision_pos[0]
            knowledge_y = decision_pos[1] - 150
            
            # Create text annotation
            annotation_id = bpmn.create_text_annotation(knowledge_name, knowledge_x, knowledge_y)
            knowledge_annotations[knowledge_id] = annotation_id
            
            # Connect to related decisions
            for decision_id in related_decisions:
                bpmn.create_association(annotation_id, decision_tasks[decision_id])

    # STEP 11: Create business knowledge models
    for knowledge_id, knowledge_name in dmn_model.business_knowledge:
        # Find related decisions
        related_decisions = []
        for src, tgt in dmn_model.knowledge_requirements:
            if src == knowledge_id:
                for decision_id, _ in dmn_model.decisions:
                    if tgt == decision_id and decision_id in decision_tasks:
                        related_decisions.append(decision_id)
        
        if related_decisions:
            # Use the position of the first related decision to place this knowledge model
            decision_id = related_decisions[0]
            decision_pos = decision_positions[decision_id]
            knowledge_x = decision_pos[0] + 150
            knowledge_y = decision_pos[1] - 100
            
            # Create data store
            store_id = bpmn.create_data_store(knowledge_name, knowledge_x, knowledge_y)
            knowledge_stores[knowledge_id] = store_id
            
            # Connect to related decisions
            for decision_id in related_decisions:
                bpmn.create_data_association(store_id, decision_tasks[decision_id])

    # STEP 12: Create end event if there are terminal decisions
    terminal_decisions = []
    for decision_id in decision_tasks:
        if not any(src == decision_id for src, _ in dmn_model.information_requirements):
            terminal_decisions.append(decision_id)
    
    if terminal_decisions:
        if len(terminal_decisions) == 1:
            # Single end event
            decision_id = terminal_decisions[0]
            decision_pos = decision_positions[decision_id]
            
            # Check if the decision has an output sumator
            if decision_id in output_sumators:
                end_x = decision_pos[0] + 200  # Position after the output sumator
                end_y = decision_pos[1]
                end_id = bpmn.create_end_event("Process End", end_x, end_y)
                connections.append((output_sumators[decision_id], end_id))
            else:
                end_x = decision_pos[0] + 150
                end_y = decision_pos[1]
                end_id = bpmn.create_end_event("Process End", end_x, end_y)
                connections.append((decision_tasks[decision_id], end_id))
        else:
            # Multiple end events need a join gateway
            join_x = max(decision_positions[d][0] for d in terminal_decisions) + 150
            join_y = sum(decision_positions[d][1] for d in terminal_decisions) // len(terminal_decisions)
            
            join_id = bpmn.create_parallel_gateway("End Join", join_x, join_y)
            
            # Connect terminal decisions to join
            for decision_id in terminal_decisions:
                if decision_id in output_sumators:
                    connections.append((output_sumators[decision_id], join_id))
                else:
                    connections.append((decision_tasks[decision_id], join_id))
            
            # Create end event after join
            end_id = bpmn.create_end_event("Process End", join_x + 100, join_y)
            connections.append((join_id, end_id))

    # Verify all elements have proper connections
    incoming_connections = defaultdict(list)
    outgoing_connections = defaultdict(list)
    
    for source, target in connections:
        outgoing_connections[source].append(target)
        incoming_connections[target].append(source)
    
    # Check all elements for missing connections
    all_elements = set()
    all_elements.update(input_elements.values())
    all_elements.update(decision_tasks.values())
    all_elements.update(input_sumators.values())
    all_elements.update(decision_sumators.values())
    
    # Specifically check sumator to decision connections
    for decision_id, sumator_id in decision_sumators.items():
        if decision_id in decision_tasks:
            # Check if sumator is connected to its decision
            if decision_tasks[decision_id] not in outgoing_connections.get(sumator_id, []):
                connections.append((sumator_id, decision_tasks[decision_id]))
    
    for element_id in all_elements:
        # Skip start events for incoming connections check
        is_start_event = any(element_id == input_elements[input_id] for input_id in input_elements 
                            if any(keyword in next((name for id_, name in dmn_model.input_data if id_ == input_id), "") 
                                  for keyword in KEYWORDS_START_EVENT))
        
        # Skip end events for outgoing connections check
        is_end_event = False  # We don't have a direct way to check this, but we can assume no end events in this check
        
        # If element has no outgoing connections and is not an end event
        if not outgoing_connections.get(element_id) and not is_end_event:
            # Find a suitable target
            if any(element_id == input_elements[input_id] for input_id in input_elements):
                # This is an input element, connect to its target decision
                input_id = next(id_ for id_ in input_elements if input_elements[id_] == element_id)
                for target_id in input_to_decision.get(input_id, []):
                    if target_id in decision_tasks:
                        if target_id in decision_sumators:
                            connections.append((element_id, decision_sumators[target_id]))
                        else:
                            connections.append((element_id, decision_tasks[target_id]))
                        break
            
        # If element has no incoming connections and is not a start event
        if not incoming_connections.get(element_id) and not is_start_event:
            # This is likely a decision sumator that needs connections from its inputs
            for decision_id, sumator_id in decision_sumators.items():
                if element_id == sumator_id:
                    # Connect inputs to this sumator
                    for input_id in decision_to_inputs.get(decision_id, []):
                        if input_id in input_elements:
                            if input_id in input_sumators:
                                connections.append((input_sumators[input_id], element_id))
                            else:
                                connections.append((input_elements[input_id], element_id))
                    break
    
    # STEP 13: Create all sequence flows
    for source, target in connections:
        bpmn.create_sequence_flow(source, target)

    return bpmn