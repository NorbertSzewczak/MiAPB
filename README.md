# DMN to BPMN Generator

A BPMN model generator based on DMN models according to the algorithm described in the article "Proposal of a Method for Creating a BPMN Model based on the Data Extracted from a DMN Model".

## Overview

This project implements an algorithm for automatically generating BPMN (Business Process Model and Notation) models from DMN (Decision Model and Notation) models. The algorithm analyzes the structure of a DMN model, including decisions, input data, business knowledge models, and their relationships, and creates a corresponding BPMN process diagram.

## Requirements

- Python 3.6+
- Libraries listed in `requirements.txt`

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/MiAPB.git
cd MiAPB
```

2. Install required libraries:
```
pip install -r requirements.txt
```

## Usage

### Generating a BPMN model from a DMN model

```python
from processing.generator import generate_bpmn_from_dmn

# Generate BPMN from DMN file
dmn_path = "event_logs/d1.dmn"
output_path = "output"
bpmn_file = generate_bpmn_from_dmn(dmn_path, output_path)
```

## Project Structure

- `models/` - directory containing model definitions
  - `dmn_model.py` - DMN model class definition with support for decisions, input data, and requirements
- `processing/` - directory containing processing modules
  - `extractor.py` - module for extracting DMN models from XML files
  - `mapper.py` - module implementing the DMN to BPMN mapping algorithm
  - `generator.py` - high-level module for generating BPMN from DMN models
- `event_logs/` - directory containing sample DMN files and event logs
- `output/` - directory for generated BPMN files

## Algorithm

The DMN to BPMN mapping algorithm consists of the following steps:

1. Extraction of the DMN model from the XML file
2. Analysis of the decision graph to determine decision levels and dependencies
3. Identification of initial elements (decisions and input data)
4. Mapping input data to appropriate BPMN elements (start events, user tasks, etc.)
5. Mapping decisions to business rule tasks
6. Adding logical gateways (AND, XOR) for parallel and exclusive flows
7. Connecting elements sequentially according to dependencies in the DMN model
8. Creating intermediate elements for non-start inputs
9. Positioning elements based on their level in the decision flow
10. Generating the final BPMN model

## Features

The current implementation includes:

- Dynamic positioning of elements based on their level in the decision flow
- Intelligent mapping of input data to appropriate BPMN elements based on context
- Automatic addition of gateways for decisions with multiple inputs or outputs
- Support for business knowledge models and knowledge sources
- Handling of redundant information requirements