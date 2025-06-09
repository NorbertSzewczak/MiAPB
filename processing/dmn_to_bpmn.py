"""
Moduł implementujący algorytm mapowania DMN na BPMN zgodnie z artykułem.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path

# Słowniki słów kluczowych zgodnie z artykułem
VERB_DECIDE = ['approve', 'choose', 'decide', 'determine', 'evaluate', 'review']
VERB_CALCULATE = ['calculate', 'compute', 'derive', 'estimate', 'price', 'solve']
KEYWORDS_DATA_STORES = ['DB', 'archive', 'backup', 'base', 'repository', 'store']
KEYWORDS_DATA_OBJECTS = ['contract', 'data', 'document', 'file', 'note', 'object']
KEYWORDS_START_EVENT = ['booking', 'call', 'claim', 'inquiry', 'order', 'request']

def refine_dmn_model(dmn_model):
    """
    Tymczasowo przetwarza model DMN usuwając redundantne wymagania informacyjne.
    
    Args:
        dmn_model (DMNModel): Model DMN do przetworzenia
        
    Returns:
        DMNModel: Przetworzony model DMN
    """
    # Tworzymy kopię modelu DMN
    refined_model = type(dmn_model)()
    
    # Kopiowanie elementów
    for decision_id, decision_name in dmn_model.decisions:
        refined_model.add_decision(decision_id, decision_name)
    
    for input_id, input_name in dmn_model.input_data:
        refined_model.add_input_data(input_id, input_name)
    
    for bkm_id, bkm_name in dmn_model.business_knowledge:
        refined_model.add_business_knowledge(bkm_id, bkm_name)
    
    for ks_id, ks_name in dmn_model.knowledge_sources:
        refined_model.add_knowledge_source(ks_id, ks_name)
    
    # Identyfikacja redundantnych wymagań
    redundant_requirements = dmn_model.find_redundant_requirements()
    
    # Kopiowanie niezbędnych wymagań informacyjnych
    for src, tgt in dmn_model.information_requirements:
        if (src, tgt) not in redundant_requirements:
            refined_model.add_information_requirement(src, tgt)
    
    # Kopiowanie pozostałych relacji
    for src, tgt in dmn_model.knowledge_requirements:
        refined_model.add_knowledge_requirement(src, tgt)
    
    for src, tgt in dmn_model.authority_requirements:
        refined_model.add_authority_requirement(src, tgt)
    
    # Kopiowanie tabel decyzyjnych
    for decision_id, table in dmn_model.decision_tables.items():
        refined_model.add_decision_table(decision_id, table)
    
    return refined_model

def get_output_type(decision_table):
    """
    Określa typ wyjściowy tabeli decyzyjnej.
    
    Args:
        decision_table: Tabela decyzyjna
        
    Returns:
        str: Typ wyjściowy (number, boolean, string, enum)
    """
    if decision_table is None:
        return None
    
    # Sprawdzenie typu na podstawie wartości w regułach
    for rule in decision_table.rules:
        for output_expr in decision_table.output_expressions:
            if output_expr in rule:
                value = rule[output_expr]
                if value is None:
                    continue
                
                # Usunięcie cudzysłowów i spacji
                value = value.strip().strip('"\'')
                
                # Sprawdzenie typu
                try:
                    float(value)
                    return "number"
                except ValueError:
                    if value.lower() in ['true', 'false']:
                        return "boolean"
                    else:
                        # Zakładamy, że jeśli nie jest liczbą ani wartością logiczną, to jest enum lub string
                        return "enum"
    
    return "string"  # Domyślny typ

def create_bpmn_from_dmn(dmn_model, output_path=None):
    """
    Tworzy model BPMN na podstawie modelu DMN.
    
    Args:
        dmn_model (DMNModel): Model DMN
        output_path (str): Ścieżka do pliku wyjściowego
        
    Returns:
        str: Ścieżka do wygenerowanego pliku BPMN
    """
    # Przetworzenie modelu DMN
    refined_model = refine_dmn_model(dmn_model)
    
    # Utworzenie korzenia dokumentu BPMN
    bpmn_root = ET.Element('definitions')
    bpmn_root.set('xmlns', 'http://www.omg.org/spec/BPMN/20100524/MODEL')
    bpmn_root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
    bpmn_root.set('xmlns:bpmn', 'http://www.omg.org/spec/BPMN/20100524/MODEL')
    bpmn_root.set('xmlns:bpmndi', 'http://www.omg.org/spec/BPMN/20100524/DI')
    bpmn_root.set('xmlns:dc', 'http://www.omg.org/spec/DD/20100524/DC')
    bpmn_root.set('xmlns:di', 'http://www.omg.org/spec/DD/20100524/DI')
    bpmn_root.set('id', 'Definitions_1')
    bpmn_root.set('targetNamespace', 'http://activiti.org/bpmn')
    
    # Utworzenie procesu
    process = ET.SubElement(bpmn_root, 'process')
    process.set('id', 'Process_1')
    process.set('isExecutable', 'true')
    
    # Informacje o elementach dla wizualizacji
    elements_info = []
    x_position = 180
    y_position = 100
    
    # Identyfikacja elementów początkowych
    start_decisions = refined_model.get_start_decisions()
    start_inputs = []
    
    # Znajdź dane wejściowe używane przez początkowe decyzje
    for decision_id, _ in start_decisions:
        for src, tgt in refined_model.information_requirements:
            if tgt == decision_id:
                for input_id, input_name in refined_model.input_data:
                    if src == input_id:
                        start_inputs.append((input_id, input_name))
    
    # Dodaj zdarzenie początkowe
    start_event_id = None
    for input_id, input_name in start_inputs:
        # Sprawdź czy nazwa zawiera słowo kluczowe dla zdarzenia początkowego
        if any(keyword.lower() in input_name.lower() for keyword in KEYWORDS_START_EVENT):
            start_event = ET.SubElement(process, 'startEvent')
            start_event_id = f"StartEvent_{input_id}"
            start_event.set('id', start_event_id)
            start_event.set('name', f"{input_name} received")
            
            elements_info.append({
                'id': start_event_id,
                'element_type': 'startEvent',
                'x': x_position,
                'y': y_position
            })
            
            last_id = start_event_id
            last_x = x_position + 36
            x_position += 100
            break
    
    # Jeśli nie znaleziono zdarzenia początkowego, utwórz domyślne
    if start_event_id is None:
        start_event = ET.SubElement(process, 'startEvent')
        start_event_id = "StartEvent_1"
        start_event.set('id', start_event_id)
        start_event.set('name', "Start")
        
        elements_info.append({
            'id': start_event_id,
            'element_type': 'startEvent',
            'x': x_position,
            'y': y_position
        })
        
        last_id = start_event_id
        last_x = x_position + 36
        x_position += 100
    
    # Dodaj bramkę równoległą na początku, jeśli mamy więcej niż jedno wejście
    parallel_gateway_id = None
    if len(start_inputs) > 1:
        parallel_gateway_id = "ParallelGateway_Start"
        parallel_gateway = ET.SubElement(process, 'parallelGateway')
        parallel_gateway.set('id', parallel_gateway_id)
        parallel_gateway.set('name', "AND")
        
        elements_info.append({
            'id': parallel_gateway_id,
            'element_type': 'parallelGateway',
            'x': x_position,
            'y': y_position
        })
        
        flow_id = f"Flow_{last_id}_{parallel_gateway_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', last_id)
        flow.set('targetRef', parallel_gateway_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': last_id,
            'targetRef': parallel_gateway_id,
            'sourceX': last_x,
            'sourceY': y_position + 18,
            'targetX': x_position,
            'targetY': y_position + 18
        })
        
        gateway_id = parallel_gateway_id
        gateway_x = x_position + 50
        x_position += 100
    else:
        gateway_id = last_id
        gateway_x = last_x
    
    # Dodaj zadania dla danych wejściowych
    input_tasks = []
    task_positions = []
    
    # Najpierw utwórz wszystkie zadania wejściowe
    y_offset = -100
    for i, (input_id, input_name) in enumerate(start_inputs):
        # Pomijamy dane wejściowe, które zostały użyte jako zdarzenie początkowe
        if start_event_id and start_event_id == f"StartEvent_{input_id}":
            continue
            
        task_id = f"Task_{input_id}"
        task = ET.SubElement(process, 'userTask')
        task.set('id', task_id)
        task.set('name', f"Provide {input_name}")
        input_tasks.append(task_id)
        
        # Rozmieść zadania pionowo, jeśli jest ich więcej niż jedno
        task_y = y_position + y_offset if len(start_inputs) > 1 else y_position - 22
        y_offset += 100  # Zwiększ odstęp dla kolejnego zadania
        
        elements_info.append({
            'id': task_id,
            'element_type': 'userTask',
            'x': x_position,
            'y': task_y
        })
        
        task_positions.append((task_id, x_position + 100, task_y + 40))
    
    # Teraz połącz bramkę z zadaniami
    for task_id, _, task_y in task_positions:
        flow_id = f"Flow_{gateway_id}_{task_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', gateway_id)
        flow.set('targetRef', task_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': gateway_id,
            'targetRef': task_id,
            'sourceX': gateway_x,
            'sourceY': y_position + 25,
            'targetX': x_position,
            'targetY': task_y
        })
    
    # Przesuń pozycję X dla kolejnych elementów
    x_position += 150
    
    # Dodaj bramkę łączącą, jeśli mamy więcej niż jedno wejście
    if len(input_tasks) > 1:
        join_gateway_id = "ParallelGateway_Join"
        join_gateway = ET.SubElement(process, 'parallelGateway')
        join_gateway.set('id', join_gateway_id)
        join_gateway.set('name', "AND")
        
        elements_info.append({
            'id': join_gateway_id,
            'element_type': 'parallelGateway',
            'x': x_position,
            'y': y_position
        })
        
        # Połącz wszystkie zadania wejściowe z bramką łączącą
        for task_id, task_x, task_y in task_positions:
            flow_id = f"Flow_{task_id}_{join_gateway_id}"
            flow = ET.SubElement(process, 'sequenceFlow')
            flow.set('id', flow_id)
            flow.set('sourceRef', task_id)
            flow.set('targetRef', join_gateway_id)
            
            elements_info.append({
                'id': flow_id,
                'sourceRef': task_id,
                'targetRef': join_gateway_id,
                'sourceX': task_x,
                'sourceY': task_y,
                'targetX': x_position,
                'targetY': y_position + 25
            })
        
        last_id = join_gateway_id
        last_x = x_position + 50
        x_position += 100
    elif len(input_tasks) == 1:
        # Jeśli mamy tylko jedno zadanie wejściowe, ustaw je jako ostatnie
        last_id = input_tasks[0]
        last_x = task_positions[0][1]
    
    # Dodaj zadania dla decyzji
    decision_tasks = []
    
    # Jeśli mamy więcej niż jedną decyzję początkową, dodaj bramkę równoległą
    if len(start_decisions) > 1:
        parallel_gateway_id = "ParallelGateway_Decisions"
        parallel_gateway = ET.SubElement(process, 'parallelGateway')
        parallel_gateway.set('id', parallel_gateway_id)
        parallel_gateway.set('name', "AND")
        
        elements_info.append({
            'id': parallel_gateway_id,
            'element_type': 'parallelGateway',
            'x': x_position,
            'y': y_position
        })
        
        flow_id = f"Flow_{last_id}_{parallel_gateway_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', last_id)
        flow.set('targetRef', parallel_gateway_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': last_id,
            'targetRef': parallel_gateway_id,
            'sourceX': last_x,
            'sourceY': y_position + 18,
            'targetX': x_position,
            'targetY': y_position + 18
        })
        
        gateway_id = parallel_gateway_id
        gateway_x = x_position + 50
        x_position += 100
    else:
        gateway_id = last_id
        gateway_x = last_x
    
    # Utwórz wszystkie zadania decyzyjne
    decision_positions = []
    y_offset = -100
    
    for i, (decision_id, decision_name) in enumerate(start_decisions):
        # Dodaj bramkę decyzyjną przed zadaniem decyzyjnym
        exclusive_gateway_id = f"ExclusiveGateway_{decision_id}"
        exclusive_gateway = ET.SubElement(process, 'exclusiveGateway')
        exclusive_gateway.set('id', exclusive_gateway_id)
        exclusive_gateway.set('name', "XOR")
        
        # Rozmieść bramki pionowo, jeśli jest ich więcej niż jedna
        gateway_y = y_position + y_offset if len(start_decisions) > 1 else y_position
        
        elements_info.append({
            'id': exclusive_gateway_id,
            'element_type': 'exclusiveGateway',
            'x': x_position,
            'y': gateway_y
        })
        
        # Połącz główną bramkę z bramką decyzyjną
        flow_id = f"Flow_{gateway_id}_{exclusive_gateway_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', gateway_id)
        flow.set('targetRef', exclusive_gateway_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': gateway_id,
            'targetRef': exclusive_gateway_id,
            'sourceX': gateway_x,
            'sourceY': y_position + 25,
            'targetX': x_position,
            'targetY': gateway_y + 25
        })
        
        # Dodaj zadanie decyzyjne
        task_id = f"Task_{decision_id}"
        task = ET.SubElement(process, 'businessRuleTask')
        task.set('id', task_id)
        decision_tasks.append(task_id)
        
        # Określ nazwę zadania na podstawie typu wyjściowego
        output_type = None
        if decision_id in refined_model.decision_tables:
            output_type = get_output_type(refined_model.decision_tables[decision_id])
        
        if output_type == "number":
            verb = VERB_CALCULATE[0]  # Użyj pierwszego czasownika z listy
            task.set('name', f"{verb} {decision_name}")
        elif output_type in ["boolean", "string", "enum"]:
            verb = VERB_DECIDE[0]  # Użyj pierwszego czasownika z listy
            task.set('name', f"{verb} {decision_name}")
        else:
            # Domyślnie użyj "Decide"
            task.set('name', f"Decide {decision_name}")
        
        task_x = x_position + 100
        task_y = gateway_y - 22
        
        elements_info.append({
            'id': task_id,
            'element_type': 'businessRuleTask',
            'x': task_x,
            'y': task_y
        })
        
        # Połącz bramkę decyzyjną z zadaniem
        flow_id = f"Flow_{exclusive_gateway_id}_{task_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', exclusive_gateway_id)
        flow.set('targetRef', task_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': exclusive_gateway_id,
            'targetRef': task_id,
            'sourceX': x_position + 50,
            'sourceY': gateway_y + 25,
            'targetX': task_x,
            'targetY': task_y + 40
        })
        
        # Dodaj bramkę łączącą po zadaniu decyzyjnym
        join_exclusive_id = f"ExclusiveGateway_Join_{decision_id}"
        join_exclusive = ET.SubElement(process, 'exclusiveGateway')
        join_exclusive.set('id', join_exclusive_id)
        join_exclusive.set('name', "XOR")
        
        join_x = task_x + 150
        
        elements_info.append({
            'id': join_exclusive_id,
            'element_type': 'exclusiveGateway',
            'x': join_x,
            'y': gateway_y
        })
        
        # Połącz zadanie z bramką łączącą
        flow_id = f"Flow_{task_id}_{join_exclusive_id}"
        flow = ET.SubElement(process, 'sequenceFlow')
        flow.set('id', flow_id)
        flow.set('sourceRef', task_id)
        flow.set('targetRef', join_exclusive_id)
        
        elements_info.append({
            'id': flow_id,
            'sourceRef': task_id,
            'targetRef': join_exclusive_id,
            'sourceX': task_x + 100,
            'sourceY': task_y + 40,
            'targetX': join_x,
            'targetY': gateway_y + 25
        })
        
        # Zapisz pozycję bramki łączącej dla późniejszego użycia
        decision_positions.append((join_exclusive_id, join_x + 50, gateway_y + 25))
        
        # Zwiększ offset dla kolejnej decyzji
        y_offset += 200
    
    # Dodaj bramkę łączącą dla wszystkich decyzji, jeśli jest ich więcej niż jedna
    if len(start_decisions) > 1:
        join_gateway_id = "ParallelGateway_Join_Decisions"
        join_gateway = ET.SubElement(process, 'parallelGateway')
        join_gateway.set('id', join_gateway_id)
        join_gateway.set('name', "AND")
        
        x_position = max(pos[1] for pos in decision_positions) + 100
        
        elements_info.append({
            'id': join_gateway_id,
            'element_type': 'parallelGateway',
            'x': x_position,
            'y': y_position
        })
        
        # Połącz wszystkie bramki łączące decyzji z główną bramką łączącą
        for gateway_id, gateway_x, gateway_y in decision_positions:
            flow_id = f"Flow_{gateway_id}_{join_gateway_id}"
            flow = ET.SubElement(process, 'sequenceFlow')
            flow.set('id', flow_id)
            flow.set('sourceRef', gateway_id)
            flow.set('targetRef', join_gateway_id)
            
            elements_info.append({
                'id': flow_id,
                'sourceRef': gateway_id,
                'targetRef': join_gateway_id,
                'sourceX': gateway_x,
                'sourceY': gateway_y,
                'targetX': x_position,
                'targetY': y_position + 25
            })
        
        last_id = join_gateway_id
        last_x = x_position + 50
        x_position += 100
    elif len(start_decisions) == 1:
        # Jeśli mamy tylko jedną decyzję, użyj jej bramki łączącej jako ostatniego elementu
        last_id = decision_positions[0][0]
        last_x = decision_positions[0][1]
        x_position = last_x + 50
    
    # Dodaj zdarzenie końcowe
    end_event = ET.SubElement(process, 'endEvent')
    end_event_id = "EndEvent_1"
    end_event.set('id', end_event_id)
    
    # Jeśli zdarzenie początkowe było zdarzeniem komunikatu, utwórz odpowiednie zdarzenie końcowe
    if start_event_id and start_event_id.startswith("StartEvent_"):
        for decision_id, decision_name in refined_model.decisions:
            if not any(tgt == decision_id for _, tgt in refined_model.information_requirements):
                end_event.set('name', f"{decision_name} sent")
                break
    else:
        end_event.set('name', "End")
    
    elements_info.append({
        'id': end_event_id,
        'element_type': 'endEvent',
        'x': x_position,
        'y': y_position
    })
    
    flow_id = f"Flow_{last_id}_{end_event_id}"
    flow = ET.SubElement(process, 'sequenceFlow')
    flow.set('id', flow_id)
    flow.set('sourceRef', last_id)
    flow.set('targetRef', end_event_id)
    
    elements_info.append({
        'id': flow_id,
        'sourceRef': last_id,
        'targetRef': end_event_id,
        'sourceX': last_x,
        'sourceY': y_position + 18,
        'targetX': x_position,
        'targetY': y_position + 18
    })
    
    # Dodaj elementy BPMNDI dla wizualizacji
    create_bpmndi_elements(process, bpmn_root, elements_info)
    
    # Zapisz do pliku
    if output_path is None:
        output_path = "output/generated_bpmn.bpmn"
    
    # Upewnij się, że katalog istnieje
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    xml_string = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_string += ET.tostring(bpmn_root, encoding='unicode', method='xml')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(xml_string)
    
    return output_path

def create_bpmndi_elements(process_element, bpmn_root, elements_info):
    """
    Tworzy elementy BPMNDI dla wizualizacji.
    
    Args:
        process_element: Element procesu
        bpmn_root: Korzeń dokumentu BPMN
        elements_info: Informacje o elementach
    """
    bpmndi = ET.SubElement(bpmn_root, 'bpmndi:BPMNDiagram')
    bpmndi.set('id', 'BPMNDiagram_1')
    
    plane = ET.SubElement(bpmndi, 'bpmndi:BPMNPlane')
    plane.set('id', 'BPMNPlane_1')
    plane.set('bpmnElement', 'Process_1')
    
    for element in elements_info:
        try:
            element_type = element.get('element_type', '')
            
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
                
            elif element_type in ['exclusiveGateway', 'parallelGateway']:
                shape = ET.SubElement(plane, 'bpmndi:BPMNShape')
                shape.set('id', f"{element['id']}_di")
                shape.set('bpmnElement', element['id'])
                
                bounds = ET.SubElement(shape, 'dc:Bounds')
                bounds.set('x', str(element['x']))
                bounds.set('y', str(element['y']))
                bounds.set('width', '50')
                bounds.set('height', '50')
                
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

def convert_dmn_to_bpmn_model(dmn_model, output_path=None):
    """
    Konwertuje model DMN na model BPMN.
    
    Args:
        dmn_model (DMNModel): Model DMN
        output_path (str): Ścieżka do pliku wyjściowego BPMN
        
    Returns:
        str: Ścieżka do wygenerowanego pliku BPMN
    """
    try:
        # Utworzenie modelu BPMN
        bpmn_path = create_bpmn_from_dmn(dmn_model, output_path)
        
        print(f"Successfully converted to {bpmn_path}")
        return bpmn_path
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return None