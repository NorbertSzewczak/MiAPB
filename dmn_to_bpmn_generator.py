import argparse
from pathlib import Path
from processing.extractor import extract_dmn_model
from processing.dmn_to_bpmn import convert_dmn_to_bpmn_model

def main():
    """
    Główna funkcja generatora BPMN z DMN.
    Implementuje algorytm opisany w artykule.
    """
    parser = argparse.ArgumentParser(description='Generate BPMN model from DMN model')
    parser.add_argument('input', help='Path to DMN file')
    parser.add_argument('-o', '--output', help='Path to output BPMN file')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = args.output
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return 1
    
    if output_path is None:
        output_path = input_path.with_suffix('.bpmn')
    
    # 1. Ekstrakcja modelu DMN
    print(f"Extracting DMN model from {input_path}")
    dmn_model = extract_dmn_model(input_path)
    
    # 2. Konwersja DMN na BPMN
    print(f"Converting DMN model to BPMN")
    result = convert_dmn_to_bpmn_model(dmn_model, output_path)
    
    if result:
        print(f"Successfully generated BPMN model: {result}")
        return 0
    else:
        print("Failed to generate BPMN model")
        return 1

if __name__ == "__main__":
    exit(main())