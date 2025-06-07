from models.dmn_model import DMNModel
from pathlib import Path
import os
import xml.etree.ElementTree as ET
from processing.extractor import extract_dmn_model

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
    refined_model = DMNModel()
    
    # Kopiowanie elementów
    for decision_id, decision_name in dmn_model.decisions:
        refined_model.add_decision(decision_id, decision_name)
    
    for input_id, input_name in dmn_model.input_data:
        refined_model.add_input_data(input_id, input_name)
    
    for bkm_id, bkm_name in dmn_model.business_knowledge:
        refined_model.add_business_knowledge(bkm_id, bkm_name)
    
    # Usuwanie redundantnych wymagań informacyjnych zgodnie z Definicją 4
    redundant_requirements = []
    
    # Identyfikacja redundantnych wymagań
    for i_src, i_tgt in dmn_model.information_requirements:
        # Sprawdzenie czy to połączenie od input data do decision
        if any(i_src == input_id for input_id, _ in dmn_model.input_data):
            # Sprawdzenie czy istnieje ścieżka od tego input data do innej decyzji
            for j_src, j_tgt in dmn_model.information_requirements:
                if i_src == j_src and i_tgt != j_tgt:
                    # Sprawdzenie czy istnieje relacja następstwa między decyzjami
                    if has_succession_relation(dmn_model, i_tgt, j_tgt):
                        redundant_requirements.append((j_src, j_tgt))
    
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

def has_succession_relation(dmn_model, decision1, decision2):
    """
    Sprawdza czy istnieje relacja następstwa między decyzjami.
    
    Args:
        dmn_model (DMNModel): Model DMN
        decision1 (str): ID pierwszej decyzji
        decision2 (str): ID drugiej decyzji
        
    Returns:
        bool: True jeśli istnieje relacja następstwa, False w przeciwnym przypadku
    """
    # Sprawdzenie bezpośredniego połączenia
    if (decision1, decision2) in dmn_model.information_requirements:
        return True
    
    # Sprawdzenie pośredniego połączenia (rekurencyjnie)
    for src, tgt in dmn_model.information_requirements:
        if src == decision1 and has_succession_relation(dmn_model, tgt, decision2):
            return True
    
    return False

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
    
    # Dodaj zadania dla danych wejściowych
    for input_id, input_name in start_inputs:
        # Pomijamy dane wejściowe, które zostały użyte jako zdarzenie początkowe
        if start_event_id and start_event_id == f"StartEvent_{input_id}":
            continue
            
        task_id = f"Task_{input_id}"
        task = ET.SubElement(process, 'userTask')
        task.set('id', task_id)
        task.set('name', f"Provide {input_name}")
        
        elements_info.append({
            'id': task_id,
            'element_type': 'userTask',
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
    
    # Dodaj zadania dla decyzji
    for decision_id, decision_name in start_decisions:
        task_id = f"Task_{decision_id}"
        task = ET.SubElement(process, 'businessRuleTask')
        task.set('id', task_id)
        
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
        
        elements_info.append({
            'id': task_id,
            'element_type': 'businessRuleTask',
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

def convert_dmn_to_bpmn(input_path, output_path=None):
    """
    Konwertuje plik DMN na plik BPMN.
    
    Args:
        input_path (str): Ścieżka do pliku DMN
        output_path (str): Ścieżka do pliku wyjściowego BPMN
        
    Returns:
        str: Ścieżka do wygenerowanego pliku BPMN
    """
    try:
        # Konwersja ścieżek na obiekty Path
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        if output_path is None:
            output_path = input_path.with_suffix('.bpmn')
        else:
            output_path = Path(output_path)
        
        # Ekstrakcja modelu DMN
        dmn_model = extract_dmn_model(input_path)
        
        # Utworzenie modelu BPMN
        bpmn_path = create_bpmn_from_dmn(dmn_model, str(output_path))
        
        print(f"Successfully converted to {bpmn_path}")
        return bpmn_path
        
    except Exception as e:
        print(f"Error during conversion: {str(e)}")
        import traceback
        print("Full traceback:")
        print(traceback.format_exc())
        return None

if __name__ == "__main__":
    # Przykładowe użycie
    input_file = r"C:\Users\lenovo\MiAPB\event_logs\d1.dmn"
    output_file = r"C:\Users\lenovo\MiAPB\output\generated_bpmn.bpmn"
    
    result = convert_dmn_to_bpmn(input_file, output_file)
    if result:
        print(f"Conversion completed successfully: {result}")
    else:
        print("Conversion failed")