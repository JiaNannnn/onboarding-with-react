# Resources Analysis for BMS to EnOS Onboarding Tool

## Overview

This document provides an analysis of the resources files used for ontology and mapping in the BMS to EnOS Onboarding Tool. The focus is on understanding how these resources are integrated into the application, their content, and recommendations for improvement.

## Resources Files

The following resource definition files have been identified in the project:

| File | Size | Description |
|------|------|-------------|
| `new_resources.json` | 130,357 bytes | Enhanced resource definitions |
| `resources.json` | 79,345 bytes | Original resource definitions |
| `enos.json` | 43,325 bytes | EnOS-specific definitions |
| `quantities.json` | 41,531 bytes | Physical quantity definitions |
| `entities.json` | 18,358 bytes | Entity type definitions |
| `status.json` | 11,066 bytes | Status values and states |
| `points.json` | 2,415 bytes | Point type definitions |

## Current Integration

The `ResourceOntologyManager` class in `bms_onboarding/agents/tagging_agent/tagging_agent.py` is responsible for loading and managing access to the resource ontology. The class attempts to load `new_resources.json` from several possible locations:

```python
possible_paths = [
    "backend/data/defs/new_resources.json",  # Local dev environment
    "data/defs/new_resources.json",          # Relative to Python execution
    "/app/data/defs/new_resources.json"      # Container environment
]
```

This manager is used by the `TaggingAgent` to apply standardized tags and metadata to BMS points based on the resource ontology.

There's also a reference to `resources.json` in `backend/src/core/data/defs/standard_definitions.py`, which suggests that the backend may be using the original resource definitions file.

## Content Analysis

### `new_resources.json`

This file contains an expanded ontology of resources organized by categories, with detailed descriptions, examples, and hierarchical relationships. The structure is:

```
{
    "<Category>": {
        "category": "<Category>",
        "description": "<Description>",
        "examples": ["<Example1>", "<Example2>", ...],
        "sub_resources": {
            "<SubResource>": {
                "description": "<Description>",
                "examples": ["<Example1>", "<Example2>", ...],
                "phenomenons": {
                    "<Phenomenon>": {
                        "description": "<Description>",
                        "aspects": {
                            "<Aspect>": {
                                "description": "<Description>"
                            },
                            ...
                        }
                    },
                    ...
                }
            },
            ...
        }
    },
    ...
}
```

The `Energy` category, for example, includes subcategories like `Electricity` with phenomena such as `Electric Power System`, which in turn has aspects like `Generation`, `Transmission`, etc.

### `resources.json`

This appears to be an earlier version of the resource definitions with a similar structure but less comprehensive content. The examples in this file use more abbreviated terminology compared to the more descriptive examples in `new_resources.json`.

## Integration with HVAC Ontology

Currently, there appears to be a gap between these generic resource definitions and the domain-specific HVAC equipment ontology that would be needed for effective BMS point processing. The resource files focus on general phenomena, quantities, and aspects, but lack specific information about:

1. HVAC equipment types and hierarchies
2. Standard point names for each equipment type
3. Component relationships within HVAC systems
4. Common naming patterns in BMS installations

## Recommendations

### 1. Extend Resource Ontology for HVAC Domain

Create a new `hvac_ontology.json` file that extends the resource definitions with HVAC-specific information:

```json
{
  "HVAC": {
    "category": "HVAC",
    "description": "Heating, Ventilation, and Air Conditioning systems and components",
    "equipment_types": {
      "Chiller": {
        "description": "Mechanical device that removes heat from a liquid via vapor-compression or absorption refrigeration cycle",
        "abbreviations": ["CH", "CH-SYS", "CHILLER", "CLR"],
        "components": ["Compressor", "Evaporator", "Condenser", "Expansion Valve"],
        "standard_points": [
          {
            "name": "ChwSt",
            "description": "Chilled Water Supply Temperature",
            "function": "sensor",
            "bacnet_type": "analog-input",
            "unit": "degrees-Celsius"
          },
          // Additional standard points
        ],
        "related_equipment": ["CHWP", "CWP", "CT"]
      },
      // Additional equipment types
    }
  }
}
```

### 2. Implement HVAC-specific Resource Manager

Create a specialized manager for HVAC resources:

```python
class HVACOntologyManager:
    """
    Manager for HVAC-specific ontology information.
    
    This class extends the generic ResourceOntologyManager with
    HVAC-specific knowledge about equipment, components, and points.
    """
    
    def __init__(self, 
                 hvac_ontology_file: str = None,
                 resource_manager: ResourceOntologyManager = None):
        """
        Initialize the HVACOntologyManager.
        
        Args:
            hvac_ontology_file: Path to the HVAC ontology file
            resource_manager: ResourceOntologyManager instance for general resources
        """
        self.resource_manager = resource_manager or ResourceOntologyManager()
        
        if hvac_ontology_file is None:
            # Default paths
            possible_paths = [
                "backend/data/defs/hvac_ontology.json",
                "data/defs/hvac_ontology.json",
                "/app/data/defs/hvac_ontology.json"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    hvac_ontology_file = path
                    break
                    
        self.hvac_ontology_file = hvac_ontology_file
        self.hvac_ontology = self._load_hvac_ontology()
    
    def get_equipment_type_info(self, equipment_type):
        """Get information about a specific equipment type"""
        
    def get_standard_points(self, equipment_type):
        """Get standard points for a specific equipment type"""
        
    def identify_equipment_type(self, point_name):
        """Identify equipment type from point name using pattern recognition"""
        
    def classify_point_function(self, point_name, bacnet_type):
        """Classify the function of a point based on name and BACnet type"""
```

### 3. Integrate with Tagging Agent

Modify the `TaggingAgent` to use both the general resource ontology and the HVAC-specific ontology:

```python
class TaggingAgent:
    """Agent for tagging and enhancing BMS points with metadata"""
    
    def __init__(self,
                 resource_manager: ResourceOntologyManager = None,
                 hvac_manager: HVACOntologyManager = None):
        """
        Initialize the TaggingAgent.
        
        Args:
            resource_manager: Optional ResourceOntologyManager instance.
            hvac_manager: Optional HVACOntologyManager instance.
        """
        self.resource_manager = resource_manager or ResourceOntologyManager()
        self.hvac_manager = hvac_manager or HVACOntologyManager(
            resource_manager=self.resource_manager
        )
        
    def process_points(self, points, equipment_type=None):
        """
        Process a list of BMS points and add tagging metadata.
        
        Args:
            points: List of BMS points to process
            equipment_type: Optional equipment type for context
            
        Returns:
            List of tagged points with metadata
        """
        tagged_points = []
        
        for point in points:
            # If equipment type not provided, try to identify it
            if not equipment_type:
                identified_type = self.hvac_manager.identify_equipment_type(point.point_name)
                if identified_type:
                    equipment_type = identified_type
            
            # Get standard points for this equipment type
            standard_points = self.hvac_manager.get_standard_points(equipment_type)
            
            # Classify point function
            function = self.hvac_manager.classify_point_function(
                point.point_name, point.point_type
            )
            
            # Apply tags based on both resource ontology and HVAC ontology
            tags = self._generate_tags(point, equipment_type, function)
            
            # Create tagged point
            tagged_point = TaggedBMSPoint.from_bms_point(
                point,
                tags=tags,
                equipment_type=equipment_type,
                function=function,
                # Additional metadata
            )
            
            tagged_points.append(tagged_point)
            
        return tagged_points
```

### 4. Consolidate Resource Files

Consider consolidating the different resource files into a more coherent structure:

1. `base_ontology.json` - General resource categories, phenomena, and quantities
2. `hvac_ontology.json` - HVAC-specific equipment, components, and relationships
3. `enos_mapping.json` - EnOS-specific mapping rules and definitions

This would simplify resource management and make the ontology easier to maintain and extend.

## Conclusion

The current resource files provide a good foundation for general resource classification but lack the HVAC domain-specific information needed for effective BMS point processing. By extending the ontology with HVAC-specific knowledge and implementing specialized managers, the application can more effectively identify equipment types, classify points, and generate accurate tags.

The draft HVAC ontology provided in the previous document (`HVAC_ONTOLOGY_DRAFT.md`) can serve as a starting point for the enhanced HVAC-specific resource definitions. This would significantly improve the accuracy of equipment grouping, point classification, and mapping to EnOS models.

---

*This analysis was performed by the HVAC/BMS/Cloud Domain Expert on March 20, 2025*