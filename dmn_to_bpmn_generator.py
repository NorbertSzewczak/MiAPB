import argparse
import os
from pathlib import Path
from processing.extractor import extract_dmn_model
from processing.dmn_to_bpmn import convert_dmn_to_bpmn_model

def main():
    """
    Główna funkcja generatora BPMN z DMN.
    Implementuje algorytm opisany w artykule.
    """
    parser = argparse.ArgumentParser(description='Generate BPMN model from DMN model')
    parser.add_argument('input', help='Path to DMN file (relative to project root or absolute)')
    parser.add_argument('-o', '--output', help='Path to output BPMN file (relative to project root or absolute)')
    
    args = parser.parse_args()
    
    # Konwersja ścieżek na absolutne
    project_root = Path(__file__).parent
    input_path = project_root / args.input if not os.path.isabs(args.input) else Path(args.input)
    
    if not input_path.exists():
        print(f"Error: Input file {input_path} does not exist")
        return 1
    
    if args.output:
        output_path = project_root / args.output if not os.path.isabs(args.output) else Path(args.output)
    else:
        output_path = input_path.with_suffix('.bpmn')
    
    # Upewnij się, że katalog wyjściowy istnieje
    os.makedirs(output_path.parent, exist_ok=True)
    
    # 1. Ekstrakcja modelu DMN
    print(f"Extracting DMN model from {input_path}")
    dmn_model = extract_dmn_model(input_path)
    
    # 2. Konwersja DMN na BPMN
    print(f"Converting DMN model to BPMN")
    result = convert_dmn_to_bpmn_model(dmn_model, str(output_path))
    
    if result:
        print(f"Successfully generated BPMN model: {result}")
        return 0
    else:
        print("Failed to generate BPMN model")
        return 1

if __name__ == "__main__":
    exit(main())