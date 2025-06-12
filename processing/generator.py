import logging
from pathlib import Path
from processing.extractor import extract_dmn_model
from processing.mapper import map_dmn_to_bpmn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_bpmn_from_dmn(dmn_path: str, output_path: str):
    """Generate a BPMN model from a DMN file."""
    logger.info(f"Generating BPMN from DMN file: {dmn_path}")
    dmn_model = extract_dmn_model(Path(dmn_path))

    # Print the extracted model
    logger.info("Extracted DMN model:")
    logger.info(f"Decisions: {len(dmn_model.decisions)}")
    for decision_id, decision_name in dmn_model.decisions:
        logger.info(f"  - {decision_id}: {decision_name}")

    logger.info(f"Input Data: {len(dmn_model.input_data)}")
    for input_id, input_name in dmn_model.input_data:
        logger.info(f"  - {input_id}: {input_name}")

    logger.info(f"Business Knowledge: {len(dmn_model.business_knowledge)}")
    for bkm_id, bkm_name in dmn_model.business_knowledge:
        logger.info(f"  - {bkm_id}: {bkm_name}")

    logger.info(f"Information Requirements: {len(dmn_model.information_requirements)}")
    for src, tgt in dmn_model.information_requirements:
        logger.info(f"  - {src} -> {tgt}")

    logger.info("Mapping DMN to BPMN")
    bpmn_graph = map_dmn_to_bpmn(dmn_model)

    # Export BPMN file
    output_file = str(Path(output_path) / "generated_from_dmn.bpmn")
    logger.info(f"Exporting BPMN to: {output_file}")
    bpmn_graph.export_xml_file(str(Path(output_path)), "/generated_from_dmn.bpmn")

    return output_file


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent.parent
    dmn_path = base_dir / "event_logs" / "d1.dmn"
    output_path = base_dir / "output"
    generate_bpmn_from_dmn(str(dmn_path), str(output_path))
    print("BPMN generation completed successfully.")