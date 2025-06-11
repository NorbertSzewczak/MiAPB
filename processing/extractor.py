import xml.etree.ElementTree as ET
from pathlib import Path
from models.dmn_model import DMNModel, DecisionTable

DMN_NAMESPACE = {'dmn': 'https://www.omg.org/spec/DMN/20191111/MODEL/'}

def get_absolute_path(relative_path):
    # Returns the absolute path based on the relative path
    return Path(relative_path).resolve()

def extract_dmn_structure(xml_file_path):
    # Loading the XML file
    try:
        print(f"Attempting to parse file: {xml_file_path}")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing XML file: {e}")
        print(f"File exists: {xml_file_path.exists()}")
        raise

    # Extracting decisions
    decisions = []
    for decision in root.findall('dmn:decision', DMN_NAMESPACE):
        decision_id = decision.get('id')
        decision_name = decision.get('name')
        decisions.append({'id': decision_id, 'name': decision_name})

    # Extracting input data
    input_data = []
    for input_element in root.findall('dmn:inputData', DMN_NAMESPACE):
        input_id = input_element.get('id')
        input_name = input_element.get('name')
        input_data.append({'id': input_id, 'name': input_name})

    # Returning decisions and input data
    return decisions, input_data

def extract_decision_table(decision_table_element):
    """Extracts a decision table from the DMN XML"""
    decision_table_id = decision_table_element.get('id')
    decision_table_name = decision_table_element.get('name')

    input_expressions = []
    for input_clause in decision_table_element.findall('dmn:input', DMN_NAMESPACE):
        input_expressions.append(input_clause.find('dmn:inputExpression', DMN_NAMESPACE).text)

    output_expressions = []
    for output_clause in decision_table_element.findall('dmn:output', DMN_NAMESPACE):
        # Try different ways to get the output expression
        output_expr = output_clause.find('dmn:outputExpression', DMN_NAMESPACE)
        if output_expr is not None and output_expr.text:
            output_expressions.append(output_expr.text)
        elif output_clause.get('name'):
            output_expressions.append(output_clause.get('name'))
        elif output_clause.get('label'):
            output_expressions.append(output_clause.get('label'))
        else:
            # Fallback to id if no other identifier is available
            output_expressions.append(output_clause.get('id', 'unknown'))

    rules = []
    for rule in decision_table_element.findall('dmn:rule', DMN_NAMESPACE):
        rule_dict = {}
        for input_entry in rule.findall('dmn:inputEntry', DMN_NAMESPACE):
            rule_dict[input_expressions[len(rule_dict)]] = input_entry.text
        for output_entry in rule.findall('dmn:outputEntry', DMN_NAMESPACE):
            rule_dict[output_expressions[len(rule_dict) - len(input_expressions)]] = output_entry.text
        rules.append(rule_dict)

    return DecisionTable(decision_table_id, decision_table_name, input_expressions, output_expressions, rules)

def extract_requirements(root, dmn_model, target):
    """Extracts the different types of requirements from the DMN XML"""
    for info_req in root.findall('.//{*}informationRequirement', DMN_NAMESPACE):
        source_element = info_req.find('.//{*}requiredDecision', DMN_NAMESPACE)
        if source_element is None:
            source_element = info_req.find('.//{*}requiredInput', DMN_NAMESPACE)
        if source_element is not None:
            source = source_element.get('href')[1:]
            dmn_model.add_information_requirement(source, target)
    for knowledge_req in root.findall('.//{*}knowledgeRequirement', DMN_NAMESPACE):
        source_element = knowledge_req.find('.//{*}requiredDecision', DMN_NAMESPACE)
        if source_element is None:
            source_element = knowledge_req.find('.//{*}requiredKnowledge', DMN_NAMESPACE)
        if source_element is not None:
            source = source_element.get('href')[1:]
            dmn_model.add_knowledge_requirement(source, target)

    for authority_req in root.findall('.//{*}authorityRequirement', DMN_NAMESPACE):
        source_element = authority_req.find('.//{*}requiredDecision', DMN_NAMESPACE)
        if source_element is None:
            source_element = authority_req.find('.//{*}requiredAuthority', DMN_NAMESPACE)
        if source_element is not None:
            source = source_element.get('href')[1:]
            dmn_model.add_authority_requirement(source, target)

def extract_dmn_model(xml_file_path: Path) -> DMNModel:
    """Extracts complete DMN model from XML file"""
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    print(f"Processing DMN file: {xml_file_path}")

    dmn_model = DMNModel()

    # Add error handling for XML parsing
    try:
        # Extract decisions
        for decision in root.findall('dmn:decision', DMN_NAMESPACE):
            decision_id = decision.get('id')
            decision_name = decision.get('name')
            dmn_model.add_decision(decision_id, decision_name)

            extract_requirements(decision, dmn_model, decision_id)

            # Extract decision table if exists
            decision_table = decision.find('.//dmn:decisionTable', DMN_NAMESPACE)
            if decision_table is not None:
                table = extract_decision_table(decision_table)
                dmn_model.add_decision_table(decision_id, table)
    except Exception as e:
        print(f"Error processing DMN file: {e}")
        raise

    # Extract input data
    for input_data in root.findall('dmn:inputData', DMN_NAMESPACE):
        input_id = input_data.get('id')
        input_name = input_data.get('name')
        dmn_model.add_input_data(input_id, input_name)

    # Extract business knowledge models
    for bkm in root.findall('dmn:businessKnowledgeModel', DMN_NAMESPACE):
        bkm_id = bkm.get('id')
        bkm_name = bkm.get('name')
        dmn_model.add_business_knowledge(bkm_id, bkm_name)
        extract_requirements(bkm, dmn_model, bkm_id)

    # Extract knowledge sources
    for ks in root.findall('dmn:knowledgeSource', DMN_NAMESPACE):
        ks_id = ks.get('id')
        ks_name = ks.get('name')
        dmn_model.add_knowledge_source(ks_id, ks_name)
        extract_requirements(ks, dmn_model, ks_id)

    return dmn_model

if __name__ == "__main__":
    current_dir = Path(__file__).parent.parent  # Go up one level from processing directory
    absolute_path = current_dir / "event_logs" / "d1.dmn"
    dmn_model = extract_dmn_model(absolute_path)

    print("Decisions:")
    for decision_id, decision_name in dmn_model.decisions:
        print(f"ID: {decision_id}, Name: {decision_name}")

    print("\nInput Data:")
    for input_id, input_name in dmn_model.input_data:
        print(f"ID: {input_id}, Name: {input_name}")

    print("\nBusiness Knowledge Models:")
    for bkm_id, bkm_name in dmn_model.business_knowledge:
        print(f"ID: {bkm_id}, Name: {bkm_name}")

    print("\nKnowledge Sources:")
    for ks_id, ks_name in dmn_model.knowledge_sources:
        print(f"ID: {ks_id}, Name: {ks_name}")

    print("\nInformation Requirements:")
    for source, target in dmn_model.information_requirements:
        print(f"Source: {source}, Target: {target}")

    print("\nKnowledge Requirements:")
    for source, target in dmn_model.knowledge_requirements:
        print(f"Source: {source}, Target: {target}")

    print("\nAuthority Requirements:")
    for source, target in dmn_model.authority_requirements:
        print(f"Source: {source}, Target: {target}")

    print("\nStart Decisions:")
    for decision_id, decision_name in dmn_model.get_start_decisions():
        print(f"ID: {decision_id}, Name: {decision_name}")

    print("\nStart Input Data:")
    for input_id, input_name in dmn_model.get_start_inputs():
        print(f"ID: {input_id}, Name: {input_name}")
