# HVAC Model Context Protocol

## Overview

The HVAC Model Context Protocol provides a structured framework for LLMs to consistently reason about HVAC systems and point mappings, enhancing accuracy and explainability in Building Management System (BMS) point classification and grouping.

Version: 1.0.0

## Installation

You can install the package directly from the source:

```bash
git clone https://github.com/your-org/hvac-model-context-protocol.git
cd hvac-model-context-protocol
pip install -e .
```

## Components

### Core Components

- **Ontology** (`ontology.py`): Hierarchical representation of HVAC systems, components, and relationships.
- **Knowledge Base** (`kb.py`): Repository of specific facts, abbreviations, naming conventions, and known patterns.
- **Reasoning Templates** (`templates.py`): Standardized step-by-step procedures for common tasks like point analysis and group verification.
- **Protocol Engine** (`engine.py`): Core engine that manages protocol context creation, ontology and KB access, and integration with the reasoning engine.

### Utilities

- **Text Processing** (`utils/text_processing.py`): Utilities for processing and analyzing point names.
- **Validation** (`utils/validation.py`): Validation functions for point names, reasoning results, and protocol context.

### Examples

- **Integration Example** (`examples/integration_example.py`): Example showing how to integrate the protocol with existing reasoning functions.

## Usage

### Basic Usage

```python
from hvac_mcp import ProtocolEngine

# Initialize the protocol engine
engine = ProtocolEngine()

# Generate context for point name analysis
points = ["AHU-1.SA-TEMP", "AHU-1.RA-TEMP"]
context = engine.generate_context(points, "point_name_analysis")

# Use the context in your LLM prompt
prompt = f"{context}\n## USER PROMPT\nAnalyze the following point: \"{points[0]}\"\n"

# Call your LLM with the enhanced prompt
response = call_llm_with_prompt(prompt)

# Extract structured reasoning from the response
reasoning = engine.extract_reasoning_from_response(response, "point_name_analysis")
```

### Integration with Existing Code

To integrate the protocol with your reasoning engine:

1. Import the protocol engine in your reasoning module:
   ```python
   from hvac_mcp import ProtocolEngine
   
   protocol_engine = ProtocolEngine()
   ```

2. Update reasoning functions to use the protocol context:
   ```python
   def reason_device_type_from_prefix(prefix, similar_points=None):
       # Generate optimized protocol context
       points_to_analyze = similar_points or [prefix]
       protocol_context = protocol_engine.generate_context(
           points_to_analyze,
           "point_name_analysis"
       )
       
       # Combine protocol context with the user prompt
       prompt = f"{protocol_context}\n## USER PROMPT\nAnalyze the following point prefix: \"{prefix}\"\n"
       
       # Call LLM with the enhanced prompt
       response = call_llm_with_prompt(prompt)
       
       # Extract structured reasoning
       reasoning = protocol_engine.extract_reasoning_from_response(
           response,
           "point_name_analysis"
       )
       
       # Return enhanced result
       return {
           "device_type": reasoning["device_type"],
           "confidence": reasoning["confidence_score"],
           "reasoning": reasoning["steps_followed"]
       }
   ```

## Features

### Context Optimization

The protocol engine dynamically selects the most relevant parts of the ontology and knowledge base based on the input points, ensuring that only the necessary context is included in the LLM prompt. This optimization helps to:

- Reduce token usage
- Focus the LLM on the most relevant information
- Improve reasoning consistency

### Structured Reasoning Templates

The protocol includes standardized reasoning templates for common tasks:

- **Point Name Analysis**: Breaking down point names into components, identifying system types, and classifying points.
- **Group Verification**: Validating that a group of points belongs to the same device type.
- **Ambiguity Resolution**: Handling uncertain or conflicting classifications.
- **Time-Based Reasoning**: Using historical data to enhance classification.

### Reasoning Extraction

The protocol engine can extract structured reasoning from LLM responses, making it easier to:

- Validate that all required reasoning steps were followed
- Extract specific information like device types and confidence scores
- Identify where reasoning might have gone wrong

## Customization

### Custom Ontology and KB

You can provide custom ontology and knowledge base files when initializing the protocol engine:

```python
engine = ProtocolEngine(
    ontology_path="path/to/custom_ontology.json",
    kb_path="path/to/custom_kb.json"
)
```

### Extending the Protocol

To add new reasoning templates or enhance existing ones, modify the templates in `templates.py`.

## Development Roadmap

### Next Steps (Version 1.1.0)

- Implement dynamic context optimization strategy
- Develop core context injection mechanism
- Begin ambiguity resolution implementation

### Future Enhancements

- Protocol handlers for reasoning extraction and validation
- Security validation layer
- Error handling framework and fallbacks
- UI components for protocol visibility
- Ambiguity visualization
- Feedback collection mechanism
- Automated KB update mechanism

## Running the Examples

To run the integration example:

```bash
cd hvac-model-context-protocol
python examples/integration_example.py
```

## License

Distributed under the MIT License. See `LICENSE` for more information. 