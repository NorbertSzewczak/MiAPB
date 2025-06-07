import argparse
from pathlib import Path
from processing.dmn_to_bpmn import convert_dmn_to_bpmn

def main():
    """
    Główna funkcja generatora BPMN z DMN.
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
    
    result = convert_dmn_to_bpmn(input_path, output_path)
    
    if result:
        print(f"Successfully generated BPMN model: {result}")
        return 0
    else:
        print("Failed to generate BPMN model")
        return 1

if __name__ == "__main__":
    exit(main())